#Requires -Version 5.1

$ErrorActionPreference = "Stop"

$ServiceName = "WorkforceOSAgent"

$AgentProject = (
    "C:\workforce-os\agent\WorkforceOS.Agent\" +
    "WorkforceOS.Agent.csproj"
)

$NativeHostProject = (
    "C:\workforce-os\agent\WorkforceOS.WebsiteNativeHost\" +
    "WorkforceOS.WebsiteNativeHost.csproj"
)

$AgentOutput = (
    "C:\workforce-os\artifacts\agent\win-x64"
)

$NativeHostOutput = (
    "C:\workforce-os\artifacts\website-native-host"
)

function Test-IsAdministrator
{
    $Identity = (
        [Security.Principal.WindowsIdentity]::GetCurrent()
    )

    $Principal = New-Object `
        Security.Principal.WindowsPrincipal($Identity)

    return $Principal.IsInRole(
        [Security.Principal.WindowsBuiltInRole]::Administrator
    )
}

Write-Host ""
Write-Host "==============================================="
Write-Host " WorkforceOS Phase 11 Publish"
Write-Host "==============================================="
Write-Host ""

if (-not (Test-IsAdministrator))
{
    Write-Host "ERROR: Administrator PowerShell is required."
    Write-Host ""
    Write-Host "Open an elevated shell with:"
    Write-Host ""
    Write-Host "Start-Process powershell.exe -Verb RunAs"
    Write-Host ""

    throw "Phase 11 publish requires Administrator privileges."
}

Write-Host "PASS Administrator privileges"
Write-Host ""

$ServiceWasRunning = $false
$ServiceStoppedByScript = $false
$PublishSucceeded = $false

try
{
    Write-Host "[1/7] Checking Agent service..."

    $Service = Get-Service `
        -Name $ServiceName `
        -ErrorAction SilentlyContinue

    if ($null -ne $Service)
    {
        Write-Host (
            "Service status: " +
            $Service.Status
        )

        if ($Service.Status -eq "Running")
        {
            $ServiceWasRunning = $true

            Write-Host "Stopping WorkforceOS Agent service..."

            Stop-Service `
                -Name $ServiceName `
                -Force `
                -ErrorAction Stop

            $Service = Get-Service `
                -Name $ServiceName `
                -ErrorAction Stop

            $Service.WaitForStatus(
                "Stopped",
                [TimeSpan]::FromSeconds(30)
            )

            $Service = Get-Service `
                -Name $ServiceName `
                -ErrorAction Stop

            if ($Service.Status -ne "Stopped")
            {
                throw "Agent service did not reach Stopped state."
            }

            $ServiceStoppedByScript = $true

            Write-Host "PASS Agent service stopped"
        }
        else
        {
            Write-Host "Agent service already stopped"
        }
    }
    else
    {
        Write-Host "Agent service is not installed"
    }

    Write-Host ""
    Write-Host "[2/7] Checking remaining Agent processes..."

    Start-Sleep `
        -Milliseconds 500

    $RemainingProcesses = Get-Process `
        -Name "WorkforceOS.Agent" `
        -ErrorAction SilentlyContinue

    if ($null -ne $RemainingProcesses)
    {
        foreach ($Process in $RemainingProcesses)
        {
            Write-Host (
                "Stopping remaining Agent PID " +
                $Process.Id
            )

            Stop-Process `
                -Id $Process.Id `
                -Force `
                -ErrorAction Stop
        }

        Start-Sleep `
            -Seconds 1
    }

    $RemainingProcesses = Get-Process `
        -Name "WorkforceOS.Agent" `
        -ErrorAction SilentlyContinue

    if ($null -ne $RemainingProcesses)
    {
        throw "WorkforceOS Agent process is still running."
    }

    Write-Host "PASS Agent artifacts unlocked"

    Write-Host ""
    Write-Host "[3/7] Building Agent..."

    dotnet build `
        $AgentProject `
        --configuration Release

    if ($LASTEXITCODE -ne 0)
    {
        throw "Agent build failed."
    }

    Write-Host "PASS Agent build"

    Write-Host ""
    Write-Host "[4/7] Publishing Agent..."

    New-Item `
        -ItemType Directory `
        -Path $AgentOutput `
        -Force |
    Out-Null

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
    Write-Host "[5/7] Publishing Website Native Host..."

    New-Item `
        -ItemType Directory `
        -Path $NativeHostOutput `
        -Force |
    Out-Null

    dotnet publish `
        $NativeHostProject `
        --configuration Release `
        --runtime win-x64 `
        --self-contained false `
        --output $NativeHostOutput

    if ($LASTEXITCODE -ne 0)
    {
        throw "Website Native Host publish failed."
    }

    Write-Host "PASS Website Native Host publish"

    Write-Host ""
    Write-Host "[6/7] Verifying published artifacts..."

    $AgentExe = Join-Path `
        $AgentOutput `
        "WorkforceOS.Agent.exe"

    $AgentDll = Join-Path `
        $AgentOutput `
        "WorkforceOS.Agent.dll"

    $NativeHostExe = Join-Path `
        $NativeHostOutput `
        "WorkforceOS.WebsiteNativeHost.exe"

    if (-not (Test-Path $AgentExe))
    {
        throw (
            "Agent executable missing: " +
            $AgentExe
        )
    }

    if (-not (Test-Path $AgentDll))
    {
        throw (
            "Agent DLL missing: " +
            $AgentDll
        )
    }

    if (-not (Test-Path $NativeHostExe))
    {
        throw (
            "Native Host executable missing: " +
            $NativeHostExe
        )
    }

    Get-Item `
        $AgentExe,
        $AgentDll,
        $NativeHostExe |
    Select-Object `
        FullName,
        Length,
        LastWriteTime

    Write-Host ""
    Write-Host "PASS published artifacts"

    $PublishSucceeded = $true

    Write-Host ""
    Write-Host "[7/7] Publish work complete"
}
finally
{
    if ($ServiceWasRunning -and $ServiceStoppedByScript)
    {
        Write-Host ""
        Write-Host "Restoring WorkforceOS Agent service..."

        Start-Service `
            -Name $ServiceName `
            -ErrorAction Stop

        $Service = Get-Service `
            -Name $ServiceName `
            -ErrorAction Stop

        $Service.WaitForStatus(
            "Running",
            [TimeSpan]::FromSeconds(30)
        )

        $Service = Get-Service `
            -Name $ServiceName `
            -ErrorAction Stop

        if ($Service.Status -ne "Running")
        {
            throw "Agent service failed to return to Running state."
        }

        Write-Host "PASS Agent service restarted"
    }
}

if (-not $PublishSucceeded)
{
    throw "Phase 11 publish did not complete."
}

Write-Host ""
Write-Host "==============================================="
Write-Host " PHASE 11 PUBLISH: PASS"
Write-Host "==============================================="
Write-Host ""