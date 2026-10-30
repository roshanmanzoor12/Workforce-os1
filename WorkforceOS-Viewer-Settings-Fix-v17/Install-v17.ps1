param([switch]$Apply, [string]$Root = 'C:\workforce-os')
$ErrorActionPreference = 'Stop'
$Python = Join-Path $Root '.venv\Scripts\python.exe'
if (!(Test-Path $Python)) { $Python = 'python' }
$Patch = Join-Path $PSScriptRoot 'patch_v17.py'
if (!(Test-Path $Patch)) { throw 'V17 patcher missing' }
$Arguments = @($Patch, '--root', $Root)
if ($Apply) { $Arguments += '--apply' }
& $Python @Arguments
if ($LASTEXITCODE -ne 0) { throw "V17 preflight/apply failed ($LASTEXITCODE). Nothing should be forcibly overwritten." }
