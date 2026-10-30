$ErrorActionPreference = 'Stop'
$Root = 'C:\workforce-os'
$Page = Join-Path $Root 'apps\web\app\(workspace)\monitoring\live-screen\page.tsx'
$Component = Join-Path $Root 'apps\web\components\monitoring\native-jpeg-stream.tsx'
$Source = Join-Path $PSScriptRoot 'native-jpeg-stream.tsx'
if (!(Test-Path -LiteralPath $Page)) { throw "Live Screen page missing: $Page" }
if (!(Test-Path -LiteralPath $Component)) { throw "3B native JPEG viewer missing: $Component" }
$Original = [System.IO.File]::ReadAllText($Page)
$Old = 'deviceId={typeof window !== "undefined" ? window.sessionStorage.getItem("wfos_screen_device_id") || "" : ""}'
$New = 'deviceId={selectedDesktopAgent?.device_name || ""}'
if (!$Original.Contains($Old) -and !$Original.Contains($New)) { throw 'Expected 3B viewer call not found; refusing page modification.' }
$Stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$Backup = Join-Path $Root ("artifacts\backups\live-screen-3d-$Stamp")
New-Item -ItemType Directory -Force -Path $Backup | Out-Null
Copy-Item -LiteralPath $Page -Destination (Join-Path $Backup 'page.tsx')
Copy-Item -LiteralPath $Component -Destination (Join-Path $Backup 'native-jpeg-stream.tsx')
$Updated = $Original.Replace($Old, $New)
[System.IO.File]::WriteAllText($Page, $Updated, [System.Text.UTF8Encoding]::new($false))
Copy-Item -LiteralPath $Source -Destination $Component -Force
Write-Host "PASS: Live Screen local viewer UI installed. Backup: $Backup" -ForegroundColor Green
Write-Host 'Restart Next.js frontend. Then select employee + desktop agent and enter viewer token in-page.'
Write-Host 'To copy your local test viewer token to clipboard, run COPY-VIEWER-TOKEN.ps1.'
