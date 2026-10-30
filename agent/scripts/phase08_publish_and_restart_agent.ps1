#Requires -Version 5.1

$ErrorActionPreference = "Stop"

$AgentProjectDirectory =
    "C:\workforce-os\agent\WorkforceOS.Agent"

$AgentProject =
    Join-Path `
        $AgentProjectDirectory `
        "WorkforceOS.Agent.csproj"

$PublishDirectory =
    "C:\workforce-os\artifacts\agent\win-x64"

$ServiceName =
    "WorkforceOSAgent"

$PublishedExecutable =
    Join-Path `
        $PublishDirectory `
        "WorkforceOS.Agent.exe"

Write-Host ""
Write-Host "================================================="
Write-Host " WorkforceOS Phase 08 Publish + Restart Agent"
Write-Host "================================================="
Write-Host ""

# ============================================================
# 1. VERIFY PROJECT
# ============================================================

Write-Host "[1/6] Verifying agent project..."

if (-not (Test-Path $AgentProject))
{
    throw (
        "Agent project not found: " +
        $AgentProject
    )
}

Write-Host "PASS agent project"
Write-Host ""

# ============================================================
# 2. RELEASE BUILD
# ============================================================

Write-Host "[2/6] Building Release agent..."

Push-Location $AgentProjectDirectory

try
{
    dotnet build `
        --configuration Release

    if ($LASTEXITCODE -ne 0)
    {
        throw (
            "Phase 08 Release build failed."
        )
    }
}
finally
{
    Pop-Location
}

Write-Host "PASS Release build"
Write-Host ""

# ============================================================
# 3. STOP SERVICE
# ============================================================

Write-Host "[3/6] Stopping WorkforceOS Agent service..."

$Service =
    Get-Service `
        -Name $ServiceName `
        -ErrorAction SilentlyContinue

if ($null -eq $Service)
{
    throw (
        "Windows service not found: " +
        $ServiceName
    )
}

if ($Service.Status -eq "Running")
{
    Stop-Service `
        -Name $ServiceName `
        -Force

    $Service.WaitForStatus(
        "Stopped",
        [TimeSpan]::FromSeconds(
            30
        )
    )
}

$Service =
    Get-Service `
        -Name $ServiceName

if ($Service.Status -ne "Stopped")
{
    throw (
        "Unable to stop WorkforceOS Agent service."
    )
}

Write-Host "PASS service stopped"
Write-Host ""

# ============================================================
# 4. PUBLISH
# ============================================================

Write-Host "[4/6] Publishing latest Phase 08 agent..."

if (Test-Path $PublishDirectory)
{
    Remove-Item `
        -Path $PublishDirectory `
        -Recurse `
        -Force
}

New-Item `
    -ItemType Directory `
    -Path $PublishDirectory `
    -Force |
    Out-Null

Push-Location $AgentProjectDirectory

try
{
    dotnet publish `
        $AgentProject `
        --configuration Release `
        --runtime win-x64 `
        --self-contained false `
        --output $PublishDirectory

    if ($LASTEXITCODE -ne 0)
    {
        throw (
            "Phase 08 agent publish failed."
        )
    }
}
finally
{
    Pop-Location
}

if (-not (Test-Path $PublishedExecutable))
{
    throw (
        "Published executable not found: " +
        $PublishedExecutable
    )
}

Write-Host "PASS agent published"
Write-Host ""

# ============================================================
# 5. START SERVICE
# ============================================================

Write-Host "[5/6] Starting WorkforceOS Agent service..."

Start-Service `
    -Name $ServiceName

$Service =
    Get-Service `
        -Name $ServiceName

$Service.WaitForStatus(
    "Running",
    [TimeSpan]::FromSeconds(
        30
    )
)

$Service =
    Get-Service `
        -Name $ServiceName

if ($Service.Status -ne "Running")
{
    throw (
        "WorkforceOS Agent service failed to start."
    )
}

Write-Host "PASS service running"
Write-Host ""

# ============================================================
# 6. BASIC AGENT STATUS
# ============================================================

Write-Host "[6/6] Checking published agent status..."

& $PublishedExecutable `
    --status

if ($LASTEXITCODE -ne 0)
{
    throw (
        "Published WorkforceOS Agent status check failed."
    )
}

Write-Host ""
Write-Host "================================================="
Write-Host " PHASE 08 PUBLISH + RESTART: PASS"
Write-Host "================================================="
Write-Host ""
Write-Host "Published executable:"
Write-Host $PublishedExecutable
Write-Host ""
Write-Host "Next:"
Write-Host "Run --activity-session-helper from the logged-in user session."
Write-Host ""