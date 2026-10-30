param(
    [int]$AgeHours = 24,
    [int]$BatchSize = 100
)

$ErrorActionPreference = "Stop"

$BackendRoot = "C:\workforce-os\backend"

$Python = (
    "C:\workforce-os\backend\" +
    ".venv\Scripts\python.exe"
)

Set-Location $BackendRoot

if ($AgeHours -lt 1)
{
    throw "AgeHours must be >= 1."
}

if ($BatchSize -lt 1)
{
    throw "BatchSize must be >= 1."
}

Write-Host "================================================="
Write-Host " WorkforceOS Attachment Orphan Cleanup"
Write-Host "================================================="
Write-Host ""

Write-Host (
    "Age threshold: " +
    $AgeHours +
    " hour(s)"
)

Write-Host (
    "Batch size: " +
    $BatchSize
)

Write-Host ""

$CleanupScript = @'
import asyncio
import sys

from app.core.database import (
    ControlSessionLocal,
)
from app.modules.attachments.cleanup import (
    AttachmentOrphanCleanupService,
)
from app.modules.attachments.storage import (
    get_attachment_storage,
)


async def main() -> None:
    age_hours = int(
        sys.argv[1]
    )

    batch_size = int(
        sys.argv[2]
    )

    async with ControlSessionLocal() as session:
        service = (
            AttachmentOrphanCleanupService(
                session=session,
                storage=(
                    get_attachment_storage()
                ),
            )
        )

        result = await service.run_once(
            age_hours=age_hours,
            batch_size=batch_size,
        )

        print(
            "Scanned:",
            result.scanned,
        )

        print(
            "Deleted:",
            result.deleted,
        )

        print(
            "Failed:",
            result.failed,
        )

        if result.failed:
            raise SystemExit(
                "Cleanup completed "
                "with failures."
            )


asyncio.run(
    main()
)
'@

$CleanupScript |
    & $Python - $AgeHours $BatchSize

if ($LASTEXITCODE -ne 0)
{
    throw (
        "Attachment orphan cleanup failed."
    )
}

Write-Host ""
Write-Host "PASS attachment orphan cleanup"