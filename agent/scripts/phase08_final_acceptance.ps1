#Requires -Version 5.1

$ErrorActionPreference = "Stop"

$AgentDirectory =
    "C:\workforce-os\agent\WorkforceOS.Agent"

$BackendDirectory =
    "C:\workforce-os\backend"

$BackendTestScript =
    "C:\workforce-os\backend\scripts\phase08_activity_backend_tests.ps1"

$BackendRuntimeScript =
    "C:\workforce-os\backend\scripts\phase08_activity_runtime_contract_smoke.ps1"

$AgentTestScript =
    "C:\workforce-os\agent\scripts\phase08_agent_core_tests.ps1"

Write-Host ""
Write-Host "============================================="
Write-Host " WorkforceOS Phase 08 Final Acceptance"
Write-Host "============================================="
Write-Host ""

# ============================================================
# 1. BACKEND TESTS
# ============================================================

Write-Host "[1/5] Backend activity tests..."

if (-not (Test-Path $BackendTestScript))
{
    throw "Missing backend test script: $BackendTestScript"
}

& $BackendTestScript

if (-not $?)
{
    throw "Backend Phase 08 tests failed."
}

Write-Host "PASS backend activity tests"
Write-Host ""

# ============================================================
# 2. BACKEND RUNTIME CONTRACT
# ============================================================

Write-Host "[2/5] Backend runtime contract..."

if (-not (Test-Path $BackendRuntimeScript))
{
    throw "Missing runtime smoke script: $BackendRuntimeScript"
}

& $BackendRuntimeScript

if (-not $?)
{
    throw "Backend runtime contract failed."
}

Write-Host "PASS backend runtime contract"
Write-Host ""

# ============================================================
# 3. AGENT CORE TESTS
# ============================================================

Write-Host "[3/5] Agent activity tests..."

if (-not (Test-Path $AgentTestScript))
{
    throw "Missing agent core test script: $AgentTestScript"
}

& $AgentTestScript

if (-not $?)
{
    throw "Agent Phase 08 tests failed."
}

Write-Host "PASS agent activity tests"
Write-Host ""

# ============================================================
# 4. RELEASE BUILD
# ============================================================

Write-Host "[4/5] Agent Release build..."

Push-Location $AgentDirectory

try
{
    dotnet build `
        --configuration Release

    if ($LASTEXITCODE -ne 0)
    {
        throw "Agent Release build failed."
    }
}
finally
{
    Pop-Location
}

Write-Host "PASS agent Release build"
Write-Host ""

# ============================================================
# 5. REQUIRED PHASE 08 FILES
# ============================================================

Write-Host "[5/5] Checking Phase 08 runtime files..."

$RequiredFiles =
    @(
        "Activity\LastInputDetector.cs",
        "Activity\ActivityStateTracker.cs",
        "Activity\ActivitySessionObservation.cs",
        "Activity\ActivityObservationValidator.cs",
        "Activity\ActivityPipeProtocol.cs",
        "Activity\ActivityPipeClient.cs",
        "Activity\ActivityPipeServer.cs",
        "Activity\ActivityServiceReceiver.cs",
        "Activity\ActivityRuntimeState.cs",
        "Activity\ActivitySessionHelperRunner.cs",
        "Activity\ActivitySessionHelperCommand.cs",
        "Activity\ActivityApiModels.cs",
        "Activity\ActivityReporter.cs",
        "Activity\ActivityBackendReporter.cs",
        "Activity\ActivityBackendReportingWorker.cs"
    )

foreach ($RelativePath in $RequiredFiles)
{
    $FullPath =
        Join-Path `
            $AgentDirectory `
            $RelativePath

    if (-not (Test-Path $FullPath))
    {
        throw (
            "Missing Phase 08 file: " +
            $FullPath
        )
    }
}

Write-Host "PASS Phase 08 runtime files"
Write-Host ""

Write-Host "============================================="
Write-Host " PHASE 08 STATIC ACCEPTANCE: PASS"
Write-Host "============================================="
Write-Host ""
Write-Host "Next required runtime step:"
Write-Host "1. Apply tenant activity migration."
Write-Host "2. Publish/restart latest Windows service."
Write-Host "3. Run --activity-session-helper interactively."
Write-Host "4. Confirm activity event reaches tenant DB."
Write-Host ""