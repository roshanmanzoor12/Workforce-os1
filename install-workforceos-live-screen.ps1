$ErrorActionPreference = 'Stop'
$root = 'C:\workforce-os'
$source = Join-Path $env:USERPROFILE 'Downloads\workforceos-live-screen-page-fixed.tsx'
$target = Join-Path $root 'apps\web\app\(workspace)\monitoring\live-screen\page.tsx'
if (-not (Test-Path -LiteralPath $source)) { throw "Downloaded replacement not found: $source" }
if (-not (Test-Path -LiteralPath $target)) { throw "Current page not found: $target" }
$backup = "$target.backup-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
Copy-Item -LiteralPath $target -Destination $backup
Copy-Item -LiteralPath $source -Destination $target -Force
Push-Location (Join-Path $root 'apps\web')
try {
    & npx tsc --noEmit
    if ($LASTEXITCODE -ne 0) { throw 'TypeScript validation failed. Original page will be restored.' }
    Write-Host 'LIVE SCREEN REGISTRY GUARD: TYPESCRIPT PASS' -ForegroundColor Green
    Write-Host "Backup: $backup"
} catch {
    Copy-Item -LiteralPath $backup -Destination $target -Force
    throw
} finally { Pop-Location }
