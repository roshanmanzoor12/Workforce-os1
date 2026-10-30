param([switch]$Apply, [string]$Root = 'C:\workforce-os')
$ErrorActionPreference = 'Stop'
$Python = Join-Path $Root '.venv\Scripts\python.exe'
if (!(Test-Path $Python)) { $Python = 'python' }
$Args = @((Join-Path $PSScriptRoot 'patch_v16.py'), '--root', $Root)
if ($Apply) { $Args += '--apply' }
& $Python @Args
if ($LASTEXITCODE -ne 0) { throw "V16 SOURCE PRECHECK/APPLY FAILED ($LASTEXITCODE)" }
