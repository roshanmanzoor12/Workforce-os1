from __future__ import annotations

from enum import Enum


class _CaseInsensitiveEnumValue(str):
    def __new__(
        cls,
        value: str,
    ) -> "_CaseInsensitiveEnumValue":
        return str.__new__(
            cls,
            value,
        )

    def __eq__(
        self,
        other: object,
    ) -> bool:
        if isinstance(
            other,
            str,
        ):
            return self.casefold() == other.casefold()

        return NotImplemented

    def __hash__(
        self,
    ) -> int:
        return hash(
            self.casefold()
        )


class _CaseInsensitiveStrEnum(
    str,
    Enum,
):
    def __new__(
        cls,
        value: str,
    ) -> "_CaseInsensitiveStrEnum":
        member = str.__new__(
            cls,
            value,
        )

        member._value_ = (
            _CaseInsensitiveEnumValue(
                value
            )
        )

        return member

    @classmethod
    def _missing_(
        cls,
        value: object,
    ) -> "_CaseInsensitiveStrEnum | None":
        if not isinstance(
            value,
            str,
        ):
            return None

        normalized = value.casefold()

        for member in cls:
            if (
                member.value.casefold()
                == normalized
            ):
                return member

        return None


class WorkspaceMembershipRole(
    _CaseInsensitiveStrEnum,
):
    OWNER = "owner"
    ADMIN = "admin"
    MANAGER = "manager"
    MEMBER = "member"
    CLIENT = "client"


class WorkspaceMembershipStatus(
    _CaseInsensitiveStrEnum,
):
    INVITED = "invited"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    REMOVED = "removed"


class WorkspaceMembershipSource(
    _CaseInsensitiveStrEnum,
):
    CREATOR = "creator"
    INVITATION = "invitation"
    ADMIN = "admin"


__all__ = [
    "WorkspaceMembershipRole",
    "WorkspaceMembershipStatus",
    "WorkspaceMembershipSource",
]