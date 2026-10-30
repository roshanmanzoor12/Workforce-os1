#Requires -Version 5.1

$ErrorActionPreference = "Stop"

$BackendDirectory =
    Split-Path `
        -Parent `
        $PSScriptRoot

$Python =
    "C:\workforce-os\.venv\Scripts\python.exe"

$ExpectedRevision =
    "f8a1c3d4e5b6"

$MigrationFile =
    Join-Path `
        $BackendDirectory `
        "migrations\tenant\versions\f8a1c3d4e5b6_add_activity_state_events.py"

Write-Host ""
Write-Host "============================================="
Write-Host " WorkforceOS Phase 08 Migration Verification"
Write-Host "============================================="
Write-Host ""

if (-not (Test-Path $Python))
{
    throw (
        "WorkforceOS Python not found: " +
        $Python
    )
}

if (-not (Test-Path $MigrationFile))
{
    throw (
        "Phase 08 tenant migration file not found: " +
        $MigrationFile
    )
}

Push-Location $BackendDirectory

try
{
    Write-Host "[1/3] Compiling migration..."

    & $Python `
        -m py_compile `
        $MigrationFile

    if ($LASTEXITCODE -ne 0)
    {
        throw (
            "Phase 08 migration compile failed."
        )
    }

    Write-Host "PASS migration compile"
    Write-Host ""

    Write-Host "[2/3] Checking migration metadata..."

    $MetadataScript = @"
import importlib.util
from pathlib import Path

path = Path(r"$MigrationFile")

spec = importlib.util.spec_from_file_location(
    "phase08_migration",
    path,
)

if spec is None or spec.loader is None:
    raise SystemExit(
        "Unable to load migration."
    )

module = importlib.util.module_from_spec(
    spec
)

spec.loader.exec_module(
    module
)

if module.revision != "$ExpectedRevision":
    raise SystemExit(
        f"Unexpected revision: {module.revision}"
    )

print(module.revision)
"@

    $Revision =
        $MetadataScript |
        & $Python -

    if ($LASTEXITCODE -ne 0)
    {
        throw (
            "Unable to verify Phase 08 migration metadata."
        )
    }

    if (
        "$Revision".Trim()
        -ne $ExpectedRevision
    )
    {
        throw (
            "Migration revision mismatch. Expected " +
            $ExpectedRevision +
            " but received " +
            "$Revision"
        )
    }

    Write-Host (
        "PASS revision " +
        $ExpectedRevision
    )

    Write-Host ""
    Write-Host "[3/3] Checking tenant Alembic configuration..."

    $TenantIniCandidates =
        @(
            (
                Join-Path `
                    $BackendDirectory `
                    "alembic_tenant.ini"
            ),
            (
                Join-Path `
                    $BackendDirectory `
                    "migrations\tenant\alembic.ini"
            ),
            (
                Join-Path `
                    $BackendDirectory `
                    "tenant_alembic.ini"
            )
        )

    $TenantIni =
        $null

    foreach (
        $Candidate
        in $TenantIniCandidates
    )
    {
        if (
            Test-Path $Candidate
        )
        {
            $TenantIni =
                $Candidate

            break
        }
    }

    if ($null -eq $TenantIni)
    {
        Write-Host (
            "INFO Tenant Alembic ini was not auto-detected."
        )

        Write-Host (
            "Migration file itself is valid; use the existing " +
            "WorkforceOS tenant migration command to apply it."
        )
    }
    else
    {
        Write-Host (
            "Detected tenant Alembic config: " +
            $TenantIni
        )

        Write-Host ""
        Write-Host "Current tenant migration heads:"

        & $Python `
            -m alembic `
            -c $TenantIni `
            heads

        if ($LASTEXITCODE -ne 0)
        {
            throw (
                "Unable to inspect tenant Alembic heads."
            )
        }
    }

    Write-Host ""
    Write-Host "============================================="
    Write-Host " PHASE 08 MIGRATION VERIFICATION: PASS"
    Write-Host "============================================="
    Write-Host ""
}
finally
{
    Pop-Location
}