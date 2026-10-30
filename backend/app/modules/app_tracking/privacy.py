from __future__ import annotations

from dataclasses import dataclass


DEFAULT_MAX_WINDOW_TITLE_LENGTH = 512


@dataclass(
    frozen=True,
    slots=True,
)
class AppTrackingPrivacyPolicy:
    capture_window_titles: bool = False

    max_window_title_length: int = (
        DEFAULT_MAX_WINDOW_TITLE_LENGTH
    )

    def sanitize_window_title(
        self,
        window_title: str | None,
    ) -> str | None:
        if not self.capture_window_titles:
            return None

        if window_title is None:
            return None

        normalized = window_title.strip()

        if not normalized:
            return None

        return normalized[
            : self.max_window_title_length
        ]

    @staticmethod
    def sanitize_executable_path(
        executable_path: str | None,
    ) -> str | None:
        if executable_path is None:
            return None

        normalized = executable_path.strip()

        return normalized or None


__all__ = [
    "DEFAULT_MAX_WINDOW_TITLE_LENGTH",
    "AppTrackingPrivacyPolicy",
]