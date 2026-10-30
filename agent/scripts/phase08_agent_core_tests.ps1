#Requires -Version 5.1

$ErrorActionPreference = "Stop"

$AgentDirectory =
    "C:\workforce-os\agent\WorkforceOS.Agent"

$TestDirectory =
    "C:\workforce-os\agent\WorkforceOS.Agent.Tests"

$TestProject =
    "C:\workforce-os\agent\WorkforceOS.Agent.Tests\WorkforceOS.Agent.Tests.csproj"

Write-Host ""
Write-Host "============================================="
Write-Host " WorkforceOS Phase 08 Agent Core Tests"
Write-Host "============================================="
Write-Host ""

# ============================================================
# 1. AGENT BUILD
# ============================================================

Write-Host "[1/4] Building WorkforceOS Agent..."

if (-not (Test-Path $AgentDirectory))
{
    throw (
        "Agent project directory not found: " +
        $AgentDirectory
    )
}

Push-Location $AgentDirectory

try
{
    dotnet build

    if ($LASTEXITCODE -ne 0)
    {
        throw (
            "WorkforceOS Agent build failed."
        )
    }
}
finally
{
    Pop-Location
}

Write-Host "PASS agent build"
Write-Host ""

# ============================================================
# 2. TEST PROJECT
# ============================================================

Write-Host "[2/4] Checking test project..."

if (-not (Test-Path $TestDirectory))
{
    throw (
        "Agent test directory not found: " +
        $TestDirectory
    )
}

if (-not (Test-Path $TestProject))
{
    throw (
        "Agent test project file not found: " +
        $TestProject
    )
}

Write-Host "PASS test project exists"
Write-Host ""

# ============================================================
# 3. ACTIVITY TESTS
# ============================================================

Write-Host "[3/4] Running activity tests..."

dotnet test `
    $TestProject `
    --configuration Debug `
    --no-restore

if ($LASTEXITCODE -ne 0)
{
    throw (
        "Phase 08 activity agent tests failed."
    )
}

Write-Host "PASS activity tests"
Write-Host ""

# ============================================================
# 4. DUPLICATE DETECTOR CHECK
# ============================================================

Write-Host "[4/4] Checking duplicate LastInputDetector..."

$DetectorMatches =
    Get-ChildItem `
        $AgentDirectory `
        -Recurse `
        -Filter *.cs |
    Select-String `
        -Pattern "class LastInputDetector"

$DetectorCount =
    @(
        $DetectorMatches
    ).Count

if ($DetectorCount -ne 1)
{
    throw (
        "Expected exactly one LastInputDetector declaration, found " +
        $DetectorCount
    )
}

Write-Host "PASS single LastInputDetector declaration"

Write-Host ""
Write-Host "============================================="
Write-Host " PHASE 08 AGENT CORE TESTS: PASS"
Write-Host "============================================="
Write-Host ""