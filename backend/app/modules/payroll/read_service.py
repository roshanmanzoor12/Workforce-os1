from __future__ import annotations

import uuid

from fastapi import (
    HTTPException,
    status,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.modules.payroll.models import (
    PayrollRun,
)
from app.modules.payroll.repository import (
    PayrollRepository,
)
from app.modules.payroll.summary import (
    PayrollSummaryBuilder,
)
from app.modules.payroll.summary_schemas import (
    PayrollRunSummaryResponse,
)


class PayrollReadService:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.repository = (
            PayrollRepository(
                session
            )
        )

    async def get_run(
        self,
        run_id: uuid.UUID,
    ) -> PayrollRun:
        run = await (
            self.repository
            .get_run(
                run_id
            )
        )

        if run is None:
            raise HTTPException(
                status_code=(
                    status
                    .HTTP_404_NOT_FOUND
                ),
                detail=(
                    "Payroll run not found."
                ),
            )

        return run

    async def summary(
        self,
        *,
        run_id: uuid.UUID,
    ) -> PayrollRunSummaryResponse:
        run = await self.get_run(
            run_id
        )

        calculations = await (
            self.repository
            .list_calculations(
                run_id=run_id
            )
        )

        return (
            PayrollSummaryBuilder.build(
                run=run,
                calculations=(
                    calculations
                ),
            )
        )


__all__ = [
    "PayrollReadService",
]