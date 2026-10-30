from __future__ import annotations

import asyncio
import sys
import uuid
from pathlib import Path


BACKEND_ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(BACKEND_ROOT),
    )


from sqlalchemy import text

from app.core.database import (
    ControlSessionLocal,
)


WORKSPACE_ID = uuid.UUID(
    "34527ffb-e094-4e5e-89ee-4cab97244fc3"
)

CHANNEL_ID = uuid.UUID(
    "58672c60-400d-428a-bdca-f4e611e3d845"
)

TEST_USERS = (
    uuid.UUID(
        "f045fb86-71b0-4deb-9012-654569d18961"
    ),
    uuid.UUID(
        "4e1a462f-e7f4-43da-a413-0f4a097ba5ca"
    ),
)


async def ensure_workspace_membership(
    session,
    *,
    user_id: uuid.UUID,
) -> None:
    result = await session.execute(
        text(
            """
            SELECT
                id,
                status
            FROM workspace_memberships
            WHERE
                workspace_id = :workspace_id
                AND user_id = :user_id
            LIMIT 1
            """
        ),
        {
            "workspace_id": WORKSPACE_ID,
            "user_id": user_id,
        },
    )

    row = result.mappings().first()

    if row is None:
        membership_id = uuid.uuid4()

        await session.execute(
            text(
                """
                INSERT INTO workspace_memberships (
                    workspace_id,
                    user_id,
                    role_key,
                    status,
                    invited_by_user_id,
                    invited_at,
                    joined_at,
                    suspended_at,
                    removed_at,
                    id,
                    created_at,
                    updated_at
                )
                VALUES (
                    :workspace_id,
                    :user_id,
                    'member',
                    'active',
                    NULL,
                    NULL,
                    NOW(),
                    NULL,
                    NULL,
                    :membership_id,
                    NOW(),
                    NOW()
                )
                """
            ),
            {
                "workspace_id": WORKSPACE_ID,
                "user_id": user_id,
                "membership_id": membership_id,
            },
        )

        print(
            "PASS workspace membership created: "
            f"{user_id}"
        )

        return

    await session.execute(
        text(
            """
            UPDATE workspace_memberships
            SET
                role_key = 'member',
                status = 'active',
                joined_at = COALESCE(
                    joined_at,
                    NOW()
                ),
                suspended_at = NULL,
                removed_at = NULL,
                updated_at = NOW()
            WHERE id = :membership_id
            """
        ),
        {
            "membership_id": row["id"],
        },
    )

    print(
        "PASS workspace membership active: "
        f"{user_id}"
    )


async def ensure_channel_membership(
    session,
    *,
    user_id: uuid.UUID,
) -> None:
    result = await session.execute(
        text(
            """
            SELECT
                id,
                left_at
            FROM workspace_channel_members
            WHERE
                channel_id = :channel_id
                AND user_id = :user_id
            LIMIT 1
            """
        ),
        {
            "channel_id": CHANNEL_ID,
            "user_id": user_id,
        },
    )

    row = result.mappings().first()

    if row is None:
        membership_id = uuid.uuid4()

        await session.execute(
            text(
                """
                INSERT INTO workspace_channel_members (
                    id,
                    channel_id,
                    user_id,
                    role,
                    joined_at,
                    left_at
                )
                VALUES (
                    :membership_id,
                    :channel_id,
                    :user_id,
                    'member',
                    NOW(),
                    NULL
                )
                """
            ),
            {
                "membership_id": membership_id,
                "channel_id": CHANNEL_ID,
                "user_id": user_id,
            },
        )

        print(
            "PASS channel membership created: "
            f"{user_id}"
        )

        return

    await session.execute(
        text(
            """
            UPDATE workspace_channel_members
            SET
                role = 'member',
                left_at = NULL
            WHERE id = :membership_id
            """
        ),
        {
            "membership_id": row["id"],
        },
    )

    print(
        "PASS channel membership active: "
        f"{user_id}"
    )


async def verify(
    session,
) -> None:
    result = await session.execute(
        text(
            """
            SELECT
                u.id AS user_id,
                u.email,
                wm.role_key AS workspace_role,
                wm.status AS workspace_status,
                cm.role AS channel_role,
                cm.left_at
            FROM users AS u
            JOIN workspace_memberships AS wm
                ON wm.user_id = u.id
            JOIN workspace_channel_members AS cm
                ON cm.user_id = u.id
            WHERE
                wm.workspace_id = :workspace_id
                AND cm.channel_id = :channel_id
                AND u.id IN (
                    :user_a,
                    :user_b
                )
            ORDER BY u.email
            """
        ),
        {
            "workspace_id": WORKSPACE_ID,
            "channel_id": CHANNEL_ID,
            "user_a": TEST_USERS[0],
            "user_b": TEST_USERS[1],
        },
    )

    rows = result.mappings().all()

    print()
    print(
        "Phase 16D runtime test memberships:"
    )
    print()

    for row in rows:
        print(
            f"user={row['email']} | "
            f"workspace_role="
            f"{row['workspace_role']} | "
            f"workspace_status="
            f"{row['workspace_status']} | "
            f"channel_role="
            f"{row['channel_role']} | "
            f"left_at="
            f"{row['left_at']}"
        )

    if len(rows) != len(TEST_USERS):
        raise RuntimeError(
            "Not all Phase 16D users "
            "have shared memberships."
        )

    verified_ids = {
        row["user_id"]
        for row in rows
    }

    if verified_ids != set(TEST_USERS):
        raise RuntimeError(
            "Unexpected Phase 16D membership users."
        )

    for row in rows:
        if row["workspace_status"] != "active":
            raise RuntimeError(
                "Workspace membership "
                "is not active."
            )

        if row["left_at"] is not None:
            raise RuntimeError(
                "Channel membership "
                "is not active."
            )

    print()
    print(
        "PASS: Phase 16D shared "
        "membership setup complete."
    )


async def main() -> None:
    async with ControlSessionLocal() as session:
        try:
            for user_id in TEST_USERS:
                await ensure_workspace_membership(
                    session,
                    user_id=user_id,
                )

                await ensure_channel_membership(
                    session,
                    user_id=user_id,
                )

            await session.commit()

            await verify(
                session,
            )

        except Exception:
            await session.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(
        main()
    )