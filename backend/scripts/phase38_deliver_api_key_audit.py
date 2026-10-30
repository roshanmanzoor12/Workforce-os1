from __future__ import annotations

import argparse
import asyncio
from contextlib import aclosing
from uuid import UUID

from sqlalchemy import select

from app.core.database import get_control_db
from app.db.tenant import (
    dispose_all_tenant_engines,
    tenant_session,
)
from app.db.tenant_models import TenantMetadata
from app.modules.api_keys.audit_delivery import APIKeyAuditDelivery
from app.modules.workspaces.models import (
    TENANT_STATUS_READY,
    TenantDatabaseRegistry,
)


async def run(
    *,
    workspace_id: UUID,
    limit: int,
) -> int:
    """
    Trusted backend command.

    Database routing comes exclusively from the control registry.
    No arbitrary database URL or database name is accepted.
    """

    async with aclosing(get_control_db()) as sessions:
        async for control_session in sessions:
            result = await control_session.execute(
                select(TenantDatabaseRegistry).where(
                    TenantDatabaseRegistry.workspace_id
                    == workspace_id
                )
            )

            registry = result.scalar_one_or_none()

            if registry is None:
                raise RuntimeError(
                    "Workspace has no tenant database registry."
                )

            if registry.status != TENANT_STATUS_READY:
                raise RuntimeError(
                    "Tenant database is not ready."
                )

            database_name = registry.database_name
            cluster_key = registry.cluster_key
            schema_version = registry.schema_version

            # Finish registry lookup before starting audit delivery.
            await control_session.rollback()

            async with tenant_session(
                database_name,
                cluster_key=cluster_key,
            ) as tenant_db:
                result = await tenant_db.execute(
                    select(TenantMetadata).limit(2)
                )

                metadata_rows = result.scalars().all()

                if len(metadata_rows) != 1:
                    raise RuntimeError(
                        "Tenant database must have one identity record."
                    )

                metadata = metadata_rows[0]

                if metadata.workspace_id != workspace_id:
                    raise RuntimeError(
                        "Physical tenant workspace identity mismatch."
                    )

                if not metadata.is_active:
                    raise RuntimeError(
                        "Physical tenant database is inactive."
                    )

                if (
                    schema_version is not None
                    and metadata.schema_version != schema_version
                ):
                    raise RuntimeError(
                        "Tenant compatibility marker mismatch."
                    )

                delivery = APIKeyAuditDelivery(
                    tenant_session=tenant_db,
                    control_session=control_session,
                    workspace_id=workspace_id,
                )

                return await delivery.deliver(limit=limit)

    raise RuntimeError(
        "Control database session was unavailable."
    )


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Deliver queued API key audit events."
    )

    parser.add_argument(
        "--workspace-id",
        required=True,
        type=UUID,
    )

    parser.add_argument(
        "--limit",
        default=100,
        type=int,
    )

    arguments = parser.parse_args()

    if not 1 <= arguments.limit <= 1000:
        parser.error("--limit must be between 1 and 1000.")

    try:
        delivered = await run(
            workspace_id=arguments.workspace_id,
            limit=arguments.limit,
        )

        print("Delivered API key audit events:", delivered)

    finally:
        await dispose_all_tenant_engines()


if __name__ == "__main__":
    asyncio.run(main())