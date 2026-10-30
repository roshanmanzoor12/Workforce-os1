$ErrorActionPreference = 'Stop'
$root = 'C:\workforce-os'
$pkg = Split-Path -Parent $MyInvocation.MyCommand.Path
if (!(Test-Path "$root\live-screen-milestone3b\relay\server.py")) { throw 'Milestone 3B relay missing. Install 3B first.' }
if (!(Test-Path "$root\agent\WorkforceOS.ScreenCompanion\WorkforceOS.ScreenCompanion.csproj")) { throw 'Screen Companion missing.' }
$target = Join-Path $root 'tools\live-screen-dev'
New-Item -ItemType Directory -Path $target -Force | Out-Null
Copy-Item "$pkg\*.ps1" $target -Force
Write-Host "Installed local development launch tools: $target"
Write-Host 'Next: run Setup.ps1, then start relay, companion, and configure viewer as described in README.md.'
