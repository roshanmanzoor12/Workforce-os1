$ErrorActionPreference = "Stop"

$BackendRoot = "C:\workforce-os\backend"
$Python = "C:\workforce-os\backend\.venv\Scripts\python.exe"

Set-Location $BackendRoot

Write-Host "================================================="
Write-Host " WorkforceOS Tenant Migration Discovery"
Write-Host "================================================="
Write-Host ""

Write-Host "[1/5] Alembic configuration files..."

$Configs = @(
    Get-ChildItem `
        -Path $BackendRoot `
        -Filter "*.ini" `
        -File `
        -Recurse
)

$AlembicConfigs = @()

foreach ($Config in $Configs)
{
    $Text = Get-Content `
        $Config.FullName `
        -Raw

    if (
        $Text -match "\[alembic\]"
    )
    {
        $AlembicConfigs += $Config

        Write-Host (
            "FOUND CONFIG: "
            + $Config.FullName
        )
    }
}

if (
    $AlembicConfigs.Count -eq 0
)
{
    throw "No Alembic config found."
}

Write-Host ""

Write-Host "[2/5] Tenant migration directories..."

$TenantDirs = @(
    Get-ChildItem `
        -Path $BackendRoot `
        -Directory `
        -Recurse |
    Where-Object {
        $_.FullName -match (
            "tenant.*migration|" +
            "migration.*tenant|" +
            "migrations\\tenant"
        )
    }
)

if (
    $TenantDirs.Count -eq 0
)
{
    Write-Host (
        "INFO no obvious tenant "
        + "migration directory name found"
    )
}
else
{
    foreach ($Dir in $TenantDirs)
    {
        Write-Host (
            "FOUND DIR: "
            + $Dir.FullName
        )
    }
}

Write-Host ""

Write-Host "[3/5] Alembic version files..."

$VersionFiles = @(
    Get-ChildItem `
        -Path $BackendRoot `
        -Filter "*.py" `
        -File `
        -Recurse |
    Where-Object {
        $_.FullName -match (
            "\\versions\\"
        )
    }
)

foreach (
    $File
    in (
        $VersionFiles |
        Sort-Object FullName
    )
)
{
    Write-Host (
        "VERSION: "
        + $File.FullName
    )
}

Write-Host ""

Write-Host "[4/5] Candidate tenant configs..."

foreach (
    $Config
    in $AlembicConfigs
)
{
    if (
        $Config.Name -match "tenant"
        -or
        (
            Get-Content `
                $Config.FullName `
                -Raw
        ) -match "tenant"
    )
    {
        Write-Host ""
        Write-Host (
            "CANDIDATE: "
            + $Config.FullName
        )

        & $Python `
            -m alembic `
            -c $Config.FullName `
            heads

        if (
            $LASTEXITCODE -ne 0
        )
        {
            Write-Host (
                "WARN unable to read heads "
                + "for this config"
            )
        }
    }
}

Write-Host ""

Write-Host "[5/5] Tenant migration references..."

$Matches = Get-ChildItem `
    -Path ".\app" `
    -Filter "*.py" `
    -File `
    -Recurse |
    Select-String `
        -Pattern @(
            "alembic.*tenant",
            "tenant.*alembic",
            "migrations.tenant",
            "tenant.*migration"
        )

foreach ($Match in $Matches)
{
    Write-Host (
        $Match.Path
        + ":"
        + $Match.LineNumber
        + " "
        + $Match.Line.Trim()
    )
}

Write-Host ""
Write-Host "================================================="
Write-Host " TENANT MIGRATION DISCOVERY: COMPLETE"
Write-Host "================================================="