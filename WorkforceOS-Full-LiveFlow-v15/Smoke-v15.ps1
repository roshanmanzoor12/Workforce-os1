param([string]$ApiBase = 'http://127.0.0.1:8001')
$ErrorActionPreference='Stop'
$Doc=Invoke-RestMethod -Method Get -Uri ($ApiBase.TrimEnd('/')+'/openapi.json') -TimeoutSec 15
$Required=@(
  '/api/v1/workspaces/{workspace_id}/live-monitoring/auto-flow/ping',
  '/api/v1/workspaces/{workspace_id}/live-monitoring/auto-flow/stop',
  '/api/v1/workspaces/{workspace_id}/live-monitoring/auto-flow/saved-approval',
  '/api/v1/device-agent/live-screen/{session_id}/stop'
)
foreach ($Endpoint in $Required) {
  if (-not ($Doc.paths.PSObject.Properties.Name -contains $Endpoint)) { throw "ENDPOINT MISSING: $Endpoint" }
  Write-Host "REGISTERED $Endpoint" -ForegroundColor Green
}
Write-Host 'OPENAPI ROUTE REGISTRATION PASS. Does not test database, consent, device or video.'
