from __future__ import annotations

import json
from dataclasses import dataclass
from html.parser import HTMLParser


DOCUMENT_PREFIX = "workforce-notes:v1:"
MAX_CONTENT_LENGTH = 100000
MAX_TAGS = 12
MAX_TAG_LENGTH = 32


@dataclass(frozen=True, slots=True)
class PersonalNoteDocument:
    content_format: str
    plain_text: str
    tags: tuple[str, ...]
    checklist_total: int
    checklist_completed: int


class _DocumentReader(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)

        self.parts: list[str] = []
        self.list_stack: list[tuple[str, bool]] = []
        self.ignored_stack: list[str] = []

        self.checklist_total = 0
        self.checklist_completed = 0

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        if tag in {
            "script",
            "style",
            "iframe",
            "object",
            "svg",
            "math",
        }:
            self.ignored_stack.append(tag)
            return

        if self.ignored_stack:
            return

        attributes = dict(attrs)

        if tag in {"ul", "ol"}:
            self.list_stack.append(
                (
                    tag,
                    tag == "ul"
                    and "data-checklist" in attributes,
                )
            )

        if tag == "li":
            self.parts.append("\n")

            if (
                self.list_stack
                and self.list_stack[-1][1]
            ):
                self.checklist_total += 1

                if attributes.get("data-checked") == "true":
                    self.checklist_completed += 1

        if tag in {
            "p",
            "div",
            "h1",
            "h2",
            "h3",
            "h4",
            "blockquote",
            "pre",
            "br",
        }:
            self.parts.append("\n")

        if tag == "img":
            alt = attributes.get("alt")

            if alt:
                self.parts.append(f" {alt} ")

    def handle_endtag(self, tag: str) -> None:
        if self.ignored_stack:
            if tag == self.ignored_stack[-1]:
                self.ignored_stack.pop()
            return

        if tag in {"ul", "ol"}:
            for index in range(
                len(self.list_stack) - 1,
                -1,
                -1,
            ):
                if self.list_stack[index][0] == tag:
                    del self.list_stack[index:]
                    break

        if tag in {
            "p",
            "div",
            "h1",
            "h2",
            "h3",
            "h4",
            "li",
            "ul",
            "ol",
            "blockquote",
            "pre",
        }:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self.ignored_stack:
            self.parts.append(data)

    def text(self) -> str:
        lines = [
            " ".join(line.split())
            for line in "".join(self.parts).splitlines()
        ]

        return "\n".join(
            line for line in lines if line
        ).strip()


def read_personal_document(
    content: str,
) -> PersonalNoteDocument:
    if len(content) > MAX_CONTENT_LENGTH:
        raise ValueError(
            "Note content must be at most 100,000 characters."
        )

    if not content.startswith(DOCUMENT_PREFIX):
        return PersonalNoteDocument(
            content_format="plain",
            plain_text=content,
            tags=(),
            checklist_total=0,
            checklist_completed=0,
        )

    try:
        document = json.loads(
            content[len(DOCUMENT_PREFIX):]
        )
    except (json.JSONDecodeError, RecursionError) as exc:
        raise ValueError(
            "The rich note document contains invalid JSON."
        ) from exc

    if not isinstance(document, dict):
        raise ValueError(
            "The rich note document must be an object."
        )

    if set(document) - {"version", "html", "tags"}:
        raise ValueError(
            "The rich note document contains unsupported fields."
        )

    if (
        type(document.get("version")) is not int
        or document["version"] != 1
    ):
        raise ValueError(
            "Unsupported rich note document version."
        )

    html = document.get("html")

    if not isinstance(html, str):
        raise ValueError(
            "The rich note document must contain HTML text."
        )

    supplied_tags = document.get("tags", [])

    if not isinstance(supplied_tags, list):
        raise ValueError(
            "Note tags must be a list."
        )

    if len(supplied_tags) > MAX_TAGS:
        raise ValueError(
            "A note can have at most 12 tags."
        )

    tags: list[str] = []
    seen: set[str] = set()

    for value in supplied_tags:
        if not isinstance(value, str):
            raise ValueError(
                "Every note tag must be text."
            )

        tag = value.strip()

        if not tag or len(tag) > MAX_TAG_LENGTH:
            raise ValueError(
                "Each tag must contain 1–32 characters."
            )

        normalized = tag.casefold()

        if normalized in seen:
            raise ValueError(
                "Note tags must be unique."
            )

        seen.add(normalized)
        tags.append(tag)

    reader = _DocumentReader()
    reader.feed(html)
    reader.close()

    return PersonalNoteDocument(
        content_format="rich",
        plain_text=reader.text(),
        tags=tuple(tags),
        checklist_total=reader.checklist_total,
        checklist_completed=reader.checklist_completed,
    )


def validate_personal_content(content: str) -> str:
    read_personal_document(content)
    return content


__all__ = [
    "DOCUMENT_PREFIX",
    "PersonalNoteDocument",
    "read_personal_document",
    "validate_personal_content",
]