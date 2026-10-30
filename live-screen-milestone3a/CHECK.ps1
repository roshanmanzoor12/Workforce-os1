#Requires -Version 5.1
param([string]$Root = 'C:\workforce-os')
$ErrorActionPreference = 'Stop'
$reportDir = Join-Path $Root 'artifacts\diagnostics\live-screen-milestone3a'
New-Item -ItemType Directory -Path $reportDir -Force | Out-Null
$report = Join-Path $reportDir ('preflight-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '.txt')
$rows = New-Object System.Collections.Generic.List[string]
$rows.Add('WorkforceOS Milestone 3A - Native Live Screen transport preflight')
$rows.Add('Generated: ' + (Get-Date -Format o))
$rows.Add('Root: ' + $Root)
$rows.Add('NOTE: This report DOES NOT enable remote video streaming.')
$rows.Add('')
$required = @(
  'agent\WorkforceOS.Agent\LiveScreen\LiveScreenInboxWorker.cs',
  'agent\WorkforceOS.Agent\LiveScreen\LiveScreenSessionCoordinator.cs',
  'agent\WorkforceOS.ScreenCompanion\WorkforceOS.ScreenCompanion.csproj',
  'apps\web\app\(workspace)\monitoring\live-screen\page.tsx',
  'apps\web\components\monitoring\native-live-video.tsx',
  'backend\app\modules\live_monitoring\router.py'
)
foreach ($relative in $required) {
  $exists = Test-Path -LiteralPath (Join-Path $Root $relative) -PathType Leaf
  $rows.Add(('{0} {1}' -f $(if ($exists) { 'FOUND  ' } else { 'MISSING' }), $relative))
}
$service = Get-Service -Name 'WorkforceOSAgent' -ErrorAction SilentlyContinue
$rows.Add('Windows Agent service: ' + $(if ($service) { $service.Status.ToString() } else { 'MISSING' }))
$agentProject = Join-Path $Root 'agent\WorkforceOS.ScreenCompanion\WorkforceOS.ScreenCompanion.csproj'
if (Test-Path -LiteralPath $agentProject) {
  $rows.Add('Desktop companion project: present')
} else { $rows.Add('Desktop companion project: missing') }
try {
  $response = Invoke-WebRequest -Uri 'http://127.0.0.1:8001/openapi.json' -UseBasicParsing -TimeoutSec 5
  $api = $response.Content | ConvertFrom-Json
  $paths = @($api.paths.PSObject.Properties.Name)
  $rows.Add('FastAPI OpenAPI: reachable')
  $screenPaths = @($paths | Where-Object { $_ -match '(live.screen|screen.share|live_screen)' })
  $rows.Add('Live Screen route count: ' + $screenPaths.Count)
  foreach ($item in $screenPaths) { $rows.Add('ROUTE ' + $item) }
} catch { $rows.Add('FastAPI OpenAPI: unreachable (' + $_.Exception.Message + ')') }
$frontend = Join-Path $Root 'apps\web\app\(workspace)\monitoring\live-screen\page.tsx'
if (Test-Path -LiteralPath $frontend) {
  $pageText = Get-Content -LiteralPath $frontend -Raw
  $rows.Add('Original page contains browser-screen-share iframe reference: ' + ($pageText.Contains('/browser-screen-share')))
  $rows.Add('Original page contains native video receiver reference: ' + ($pageText.Contains('NativeLiveVideo')))
}
$senderPath = Join-Path $Root 'agent\WorkforceOS.ScreenCompanion'
if (Test-Path -LiteralPath $senderPath) {
  $sources = @(Get-ChildItem -LiteralPath $senderPath -Recurse -Filter '*.cs' -File -ErrorAction SilentlyContinue | Where-Object { $_.FullName -notmatch '\\(bin|obj)\\' })
  $senderMatches = @($sources | Select-String -Pattern 'RTCPeerConnection|PeerConnection|WebSocket|MediaFoundation|VideoEncoder' -ErrorAction SilentlyContinue)
  $rows.Add('Potential native sender/WebRTC code matches (not proof of streaming): ' + $senderMatches.Count)
}
$rows.Add('')
$rows.Add('NEXT: Real WebRTC video sender, authenticated session signaling, and direct viewer connection require implementation and Windows end-to-end tests.')
$rows | Set-Content -LiteralPath $report -Encoding UTF8
$rows | ForEach-Object { Write-Host $_ }
Write-Host ('REPORT: ' + $report) -ForegroundColor Green
