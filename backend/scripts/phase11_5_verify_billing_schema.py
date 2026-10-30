from __future__ import annotations

import asyncio

from sqlalchemy import text

from app.core.database import control_engine


EXPECTED_REVISION = (
    "d3e4f5a6b7c8"
)

EXPECTED_TABLES = {
    "billing_customers",
    "billing_subscriptions",
}


async def main() -> None:
    async with control_engine.connect() as connection:
        revision_result = (
            await connection.execute(
                text(
                    """
                    SELECT version_num
                    FROM alembic_version
                    """
                )
            )
        )

        revision = (
            revision_result
            .scalar_one()
        )

        print(
            "Control revision:",
            revision,
        )

        if revision != EXPECTED_REVISION:
            raise RuntimeError(
                "Unexpected control database "
                "migration revision."
            )

        table_result = (
            await connection.execute(
                text(
                    """
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                      AND table_name IN (
                          'billing_customers',
                          'billing_subscriptions'
                      )
                    ORDER BY table_name
                    """
                )
            )
        )

        tables = {
            row[0]
            for row in table_result.fetchall()
        }

        for table in sorted(
            tables
        ):
            print(
                "Table:",
                table,
            )

        missing = (
            EXPECTED_TABLES
            - tables
        )

        if missing:
            raise RuntimeError(
                "Missing billing tables: "
                + ", ".join(
                    sorted(missing)
                )
            )

        column_result = (
            await connection.execute(
                text(
                    """
                    SELECT
                        table_name,
                        column_name
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name IN (
                          'billing_customers',
                          'billing_subscriptions'
                      )
                    ORDER BY
                        table_name,
                        ordinal_position
                    """
                )
            )
        )

        columns = (
            column_result.fetchall()
        )

        forbidden = {
            "card_number",
            "cardnumber",
            "cvv",
            "cvc",
            "security_code",
        }

        for table_name, column_name in columns:
            if (
                column_name.lower()
                in forbidden
            ):
                raise RuntimeError(
                    "Forbidden payment field found: "
                    f"{table_name}.{column_name}"
                )

        print(
            "PASS billing control schema"
        )


if __name__ == "__main__":
    asyncio.run(
        main()
    )