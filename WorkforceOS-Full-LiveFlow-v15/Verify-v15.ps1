param([string]$Root = 'C:\workforce-os')
$ErrorActionPreference='Stop'
$Python = Join-Path $Root '.venv\Scripts\python.exe'
if (!(Test-Path $Python)) {$Python='python'}
& $Python -m py_compile `
  (Join-Path $Root 'backend\app\main.py') `
  (Join-Path $Root 'backend\app\modules\devices\agent_router.py') `
  (Join-Path $Root 'backend\app\modules\live_monitoring\auto_flow_router.py') `
  (Join-Path $Root 'backend\app\modules\live_monitoring\auto_lease.py') `
  (Join-Path $Root 'backend\app\modules\live_monitoring\login_lifecycle.py')
if ($LASTEXITCODE -ne 0) {throw 'Python compilation FAILED'}
Write-Host 'PYTHON COMPILE PASS' -ForegroundColor Green
Write-Host 'Next: run your Next.js type checker and build both .NET projects to staging.'
