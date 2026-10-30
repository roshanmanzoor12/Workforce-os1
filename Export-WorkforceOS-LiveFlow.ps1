$ErrorActionPreference = 'Stop'
$Root = 'C:\workforce-os'
$Dest = Join-Path $Root 'WorkforceOS-LiveFlow-Current.zip'
$Paths = @(
 'backend/app/modules/auth/router.py',
 'backend/app/modules/auth/service.py',
 'backend/app/modules/auth/models.py',
 'backend/app/modules/work_sessions/service.py',
 'backend/app/modules/work_sessions/models.py',
 'backend/app/modules/work_sessions/live_integration.py',
 'backend/app/modules/work_sessions/activity_hook.py',
 'backend/app/modules/devices/heartbeat_service.py',
 'backend/app/modules/devices/desktop_presence_bridge.py',
 'backend/app/modules/devices/heartbeat_router.py',
 'backend/app/modules/devices/heartbeat_api_router.py',
 'backend/app/modules/devices/models.py',
 'backend/app/modules/desktop_agent/models.py',
 'backend/app/modules/live_monitoring/service.py',
 'backend/app/modules/live_monitoring/repository.py',
 'backend/app/modules/live_monitoring/router.py',
 'backend/app/modules/live_monitoring/access.py',
 'backend/app/modules/live_monitoring/models.py',
 'backend/app/modules/live_monitoring/schemas.py',
 'backend/app/modules/live_monitoring/native_http_gateway.py',
 'backend/app/modules/live_monitoring/native_frame_relay.py',
 'backend/app/modules/monitoring/models.py',
 'backend/app/modules/workspace_search/access.py',
 'backend/app/modules/workspace_permissions/permissions.py',
 'agent/WorkforceOS.Agent/LiveScreen/LiveScreenInboxWorker.cs',
 'agent/WorkforceOS.Agent/LiveScreen/LiveScreenInboxClient.cs',
 'agent/WorkforceOS.Agent/LiveScreen/CompanionRequestNotifier.cs',
 'agent/WorkforceOS.Agent/LiveScreen/LiveScreenEligibility.cs',
 'agent/WorkforceOS.Agent/LiveScreen/LiveScreenInboxStateTracker.cs',
 'agent/WorkforceOS.ScreenCompanion/Program.cs',
 'agent/WorkforceOS.ScreenCompanion/IncomingRequestPipe.cs',
 'agent/WorkforceOS.ScreenCompanion/RemoteFramePublisher.cs',
 'agent/WorkforceOS.Agent/WorkforceOS.Agent.csproj',
 'agent/WorkforceOS.ScreenCompanion/WorkforceOS.ScreenCompanion.csproj',
 'apps/web/contexts/workspace-context.tsx',
 'apps/web/app/(workspace)/monitoring/live-screen/page.tsx'
)
$Stage = Join-Path $env:TEMP ('wfos-liveflow-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $Stage -Force | Out-Null
try {
  foreach($Rel in $Paths) {
    $Src = Join-Path $Root ($Rel -replace '/', '\')
    if (Test-Path -LiteralPath $Src -PathType Leaf) {
      $Target = Join-Path $Stage ($Rel -replace '/', '\')
      New-Item -ItemType Directory -Path (Split-Path $Target) -Force | Out-Null
      Copy-Item -LiteralPath $Src -Destination $Target -ErrorAction Stop
    } else { Write-Warning "Not found: $Rel" }
  }
  # Small, focused path-only inventory for locating workspace login/logout entry points.
  $Inventory = Get-ChildItem (Join-Path $Root 'apps\web') -Recurse -File -Include '*.ts','*.tsx' -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -notmatch '\\(node_modules|\.next|dist|build)\\' -and $_.Name -match 'auth|login|logout|session|workspace|layout|provider' } |
    Select-Object -ExpandProperty FullName
  $Inventory | ForEach-Object { $_.Substring($Root.Length + 1) } |
    Set-Content -Path (Join-Path $Stage 'frontend-auth-file-paths.txt') -Encoding UTF8
  if (Test-Path $Dest) { Remove-Item $Dest -Force }
  Compress-Archive -Path (Join-Path $Stage '*') -DestinationPath $Dest -CompressionLevel Optimal
  Write-Host "Created: $Dest" -ForegroundColor Green
  Write-Host 'Review archive for confidential application code before sharing.'
} finally {
  Remove-Item -LiteralPath $Stage -Recurse -Force -ErrorAction SilentlyContinue
}
