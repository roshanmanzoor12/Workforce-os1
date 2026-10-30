param([string]$Root = 'C:\workforce-os', [int]$BackendPort = 8001)
$ErrorActionPreference = 'Stop'
$report = [ordered]@{}
$agent = Join-Path $Root 'agent\WorkforceOS.Agent\LiveScreen\LiveScreenInboxWorker.cs'
$companion = Join-Path $Root 'agent\WorkforceOS.ScreenCompanion\Program.cs'
$publisher = Join-Path $Root 'agent\WorkforceOS.ScreenCompanion\RemoteFramePublisher.cs'
$service = Join-Path $Root 'backend\app\modules\desktop_agent\service.py'
$report.CheckedAt = (Get-Date).ToString('o')
$report.AgentInboxSourceExists = Test-Path -LiteralPath $agent
$report.CompanionSourceExists = Test-Path -LiteralPath $companion
$report.PublisherSourceExists = Test-Path -LiteralPath $publisher
$report.BackendCapabilitySourceExists = Test-Path -LiteralPath $service
if ($report.AgentInboxSourceExists) {
 $text = Get-Content -LiteralPath $agent -Raw
 $report.AgentInboxReadOnly = $text.Contains('Never starts video capture') -or $text.Contains('Media transport not configured')
}
if ($report.CompanionSourceExists) {
 $text = Get-Content -LiteralPath $companion -Raw
 $report.CompanionUsesManualEnvironmentUrl = $text.Contains('WFOS_SCREEN_SEND_URL')
 $report.CompanionHasLocalConsent = $text.Contains('StartPreview') -and $text.Contains('MessageBox.Show')
 $report.CompanionHasStop = $text.Contains('StopPreview')
}
if ($report.BackendCapabilitySourceExists) {
 $text = Get-Content -LiteralPath $service -Raw
 $report.BackendSourceReportsLiveScreenFalse = $text -match '"live_screen"\s*:\s*False'
}
$running = @(Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'WorkforceOS.ScreenCompanion.exe' })
$report.CompanionProcessCount = $running.Count
$report.CompanionPaths = @($running | ForEach-Object { $_.ExecutablePath })
$agentSvc = Get-Service -Name 'WorkforceOSAgent' -ErrorAction SilentlyContinue
$report.AgentServiceStatus = if ($agentSvc) { [string]$agentSvc.Status } else { 'Not found' }
try {
 $url = "http://127.0.0.1:$BackendPort/openapi.json"
 $schema = Invoke-RestMethod -Uri $url -TimeoutSec 7
 $paths = @($schema.paths.PSObject.Properties.Name)
 $report.BackendReachable = $true
 $report.NativeInboxRouteAdvertised = [bool](@($paths | Where-Object { $_ -match '/device-agent/live-screen/inbox' }).Count)
 $report.LiveMonitoringSessionRoutes = @($paths | Where-Object { $_ -match '/live-monitoring/live-screen' })
} catch {
 $report.BackendReachable = $false
 $report.BackendErrorType = $_.Exception.GetType().Name
}
$report | ConvertTo-Json -Depth 6
Write-Host '\nNative media relay readiness requires an authenticated frame transport and owner viewer.' -ForegroundColor Yellow
Write-Host 'This script is READ-ONLY. No credentials, screen pixels, or tokens are collected.' -ForegroundColor Cyan
