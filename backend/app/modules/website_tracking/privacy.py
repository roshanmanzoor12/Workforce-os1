from __future__ import annotations

import ipaddress
from dataclasses import dataclass
from urllib.parse import urlsplit


@dataclass(
    frozen=True,
    slots=True,
)
class WebsiteTrackingPrivacyPolicy:
    """
    Privacy boundary for Website Tracking.

    Default policy deliberately stores only the normalized domain.

    It does not retain:
    - query strings
    - fragments
    - typed text
    - form values
    - passwords
    - page content
    - page titles
    - full URLs

    Full URL/title capture can only be enabled explicitly later
    through a monitoring/privacy policy.
    """

    capture_page_urls: bool = False
    capture_page_titles: bool = False

    maximum_domain_length: int = 255
    maximum_url_length: int = 8192
    maximum_title_length: int = 1024

    def sanitize_domain(
        self,
        value: str,
    ) -> str:
        normalized = normalize_domain(
            value
        )

        if (
            len(normalized)
            > self.maximum_domain_length
        ):
            raise ValueError(
                "Normalized domain exceeds maximum length."
            )

        return normalized

    def sanitize_page_url(
        self,
        value: str | None,
    ) -> str | None:
        if not self.capture_page_urls:
            return None

        if value is None:
            return None

        cleaned = value.strip()

        if not cleaned:
            return None

        if (
            len(cleaned)
            > self.maximum_url_length
        ):
            cleaned = cleaned[
                : self.maximum_url_length
            ]

        try:
            parsed = urlsplit(
                cleaned
            )
        except ValueError:
            return None

        scheme = parsed.scheme.lower()

        if scheme not in {
            "http",
            "https",
        }:
            return None

        hostname = parsed.hostname

        if hostname is None:
            return None

        try:
            normalized_domain = (
                normalize_domain(
                    hostname
                )
            )
        except ValueError:
            return None

        try:
            port = parsed.port
        except ValueError:
            return None

        netloc = normalized_domain

        if port is not None:
            is_default_port = (
                (
                    scheme == "http"
                    and port == 80
                )
                or (
                    scheme == "https"
                    and port == 443
                )
            )

            if not is_default_port:
                netloc = (
                    f"{normalized_domain}:{port}"
                )

        path = parsed.path or "/"

        # Deliberately drop query + fragment.
        return (
            f"{scheme}://"
            f"{netloc}"
            f"{path}"
        )

    def sanitize_page_title(
        self,
        value: str | None,
    ) -> str | None:
        if not self.capture_page_titles:
            return None

        if value is None:
            return None

        cleaned = value.strip()

        if not cleaned:
            return None

        return cleaned[
            : self.maximum_title_length
        ]


def normalize_domain(
    value: str,
) -> str:
    """
    Convert browser/domain input into a stable domain identifier.

    Examples:

        www.github.com
            -> github.com

        https://github.com/user?a=b
            -> github.com

        EXAMPLE.COM:443
            -> example.com

    This is hostname normalization, not registrable-domain
    collapsing. For example:

        docs.example.com
            stays docs.example.com
    """

    if not isinstance(
        value,
        str,
    ):
        raise ValueError(
            "Domain must be a string."
        )

    raw = value.strip().lower()

    if not raw:
        raise ValueError(
            "Domain is required."
        )

    if "://" in raw:
        try:
            parsed = urlsplit(
                raw
            )
        except ValueError as exception:
            raise ValueError(
                "Domain is invalid."
            ) from exception

        raw = (
            parsed.hostname
            or ""
        )

    else:
        raw = raw.split(
            "/",
            1,
        )[0]

        raw = raw.split(
            "?",
            1,
        )[0]

        raw = raw.split(
            "#",
            1,
        )[0]

        if raw.startswith(
            "["
        ):
            closing_index = raw.find(
                "]"
            )

            if closing_index < 0:
                raise ValueError(
                    "Domain is invalid."
                )

            raw = raw[
                1:closing_index
            ]

        elif ":" in raw:
            (
                host_candidate,
                separator,
                port_candidate,
            ) = raw.rpartition(
                ":"
            )

            if (
                separator
                and host_candidate
                and port_candidate.isdigit()
            ):
                raw = host_candidate

    raw = raw.strip(
        "."
    )

    if raw.startswith(
        "www."
    ):
        raw = raw[
            len("www.") :
        ]

    if not raw:
        raise ValueError(
            "Domain is invalid."
        )

    try:
        ipaddress.ip_address(
            raw
        )

        return raw

    except ValueError:
        pass

    labels = raw.split(
        "."
    )

    normalized_labels: list[str] = []

    for label in labels:
        if not label:
            raise ValueError(
                "Domain contains an empty label."
            )

        try:
            ascii_label = (
                label.encode(
                    "idna"
                )
                .decode(
                    "ascii"
                )
                .lower()
            )

        except UnicodeError as exception:
            raise ValueError(
                "Domain is invalid."
            ) from exception

        if (
            len(ascii_label)
            > 63
        ):
            raise ValueError(
                "Domain label exceeds maximum length."
            )

        if (
            ascii_label.startswith(
                "-"
            )
            or ascii_label.endswith(
                "-"
            )
        ):
            raise ValueError(
                "Domain label is invalid."
            )

        normalized_labels.append(
            ascii_label
        )

    normalized = ".".join(
        normalized_labels
    )

    if len(normalized) > 255:
        raise ValueError(
            "Domain exceeds maximum length."
        )

    return normalized


__all__ = [
    "WebsiteTrackingPrivacyPolicy",
    "normalize_domain",
]