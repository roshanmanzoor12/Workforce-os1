"""Keep an explicit profile-photo choice across later Google sign-ins."""
from typing import Protocol


class AvatarOwner(Protocol):
    avatar_url: str | None
    avatar_source: str


def sync_google_avatar(user: AvatarOwner, google_photo: str | None) -> None:
    if user.avatar_source in {"auto", "google"} and google_photo:
        user.avatar_url = google_photo
        user.avatar_source = "google"
