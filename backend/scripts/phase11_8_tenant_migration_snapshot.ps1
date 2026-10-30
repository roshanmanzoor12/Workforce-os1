$ErrorActionPreference = "Stop"

$BackendRoot = "C:\workforce-os\backend"
$Python = "C:\workforce-os\backend\.venv\Scripts\python.exe"

Set-Location $BackendRoot

Write-Host "================================================="
Write-Host " WorkforceOS Phase 11.8 Tenant Migration Snapshot"
Write-Host "================================================="
Write-Host ""

# =========================================================
# 1. FIND ALEMBIC CONFIGS
# =========================================================

Write-Host "[1/6] Alembic configs..."

$AlembicConfigs = @()

$IniFiles = Get-ChildItem `
    -Path $BackendRoot `
    -Filter "*.ini" `
    -File `
    -Recurse

foreach ($File in $IniFiles)
{
    $Text = Get-Content `
        -Path $File.FullName `
        -Raw

    if ($Text -match "\[alembic\]")
    {
        $AlembicConfigs += $File

        Write-Host ("ALEMBIC_CONFIG={0}" -f $File.FullName)
    }
}

if ($AlembicConfigs.Count -eq 0)
{
    throw "No Alembic configuration found."
}

Write-Host ""

# =========================================================
# 2. FIND TENANT CONFIG CANDIDATES
# =========================================================

Write-Host "[2/6] Tenant config candidates..."

$TenantConfigs = @()

foreach ($Config in $AlembicConfigs)
{
    $Text = Get-Content `
        -Path $Config.FullName `
        -Raw

    $IsTenantName = (
        $Config.Name -match "tenant"
    )

    $IsTenantContent = (
        $Text -match "tenant"
    )

    if (
        $IsTenantName `
        -or $IsTenantContent
    )
    {
        $TenantConfigs += $Config

        Write-Host ("TENANT_CONFIG={0}" -f $Config.FullName)
    }
}

if ($TenantConfigs.Count -eq 0)
{
    Write-Host "WARN no config explicitly identified as tenant"
}

Write-Host ""

# =========================================================
# 3. READ SCRIPT LOCATIONS
# =========================================================

Write-Host "[3/6] Alembic script locations..."

foreach ($Config in $AlembicConfigs)
{
    $Text = Get-Content `
        -Path $Config.FullName `
        -Raw

    $Match = [regex]::Match(
        $Text,
        '(?m)^\s*script_location\s*=\s*(.+?)\s*$'
    )

    if ($Match.Success)
    {
        $Location = $Match.Groups[1].Value.Trim()

        Write-Host (
            "SCRIPT_LOCATION[{0}]={1}" `
            -f $Config.Name, $Location
        )
    }
}

Write-Host ""

# =========================================================
# 4. ALEMBIC HEADS
# =========================================================

Write-Host "[4/6] Alembic heads..."

if ($TenantConfigs.Count -eq 0)
{
    Write-Host "INFO no tenant Alembic candidate available for heads"
}
else
{
    foreach ($Config in $TenantConfigs)
    {
        Write-Host ""

        Write-Host ("CONFIG_HEADS={0}" -f $Config.FullName)

        & $Python `
            -m alembic `
            -c $Config.FullName `
            heads

        if ($LASTEXITCODE -ne 0)
        {
            Write-Host (
                "WARN heads failed for {0}" `
                -f $Config.FullName
            )
        }
    }
}

Write-Host ""

# =========================================================
# 5. VERSION FILES + REVISION CHAIN
# =========================================================

Write-Host "[5/6] Migration revision files..."

$VersionFiles = @(
    Get-ChildItem `
        -Path $BackendRoot `
        -Filter "*.py" `
        -File `
        -Recurse |
    Where-Object {
        $_.FullName -match "\\versions\\"
    }
)

foreach ($File in ($VersionFiles | Sort-Object FullName))
{
    $Content = Get-Content `
        -Path $File.FullName `
        -Raw

    $RevisionMatch = [regex]::Match(
        $Content,
        '(?m)^\s*revision\s*(?::[^=]+)?=\s*["'']([^"'']+)["'']'
    )

    $DownMatch = [regex]::Match(
        $Content,
        '(?m)^\s*down_revision\s*(?::[^=]+)?=\s*["'']([^"'']+)["'']'
    )

    if ($RevisionMatch.Success)
    {
        $Revision = $RevisionMatch.Groups[1].Value

        $DownRevision = "None"

        if ($DownMatch.Success)
        {
            $DownRevision = $DownMatch.Groups[1].Value
        }

        Write-Host ("REVISION_FILE={0}" -f $File.FullName)
        Write-Host ("REVISION={0}" -f $Revision)
        Write-Host ("DOWN_REVISION={0}" -f $DownRevision)
        Write-Host "---"
    }
}

Write-Host ""

# =========================================================
# 6. MEETING METADATA
# =========================================================

Write-Host "[6/6] Meeting model metadata..."

$MetadataScript = @'
from app.modules.meetings.models import (
    Meeting,
    MeetingParticipant,
)

print(
    "MEETING_TABLE="
    + Meeting.__tablename__
)

print(
    "PARTICIPANT_TABLE="
    + MeetingParticipant.__tablename__
)

print(
    "MEETING_COLUMNS="
    + ",".join(
        column.name
        for column
        in Meeting.__table__.columns
    )
)

print(
    "PARTICIPANT_COLUMNS="
    + ",".join(
        column.name
        for column
        in MeetingParticipant.__table__.columns
    )
)

for model in (
    Meeting,
    MeetingParticipant,
):
    columns = {
        column.name
        for column
        in model.__table__.columns
    }

    if "workspace_id" in columns:
        raise SystemExit(
            model.__name__
            + " must not contain workspace_id."
        )

print("TENANT_SCOPE_CHECK=PASS")
'@

$MetadataScript | & $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "Meeting metadata inspection failed."
}

Write-Host ""
Write-Host "================================================="
Write-Host " TENANT MIGRATION SNAPSHOT: COMPLETE"
Write-Host "================================================="