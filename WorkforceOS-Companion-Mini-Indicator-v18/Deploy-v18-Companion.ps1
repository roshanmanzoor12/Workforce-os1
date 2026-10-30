param(
    [switch]$Apply,
    [switch]$PauseAndRestartSupervisor,
    [string]$Root = 'C:\workforce-os'
)
$ErrorActionPreference = 'Stop'
$Stage = Join-Path $Root 'artifacts\screen-companion-v18-staging'
$Live = Join-Path $Root 'artifacts\screen-companion'
$File = 'WorkforceOS.ScreenCompanion.dll'
$Exe = Join-Path $Live 'WorkforceOS.ScreenCompanion.exe'
foreach ($required in @((Join-Path $Stage $File),(Join-Path $Live $File),(Join-Path $Stage 'WorkforceOS.ScreenCompanion.exe'))) {
    if (!(Test-Path $required)) { throw "Required file not found: $required" }
}
$SourceText = Get-Content (Join-Path $Root 'agent\WorkforceOS.ScreenCompanion\Program.cs') -Raw
if (!$SourceText.Contains('WFOS_V18_MINI_SHARING_OVERLAY')) {throw 'V18 source not installed; refusing to deploy unrelated build'}
$StagedHash = (Get-FileHash (Join-Path $Stage $File)).Hash
$LiveHash = (Get-FileHash (Join-Path $Live $File)).Hash
Write-Host "V18 STAGED DLL: $StagedHash"
Write-Host "LIVE DLL:       $LiveHash"
$Running = @(Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'WorkforceOS.ScreenCompanion.exe' })
if (!$Apply) {
    $Running | Select-Object ProcessId,ParentProcessId,CommandLine | Format-List
    Write-Host 'PREFLIGHT ONLY. No processes or files changed.' -ForegroundColor Green
    return
}
$ParentExe = $null
$ParentArgs = $null
$Stopped = $false
if ($Running.Count -gt 0) {
    if (!$PauseAndRestartSupervisor) {throw 'Companion running. Employee should Stop Sharing, then pause the supervisor (or use -PauseAndRestartSupervisor explicitly).'}
    if ($Running.Count -ne 1 -or $Running[0].ExecutablePath -ine $Exe) {throw 'Unexpected Companion process. Refusing to stop anything.'}
    $Parent = Get-CimInstance Win32_Process -Filter "ProcessId=$($Running[0].ParentProcessId)"
    if (!$Parent -or $Parent.Name -ne 'powershell.exe') {throw 'Supervisor not verified as powershell.exe'}
    $ParentExe = $Parent.ExecutablePath
    $Command = $Parent.CommandLine
    $ArgumentMatch = [regex]::Match($Command, '(?i)\s(-NoProfile\b.*)$')
    if (!$ArgumentMatch.Success -or !$ParentExe) {throw 'Supervisor launch arguments could not be verified'}
    $ParentArgs = $ArgumentMatch.Groups[1].Value
    $ScriptMatch = [regex]::Match($ParentArgs, '(?i)-File\s+(?:"([^"]+)"|(\S+))')
    if (!$ScriptMatch.Success) {throw 'Supervisor script not found in command line'}
    $ScriptFile = if ($ScriptMatch.Groups[1].Success) {$ScriptMatch.Groups[1].Value} else {$ScriptMatch.Groups[2].Value}
    $ScriptFile = [System.IO.Path]::GetFullPath($ScriptFile)
    $FullRoot = [System.IO.Path]::GetFullPath($Root).TrimEnd('\') + '\'
    if (!$ScriptFile.StartsWith($FullRoot,[System.StringComparison]::OrdinalIgnoreCase) -or !(Test-Path $ScriptFile)) {
        throw 'Supervisor script not verified inside WorkforceOS root'
    }
    Write-Host "Pausing verified interactive supervisor: $ScriptFile"
    Stop-Process -Id $Parent.ProcessId -Force -ErrorAction Stop
    Start-Sleep -Seconds 2
    Get-Process 'WorkforceOS.ScreenCompanion' -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction Stop
    Start-Sleep -Seconds 3
    $Stopped = $true
}
if (Get-Process 'WorkforceOS.ScreenCompanion' -ErrorAction SilentlyContinue) {
    throw 'Companion relaunched unexpectedly. No DLL replaced.'
}
$Stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$Backup = Join-Path $Root "WorkforceOS-v18-live-backup-$Stamp"
New-Item -ItemType Directory -Force -Path $Backup | Out-Null
Copy-Item -Path (Join-Path $Live '*') -Destination $Backup -Recurse -Force -ErrorAction Stop
Write-Host "Live binaries backed up to $Backup"
try {
    Copy-Item -Path (Join-Path $Stage '*') -Destination $Live -Recurse -Force -ErrorAction Stop
    $NewHash = (Get-FileHash (Join-Path $Live $File)).Hash
    if ($NewHash -ne $StagedHash) {throw 'V18 live/staging DLL hashes differ'}
    Write-Host 'V18 MINI INDICATOR DEPLOYMENT VERIFIED: PASS' -ForegroundColor Green
} catch {
    Write-Warning "Deployment failed. Backup preserved at $Backup. Supervisor remains paused."
    throw
}
if ($Stopped -and $ParentExe -and $ParentArgs) {
    Start-Process -FilePath $ParentExe -ArgumentList $ParentArgs -WorkingDirectory $Root -ErrorAction Stop
    Start-Sleep -Seconds 4
    $NewProc = @(Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'WorkforceOS.ScreenCompanion.exe' })
    if ($NewProc.Count -eq 0) {throw 'V18 deployed but Companion supervisor did not restart process. Investigate supervisor.'}
    Write-Host ('Companion restarted PID(s): ' + (($NewProc | ForEach-Object {$_.ProcessId}) -join ', '))
}
