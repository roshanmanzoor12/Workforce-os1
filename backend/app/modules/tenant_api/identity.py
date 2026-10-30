from __future__ import annotations

import uuid


def user_id_from(
    user: object,
) -> uuid.UUID:
    value = getattr(
        user,
        "id",
        None,
    )

    if value is None:
        raise RuntimeError(
            "Authenticated user does not expose id."
        )

    if isinstance(
        value,
        uuid.UUID,
    ):
        return value

    return uuid.UUID(
        str(value)
    )


__all__ = [
    "user_id_from",
]