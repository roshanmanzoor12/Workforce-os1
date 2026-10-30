# Read-only WorkforceOS connectivity diagnosis. No credentials, request bodies, or configuration exported.
$ErrorActionPreference = 'Continue'
$Root = 'C:\workforce-os'
$Out = Join-Path $Root ('workforce-connection-check-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Path $Out -Force | Out-Null
function Save([string]$name, [object]$content) { $content | Out-File -LiteralPath (Join-Path $Out $name) -Encoding UTF8 }
$services = Get-CimInstance Win32_Service | Where-Object { $_.Name -like '*Workforce*' -or $_.DisplayName -like '*Workforce*' } | Select-Object Name,State,StartMode,ProcessId
Save 'services.txt' ($services | Format-Table -AutoSize | Out-String)
$procs = Get-Process | Where-Object {$_.ProcessName -like '*Workforce*'} | Select-Object ProcessName,Id,StartTime
Save 'processes.txt' ($procs | Format-Table -AutoSize | Out-String)
$checks = foreach($url in @('http://127.0.0.1:8001/openapi.json','http://127.0.0.1:3001/')) {
  try {
    $resp = Invoke-WebRequest -Uri $url -Method Get -TimeoutSec 8 -UseBasicParsing
    [pscustomobject]@{ Endpoint=$url; Status=[int]$resp.StatusCode; Result='reachable' }
  } catch {
    $code = 'none'
    if ($_.Exception.Response) { try { $code = [int]$_.Exception.Response.StatusCode } catch {} }
    [pscustomobject]@{ Endpoint=$url; Status=$code; Result='failed (response body not recorded)' }
  }
}
Save 'http-status.txt' ($checks | Format-Table -AutoSize | Out-String)
$portList = foreach($port in @(8001,3001,5434,6381)) {
  $listeners = @(Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue)
  [pscustomobject]@{Port=$port; Listening=($listeners.Count -gt 0)}
}
Save 'listeners.txt' ($portList | Format-Table -AutoSize | Out-String)
# Event logs: export only counts, not message text (message text may include secrets).
$since = (Get-Date).AddHours(-24)
$logs = foreach($logName in @('Application','System')) {
  try {
    $events = @(Get-WinEvent -FilterHashtable @{LogName=$logName;StartTime=$since;Level=2,3} -MaxEvents 250 -ErrorAction Stop)
    $workforce = @($events | Where-Object {$_.ProviderName -match 'Workforce|\.NET Runtime|Application Error|Service Control Manager'})
    [pscustomobject]@{ Log=$logName; MatchingWarningsOrErrors=$workforce.Count; MostRecent=($workforce | Select-Object -First 1 -ExpandProperty TimeCreated) }
  } catch { [pscustomobject]@{ Log=$logName; MatchingWarningsOrErrors='unavailable'; MostRecent='' } }
}
Save 'event-summary.txt' ($logs | Format-Table -AutoSize | Out-String)
Write-Host "Read-only connection check saved to: $Out" -ForegroundColor Green
Write-Host 'Only process status, HTTP status, ports, and event counts were collected.'
Write-Host 'Review every file before uploading.' -ForegroundColor Yellow
