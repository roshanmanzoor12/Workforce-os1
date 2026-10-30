$ErrorActionPreference = 'Stop'
$Root = 'C:\workforce-os'
$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
$Backend = Join-Path $Root 'backend\app'
$Router = Join-Path $Backend 'modules\live_monitoring\browser_share_router.py'
$Main = Join-Path $Backend 'main.py'
$PageDir = Join-Path $Root 'apps\web\app\(workspace)\browser-screen-share'
$Page = Join-Path $PageDir 'page.tsx'
foreach ($p in @($Main,(Join-Path $Here 'browser_share_router.py'),(Join-Path $Here 'page.tsx'))) { if (!(Test-Path -LiteralPath $p)) { throw "Missing: $p" } }
$Stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
Copy-Item -LiteralPath $Main -Destination "$Main.backup-$Stamp"
if (Test-Path -LiteralPath $Router) { Copy-Item -LiteralPath $Router -Destination "$Router.backup-$Stamp" }
New-Item -ItemType Directory -Path $PageDir -Force | Out-Null
if (Test-Path -LiteralPath $Page) { Copy-Item -LiteralPath $Page -Destination "$Page.backup-$Stamp" }
Copy-Item -LiteralPath (Join-Path $Here 'browser_share_router.py') -Destination $Router -Force
Copy-Item -LiteralPath (Join-Path $Here 'page.tsx') -Destination $Page -Force
$Source = Get-Content -LiteralPath $Main -Raw
$Import = 'from app.modules.live_monitoring.browser_share_router import router as browser_screen_share_router'
$Include = 'app.include_router(browser_screen_share_router, prefix=settings.api_v1_prefix)'
if (-not $Source.Contains($Import)) { $Source = $Import + "`r`n" + $Source }
# Respect Python's __future__ import placement.
$Source = $Source.Replace($Import + "`r`n", '')
if (-not $Source.Contains($Import)) { $Source = $Source.Replace('from __future__ import annotations', "from __future__ import annotations`r`n`r`n$Import") }
if (-not $Source.Contains($Include)) { $Source += "`r`n$Include`r`n" }
Set-Content -LiteralPath $Main -Value $Source -Encoding UTF8
$Python = Join-Path $Root 'backend\.venv\Scripts\python.exe'
if (!(Test-Path -LiteralPath $Python)) { throw "Missing backend Python $Python" }
& $Python -m py_compile $Main $Router
if ($LASTEXITCODE -ne 0) { throw 'Python syntax verification failed; restore backup' }
Write-Host 'Browser share files installed. Python syntax PASS.' -ForegroundColor Green
Write-Host 'Restart ONLY the existing backend process on port 8001. Restart Next.js if hot reload does not pick up the new route.'
Write-Host 'Owner and employee open: http://localhost:3001/browser-screen-share'
