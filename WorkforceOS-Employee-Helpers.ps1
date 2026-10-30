# WorkforceOS disclosed interactive-session helpers (per-user startup)
# Actions: Install, Start, Status, Stop, Uninstall
[CmdletBinding()]
param(
    [ValidateSet('Install','Start','Status','Stop','Uninstall')]
    [string]$Action = 'Status',
    [string]$AgentExe = 'C:\workforce-os\artifacts\agent\win-x64\WorkforceOS.Agent.exe'
)
$ErrorActionPreference = 'Stop'
$AppRoot = Join-Path $env:LOCALAPPDATA 'WorkforceOS\EmployeeHelpers'
$InstalledScript = Join-Path $AppRoot 'WorkforceOS-Employee-Helpers.ps1'
$StartupFolder = [Environment]::GetFolderPath('Startup')
$ShortcutPath = Join-Path $StartupFolder 'WorkforceOS Employee Monitoring.lnk'
$ConfigPath = Join-Path $AppRoot 'agent-path.txt'
$ModeArgs = @('--activity-session-helper','--app-tracking-session-helper')

function Assert-InteractiveSession {
    $sessionId = (Get-Process -Id $PID).SessionId
    if ($sessionId -le 0) { throw 'Run this as the signed-in employee, in an interactive Windows session (not Session 0).' }
    return $sessionId
}
function Get-ConfiguredAgent {
    if (Test-Path -LiteralPath $ConfigPath) {
        $saved = (Get-Content -LiteralPath $ConfigPath -Raw).Trim()
        if ($saved) { return $saved }
    }
    return $AgentExe
}
function Get-OwnHelpers {
    $sid = Assert-InteractiveSession
    $user = [Security.Principal.WindowsIdentity]::GetCurrent().Name
    @(
        Get-CimInstance Win32_Process -Filter "Name = 'WorkforceOS.Agent.exe'" |
            Where-Object {
                $cmd = $_.CommandLine
                $s = $_.SessionId
                ($s -eq $sid) -and ($null -ne $cmd) -and
                ($ModeArgs | Where-Object { $cmd.Contains($_) }).Count -gt 0
            } |
            Where-Object {
                $who = Invoke-CimMethod -InputObject $_ -MethodName GetOwner -ErrorAction SilentlyContinue
                $who -and ("$($who.Domain)\$($who.User)" -ieq $user)
            }
    )
}
function Write-Status {
    $sid = Assert-InteractiveSession
    Write-Host "Employee: $([Security.Principal.WindowsIdentity]::GetCurrent().Name) | Windows Session: $sid"
    Write-Host "Login startup enabled: $(Test-Path -LiteralPath $ShortcutPath)"
    $helpers = @(Get-OwnHelpers)
    foreach ($mode in $ModeArgs) {
        $found = @($helpers | Where-Object { $_.CommandLine.Contains($mode) })
        Write-Host "$mode : $($found.Count) process(es)" 
    }
}
function Stop-OwnHelpers {
    foreach ($p in @(Get-OwnHelpers)) {
        Write-Host "Stopping helper PID $($p.ProcessId)"
        Stop-Process -Id $p.ProcessId -ErrorAction SilentlyContinue
    }
}

switch ($Action) {
    'Install' {
        [void](Assert-InteractiveSession)
        if (-not (Test-Path -LiteralPath $AgentExe -PathType Leaf)) { throw "Agent executable missing: $AgentExe" }
        Write-Host 'WorkforceOS will start disclosed Activity and App Tracking helpers when YOU sign in.'
        Write-Host 'They observe active/idle status and foreground applications; website tracking runs separately in the Agent.'
        Write-Host 'Use -Action Stop to disable future helper auto-start and stop your current helpers.'
        $answer = Read-Host 'Enable employee-session monitoring auto-start for this Windows user? Type YES'
        if ($answer -cne 'YES') { Write-Host 'Not installed.'; break }
        New-Item -ItemType Directory -Path $AppRoot -Force | Out-Null
        if ($PSCommandPath -ine $InstalledScript) { Copy-Item -LiteralPath $PSCommandPath -Destination $InstalledScript -Force }
        [IO.File]::WriteAllText($ConfigPath, $AgentExe, [Text.UTF8Encoding]::new($false))
        $shell = New-Object -ComObject WScript.Shell
        $shortcut = $shell.CreateShortcut($ShortcutPath)
        $shortcut.TargetPath = "$PSHOME\powershell.exe"
        $shortcut.Arguments = '-NoProfile -ExecutionPolicy Bypass -File "' + $InstalledScript + '" -Action Start'
        $shortcut.WorkingDirectory = $AppRoot
        $shortcut.Description = 'WorkforceOS disclosed employee monitoring helpers'
        $shortcut.Save()
        Write-Host "Installed current-user login startup: $ShortcutPath"
        & "$PSHOME\powershell.exe" -NoProfile -ExecutionPolicy Bypass -File $InstalledScript -Action Start
        if ($LASTEXITCODE -ne 0) { throw "Helper startup failed (exit $LASTEXITCODE)" }
    }
    'Start' {
        [void](Assert-InteractiveSession)
        if (-not (Test-Path -LiteralPath $ShortcutPath)) {
            Write-Host 'Monitoring is stopped/disabled for this Windows user. Run -Action Install to opt in.'
            break
        }
        $exe = Get-ConfiguredAgent
        if (-not (Test-Path -LiteralPath $exe -PathType Leaf)) { throw "Agent executable missing: $exe" }
        $mutexName = 'Local\WorkforceOS.EmployeeHelpers.Start'
        $mutex = [Threading.Mutex]::new($false, $mutexName)
        $locked = $false
        try {
            $locked = $mutex.WaitOne([TimeSpan]::FromSeconds(10))
            if (-not $locked) { throw 'Another helper startup is in progress.' }
            $running = @(Get-OwnHelpers)
            foreach ($mode in $ModeArgs) {
                if (@($running | Where-Object { $_.CommandLine.Contains($mode) }).Count -eq 0) {
                    $p = Start-Process -FilePath $exe -ArgumentList $mode -PassThru
                    Write-Host "Started $mode PID $($p.Id)"
                } else { Write-Host "$mode already running; skipped." }
            }
        } finally {
            if ($locked) { $mutex.ReleaseMutex() }
            $mutex.Dispose()
        }
        Write-Status
    }
    'Status' { Write-Status }
    'Stop' {
        [void](Assert-InteractiveSession)
        if (Test-Path -LiteralPath $ShortcutPath) { Remove-Item -LiteralPath $ShortcutPath -Force }
        Stop-OwnHelpers
        Write-Host 'Current-user helper monitoring stopped; future automatic launch disabled.'
        Write-Host 'Note: this does NOT stop the machine Windows Service, heartbeat or browser website tracker.'
    }
    'Uninstall' {
        [void](Assert-InteractiveSession)
        if (Test-Path -LiteralPath $ShortcutPath) { Remove-Item -LiteralPath $ShortcutPath -Force }
        Stop-OwnHelpers
        if (Test-Path -LiteralPath $ConfigPath) { Remove-Item -LiteralPath $ConfigPath -Force }
        Write-Host 'Employee startup entry and configuration removed. Script retained for safe management.'
    }
}
