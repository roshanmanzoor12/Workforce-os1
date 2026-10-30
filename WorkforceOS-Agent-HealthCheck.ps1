param(
    [string]$Root = 'C:\workforce-os',
    [switch]$SkipBuild
)
$ErrorActionPreference = 'Stop'
$report = [ordered]@{
    CheckedAt = (Get-Date).ToString('o')
    Root = $Root
    Checks = @()
}
function Add-Check([string]$Name, [string]$Status, [string]$Details) {
    $report.Checks += [pscustomobject]@{ Name=$Name; Status=$Status; Details=$Details }
    $color = switch ($Status) { 'PASS' {'Green'} 'WARN' {'Yellow'} default {'Red'} }
    Write-Host ('[{0}] {1}: {2}' -f $Status,$Name,$Details) -ForegroundColor $color
}
function Has-Pattern([string]$Path, [string]$Pattern) {
    if (-not (Test-Path -LiteralPath $Path)) { return $false }
    return [bool](Select-String -LiteralPath $Path -Pattern $Pattern -Quiet)
}
if (-not (Test-Path -LiteralPath $Root)) { throw "Project path not found: $Root" }
$agent = Join-Path $Root 'agent\WorkforceOS.Agent'
$program = Join-Path $agent 'program.cs'
$worker = Join-Path $agent 'agentworker.cs'
$tests = Join-Path $Root 'agent\WorkforceOS.Agent.Tests\WorkforceOS.Agent.Tests.csproj'
$agentProject = Join-Path $agent 'WorkforceOS.Agent.csproj'
$dotnet = 'C:\Program Files\dotnet\dotnet.exe'
if (-not (Test-Path -LiteralPath $dotnet)) { $cmd = Get-Command dotnet -ErrorAction SilentlyContinue; if ($cmd) { $dotnet = $cmd.Source } }
if (Test-Path -LiteralPath $dotnet) { Add-Check 'DotNet SDK' 'PASS' ((& $dotnet --version) -join ' ') }
else { Add-Check 'DotNet SDK' 'FAIL' '.NET SDK unavailable' }

$modules = [ordered]@{
 'Enrollment'='Enrollment\EnrollmentService.cs'
 'Heartbeat'='Runtime\HeartbeatRunner.cs'
 'Activity tracking'='Activity\ActivityServiceReceiver.cs'
 'Application tracking'='AppTracking\AppTrackingRuntimeCoordinator.cs'
 'Website tracking'='WebsiteTracking\WebsiteTrackingRuntimeCoordinator.cs'
 'Live eligibility'='LiveScreen\LiveScreenEligibility.cs'
 'Live coordinator'='LiveScreen\LiveScreenSessionCoordinator.cs'
 'Live inbox client'='LiveScreen\LiveScreenInboxClient.cs'
 'Live inbox worker'='LiveScreen\LiveScreenInboxWorker.cs'
 'Live inbox diagnostics'='LiveScreen\LiveScreenInboxStateTracker.cs'
}
foreach ($entry in $modules.GetEnumerator()) {
    $p = Join-Path $agent $entry.Value
    Add-Check $entry.Key $(if (Test-Path -LiteralPath $p) {'PASS'} else {'WARN'}) $(if (Test-Path -LiteralPath $p) {'Source present'} else {'Source not found'})
}
$registrationChecks = @(
 @('Live inbox host registration','LiveScreenInboxWorker'),
 @('Activity host registration','Activity'),
 @('Application host registration','AppTracking'),
 @('Website host registration','WebsiteTracking')
)
foreach ($check in $registrationChecks) {
 $found = Has-Pattern $program ([regex]::Escape($check[1]))
 Add-Check $check[0] $(if ($found) {'PASS'} else {'WARN'}) $(if ($found) {'Referenced in program.cs'} else {'Not referenced in program.cs; manual wiring review needed'})
}
$heartbeat = Has-Pattern $worker 'HeartbeatRunner|RunAsync'
Add-Check 'Heartbeat worker reference' $(if ($heartbeat) {'PASS'} else {'WARN'}) $(if ($heartbeat) {'Worker references heartbeat flow'} else {'Heartbeat flow not clearly referenced'})

$svc = Get-CimInstance Win32_Service -ErrorAction SilentlyContinue | Where-Object { $_.Name -like '*Workforce*' -or $_.DisplayName -like '*Workforce*' } | Select-Object -First 5
if ($svc) {
 foreach ($s in $svc) { Add-Check ('Windows Service '+$s.Name) $(if ($s.State -eq 'Running') {'PASS'} else {'WARN'}) ("State={0}; StartMode={1}" -f $s.State,$s.StartMode) }
} else { Add-Check 'Windows Service' 'WARN' 'No Workforce-named service found (build/test does not install service)' }
$processes = Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -like '*Workforce*' } | Select-Object -First 8
if ($processes) { Add-Check 'Agent process' 'PASS' ('Processes: '+(($processes.ProcessName | Sort-Object -Unique) -join ', ')) }
else { Add-Check 'Agent process' 'WARN' 'No Workforce-named process detected' }

$base = $null
$config = Join-Path $agent 'appsettings.json'
if (Test-Path -LiteralPath $config) {
 try {
  $json = Get-Content -LiteralPath $config -Raw | ConvertFrom-Json
  if ($json.Agent.ApiBaseUrl) { $base = [uri]$json.Agent.ApiBaseUrl }
 } catch { Add-Check 'Agent configuration' 'WARN' 'Cannot parse local appsettings.json' }
}
if ($base -and $base.Host -in @('localhost','127.0.0.1','::1')) {
 try {
  $tcp = Test-NetConnection -ComputerName $base.Host -Port $(if ($base.IsDefaultPort) { if ($base.Scheme -eq 'https') {443} else {80} } else {$base.Port}) -InformationLevel Quiet -WarningAction SilentlyContinue
  Add-Check 'Local backend TCP' $(if ($tcp) {'PASS'} else {'WARN'}) ("Reachable={0} ({1}://{2}:{3})" -f $tcp,$base.Scheme,$base.Host,$base.Port)
 } catch { Add-Check 'Local backend TCP' 'WARN' 'Unable to check localhost API port' }
} elseif ($base) { Add-Check 'Remote backend URL' 'WARN' ("Configured host: {0}; remote endpoint not probed" -f $base.Host) }
else { Add-Check 'Backend connectivity' 'WARN' 'No Agent:ApiBaseUrl found; not probing device-authenticated routes' }

if (-not $SkipBuild -and (Test-Path -LiteralPath $dotnet) -and (Test-Path -LiteralPath $agentProject)) {
 & $dotnet build $agentProject --nologo -v:q
 $buildCode = $LASTEXITCODE
 Add-Check 'Agent build' $(if ($buildCode -eq 0) {'PASS'} else {'FAIL'}) ("ExitCode=$buildCode")
 if ($buildCode -eq 0 -and (Test-Path -LiteralPath $tests)) {
  & $dotnet test $tests --nologo -v:q
  $testCode = $LASTEXITCODE
  Add-Check 'Agent unit tests' $(if ($testCode -eq 0) {'PASS'} else {'FAIL'}) ("ExitCode=$testCode")
 }
}
Add-Check 'Live video' 'WARN' 'No verified native capture/WebRTC transport. Inbox polling is not video streaming.'
Add-Check 'Production data ingestion' 'WARN' 'Requires authenticated endpoint/database checks; not proven by source/build alone.'
$outDir = Join-Path $Root 'artifacts\agent-health'
New-Item -ItemType Directory -Path $outDir -Force | Out-Null
$outPath = Join-Path $outDir ('agent-health-'+(Get-Date -Format 'yyyyMMdd-HHmmss')+'.json')
$report | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $outPath -Encoding UTF8
Write-Host "`nHealth report saved: $outPath" -ForegroundColor Cyan
Write-Host 'NOTE: Report intentionally excludes device secrets, tokens and full URLs.' -ForegroundColor Gray
