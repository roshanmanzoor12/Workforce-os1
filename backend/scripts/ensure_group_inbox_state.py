"""Run from C:\\workforce-os\\backend using the project's virtual environment."""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text
from app.core.database import ControlSessionLocal


async def main() -> None:
    async with ControlSessionLocal() as session:
        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS chat_group_inbox_state (
                conversation_id UUID NOT NULL
                    REFERENCES conversations(id) ON DELETE CASCADE,
                user_id UUID NOT NULL,
                cleared_before TIMESTAMPTZ NOT NULL,
                PRIMARY KEY (conversation_id, user_id)
            )
        """))
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_chat_group_inbox_state_user
            ON chat_group_inbox_state (user_id)
        """))
        await session.commit()
    print("Group inbox personal-clear state is ready.")


if __name__ == "__main__":
    asyncio.run(main())
