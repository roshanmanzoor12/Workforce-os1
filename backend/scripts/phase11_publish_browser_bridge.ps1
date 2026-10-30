#Requires -Version 5.1

$ErrorActionPreference = "Stop"

$AgentProject = (
    "C:\workforce-os\agent\WorkforceOS.Agent\WorkforceOS.Agent.csproj"
)

$LauncherProject = (
    "C:\workforce-os\agent\WorkforceOS.WebsiteNativeHost\WorkforceOS.WebsiteNativeHost.csproj"
)

$AgentOutput = (
    "C:\workforce-os\artifacts\agent\win-x64"
)

$LauncherOutput = (
    "C:\workforce-os\artifacts\website-native-host"
)

Write-Host ""
Write-Host "==============================================="
Write-Host " WorkforceOS Phase 11 Browser Bridge Publish"
Write-Host "==============================================="
Write-Host ""

Write-Host "[1/4] Publishing Agent..."

dotnet publish `
    $AgentProject `
    --configuration Release `
    --runtime win-x64 `
    --self-contained false `
    --output $AgentOutput

if ($LASTEXITCODE -ne 0)
{
    throw "Agent publish failed."
}

Write-Host "PASS Agent publish"
Write-Host ""

Write-Host "[2/4] Publishing Native Host Launcher..."

dotnet publish `
    $LauncherProject `
    --configuration Release `
    --runtime win-x64 `
    --self-contained false `
    --output $LauncherOutput

if ($LASTEXITCODE -ne 0)
{
    throw "Native Host Launcher publish failed."
}

Write-Host "PASS Native Host Launcher publish"
Write-Host ""

Write-Host "[3/4] Verifying artifacts..."

$AgentExe = Join-Path `
    $AgentOutput `
    "WorkforceOS.Agent.exe"

$LauncherExe = Join-Path `
    $LauncherOutput `
    "WorkforceOS.WebsiteNativeHost.exe"

if (-not (Test-Path $AgentExe))
{
    throw (
        "Published Agent missing: " +
        $AgentExe
    )
}

if (-not (Test-Path $LauncherExe))
{
    throw (
        "Published Native Host Launcher missing: " +
        $LauncherExe
    )
}

Write-Host "PASS Agent executable exists"
Write-Host "PASS Native Host executable exists"
Write-Host ""

Write-Host "[4/4] Artifact summary..."

Get-Item `
    $AgentExe,
    $LauncherExe |
Select-Object `
    FullName,
    Length,
    LastWriteTime

Write-Host ""
Write-Host "==============================================="
Write-Host " PHASE 11 BROWSER BRIDGE PUBLISH: PASS"
Write-Host "==============================================="
Write-Host ""