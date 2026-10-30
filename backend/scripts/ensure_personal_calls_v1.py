
import asyncio

from sqlalchemy import text
from app.core.database import get_control_db

DDL = [
    """
    CREATE TABLE IF NOT EXISTS personal_call_numbers_v1 (
        user_id UUID PRIMARY KEY
            REFERENCES users(id) ON DELETE CASCADE,
        calling_number VARCHAR(10) NOT NULL UNIQUE,
        CONSTRAINT ck_personal_call_number_v1
            CHECK (calling_number ~ '^[1-9][0-9]{9}$')
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS personal_call_favorites_v1 (
        owner_id UUID NOT NULL
            REFERENCES users(id) ON DELETE CASCADE,
        target_id UUID NOT NULL
            REFERENCES users(id) ON DELETE CASCADE,
        PRIMARY KEY (owner_id, target_id),
        CONSTRAINT ck_personal_call_favorite_not_self_v1
            CHECK (owner_id <> target_id)
    )
    """,
]


async def main():
    async for session in get_control_db():
        for statement in DDL:
            await session.execute(text(statement))
        await session.commit()
        print(
            "Personal call numbers and favorites tables are ready."
        )
        return


if __name__ == "__main__":
    asyncio.run(main())
