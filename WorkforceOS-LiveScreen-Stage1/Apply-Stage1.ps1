$ErrorActionPreference = 'Stop'
$Root = 'C:\workforce-os'
$Relative = 'apps\web\app\(workspace)\monitoring\live-screen\page.tsx'
$ExpectedSha256 = '73dc153ca16094a5a3044229649c2d400523583ba3b2d8e9c378f622b4d0af5c'
$Source = Join-Path $PSScriptRoot ('patch\' + $Relative)
$Target = Join-Path $Root $Relative
if (-not (Test-Path -LiteralPath $Source)) { throw "Patch missing: $Source" }
if (-not (Test-Path -LiteralPath $Target)) { throw "Project target missing: $Target" }
$Actual = (Get-FileHash -LiteralPath $Target -Algorithm SHA256).Hash.ToLowerInvariant()
if ($Actual -ne $ExpectedSha256) {
  throw "Target has changed since supplied ZIP. Patch NOT applied. Expected $ExpectedSha256; found $Actual. Upload current page.tsx for safe merge."
}
$Stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$BackupDir = Join-Path $Root ('workforce-patch-backups\live-screen-stage1-' + $Stamp)
$Backup = Join-Path $BackupDir $Relative
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Backup) | Out-Null
Copy-Item -LiteralPath $Target -Destination $Backup -Force
try {
  Copy-Item -LiteralPath $Source -Destination $Target -Force
  $ExpectedPatch = (Get-FileHash -LiteralPath $Source -Algorithm SHA256).Hash
  $ActualPatch = (Get-FileHash -LiteralPath $Target -Algorithm SHA256).Hash
  if ($ExpectedPatch -ne $ActualPatch) { throw 'Installed patch checksum mismatch' }
  Write-Host 'Stage 1 UI patch installed.' -ForegroundColor Green
  Write-Host "Backup: $Backup"
  Write-Host 'Restart the Next.js frontend or rebuild it, then reload Live Screen.'
  Write-Host 'Note: This patch does NOT enable screen streaming.' -ForegroundColor Yellow
} catch {
  Copy-Item -LiteralPath $Backup -Destination $Target -Force
  throw
}
