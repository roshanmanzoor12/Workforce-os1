param(
    [switch]$Apply,
    [string]$Root = 'C:\workforce-os'
)
$ErrorActionPreference = 'Stop'
$Py = Join-Path $Root '.venv\Scripts\python.exe'
if (!(Test-Path $Py)) { throw "WorkforceOS Python environment not found: $Py" }
$Patch = Join-Path $PSScriptRoot 'patch_v18.py'
if (!(Test-Path $Patch)) { throw 'V18 patcher missing' }
$Arguments = @($Patch, '--root', $Root)
if ($Apply) { $Arguments += '--apply' }
& $Py @Arguments
if ($LASTEXITCODE -ne 0) { throw 'V18 source conflict / patch failed; no forced overwrite' }
