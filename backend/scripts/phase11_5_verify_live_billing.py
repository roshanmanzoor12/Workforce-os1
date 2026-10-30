from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from sqlalchemy import text


BACKEND_ROOT = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)

backend_root_text = str(
    BACKEND_ROOT
)

if backend_root_text not in sys.path:
    sys.path.insert(
        0,
        backend_root_text,
    )


from app.core.database import control_engine  # noqa: E402


EXPECTED_REVISION = (
    "d3e4f5a6b7c8"
)


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
                "Unexpected control DB revision."
            )

        result = await connection.execute(
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

        rows = result.fetchall()

        if not rows:
            raise RuntimeError(
                "Billing schema not found."
            )

        tables = {
            row[0]
            for row in rows
        }

        expected_tables = {
            "billing_customers",
            "billing_subscriptions",
        }

        missing = (
            expected_tables
            - tables
        )

        if missing:
            raise RuntimeError(
                "Missing billing tables: "
                + ", ".join(
                    sorted(missing)
                )
            )

        print(
            "PASS billing tables present"
        )

        forbidden_columns = {
            "card_number",
            "cardnumber",
            "cvv",
            "cvc",
            "security_code",
        }

        for table_name, column_name in rows:
            if (
                column_name.lower()
                in forbidden_columns
            ):
                raise RuntimeError(
                    "Raw payment field exists: "
                    f"{table_name}.{column_name}"
                )

        print(
            "PASS no raw payment-card columns"
        )

        customer_count_result = (
            await connection.execute(
                text(
                    """
                    SELECT COUNT(*)
                    FROM billing_customers
                    """
                )
            )
        )

        subscription_count_result = (
            await connection.execute(
                text(
                    """
                    SELECT COUNT(*)
                    FROM billing_subscriptions
                    """
                )
            )
        )

        customer_count = int(
            customer_count_result.scalar_one()
        )

        subscription_count = int(
            subscription_count_result.scalar_one()
        )

        print(
            "Billing customers:",
            customer_count,
        )

        print(
            "Billing subscriptions:",
            subscription_count,
        )

        print(
            "PASS Phase 11.5 live billing schema"
        )


if __name__ == "__main__":
    asyncio.run(
        main()
    )