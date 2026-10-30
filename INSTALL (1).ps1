$ErrorActionPreference = 'Stop'
$Root = 'C:\workforce-os'
$Installer = Join-Path $PSScriptRoot 'install_device_link.py'
$Python = Join-Path $Root 'backend\.venv\Scripts\python.exe'
if (!(Test-Path $Python)) { $Python = 'python' }
& $Python $Installer $Root
if ($LASTEXITCODE -ne 0) { throw 'Patch not applied. Check error above.' }
