"use client";

import {
  Archive,
  ArchiveRestore,
  ArrowDownUp,
  Bold,
  Check,
  CheckCircle2,
  CheckSquare,
  ChevronDown,
  Copy,
  Download,
  FileText,
  ImagePlus,
  Italic,
  Link2,
  List,
  ListOrdered,
  LoaderCircle,
  Lock,
  MoreHorizontal,
  Pin,
  PinOff,
  Plus,
  RefreshCcw,
  Save,
  Search,
  Share2,
  Sparkles,
  Tag,
  Trash2,
  Underline,
  X,
} from "lucide-react";

import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type KeyboardEvent as ReactKeyboardEvent,
} from "react";

import { NotesAttachments } from "@/components/notes/notes-attachments";
import { NoteLinkDialog } from "@/components/notes/note-link-dialog";
import { useNoteAutosave } from "@/lib/notes/use-note-autosave";
import { exportNoteText } from "@/lib/notes/export-note";
import { useWorkspace } from "@/contexts/workspace-context";

import {
  employeesService,
  type Employee,
} from "@/services/employees.service";

import {
  notesService,
  type NotePublic,
} from "@/services/notes-page.service";

const DOCUMENT_PREFIX = "workforce-notes:v1:";
const CONTENT_LIMIT = 100000;
const TITLE_LIMIT = 200;
const TAG_LIMIT = 12;
const TAG_LENGTH_LIMIT = 32;

type Filter = "all" | "pinned" | "checklists" | "archived";
type Sort = "updated" | "created" | "oldest" | "title";
type MobileView = "list" | "editor";

type NoteDocument = {
  version: 1;
  html: string;
  tags: string[];
};

type EditorFormats = {
  bold: boolean;
  italic: boolean;
  underline: boolean;
};

const EMPTY_FORMATS: EditorFormats = {
  bold: false,
  italic: false,
  underline: false,
};

function errorMessage(cause: unknown, fallback: string) {
  return cause instanceof Error && cause.message
    ? cause.message
    : fallback;
}

function escapeHTML(value: string) {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function plainTextToHTML(value: string) {
  if (!value) return "";

  return value
    .split(/\r?\n/)
    .map((line) => `<p>${escapeHTML(line) || "<br>"}</p>`)
    .join("");
}

function safeURL(value: string, image = false): string | null {
  try {
    const url = new URL(value.trim());

    const allowed = image
      ? ["https:", "http:"]
      : ["https:", "http:", "mailto:", "tel:"];

    if (!allowed.includes(url.protocol)) return null;
    if (url.username || url.password) return null;

    return url.href;
  } catch {
    return null;
  }
}

function sanitizeHTML(value: string): string {
  if (typeof document === "undefined") return "";

  const template = document.createElement("template");
  template.innerHTML = value;

  const allowed = new Set([
    "P", "DIV", "BR", "STRONG", "B", "EM", "I", "U",
    "S", "STRIKE", "H1", "H2", "H3", "H4", "UL", "OL",
    "LI", "A", "IMG", "BLOCKQUOTE", "PRE", "CODE",
    "HR", "SPAN", "INPUT",
  ]);

  const removeCompletely = new Set([
    "SCRIPT", "STYLE", "IFRAME", "OBJECT", "EMBED",
    "SVG", "MATH", "FORM", "BUTTON", "TEXTAREA",
    "SELECT", "TEMPLATE", "LINK", "META",
  ]);

  function clean(parent: Node) {
    for (const child of Array.from(parent.childNodes)) {
      if (child.nodeType === Node.COMMENT_NODE) {
        child.remove();
        continue;
      }

      if (!(child instanceof HTMLElement)) continue;

      if (removeCompletely.has(child.tagName)) {
        child.remove();
        continue;
      }

      clean(child);

      if (!allowed.has(child.tagName)) {
        child.replaceWith(...Array.from(child.childNodes));
        continue;
      }

      const href = child.getAttribute("href");
      const src = child.getAttribute("src");
      const alt = child.getAttribute("alt");
      const checked = child.getAttribute("data-checked");
      const checklist = child.hasAttribute("data-checklist");
      const inputType = child.getAttribute("type");
      const inputChecked =
        child instanceof HTMLInputElement && child.checked;
      const spanStyle = child.getAttribute("style") ?? "";

      for (const attribute of Array.from(child.attributes)) {
        child.removeAttribute(attribute.name);
      }

      if (child.tagName === "SPAN" && spanStyle) {
        const probe = document.createElement("span");
        probe.setAttribute("style", spanStyle);

        if (
          probe.style.fontWeight === "bold" ||
          Number(probe.style.fontWeight) >= 600
        ) {
          child.style.fontWeight = "700";
        }

        if (probe.style.fontStyle === "italic") {
          child.style.fontStyle = "italic";
        }

        if (
          probe.style.textDecoration.includes("underline") ||
          probe.style.textDecorationLine.includes("underline")
        ) {
          child.style.textDecoration = "underline";
        }
      }

      if (child.tagName === "A") {
        const url = href ? safeURL(href) : null;

        if (!url) {
          child.replaceWith(...Array.from(child.childNodes));
          continue;
        }

        child.setAttribute("href", url);
        child.setAttribute("target", "_blank");
        child.setAttribute("rel", "noopener noreferrer");
      }

      if (child.tagName === "IMG") {
        const url = src ? safeURL(src, true) : null;

        if (!url) {
          child.remove();
          continue;
        }

        child.setAttribute("src", url);
        child.setAttribute("alt", alt ?? "");
        child.setAttribute("loading", "lazy");
        child.setAttribute("referrerpolicy", "no-referrer");
      }

      if (child.tagName === "UL" && checklist) {
        child.setAttribute("data-checklist", "true");
      }

      if (child.tagName === "LI" && checked !== null) {
        child.setAttribute(
          "data-checked",
          checked === "true" ? "true" : "false",
        );
      }

      if (child.tagName === "INPUT") {
        if (
          inputType !== "checkbox" ||
          !child.closest("ul[data-checklist]")
        ) {
          child.remove();
          continue;
        }

        child.setAttribute("type", "checkbox");
        child.setAttribute("contenteditable", "false");
        child.setAttribute("aria-label", "Complete checklist item");

        const item = child.closest("li");

        if (
          item?.getAttribute("data-checked") === "true" ||
          inputChecked
        ) {
          child.setAttribute("checked", "");
          item?.setAttribute("data-checked", "true");
        } else {
          item?.setAttribute("data-checked", "false");
        }
      }
    }
  }

  clean(template.content);

  return template.innerHTML;
}

function normalizeTags(value: unknown): string[] {
  if (!Array.isArray(value)) return [];

  const result: string[] = [];

  for (const entry of value) {
    if (typeof entry !== "string") continue;

    const tag = entry.trim().slice(0, TAG_LENGTH_LIMIT);

    if (
      tag &&
      !result.some(
        (existing) => existing.toLowerCase() === tag.toLowerCase(),
      )
    ) {
      result.push(tag);
    }

    if (result.length === TAG_LIMIT) break;
  }

  return result;
}

function decodeDocument(content: string): NoteDocument {
  if (content.startsWith(DOCUMENT_PREFIX)) {
    try {
      const parsed: unknown = JSON.parse(
        content.slice(DOCUMENT_PREFIX.length),
      );

      if (
        parsed &&
        typeof parsed === "object" &&
        "version" in parsed &&
        parsed.version === 1 &&
        "html" in parsed &&
        typeof parsed.html === "string"
      ) {
        return {
          version: 1,
          html: sanitizeHTML(parsed.html),
          tags: normalizeTags("tags" in parsed ? parsed.tags : []),
        };
      }
    } catch {
      // Keep previously stored malformed content readable.
    }
  }

  return {
    version: 1,
    html: plainTextToHTML(content),
    tags: [],
  };
}

function encodeDocument(html: string, tags: string[]) {
  return (
    DOCUMENT_PREFIX +
    JSON.stringify({
      version: 1,
      html: sanitizeHTML(html),
      tags: normalizeTags(tags),
    } satisfies NoteDocument)
  );
}

function htmlText(html: string) {
  if (typeof document === "undefined") return "";

  const container = document.createElement("div");
  container.innerHTML = sanitizeHTML(html);

  container.querySelectorAll("br").forEach((br) => {
    br.replaceWith("\n");
  });

  container
    .querySelectorAll("p, div, h1, h2, h3, h4, li, blockquote")
    .forEach((block) => {
      block.append(document.createTextNode("\n"));
    });

  return (container.textContent ?? "")
    .replace(/[ \t]+/g, " ")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

function checklistProgress(html: string) {
  if (typeof document === "undefined") {
    return { total: 0, done: 0 };
  }

  const container = document.createElement("div");
  container.innerHTML = sanitizeHTML(html);

  const items = Array.from(
    container.querySelectorAll("ul[data-checklist] > li"),
  );

  return {
    total: items.length,
    done: items.filter(
      (item) => item.getAttribute("data-checked") === "true",
    ).length,
  };
}

function dateValue(value: string) {
  const result = new Date(value).getTime();
  return Number.isNaN(result) ? 0 : result;
}

function fullDate(value: string) {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) return "Unknown date";

  return date.toLocaleString(undefined, {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

function shortDate(value: string) {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) return "";

  const today = new Date();
  const yesterday = new Date();
  yesterday.setDate(yesterday.getDate() - 1);

  const time = date.toLocaleTimeString(undefined, {
    hour: "numeric",
    minute: "2-digit",
  });

  if (date.toDateString() === today.toDateString()) {
    return `Today, ${time}`;
  }

  if (date.toDateString() === yesterday.toDateString()) {
    return `Yesterday, ${time}`;
  }

  return date.toLocaleString(undefined, {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

function createdDate(value: string) {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) return "—";

  return date.toLocaleDateString(undefined, {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

export default function NotesPage() {
  const { workspaceId, user } = useWorkspace();

  return (
    <NotesContent
      key={`${workspaceId ?? "personal"}:${user?.id ?? "none"}`}
    />
  );
}

function NotesContent() {
  const {
    workspaceId,
    workspace,
    user,
    loading: contextLoading,
    workspaceLoading,
  } = useWorkspace();

  const [employee, setEmployee] = useState<Employee | null>(null);
  const [employeeError, setEmployeeError] = useState<string | null>(null);
  const [notes, setNotes] = useState<NotePublic[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const [title, setTitle] = useState("");
  const [html, setHTML] = useState("");
  const [tags, setTags] = useState<string[]>([]);

  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState<Filter>("all");
  const [sort, setSort] = useState<Sort>("updated");
  const [mobileView, setMobileView] = useState<MobileView>("list");

  const [loading, setLoading] = useState(true);
  const [pending, setPending] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const [menuOpen, setMenuOpen] = useState(false);
  const [addingTag, setAddingTag] = useState(false);
  const [tagDraft, setTagDraft] = useState("");
  const [formats, setFormats] = useState<EditorFormats>(EMPTY_FORMATS);
  const [linkOpen, setLinkOpen] = useState(false);
  const [linkURL, setLinkURL] = useState("");
  const [linkText, setLinkText] = useState("");

  const linkRangeRef = useRef<Range | null>(null);
  const linkTargetRef = useRef<HTMLAnchorElement | null>(null);

  const alive = useRef(false);
  const loadSequence = useRef(0);
  const actionLock = useRef(false);
  const selectedIdRef = useRef<string | null>(null);
  const editorRef = useRef<HTMLDivElement | null>(null);
  const htmlRef = useRef("");
  const savedRange = useRef<Range | null>(null);
  const menuRef = useRef<HTMLDivElement | null>(null);
  const tagInputRef = useRef<HTMLInputElement | null>(null);

  const resolving =
    contextLoading || Boolean(workspaceId && workspaceLoading);

  const hasScope = Boolean(user?.id);
  const busy = resolving || loading || pending !== null;
  const canCreate = hasScope && (!workspaceId || Boolean(employee));

  const selected = useMemo(
    () => notes.find((note) => note.id === selectedId) ?? null,
    [notes, selectedId],
  );

  const selectedDocument = useMemo(
    () =>
      selected
        ? decodeDocument(selected.content)
        : { version: 1 as const, html: "", tags: [] },
    [selected],
  );

  const dirty = Boolean(
    selected &&
      (
        title !== selected.title ||
        sanitizeHTML(html) !== selectedDocument.html ||
        JSON.stringify(tags) !== JSON.stringify(selectedDocument.tags)
      ),
  );

  const autosave = useNoteAutosave({
    workspaceId,
    noteId: selected?.id ?? null,
    title,
    content: encodeDocument(html, tags),
    dirty,
    enabled: hasScope && !resolving && !loading,
    onSaved(updated) {
      replaceNote(updated);

      setTitle((current) => {
        const normalized = current.trim() || "Untitled Note";

        return normalized === updated.title
          ? updated.title
          : current;
      });
    },
  });  

  const records = useMemo(
    () =>
      notes.map((note) => {
        const document = decodeDocument(note.content);

        return {
          note,
          document,
          text: htmlText(document.html),
          checklist: checklistProgress(document.html),
        };
      }),
    [notes],
  );

  const counts = useMemo(
    () => ({
      total: notes.length,
      pinned: notes.filter((note) => note.is_pinned).length,
      archived: notes.filter((note) => note.is_archived).length,
    }),
    [notes],
  );

  const filtered = useMemo(() => {
    const query = search.trim().toLowerCase();

    return records
      .filter(({ note, document, text, checklist }) => {
        if (filter === "archived") {
          if (!note.is_archived) return false;
        } else {
          if (note.is_archived) return false;
          if (filter === "pinned" && !note.is_pinned) return false;
          if (filter === "checklists" && checklist.total === 0) {
            return false;
          }
        }

        return (
          !query ||
          [note.title, text, ...document.tags]
            .join(" ")
            .toLowerCase()
            .includes(query)
        );
      })
      .sort((left, right) => {
        if (left.note.is_pinned !== right.note.is_pinned) {
          return left.note.is_pinned ? -1 : 1;
        }

        if (sort === "title") {
          return left.note.title.localeCompare(right.note.title);
        }

        if (sort === "created") {
          return (
            dateValue(right.note.created_at) -
            dateValue(left.note.created_at)
          );
        }

        if (sort === "oldest") {
          return (
            dateValue(left.note.updated_at) -
            dateValue(right.note.updated_at)
          );
        }

        return (
          dateValue(right.note.updated_at) -
          dateValue(left.note.updated_at)
        );
      });
  }, [records, search, filter, sort]);

  const currentProgress = useMemo(
    () => checklistProgress(html),
    [html],
  );

  const wordCount = useMemo(() => {
    const text = htmlText(html);
    return text ? text.split(/\s+/).length : 0;
  }, [html]);

  const showNote = useCallback((note: NotePublic | null) => {
    const document = note
      ? decodeDocument(note.content)
      : { html: "", tags: [] };

    selectedIdRef.current = note?.id ?? null;
    htmlRef.current = document.html;
    savedRange.current = null;

    setSelectedId(note?.id ?? null);
    setTitle(note?.title ?? "");
    setHTML(document.html);
    setTags(document.tags);
    setMenuOpen(false);
    setAddingTag(false);
    setTagDraft("");
    setFormats(EMPTY_FORMATS);

    if (editorRef.current) {
      editorRef.current.innerHTML = document.html;
    }
  }, []);

  useEffect(() => {
    alive.current = true;

    return () => {
      alive.current = false;
      loadSequence.current += 1;
      savedRange.current = null;
    };
  }, []);

  useEffect(() => {
    if (editorRef.current) {
      editorRef.current.innerHTML = htmlRef.current;
    }
  }, [selectedId]);

  useEffect(() => {
    if (addingTag) tagInputRef.current?.focus();
  }, [addingTag]);

  useEffect(() => {
    if (!success) return;

    const timer = window.setTimeout(() => setSuccess(null), 3500);
    return () => window.clearTimeout(timer);
  }, [success]);

  useEffect(() => {
    if (!dirty) return;

    function beforeUnload(event: BeforeUnloadEvent) {
      event.preventDefault();
      event.returnValue = "";
    }

    window.addEventListener("beforeunload", beforeUnload);

    return () => {
      window.removeEventListener("beforeunload", beforeUnload);
    };
  }, [dirty]);

  useEffect(() => {
    function rememberSelection() {
      const editor = editorRef.current;
      const selection = window.getSelection();

      if (
        !editor ||
        !selection ||
        selection.rangeCount === 0 ||
        !selection.anchorNode ||
        !selection.focusNode ||
        !editor.contains(selection.anchorNode) ||
        !editor.contains(selection.focusNode)
      ) {
        return;
      }

      savedRange.current = selection.getRangeAt(0).cloneRange();

      try {
        setFormats({
          bold: document.queryCommandState("bold"),
          italic: document.queryCommandState("italic"),
          underline: document.queryCommandState("underline"),
        });
      } catch {
        setFormats(EMPTY_FORMATS);
      }
    }

    document.addEventListener("selectionchange", rememberSelection);

    return () => {
      document.removeEventListener(
        "selectionchange",
        rememberSelection,
      );
    };
  }, []);

  useEffect(() => {
    if (!menuOpen) return;

    function outsideClick(event: PointerEvent) {
      if (
        event.target instanceof Node &&
        !menuRef.current?.contains(event.target)
      ) {
        setMenuOpen(false);
      }
    }

    function escape(event: KeyboardEvent) {
      if (event.key === "Escape") setMenuOpen(false);
    }

    document.addEventListener("pointerdown", outsideClick);
    document.addEventListener("keydown", escape);

    return () => {
      document.removeEventListener("pointerdown", outsideClick);
      document.removeEventListener("keydown", escape);
    };
  }, [menuOpen]);

  const load = useCallback(async () => {
    const sequence = ++loadSequence.current;

    if (resolving) {
      setLoading(true);
      return;
    }

    if (!user?.id) {
      setNotes([]);
      setEmployee(null);
      setEmployeeError(null);
      showNote(null);
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);
    setEmployeeError(null);

    try {
      const [employeeResult, notesResult] = await Promise.allSettled([
        workspaceId
          ? employeesService.list(workspaceId, {
              includeInactive: true,
            })
          : Promise.resolve({ employees: [] }),
        notesService.listMine(workspaceId, true),
      ]);

      if (
        !alive.current ||
        sequence !== loadSequence.current
      ) {
        return;
      }

      if (employeeResult.status === "fulfilled") {
        setEmployee(
          employeeResult.value.employees.find(
            (item) => item.user_id === user.id,
          ) ?? null,
        );
      } else {
        setEmployee(null);
        setEmployeeError(
          errorMessage(
            employeeResult.reason,
            "Unable to resolve your employee account.",
          ),
        );
      }

      if (notesResult.status === "rejected") {
        throw notesResult.reason;
      }

      const items = notesResult.value.items;

      const current =
        items.find((note) => note.id === selectedIdRef.current) ??
        [...items]
          .filter((note) => !note.is_archived)
          .sort((left, right) => {
            if (left.is_pinned !== right.is_pinned) {
              return left.is_pinned ? -1 : 1;
            }

            return (
              dateValue(right.updated_at) -
              dateValue(left.updated_at)
            );
          })[0] ??
        items[0] ??
        null;

      setNotes(items);
      showNote(current);
    } catch (cause) {
      if (
        alive.current &&
        sequence === loadSequence.current
      ) {
        setError(
          errorMessage(cause, "Unable to load notes. Try Refresh."),
        );
      }
    } finally {
      if (
        alive.current &&
        sequence === loadSequence.current
      ) {
        setLoading(false);
      }
    }
  }, [workspaceId, user?.id, resolving, showNote]);

  useEffect(() => {
    void load();

    return () => {
      loadSequence.current += 1;
    };
  }, [load]);

  function canDiscardDraft() {
    return true;
  }

  async function runAction(
    label: string,
    fallback: string,
    action: () => Promise<void>,
  ) {
    if (busy || !hasScope || actionLock.current) return;

    actionLock.current = true;
    setPending(label);
    setError(null);
    setSuccess(null);
    setMenuOpen(false);

    try {
      await autosave.flush();
      await action();
    } catch (cause) {
      if (alive.current) {
        setError(errorMessage(cause, fallback));
      }
    } finally {
      actionLock.current = false;

      if (alive.current) setPending(null);
    }
  }

  function replaceNote(updated: NotePublic) {
    setNotes((current) =>
      current.map((note) =>
        note.id === updated.id ? updated : note,
      ),
    );
  }

  async function openNote(note: NotePublic) {
    if (busy || !hasScope) return;

    if (note.id === selectedId) {
      setMobileView("editor");
      return;
    }

    if (!canDiscardDraft()) return;

    await runAction(
      "Opening note",
      "Unable to open this note.",
      async () => {
        const result = await notesService.getMine(
          workspaceId,
          note.id,
        );

        if (!alive.current) return;

        replaceNote(result);
        showNote(result);
        setMobileView("editor");
      },
    );
  }

  async function createNote() {
    if (busy || !canCreate || !canDiscardDraft()) return;

    await runAction(
      "Creating note",
      "Unable to create note.",
      async () => {
        const created = await notesService.createMine(
          workspaceId,
          {
            ...(workspaceId && employee
              ? { owner_employee_id: employee.id }
              : {}),
            title: "Untitled Note",
            content: "",
          },
        );

        if (!alive.current) return;

        setNotes((current) => [created, ...current]);
        setSearch("");
        setFilter("all");
        showNote(created);
        setMobileView("editor");
        setSuccess("Note created.");
      },
    );
  }

  async function saveNote() {
    if (!selected || busy || !hasScope) return;

    try {
      await autosave.flush();
    } catch {
      // The automatic-save error is displayed with a Retry button.
    }
  }

  async function togglePin() {
    if (!selected || busy) return;

    await runAction(
      selected.is_pinned ? "Unpinning note" : "Pinning note",
      "Unable to change the pin status.",
      async () => {
        const updated = await notesService.updateMine(
          workspaceId,
          selected.id,
          { is_pinned: !selected.is_pinned },
        );

        if (!alive.current) return;

        replaceNote(updated);
        setSuccess(
          updated.is_pinned ? "Note pinned." : "Note unpinned.",
        );
      },
    );
  }

  async function toggleArchive() {
    if (!selected || busy || !canDiscardDraft()) return;

    await runAction(
      selected.is_archived ? "Restoring note" : "Archiving note",
      "Unable to change the archive status.",
      async () => {
        const updated = await notesService.updateMine(
          workspaceId,
          selected.id,
          { is_archived: !selected.is_archived },
        );

        if (!alive.current) return;

        replaceNote(updated);
        showNote(updated);
        setFilter(updated.is_archived ? "archived" : "all");
        setSuccess(
          updated.is_archived ? "Note archived." : "Note restored.",
        );
      },
    );
  }

  async function duplicateNote() {
    if (
      !selected ||
      busy ||
      !canCreate ||
      !canDiscardDraft()
    ) {
      return;
    }

    await runAction(
      "Duplicating note",
      "Unable to duplicate note.",
      async () => {
        const original = {
          html,
          tags,
        };

        const created = await notesService.createMine(
          workspaceId,
          {
            ...(workspaceId && employee
              ? { owner_employee_id: employee.id }
              : {}),
            title: `${title.trim() || "Untitled Note"} (copy)`.slice(
              0,
              TITLE_LIMIT,
            ),
            content: encodeDocument(original.html, original.tags),
          },
        );

        if (!alive.current) return;

        setNotes((current) => [created, ...current]);
        setSearch("");
        setFilter("all");
        showNote(created);
        setMobileView("editor");
        setSuccess("Saved note duplicated.");
      },
    );
  }

  async function deleteNote() {
    if (!selected || busy) return;

    if (
      !window.confirm(
        `Delete "${selected.title}" permanently? This also discards its current draft and removes its attached files.`,
      )
    ) {
      return;
    }

    await runAction(
      "Deleting note",
      "Unable to delete note.",
      async () => {
        await notesService.deleteMine(workspaceId, selected.id);

        if (!alive.current) return;

        const remaining = notes.filter(
          (note) => note.id !== selected.id,
        );

        const next =
          filtered.find(
            (record) => record.note.id !== selected.id,
          )?.note ?? null;

        setNotes(remaining);
        showNote(next);

        if (!next) setMobileView("list");

        setSuccess("Note deleted.");
      },
    );
  }

  function refreshNotes() {
    if (busy || !hasScope) return;

    void runAction(
      "Refreshing notes",
      "Unable to refresh notes.",
      load,
    );
  }

  function changeFilter(next: Filter) {
    if (busy || next === filter) return;

    setFilter(next);
    setMobileView("list");
  }

  function syncEditor() {
    if (!editorRef.current) return;

    const next = sanitizeHTML(editorRef.current.innerHTML);

    htmlRef.current = next;
    setHTML(next);
    setSuccess(null);
  }

  function restoreEditorSelection() {
    const editor = editorRef.current;
    if (!editor) return;

    editor.focus();

    const selection = window.getSelection();
    const range = savedRange.current;

    if (
      selection &&
      range &&
      editor.contains(range.commonAncestorContainer)
    ) {
      selection.removeAllRanges();
      selection.addRange(range);
    }
  }

  function editorCommand(command: string, value?: string) {
    if (!selected || busy) return;

    restoreEditorSelection();

    try {
      document.execCommand(command, false, value);
      syncEditor();

      setFormats({
        bold: document.queryCommandState("bold"),
        italic: document.queryCommandState("italic"),
        underline: document.queryCommandState("underline"),
      });
    } catch {
      setError(
        "This formatting command is unavailable in your browser.",
      );
    }
  }

  function insertLink() {
    if (!selected || busy || !editorRef.current) return;

    const editor = editorRef.current;
    const selection = window.getSelection();

    let range = savedRange.current?.cloneRange() ?? null;

    if (
      selection &&
      selection.rangeCount > 0 &&
      selection.anchorNode &&
      selection.focusNode &&
      editor.contains(selection.anchorNode) &&
      editor.contains(selection.focusNode)
    ) {
      range = selection.getRangeAt(0).cloneRange();
    }

    if (
      !range ||
      !editor.contains(range.commonAncestorContainer)
    ) {
      range = document.createRange();
      range.selectNodeContents(editor);
      range.collapse(false);
    }

    linkRangeRef.current = range.cloneRange();

    const startElement =
      range.startContainer instanceof Element
        ? range.startContainer
        : range.startContainer.parentElement;

    const existingAnchor = startElement?.closest("a");

    linkTargetRef.current =
      range.collapsed &&
      existingAnchor instanceof HTMLAnchorElement &&
      editor.contains(existingAnchor)
        ? existingAnchor
        : null;

    setLinkURL(
      linkTargetRef.current?.getAttribute("href") ?? "",
    );

    setLinkText(
      range.toString() ||
        linkTargetRef.current?.textContent ||
        "",
    );

    setLinkOpen(true);
  }

  function applyNoteLink(url: string) {
    const editor = editorRef.current;
    const range = linkRangeRef.current;

    if (
      !editor ||
      !range ||
      !editor.contains(range.commonAncestorContainer)
    ) {
      setLinkOpen(false);
      setError(
        "Select the text again before adding the link.",
      );
      return;
    }

    const existingAnchor = linkTargetRef.current;

    let anchor: HTMLAnchorElement;

    if (
      existingAnchor &&
      editor.contains(existingAnchor)
    ) {
      anchor = existingAnchor;
    } else {
      anchor = document.createElement("a");

      if (range.collapsed) {
        anchor.textContent = url;
      } else {
        const fragment = range.extractContents();

        fragment.querySelectorAll("a").forEach((nested) => {
          nested.replaceWith(
            ...Array.from(nested.childNodes),
          );
        });

        anchor.append(fragment);
      }

      range.insertNode(anchor);
    }

    anchor.setAttribute("href", url);
    anchor.setAttribute("target", "_blank");
    anchor.setAttribute("rel", "noopener noreferrer");

    editor.focus();

    const caret = document.createRange();
    caret.setStartAfter(anchor);
    caret.collapse(true);

    const selection = window.getSelection();

    if (selection) {
      selection.removeAllRanges();
      selection.addRange(caret);
    }

    savedRange.current = caret.cloneRange();
    linkRangeRef.current = null;
    linkTargetRef.current = null;

    syncEditor();
    setLinkOpen(false);
    setError(null);
  }

  async function exportNote() {
    if (!selected) return;

    try {
      await exportNoteText(
        title.trim() || "Untitled Note",
        sanitizeHTML(html),
        tags,
      );
    } catch (cause) {
      if (
        cause instanceof DOMException &&
        cause.name === "AbortError"
      ) {
        return;
      }

      setError(
        errorMessage(
          cause,
          "Unable to export this note.",
        ),
      );
    }
  }

  function insertImage() {
    if (!selected || busy) return;

    const entered = window.prompt(
      "Enter a public HTTP or HTTPS image URL.",
    );

    if (entered === null) return;

    const url = safeURL(entered, true);

    if (!url) {
      setError("Enter a valid HTTP or HTTPS image URL.");
      return;
    }

    const description =
      window.prompt("Image description", "") ?? "";

    editorCommand(
      "insertHTML",
      `<p><img src="${escapeHTML(url)}" alt="${escapeHTML(description)}" loading="lazy" referrerpolicy="no-referrer"></p><p><br></p>`,
    );
  }

  function insertChecklist() {
    editorCommand(
      "insertHTML",
      [
        '<ul data-checklist="true">',
        '<li data-checked="false">',
        '<input type="checkbox" contenteditable="false" aria-label="Complete checklist item">',
        "<span>New checklist item</span>",
        "</li></ul><p><br></p>",
      ].join(""),
    );
  }

  function addTag() {
    const next = tagDraft.trim();

    if (!next) {
      setAddingTag(false);
      setTagDraft("");
      return;
    }

    if (
      tags.some(
        (tag) => tag.toLowerCase() === next.toLowerCase(),
      )
    ) {
      setError("This tag is already on the note.");
      return;
    }

    if (tags.length >= TAG_LIMIT) {
      setError(`A note can have up to ${TAG_LIMIT} tags.`);
      return;
    }

    setTags((current) => [
      ...current,
      next.slice(0, TAG_LENGTH_LIMIT),
    ]);

    setTagDraft("");
    setAddingTag(false);
    setSuccess(null);
  }

  function handleChecklistClick(target: EventTarget | null) {
    if (
      busy ||
      !(target instanceof HTMLInputElement) ||
      target.type !== "checkbox"
    ) {
      return;
    }

    const item = target.closest("ul[data-checklist] > li");

    if (!item || !editorRef.current?.contains(item)) return;

    item.setAttribute(
      "data-checked",
      target.checked ? "true" : "false",
    );

    if (target.checked) {
      target.setAttribute("checked", "");
    } else {
      target.removeAttribute("checked");
    }

    syncEditor();
  }

  function checklistEnter(
    event: ReactKeyboardEvent<HTMLDivElement>,
  ) {
    if (
      event.key !== "Enter" ||
      event.shiftKey ||
      event.ctrlKey ||
      event.metaKey
    ) {
      return;
    }

    const selection = window.getSelection();

    if (!selection?.anchorNode || !selection.isCollapsed) return;

    const anchor =
      selection.anchorNode instanceof HTMLElement
        ? selection.anchorNode
        : selection.anchorNode.parentElement;

    const item = anchor?.closest("ul[data-checklist] > li");
    const list = item?.parentElement;

    if (
      !(item instanceof HTMLLIElement) ||
      !list ||
      !editorRef.current?.contains(item)
    ) {
      return;
    }

    event.preventDefault();

    if (!(item.textContent ?? "").trim()) {
      const paragraph = document.createElement("p");
      paragraph.append(document.createElement("br"));

      list.after(paragraph);
      item.remove();

      if (!list.children.length) list.remove();

      const range = document.createRange();
      range.setStart(paragraph, 0);
      range.collapse(true);

      selection.removeAllRanges();
      selection.addRange(range);
      savedRange.current = range.cloneRange();

      syncEditor();
      return;
    }

    const tailRange = selection.getRangeAt(0).cloneRange();
    tailRange.setEnd(item, item.childNodes.length);

    const tail = tailRange.extractContents();

    const next = document.createElement("li");
    next.setAttribute("data-checked", "false");

    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.setAttribute("contenteditable", "false");
    checkbox.setAttribute(
      "aria-label",
      "Complete checklist item",
    );

    const text = document.createElement("span");
    text.append(tail);

    if (!text.textContent && !text.querySelector("img")) {
      text.append(document.createElement("br"));
    }

    next.append(checkbox, text);
    item.after(next);

    const range = document.createRange();
    range.selectNodeContents(text);
    range.collapse(true);

    selection.removeAllRanges();
    selection.addRange(range);
    savedRange.current = range.cloneRange();

    syncEditor();
  }

  const statusLabel = pending
    ? `${pending}…`
    : autosave.error
      ? "Could not save"
      : autosave.saving || dirty
        ? "Saving…"
        : "Saved";

  return (
    <div className="wn-page">
      <header className="wn-header">
        <div className="wn-heading">
          <div className="wn-breadcrumb">
            <span>{workspaceId ? "Workspace" : "Personal"}</span>
            <span aria-hidden="true">/</span>
            <span>Notes</span>
          </div>

          <h1>My Notes</h1>

          <p>
            {workspaceId
              ? `Private notes for ${workspace?.name ?? "this workspace"}.`
              : "Capture ideas, organize your thoughts and turn them into action."}
          </p>
        </div>

        <div className="wn-header-actions">
          <button
            type="button"
            className="wn-icon wn-refresh"
            aria-label="Refresh notes"
            title="Refresh notes"
            disabled={busy || !hasScope}
            onClick={refreshNotes}
          >
            {loading ? (
              <LoaderCircle size={16} className="wn-spin" />
            ) : (
              <RefreshCcw size={16} />
            )}
          </button>

          <button
            type="button"
            className="wn-new"
            disabled={busy || !canCreate}
            onClick={() => void createNote()}
          >
            <Plus size={18} />
            <span>New note</span>
          </button>
        </div>
      </header>

      {error && (
        <div className="wn-alert wn-alert-error" role="alert">
          <span>{error}</span>

          <button
            type="button"
            aria-label="Dismiss error"
            onClick={() => setError(null)}
          >
            <X size={16} />
          </button>
        </div>
      )}
      {autosave.error && (
        <div
          className="wn-alert wn-alert-error"
          role="alert"
        >
          <span>
            {autosave.error} Your draft is still here.
          </span>

          <button
            type="button"
            disabled={busy || autosave.saving}
            onClick={() => void saveNote()}
          >
            Retry
          </button>
        </div>
      )}
      {success && (
        <div className="wn-alert wn-alert-success" role="status">
          <CheckCircle2 size={16} />
          <span>{success}</span>
        </div>
      )}

      {!resolving && !hasScope && (
        <div className="wn-alert" role="status">
          Sign in to load and save your notes.
        </div>
      )}

      {!busy && workspaceId && hasScope && !employee && (
        <div className="wn-alert" role="status">
          {employeeError ? `${employeeError} ` : ""}
          Creating workspace notes requires your linked employee
          account. Authorized existing notes can still be opened.
        </div>
      )}

      <section className="wn-stats" aria-label="Note statistics">
        <div>
          <FileText size={17} />
          <span><strong>{counts.total}</strong> Notes</span>
        </div>

        <div>
          <Pin size={17} />
          <span><strong>{counts.pinned}</strong> Pinned</span>
        </div>

        <div>
          <Archive size={17} />
          <span><strong>{counts.archived}</strong> Archived</span>
        </div>

        {loading && (
          <LoaderCircle
            size={15}
            className="wn-spin wn-stats-loading"
            aria-label="Loading notes"
          />
        )}
      </section>

      <section className="wn-controls" aria-label="Find notes">
        <label className="wn-search">
          <Search size={17} aria-hidden="true" />

          <input
            type="search"
            placeholder="Search notes or tags"
            aria-label="Search notes or tags"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
        </label>

        <div
          className="wn-filters"
          role="group"
          aria-label="Filter notes"
        >
          {(
            [
              ["all", "All notes"],
              ["pinned", "Pinned"],
              ["checklists", "Checklists"],
              ["archived", "Archived"],
            ] as const
          ).map(([value, label]) => (
            <button
              key={value}
              type="button"
              className={
                filter === value
                  ? "wn-filter is-active"
                  : "wn-filter"
              }
              aria-pressed={filter === value}
              disabled={busy}
              onClick={() => changeFilter(value)}
            >
              {label}
            </button>
          ))}
        </div>

        <label className="wn-sort">
          <ArrowDownUp size={16} aria-hidden="true" />

          <select
            aria-label="Sort notes"
            value={sort}
            onChange={(event) => {
              setSort(event.target.value as Sort);
            }}
          >
            <option value="updated">Recently updated</option>
            <option value="created">Recently created</option>
            <option value="oldest">Oldest updated</option>
            <option value="title">Title A–Z</option>
          </select>

          <ChevronDown size={13} aria-hidden="true" />
        </label>
      </section>

      <nav className="wn-mobile-nav" aria-label="Notes view">
        <button
          type="button"
          aria-pressed={mobileView === "list"}
          onClick={() => setMobileView("list")}
        >
          Notes ({filtered.length})
        </button>

        <button
          type="button"
          aria-pressed={mobileView === "editor"}
          onClick={() => setMobileView("editor")}
        >
          Editor{dirty ? " · Unsaved" : ""}
        </button>
      </nav>

      <section
        className="wn-layout"
        data-mobile-view={mobileView}
        aria-label="Notes workspace"
        aria-busy={busy}
      >
        <aside className="wn-list" aria-label="Your notes">
          {loading && records.length === 0 ? (
            <div className="wn-list-empty" role="status">
              <LoaderCircle size={24} className="wn-spin" />

              <strong>
                {resolving
                  ? "Loading your account"
                  : "Loading notes"}
              </strong>

              <p>Your notes will appear here.</p>
            </div>
          ) : filtered.length === 0 ? (
            <div className="wn-list-empty">
              <FileText size={27} strokeWidth={1.5} />

              <strong>
                {search.trim()
                  ? "No matching notes"
                  : filter === "pinned"
                    ? "No pinned notes"
                    : filter === "checklists"
                      ? "No checklists yet"
                      : filter === "archived"
                        ? "No archived notes"
                        : "No notes yet"}
              </strong>

              <p>
                {search.trim()
                  ? "Try another title, word or tag."
                  : filter === "all"
                    ? "Create a note to start writing."
                    : "Choose All notes to see your other notes."}
              </p>

              {filter === "all" && canCreate && (
                <button
                  type="button"
                  className="wn-small-action"
                  disabled={busy}
                  onClick={() => void createNote()}
                >
                  <Plus size={15} />
                  New note
                </button>
              )}
            </div>
          ) : (
            filtered.map(({ note, document, text, checklist }) => (
              <button
                key={note.id}
                type="button"
                className={
                  note.id === selectedId
                    ? "wn-note-card is-selected"
                    : "wn-note-card"
                }
                aria-pressed={note.id === selectedId}
                disabled={busy}
                onClick={() => void openNote(note)}
              >
                <span className="wn-card-heading">
                  <strong>{note.title || "Untitled Note"}</strong>

                  {note.is_pinned ? (
                    <Pin size={15} aria-label="Pinned" />
                  ) : note.is_archived ? (
                    <Archive size={15} aria-label="Archived" />
                  ) : null}
                </span>

                <span className="wn-card-preview">
                  {text || "Empty note"}
                </span>

                {checklist.total > 0 && (
                  <span className="wn-card-progress">
                    <span className="wn-progress-track">
                      <span
                        style={{
                          width: `${(checklist.done / checklist.total) * 100}%`,
                        }}
                      />
                    </span>

                    <span>
                      {checklist.done} of {checklist.total}
                    </span>
                  </span>
                )}

                <span className="wn-card-bottom">
                  <span className="wn-card-tags">
                    {document.tags.slice(0, 2).map((tag) => (
                      <span key={tag} className="wn-tag">
                        {tag}
                      </span>
                    ))}

                    {document.tags.length > 2 && (
                      <span className="wn-tag">
                        +{document.tags.length - 2}
                      </span>
                    )}
                  </span>

                  <time dateTime={note.updated_at}>
                    {shortDate(note.updated_at)}
                  </time>
                </span>
              </button>
            ))
          )}
        </aside>

        <section
          className="wn-editor-panel"
          aria-label="Note editor"
        >
          {selected ? (
            <>
              <div className="wn-document-header">
                <div className="wn-document-heading">
                  <label
                    className="wn-sr-only"
                    htmlFor="wn-note-title"
                  >
                    Note title
                  </label>

                  <input
                    id="wn-note-title"
                    className="wn-title"
                    value={title}
                    placeholder="Untitled Note"
                    maxLength={TITLE_LIMIT}
                    disabled={busy}
                    onChange={(event) => {
                      setTitle(event.target.value);
                      setSuccess(null);
                    }}
                  />
                </div>

                <div className="wn-document-actions">
                  <span className="wn-private">
                    <Lock size={12} />
                    Private note
                  </span>

                  <span
                    className={
                      autosave.error
                        ? "wn-save-state is-error"
                        : dirty || autosave.saving || pending
                          ? "wn-save-state is-unsaved"
                          : "wn-save-state"
                    }
                    role="status"
                    aria-live="polite"
                    title={statusLabel}
                  >
                    {pending || autosave.saving ? (
                      <LoaderCircle
                        size={14}
                        className="wn-spin"
                      />
                    ) : autosave.error ? (
                      <X size={14} />
                    ) : dirty ? (
                      <span className="wn-unsaved-dot" />
                    ) : (
                      <CheckCircle2 size={14} />
                    )}

                    <span>{statusLabel}</span>
                  </span>

                  <button
                    type="button"
                    className={
                      selected.is_pinned
                        ? "wn-icon is-pinned"
                        : "wn-icon"
                    }
                    aria-label={selected.is_pinned ? "Unpin note" : "Pin note"}
                    title={selected.is_pinned ? "Unpin note" : "Pin note"}
                    disabled={busy}
                    onClick={() => void togglePin()}
                  >
                    <Pin size={16} />
                  </button>

                  <button
                    type="button"
                    className="wn-icon"
                    aria-label={
                      selected.is_archived ? "Restore note" : "Archive note"
                    }
                    title={
                      selected.is_archived ? "Restore note" : "Archive note"
                    }
                    disabled={busy}
                    onClick={() => void toggleArchive()}
                  >
                    {selected.is_archived ? (
                      <ArchiveRestore size={16} />
                    ) : (
                      <Archive size={16} />
                    )}
                  </button>

                  <div className="wn-menu-container" ref={menuRef}>
                    <button
                      type="button"
                      className={
                        menuOpen ? "wn-icon is-open" : "wn-icon"
                      }
                      aria-label="More note actions"
                      aria-expanded={menuOpen}
                      aria-controls="wn-note-menu"
                      title="More note actions"
                      disabled={busy}
                      onClick={() => setMenuOpen((current) => !current)}
                    >
                      <MoreHorizontal size={17} />
                    </button>

                    {menuOpen && (
                      <div
                        id="wn-note-menu"
                        className="wn-menu"
                        aria-label="More note actions"
                      >
                        <button
                          type="button"
                          onClick={() => void togglePin()}
                        >
                          {selected.is_pinned ? (
                            <PinOff size={15} />
                          ) : (
                            <Pin size={15} />
                          )}
                          {selected.is_pinned ? "Unpin" : "Pin"}
                        </button>

                        <button
                          type="button"
                          onClick={() => void toggleArchive()}
                        >
                          {selected.is_archived ? (
                            <ArchiveRestore size={15} />
                          ) : (
                            <Archive size={15} />
                          )}
                          {selected.is_archived ? "Restore" : "Archive"}
                        </button>

                        <button
                          type="button"
                          disabled={!canCreate}
                          title="Duplicate the last saved document"
                          onClick={() => void duplicateNote()}
                        >
                          <Copy size={15} />
                          Duplicate
                        </button>

                        <div className="wn-menu-divider" />

                        <button
                          type="button"
                          className="wn-delete-action"
                          onClick={() => void deleteNote()}
                        >
                          <Trash2 size={15} />
                          Delete note
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              <div className="wn-document-tags">
                {tags.map((tag) => (
                  <span
                    key={tag}
                    className="wn-tag wn-editor-tag"
                  >
                    <span>{tag}</span>

                    <button
                      type="button"
                      aria-label={`Remove ${tag} tag`}
                      disabled={busy}
                      onClick={() => {
                        setTags((current) =>
                          current.filter((entry) => entry !== tag),
                        );
                        setSuccess(null);
                      }}
                    >
                      <X size={11} />
                    </button>
                  </span>
                ))}

                {addingTag ? (
                  <form
                    className="wn-tag-form"
                    onSubmit={(event) => {
                      event.preventDefault();
                      addTag();
                    }}
                  >
                    <input
                      ref={tagInputRef}
                      value={tagDraft}
                      placeholder="Tag name"
                      aria-label="New tag name"
                      maxLength={TAG_LENGTH_LIMIT}
                      disabled={busy}
                      onChange={(event) => setTagDraft(event.target.value)}
                      onKeyDown={(event) => {
                        if (event.key === "Escape") {
                          setAddingTag(false);
                          setTagDraft("");
                        }
                      }}
                    />

                    <button
                      type="submit"
                      aria-label="Add tag"
                      disabled={busy}
                    >
                      <Check size={13} />
                    </button>

                    <button
                      type="button"
                      aria-label="Cancel adding tag"
                      onClick={() => {
                        setAddingTag(false);
                        setTagDraft("");
                      }}
                    >
                      <X size={13} />
                    </button>
                  </form>
                ) : (
                  <button
                    type="button"
                    className="wn-add-tag"
                    disabled={busy || tags.length >= TAG_LIMIT}
                    onClick={() => setAddingTag(true)}
                  >
                    <Plus size={13} />
                    Add tag
                  </button>
                )}
              </div>

              <div
                className="wn-format-toolbar"
                role="toolbar"
                aria-label="Text formatting"
              >
                <label className="wn-heading-select">
                  <span className="wn-sr-only">Text block style</span>

                  <select
                    defaultValue=""
                    disabled={busy}
                    onChange={(event) => {
                      const value = event.target.value;

                      if (value) editorCommand("formatBlock", value);

                      event.target.value = "";
                    }}
                  >
                    <option value="" disabled>H1</option>
                    <option value="p">Paragraph</option>
                    <option value="h1">Heading 1</option>
                    <option value="h2">Heading 2</option>
                    <option value="h3">Heading 3</option>
                    <option value="blockquote">Quote</option>
                  </select>

                  <ChevronDown size={12} />
                </label>

                <span className="wn-toolbar-divider" />

                <button
                  type="button"
                  className={formats.bold ? "is-active" : undefined}
                  aria-label="Bold"
                  aria-pressed={formats.bold}
                  title="Bold — Ctrl+B"
                  disabled={busy}
                  onMouseDown={(event) => event.preventDefault()}
                  onClick={() => editorCommand("bold")}
                >
                  <Bold size={18} />
                </button>

                <button
                  type="button"
                  className={formats.italic ? "is-active" : undefined}
                  aria-label="Italic"
                  aria-pressed={formats.italic}
                  title="Italic — Ctrl+I"
                  disabled={busy}
                  onMouseDown={(event) => event.preventDefault()}
                  onClick={() => editorCommand("italic")}
                >
                  <Italic size={18} />
                </button>

                <button
                  type="button"
                  className={formats.underline ? "is-active" : undefined}
                  aria-label="Underline"
                  aria-pressed={formats.underline}
                  title="Underline — Ctrl+U"
                  disabled={busy}
                  onMouseDown={(event) => event.preventDefault()}
                  onClick={() => editorCommand("underline")}
                >
                  <Underline size={18} />
                </button>

                <span className="wn-toolbar-divider" />

                <button
                  type="button"
                  aria-label="Bulleted list"
                  title="Bulleted list"
                  disabled={busy}
                  onMouseDown={(event) => event.preventDefault()}
                  onClick={() => editorCommand("insertUnorderedList")}
                >
                  <List size={18} />
                </button>

                <button
                  type="button"
                  aria-label="Numbered list"
                  title="Numbered list"
                  disabled={busy}
                  onMouseDown={(event) => event.preventDefault()}
                  onClick={() => editorCommand("insertOrderedList")}
                >
                  <ListOrdered size={18} />
                </button>

                <button
                  type="button"
                  aria-label="Insert checklist"
                  title="Insert checklist"
                  disabled={busy}
                  onMouseDown={(event) => event.preventDefault()}
                  onClick={insertChecklist}
                >
                  <CheckSquare size={18} />
                </button>

                <button
                  type="button"
                  aria-label="Insert link"
                  title="Insert link"
                  disabled={busy}
                  onMouseDown={(event) => event.preventDefault()}
                  onClick={insertLink}
                >
                  <Link2 size={18} />
                </button>

                <button
                  type="button"
                  aria-label="Insert image from URL"
                  title="Insert image from URL"
                  disabled={busy}
                  onMouseDown={(event) => event.preventDefault()}
                  onClick={insertImage}
                >
                  <ImagePlus size={18} />
                </button>
              </div>

              {selected.is_archived && (
                <div className="wn-archived-banner">
                  <Archive size={14} />
                  This note is archived.

                  <button
                    type="button"
                    disabled={busy}
                    onClick={() => void toggleArchive()}
                  >
                    Restore
                  </button>
                </div>
              )}

              <div
                ref={editorRef}
                className="wn-document-body"
                contentEditable={!busy}
                suppressContentEditableWarning
                role="textbox"
                aria-label="Note content"
                aria-multiline="true"
                aria-readonly={busy}
                data-placeholder="Start writing your note…"
                spellCheck
                onInput={syncEditor}
                onClick={(event) => handleChecklistClick(event.target)}
                onKeyDown={(event) => {
                  const shortcut = event.ctrlKey || event.metaKey;
                  const key = event.key.toLowerCase();

                  if (shortcut && key === "s") {
                    event.preventDefault();
                    void saveNote();
                    return;
                  }

                  if (shortcut && ["b", "i", "u"].includes(key)) {
                    event.preventDefault();

                    const commands = {
                      b: "bold",
                      i: "italic",
                      u: "underline",
                    };

                    editorCommand(commands[key as keyof typeof commands]);
                    return;
                  }

                  checklistEnter(event);
                }}
                onPaste={(event) => {
                  event.preventDefault();

                  editorCommand(
                    "insertText",
                    event.clipboardData.getData("text/plain"),
                  );
                }}
                onDrop={(event) => event.preventDefault()}
                onDragOver={(event) => event.preventDefault()}
              />

              <NotesAttachments
                key={selected.id}
                noteId={selected.id}
                workspaceId={workspaceId}
              />

              <footer className="wn-document-footer">
                <div className="wn-footer-left">
                  <span title={fullDate(selected.updated_at)}>
                    Last edited {shortDate(selected.updated_at)}
                  </span>

                  <span className="wn-word-count">
                    {wordCount} {wordCount === 1 ? "word" : "words"}
                  </span>
                </div>

                <div className="wn-footer-right">
                  <button
                    type="button"
                    className="wn-save-button wn-export-button"
                    disabled={busy}
                    onClick={() => void exportNote()}
                    title="Export this note as a text file"
                  >
                    <Download size={13} />
                    Export text
                  </button>

                  <span className="wn-footer-privacy">
                    <Lock size={13} />
                    {workspaceId ? "Workspace" : "Personal"}
                    <span aria-hidden="true">·</span>
                    Only you
                  </span>
                </div>
              </footer>
            </>
          ) : (
            <div className="wn-editor-empty">
              <div className="wn-empty-icon">
                <FileText size={32} strokeWidth={1.4} />
              </div>

              <h2>
                {loading
                  ? "Loading your notes"
                  : "A little space for your ideas"}
              </h2>

              <p>
                {loading
                  ? "Your saved notes are on their way."
                  : "Select a note from the list or create a new one to start writing."}
              </p>

              {!loading && (
                <button
                  type="button"
                  className="wn-new"
                  disabled={busy || !canCreate}
                  onClick={() => void createNote()}
                >
                  <Plus size={17} />
                  New note
                </button>
              )}
            </div>
          )}
        </section>

        <aside
          className="wn-right-panel"
          aria-label="Note assistance and details"
        >
          <section className="wn-side-card">
            <div className="wn-side-heading">
              <h2>AI assistance</h2>
              <Sparkles size={16} />
            </div>

            <button
              type="button"
              className="wn-side-action"
              disabled
              title="Summarization is not available yet."
            >
              <FileText size={17} />
              Summarize note
            </button>

            <button
              type="button"
              className="wn-side-action"
              disabled
              title="Rewriting is not available yet."
            >
              <Sparkles size={17} />
              Rewrite note
            </button>

            <div className="wn-side-divider" />

            <p className="wn-summary-label">Suggested summary</p>

            <div className="wn-summary">
              <p>
                {selected
                  ? "AI suggestions will appear here when this feature is available."
                  : "Open a note to see its suggestions here."}
              </p>
            </div>

            <button
              type="button"
              className="wn-apply"
              disabled
              title="There is no suggestion to apply."
            >
              <FileText size={15} />
              Apply
            </button>
          </section>

          <section className="wn-side-card">
            <div className="wn-side-heading">
              <h2>Turn ideas into action</h2>
            </div>

            <button
              type="button"
              className="wn-side-action"
              disabled
              title="Task conversion is not available yet."
            >
              <CheckCircle2 size={17} />
              Convert to task
            </button>

            <button
              type="button"
              className="wn-side-action"
              disabled
              title="Workspace sharing is not available yet."
            >
              <Share2 size={17} />
              Share to workspace
            </button>

            <p className="wn-action-caption">
              Choose a destination before sharing.
            </p>
          </section>

          <section className="wn-side-card">
            <div className="wn-side-heading">
              <h2>Note details</h2>
            </div>

            <dl className="wn-details">
              <div>
                <dt>
                  <FileText size={14} />
                  Created
                </dt>
                <dd>
                  {selected ? createdDate(selected.created_at) : "—"}
                </dd>
              </div>

              <div>
                <dt>
                  <Tag size={14} />
                  Tags
                </dt>

                <dd className="wn-detail-tags">
                  {tags.length ? (
                    tags.map((tag) => (
                      <span key={tag} className="wn-tag">
                        {tag}
                      </span>
                    ))
                  ) : (
                    <span className="wn-muted">No tags</span>
                  )}
                </dd>
              </div>

              <div>
                <dt>
                  <Lock size={14} />
                  Visibility
                </dt>
                <dd>{selected ? "Private" : "—"}</dd>
              </div>

              {currentProgress.total > 0 && (
                <div>
                  <dt>
                    <CheckSquare size={14} />
                    Checklist
                  </dt>
                  <dd>
                    {currentProgress.done} of {currentProgress.total} complete
                  </dd>
                </div>
              )}
            </dl>
          </section>
        </aside>
      </section>
      {linkOpen && (
        <NoteLinkDialog
          initialURL={linkURL}
          selectedText={linkText}
          onApply={applyNoteLink}
          onCancel={() => {
            setLinkOpen(false);
            linkRangeRef.current = null;
            linkTargetRef.current = null;
          }}
        />
      )}
      <style jsx global>{`
        .wn-page {
          container: notes / inline-size;
          width: 100%;
          max-width: 100%;
          min-width: 0;
          padding: 18px;
          box-sizing: border-box;
          color: #191b2e;
          background: #faf7ee;
          font-family: inherit;
          font-size: 14px;
          line-height: 1.5;
          text-align: left;
          color-scheme: light;
        }

        .wn-page *,
        .wn-page *::before,
        .wn-page *::after {
          box-sizing: border-box;
          min-width: 0;
        }

        .wn-page button,
        .wn-page input,
        .wn-page select {
          font-family: inherit;
        }

        .wn-page button {
          cursor: pointer;
          touch-action: manipulation;
        }

        .wn-page button:disabled {
          cursor: not-allowed;
          opacity: 0.58;
        }

        .wn-page svg {
          flex-shrink: 0;
          stroke-width: 1.65;
        }

        .wn-page button:focus-visible,
        .wn-page input:focus-visible,
        .wn-page select:focus-visible,
        .wn-document-body:focus-visible {
          outline: 2px solid #a77800;
          outline-offset: 3px;
        }

        .wn-page ::selection {
          color: #17192e;
          background: #ffe69e;
        }

        .wn-page input::placeholder {
          color: #707689;
          opacity: 1;
        }

        .wn-page ::-webkit-scrollbar {
          width: 5px;
          height: 5px;
        }

        .wn-page ::-webkit-scrollbar-thumb {
          border-radius: 8px;
          background: #d2cbbd;
        }

        .wn-page ::-webkit-scrollbar-track {
          background: transparent;
        }

        .wn-header {
          display: flex;
          align-items: flex-end;
          justify-content: space-between;
          gap: 16px;
          margin-bottom: 16px;
        }

        .wn-heading {
          flex: 1;
        }

        .wn-heading h1 {
          margin: 0;
          color: #202126;
          font-size: 36px;
          font-weight: 450;
          line-height: 1.15;
          letter-spacing: -0.03em;
        }

        .wn-heading p {
          margin: 5px 0 0;
          color: #51576d;
          font-size: 14px;
          line-height: 1.5;
        }

        .wn-breadcrumb {
          display: flex;
          gap: 10px;
          margin-bottom: 10px;
          color: #60677a;
          font-size: 11px;
        }

        .wn-header-actions {
          display: flex;
          align-items: center;
          flex-shrink: 0;
          gap: 7px;
        }

        .wn-page .wn-new {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
          min-height: 39px;
          padding: 9px 15px;
          border: 1px solid #252525;
          border-radius: 9px;
          color: #ffffff;
          background: #272727;
          font-size: 13px;
          font-weight: 500;
          white-space: nowrap;
        }

        .wn-page .wn-new:hover:not(:disabled) {
          background: #111111;
        }

        .wn-page .wn-icon {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          flex: 0 0 auto;
          width: 30px;
          height: 31px;
          padding: 0;
          border: 1px solid #e0ddd7;
          border-radius: 7px;
          color: #272a3e;
          background: #fffefd;
        }

        .wn-page .wn-refresh {
          width: 35px;
          height: 35px;
          background: transparent;
        }

        .wn-icon.is-pinned svg {
          fill: #ffd75c;
        }

        .wn-page .wn-icon.is-open,
        .wn-page .wn-icon:hover:not(:disabled) {
          background: #f3efe6;
        }

        .wn-alert {
          display: flex;
          align-items: center;
          gap: 8px;
          margin: 0 0 12px;
          padding: 10px 12px;
          border: 1px solid #e4d6ae;
          border-radius: 8px;
          color: #6a5627;
          background: #fff8e5;
          font-size: 12px;
        }

        .wn-alert > button {
          margin-left: auto;
          padding: 0;
          border: 0;
          color: inherit;
          background: transparent;
        }

        .wn-alert-error {
          border-color: #efc9c4;
          color: #a3342c;
          background: #fff2ef;
        }

        .wn-alert-success {
          border-color: #c5e1cf;
          color: #276b43;
          background: #f0faf3;
        }

        .wn-stats {
          display: flex;
          align-items: center;
          flex-wrap: wrap;
          gap: 27px;
          min-height: 44px;
          margin-bottom: 12px;
          padding: 11px 13px;
          border: 1px solid #ebdfc5;
          border-radius: 10px;
          font-size: 13px;
        }

        .wn-stats > div {
          display: flex;
          align-items: center;
          gap: 9px;
        }

        .wn-stats strong {
          font-weight: 500;
          font-variant-numeric: tabular-nums;
        }

        .wn-stats-loading {
          margin-left: auto;
        }

        .wn-controls {
          display: flex;
          align-items: center;
          flex-wrap: wrap;
          gap: 10px;
          margin-bottom: 13px;
        }

        .wn-search {
          display: flex;
          align-items: center;
          flex: 1 1 250px;
          gap: 9px;
          height: 35px;
          padding: 0 11px;
          border: 1px solid #dedbd5;
          border-radius: 9px;
          background: #fffdfa;
        }

        .wn-search input {
          width: 100%;
          height: 100%;
          padding: 0;
          border: 0;
          outline: none;
          color: #252a3e;
          background: transparent;
          font-size: 12px;
        }

        .wn-search:focus-within {
          border-color: #bba069;
        }

        .wn-filters {
          display: flex;
          gap: 5px;
        }

        .wn-page .wn-filter {
          min-height: 35px;
          padding: 0 17px;
          border: 1px solid #dedbd5;
          border-radius: 999px;
          color: #34384d;
          background: #fffdfa;
          font-size: 11px;
          white-space: nowrap;
        }

        .wn-page .wn-filter.is-active {
          border-color: #292936;
          color: #ffffff;
          background: #292936;
        }

        .wn-page .wn-filter:hover:not(:disabled):not(.is-active) {
          background: #f0ebe0;
        }

        .wn-sort {
          display: flex;
          align-items: center;
          gap: 7px;
          height: 35px;
          margin-left: auto;
          padding: 0 10px;
          border: 1px solid #dedbd5;
          border-radius: 9px;
          background: #fffdfa;
          font-size: 11px;
        }

        .wn-sort select {
          max-width: 160px;
          padding: 0;
          border: 0;
          appearance: none;
          color: #34384d;
          background: transparent;
          font: inherit;
          cursor: pointer;
        }

        .wn-layout {
          display: grid;
          grid-template-columns:
            minmax(0, 1.1fr)
            minmax(0, 2.1fr)
            minmax(0, 0.95fr);
          align-items: start;
          gap: 12px;
        }

        .wn-list {
          display: flex;
          flex-direction: column;
          gap: 7px;
          max-height: 760px;
          padding: 2px 0;
          overflow-y: auto;
          scrollbar-width: thin;
          scrollbar-color: #d2cbbd transparent;
        }

        .wn-page .wn-note-card {
          display: flex;
          flex-direction: column;
          flex-shrink: 0;
          align-items: stretch;
          gap: 4px;
          width: 100%;
          min-height: 112px;
          padding: 12px;
          border: 1px solid #eee9e0;
          border-radius: 10px;
          color: inherit;
          background: #fffefd;
          text-align: left;
        }

        .wn-page .wn-note-card:hover:not(:disabled) {
          border-color: #ddd3be;
          background: #fffaf0;
        }

        .wn-page .wn-note-card.is-selected {
          border-color: #ffdc83;
          background: #fff2c8;
        }

        .wn-page .wn-note-card:disabled {
          opacity: 0.82;
        }

        .wn-card-heading {
          display: flex;
          align-items: start;
          justify-content: space-between;
          gap: 7px;
          width: 100%;
        }

        .wn-card-heading strong {
          overflow: hidden;
          color: #1d2035;
          font-size: 15px;
          font-weight: 600;
          line-height: 1.3;
          letter-spacing: -0.02em;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .wn-card-heading svg {
          margin-top: 2px;
        }

        .wn-card-preview {
          display: -webkit-box;
          overflow: hidden;
          color: #52586e;
          font-size: 12px;
          line-height: 1.45;
          -webkit-line-clamp: 2;
          -webkit-box-orient: vertical;
          overflow-wrap: anywhere;
        }

        .wn-card-bottom {
          display: flex;
          align-items: flex-end;
          justify-content: space-between;
          flex-wrap: wrap;
          gap: 6px;
          margin-top: auto;
          padding-top: 7px;
        }

        .wn-card-tags,
        .wn-document-tags,
        .wn-detail-tags {
          display: flex;
          align-items: center;
          flex-wrap: wrap;
          gap: 5px;
        }

        .wn-tag {
          display: inline-flex;
          align-items: center;
          gap: 4px;
          max-width: 100%;
          padding: 3px 9px;
          border: 1px solid #dad9d4;
          border-radius: 999px;
          color: #36394d;
          background: #f2f1ee;
          font-size: 10px;
          line-height: 1.35;
          overflow-wrap: anywhere;
        }

        .wn-card-bottom time {
          margin-left: auto;
          color: #666c7d;
          font-size: 10px;
          font-variant-numeric: tabular-nums;
          white-space: nowrap;
        }

        .wn-card-progress {
          display: flex;
          align-items: center;
          gap: 7px;
          margin: 4px 0;
          color: #555d70;
          font-size: 10px;
        }

        .wn-progress-track {
          display: block;
          width: 105px;
          height: 7px;
          overflow: hidden;
          border: 1px solid #ddd9d0;
          border-radius: 99px;
          background: #f7f6f2;
        }

        .wn-progress-track > span {
          display: block;
          height: 100%;
          border-radius: inherit;
          background: #ffcb24;
        }

        .wn-editor-panel {
          display: flex;
          flex-direction: column;
          min-height: 590px;
          padding: 17px 17px 12px;
          border-radius: 11px;
          background: #fffefd;
        }

        .wn-document-header {
          display: flex;
          align-items: flex-start;
          justify-content: space-between;
          flex-wrap: wrap;
          gap: 7px;
          margin-bottom: 8px;
        }

        .wn-document-heading {
          flex: 1 1 180px;
        }

        .wn-title {
          width: 100%;
          height: 32px;
          margin: 0;
          padding: 0;
          border: 0;
          outline: none;
          color: #191b31;
          background: transparent;
          font-family: inherit;
          font-size: 23px;
          font-weight: 600;
          line-height: 1.3;
          letter-spacing: -0.03em;
        }

        .wn-document-actions {
          display: flex;
          align-items: center;
          flex-wrap: wrap;
          gap: 5px;
          margin-left: auto;
        }

        .wn-private {
          display: inline-flex;
          align-items: center;
          gap: 4px;
          padding: 5px 8px;
          border-radius: 999px;
          color: #69542a;
          background: #fff6db;
          font-size: 10px;
          white-space: nowrap;
        }

        .wn-save-state {
          display: flex;
          align-items: center;
          gap: 4px;
          color: #276442;
          font-size: 10px;
          white-space: nowrap;
        }

        .wn-save-state.is-unsaved {
          color: #89671e;
        }

        .wn-unsaved-dot {
          width: 6px;
          height: 6px;
          border-radius: 50%;
          background: #b98723;
        }

        .wn-document-tags {
          margin-bottom: 12px;
        }

        .wn-editor-tag {
          border-color: #cce5ef;
          color: #304959;
          background: #e9f5fa;
          font-size: 11px;
        }

        .wn-editor-tag button {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          width: 16px;
          height: 16px;
          padding: 0;
          border: 0;
          border-radius: 50%;
          color: #526e7b;
          background: transparent;
        }

        .wn-add-tag {
          display: inline-flex;
          align-items: center;
          gap: 4px;
          min-height: 25px;
          padding: 3px 8px;
          border: 1px solid #dedbd4;
          border-radius: 999px;
          color: #5e6576;
          background: #fffefd;
          font-size: 11px;
        }

        .wn-tag-form {
          display: flex;
          align-items: center;
          gap: 3px;
          padding: 3px 6px;
          border: 1px solid #dbd6cb;
          border-radius: 99px;
        }

        .wn-tag-form input {
          width: 100px;
          padding: 0;
          border: 0;
          outline: none;
          color: #33394f;
          background: transparent;
          font-size: 12px;
        }

        .wn-tag-form button {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 22px;
          height: 22px;
          padding: 0;
          border: 0;
          color: #606779;
          background: transparent;
        }

        .wn-menu-container {
          position: relative;
        }

        .wn-menu {
          position: absolute;
          top: calc(100% + 5px);
          right: 0;
          z-index: 30;
          width: 142px;
          max-width: calc(100vw - 40px);
          padding: 5px;
          border-radius: 9px;
          background: #fffefd;
          box-shadow: 0 8px 22px rgb(40 32 15 / 16%);
        }

        .wn-menu button {
          display: flex;
          align-items: center;
          gap: 10px;
          width: 100%;
          min-height: 34px;
          padding: 8px;
          border: 0;
          border-radius: 5px;
          color: #50586b;
          background: transparent;
          font-size: 12px;
          text-align: left;
        }

        .wn-menu button:hover:not(:disabled) {
          background: #f6f1e6;
        }

        .wn-menu-divider {
          height: 1px;
          margin: 5px -5px;
          background: #e8e2d7;
        }

        .wn-menu .wn-delete-action {
          color: #bd352b;
        }

        .wn-format-toolbar {
          display: flex;
          align-items: center;
          gap: 3px;
          width: 100%;
          margin-bottom: 17px;
          padding: 5px 6px;
          overflow-x: auto;
          border: 1px solid #e4e0d9;
          border-radius: 8px;
          background: #fcfaf7;
          overscroll-behavior-x: contain;
          scrollbar-width: thin;
        }

        .wn-format-toolbar > button {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          flex: 0 0 31px;
          height: 31px;
          padding: 0;
          border: 0;
          border-radius: 5px;
          color: #1e2238;
          background: transparent;
        }

        .wn-format-toolbar > button.is-active {
          background: #ffe8ab;
        }

        .wn-format-toolbar > button:hover:not(:disabled) {
          background: #eee8db;
        }

        .wn-heading-select {
          display: flex;
          align-items: center;
          flex: 0 0 49px;
          gap: 4px;
        }

        .wn-heading-select select {
          width: 36px;
          padding: 0;
          border: 0;
          outline: none;
          appearance: none;
          color: #292e43;
          background: transparent;
          font-size: 12px;
        }

        .wn-toolbar-divider {
          flex: 0 0 1px;
          width: 1px;
          height: 22px;
          margin: 0 4px;
          background: #e2ded6;
        }

        .wn-archived-banner {
          display: flex;
          align-items: center;
          gap: 7px;
          margin-bottom: 12px;
          padding: 8px;
          border-radius: 6px;
          color: #7c6127;
          background: #fff4d5;
          font-size: 12px;
        }

        .wn-archived-banner button {
          margin-left: auto;
          border: 0;
          color: inherit;
          background: transparent;
          text-decoration: underline;
        }

        .wn-document-body {
          flex: 1;
          min-height: 325px;
          padding: 0 2px 15px;
          outline: none;
          color: #444b62;
          font-size: 14px;
          line-height: 1.65;
          caret-color: #9d7000;
          overflow-wrap: anywhere;
          white-space: pre-wrap;
        }

        .wn-document-body:empty::before {
          color: #7b8190;
          content: attr(data-placeholder);
          pointer-events: none;
        }

        .wn-document-body h1 {
          margin: 2px 0 12px;
          color: #191b31;
          font-size: 26px;
          font-weight: 650;
          line-height: 1.3;
          letter-spacing: -0.025em;
        }

        .wn-document-body h2 {
          margin: 18px 0 7px;
          color: #202338;
          font-size: 18px;
          font-weight: 600;
          line-height: 1.35;
        }

        .wn-document-body h3 {
          margin: 17px 0 6px;
          color: #202338;
          font-size: 16px;
          font-weight: 600;
        }

        .wn-document-body h4 {
          margin: 16px 0 6px;
          font-size: 15px;
        }

        .wn-document-body p,
        .wn-document-body div {
          margin: 0 0 10px;
        }

        .wn-document-body strong,
        .wn-document-body b {
          font-weight: 700;
        }

        .wn-document-body i,
        .wn-document-body em {
          font-style: italic;
        }

        .wn-document-body u {
          text-decoration: underline;
          text-underline-offset: 3px;
        }

        .wn-document-body ul,
        .wn-document-body ol {
          margin: 6px 0 17px;
          padding-left: 27px;
        }

        .wn-document-body li {
          margin: 4px 0;
          padding-left: 2px;
        }

        .wn-document-body li > p {
          margin: 0;
        }

        .wn-document-body ul[data-checklist] {
          padding: 0;
          list-style: none;
        }

        .wn-document-body ul[data-checklist] > li {
          position: relative;
          min-height: 25px;
          padding-left: 30px;
          list-style: none;
        }

        .wn-document-body ul[data-checklist] input[type="checkbox"] {
          position: absolute;
          top: 5px;
          left: 2px;
          width: 16px;
          height: 16px;
          margin: 0;
          accent-color: #daa000;
          cursor: pointer;
        }

        .wn-document-body ul[data-checklist] > li[data-checked="true"] {
          color: #7c8290;
          text-decoration: line-through;
        }

        .wn-document-body a {
          color: #386d95;
          text-decoration: underline;
          text-underline-offset: 3px;
        }

        .wn-document-body img {
          display: block;
          max-width: 100%;
          height: auto;
          margin: 12px 0;
          border-radius: 8px;
        }

        .wn-document-body blockquote {
          margin: 14px 0;
          padding: 12px 14px;
          border-left: 1px solid #d5c084;
          background: #fbf5e4;
        }

        .wn-document-body pre {
          max-width: 100%;
          overflow: auto;
          padding: 12px;
          border-radius: 6px;
          background: #f3f0e8;
        }

        .wn-document-body code {
          padding: 2px 4px;
          background: #f3f0e8;
          font-size: 0.9em;
        }

        .wn-document-body hr {
          margin: 16px 0;
          border: 0;
          border-top: 1px solid #e4dfd4;
        }

        .wn-document-footer {
          display: flex;
          align-items: center;
          justify-content: space-between;
          flex-wrap: wrap;
          gap: 8px;
          padding-top: 13px;
          color: #696f81;
          font-size: 10px;
        }

        .wn-footer-left,
        .wn-footer-right,
        .wn-footer-privacy {
          display: flex;
          align-items: center;
          flex-wrap: wrap;
          gap: 6px;
        }

        .wn-footer-right {
          margin-left: auto;
        }

        .wn-small-action,
        .wn-save-button {
          display: inline-flex;
          align-items: center;
          gap: 5px;
          padding: 6px 9px;
          border: 1px solid #e3ce91;
          border-radius: 6px;
          color: #614917;
          background: #fff0bd;
          font-size: 11px;
        }

        .wn-right-panel {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .wn-side-card {
          padding: 13px;
          border: 1px solid #eee0c1;
          border-radius: 10px;
          background: #fcf9f0;
        }

        .wn-side-heading {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 7px;
          margin-bottom: 9px;
        }

        .wn-side-heading h2 {
          margin: 0;
          color: #24263b;
          font-size: 14px;
          font-weight: 600;
          line-height: 1.4;
          letter-spacing: -0.02em;
        }

        .wn-side-action {
          display: flex;
          align-items: center;
          gap: 9px;
          width: 100%;
          min-height: 34px;
          margin-top: 5px;
          padding: 7px 10px;
          border: 1px solid #dcd8d0;
          border-radius: 8px;
          color: #33394f;
          background: #fffdfa;
          font-size: 11px;
          text-align: left;
        }

        .wn-side-divider {
          height: 1px;
          margin: 12px 0;
          background: #e6dfd2;
        }

        .wn-summary-label {
          margin: 0 0 6px;
          color: #35394a;
          font-size: 11px;
        }

        .wn-summary {
          min-height: 122px;
          padding: 9px;
          border: 1px solid #e6e1d8;
          border-radius: 8px;
          color: #555c70;
          background: #f8f6f2;
          font-size: 12px;
          line-height: 1.5;
        }

        .wn-summary p {
          margin: 0;
        }

        .wn-apply {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 7px;
          width: 100%;
          min-height: 34px;
          margin-top: 9px;
          border: 1px solid #f3ce5a;
          border-radius: 8px;
          color: #5d491b;
          background: #ffe27c;
          font-size: 12px;
        }

        .wn-action-caption {
          margin: 6px 0 0;
          color: #6b6d78;
          font-size: 10px;
          line-height: 1.5;
        }

        .wn-details {
          display: flex;
          flex-direction: column;
          gap: 8px;
          margin: 0;
          font-size: 11px;
        }

        .wn-details > div {
          display: grid;
          grid-template-columns: 78px minmax(0, 1fr);
          gap: 7px;
        }

        .wn-details dt {
          display: flex;
          align-items: center;
          gap: 7px;
          color: #60687b;
        }

        .wn-details dd {
          margin: 0;
          color: #41495f;
          overflow-wrap: anywhere;
        }

        .wn-detail-tags .wn-tag {
          padding: 3px 7px;
          font-size: 10px;
        }

        .wn-muted {
          color: #72798b;
        }

        .wn-list-empty,
        .wn-editor-empty {
          display: flex;
          align-items: center;
          justify-content: center;
          flex-direction: column;
          gap: 10px;
          padding: 30px 16px;
          color: #656d80;
          text-align: center;
        }

        .wn-list-empty {
          min-height: 200px;
          border: 1px dashed #e2d8bf;
          border-radius: 10px;
        }

        .wn-list-empty p,
        .wn-editor-empty p {
          margin: 0;
          font-size: 12px;
          line-height: 1.6;
        }

        .wn-editor-empty {
          flex: 1;
          min-height: 450px;
        }

        .wn-editor-empty h2 {
          margin: 0;
          color: #25283b;
          font-size: 22px;
          font-weight: 550;
        }

        .wn-editor-empty p {
          max-width: 310px;
        }

        .wn-empty-icon {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 62px;
          height: 62px;
          border-radius: 15px;
          color: #92712c;
          background: #fff3cf;
        }

        .wn-mobile-nav {
          display: none;
        }

        .wn-sr-only {
          position: absolute;
          width: 1px;
          height: 1px;
          margin: -1px;
          padding: 0;
          overflow: hidden;
          border: 0;
          clip: rect(0, 0, 0, 0);
          white-space: nowrap;
        }

        .wn-spin {
          animation: wn-spin 0.85s linear infinite;
        }

        @keyframes wn-spin {
          to {
            transform: rotate(360deg);
          }
        }

        /*
         * Respond to the space available inside the application
         * shell, rather than assuming the full viewport is usable.
         */
        @container notes (max-width: 1000px) {
          .wn-layout {
            grid-template-columns:
              minmax(200px, 0.8fr)
              minmax(0, 1.6fr);
          }

          .wn-right-panel {
            display: grid;
            grid-column: 1 / -1;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            align-items: start;
          }

          .wn-controls {
            gap: 8px;
          }

          .wn-filters {
            order: 3;
            flex-basis: 100%;
          }

          .wn-sort {
            margin-left: 0;
          }

          .wn-document-heading {
            flex-basis: 100%;
          }

          .wn-document-actions {
            margin-left: 0;
          }
        }

        @container notes (max-width: 660px) {
          .wn-header {
            align-items: flex-start;
            gap: 10px;
          }

          .wn-heading h1 {
            font-size: 30px;
          }

          .wn-heading p {
            font-size: 13px;
          }

          .wn-header-actions {
            flex-shrink: 1;
            flex-wrap: wrap;
            justify-content: flex-end;
          }

          .wn-header-actions .wn-new {
            min-height: 40px;
            padding: 8px 10px;
            font-size: 12px;
          }

          .wn-stats {
            gap: 15px;
            font-size: 12px;
          }

          .wn-controls {
            display: grid;
            grid-template-columns: minmax(0, 1fr);
          }

          .wn-search {
            width: 100%;
            height: 42px;
          }

          .wn-sort {
            justify-content: space-between;
            width: 100%;
            height: 40px;
          }

          .wn-sort select {
            width: 100%;
            max-width: 100%;
          }

          .wn-filters {
            display: grid;
            order: initial;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            width: 100%;
          }

          .wn-page .wn-filter {
            min-height: 40px;
            padding: 0 4px;
            font-size: 11px;
          }

          .wn-mobile-nav {
            display: flex;
            gap: 6px;
            margin: 0 0 12px;
            padding: 4px;
            border-radius: 9px;
            background: #ede9df;
          }

          .wn-mobile-nav button {
            flex: 1;
            min-height: 40px;
            padding: 7px;
            border: 0;
            border-radius: 6px;
            color: #575d70;
            background: transparent;
            font-size: 13px;
          }

          .wn-mobile-nav button[aria-pressed="true"] {
            color: #202338;
            background: #fffefd;
          }

          .wn-layout {
            display: flex;
            flex-direction: column;
            gap: 12px;
          }

          .wn-list {
            width: 100%;
            max-height: none;
            overflow: visible;
          }

          .wn-editor-panel {
            width: 100%;
            min-height: 520px;
            padding: 14px;
          }

          .wn-layout[data-mobile-view="list"] > .wn-editor-panel,
          .wn-layout[data-mobile-view="list"] > .wn-right-panel {
            display: none;
          }

          .wn-layout[data-mobile-view="editor"] > .wn-list {
            display: none;
          }

          .wn-right-panel {
            display: flex;
            flex-direction: column;
            width: 100%;
          }

          .wn-document-body {
            min-height: 300px;
            font-size: 16px;
          }

          .wn-document-body h1 {
            font-size: 25px;
          }

          .wn-document-actions {
            width: 100%;
            gap: 7px;
          }

          .wn-title {
            height: 38px;
            font-size: 23px;
          }

          .wn-format-toolbar > button {
            flex-basis: 44px;
            height: 44px;
          }

          .wn-heading-select {
            flex-basis: 54px;
            min-height: 44px;
          }

          .wn-heading-select select {
            font-size: 16px;
          }

          .wn-page .wn-icon {
            width: 40px;
            height: 40px;
          }

          .wn-footer-right {
            margin-left: 0;
          }

          .wn-save-button {
            min-height: 38px;
            padding: 7px 11px;
          }

          .wn-menu button {
            min-height: 44px;
          }

          .wn-editor-tag button {
            width: 28px;
            height: 28px;
          }

          .wn-add-tag {
            min-height: 36px;
          }

          .wn-tag-form input {
            font-size: 16px;
          }

          .wn-document-body ul[data-checklist] > li {
            min-height: 32px;
          }

          .wn-document-body ul[data-checklist] input[type="checkbox"] {
            top: 4px;
            width: 20px;
            height: 20px;
          }

          .wn-side-action {
            min-height: 42px;
            font-size: 13px;
          }

          .wn-side-heading h2 {
            font-size: 16px;
          }

          .wn-summary {
            font-size: 14px;
          }

          .wn-apply {
            min-height: 42px;
          }

          .wn-details {
            font-size: 12px;
          }

          .wn-list-empty p {
            font-size: 14px;
          }
        }

        @media (max-width: 600px) {
          .wn-page {
            padding:
              14px
              10px
              max(18px, env(safe-area-inset-bottom));
          }

          .wn-search input,
          .wn-sort select {
            font-size: 16px;
          }
        }

        @media (pointer: coarse) {
          .wn-page .wn-icon {
            min-width: 44px;
            min-height: 44px;
          }
        }

        @media (prefers-reduced-motion: reduce) {
          .wn-spin {
            animation-duration: 1.6s;
          }
        }
        .wn-page button:focus,
        .wn-page button:focus-visible,
        .wn-page input:focus,
        .wn-page input:focus-visible,
        .wn-page select:focus,
        .wn-page select:focus-visible,
        .wn-page [contenteditable]:focus,
        .wn-page [contenteditable]:focus-visible {
          outline: none !important;
          box-shadow: none !important;
        }

        .wn-page .wn-title,
        .wn-page .wn-title:focus,
        .wn-page .wn-document-body,
        .wn-page .wn-document-body:focus,
        .wn-page .wn-heading-select select {
          border: 0 !important;
          outline: none !important;
          box-shadow: none !important;
        }

        .wn-page button:focus-visible {
          background-color: #eee8db;
        }

        .wn-page .wn-new:focus-visible {
          background-color: #373742;
        }

        .wn-save-state.is-error {
          color: #b2362c;
        }

        .wn-export-button {
          white-space: nowrap;
        }

        @media (max-width: 600px) {
          .wn-export-button {
            min-height: 44px;
            padding: 8px 12px;
          }
        }
      `}</style>
    </div>
  );
}