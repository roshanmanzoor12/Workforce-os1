$ErrorActionPreference = "Stop"

$backendDirectory = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $backendDirectory

$python = Join-Path $backendDirectory ".venv\Scripts\python.exe"
$config = Join-Path $backendDirectory "alembic-control.ini"

if (-not (Test-Path -LiteralPath $python)) {
    throw "Backend virtual environment Python is missing: $python"
}

if (-not (Test-Path -LiteralPath $config)) {
    throw "Control migration configuration is missing: $config"
}

$env:PYTHONPATH = $backendDirectory

Write-Host "Checking that the control migration head includes scope storage..."

$verifyAncestry = @'
from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory

config_path = Path("alembic-control.ini").resolve()
config = Config(str(config_path))
scripts = ScriptDirectory.from_config(config)

required_revision = "phase38_member_scopes_01"
heads = scripts.get_heads()

if len(heads) != 1:
    raise SystemExit(
        "Expected one control migration head; found: "
        + ", ".join(heads)
    )

head = heads[0]

try:
    required = scripts.get_revision(required_revision)
except Exception as exc:
    raise SystemExit(
        f"Cannot resolve required scope migration: {required_revision}"
    ) from exc

if required is None:
    raise SystemExit(
        f"Required scope migration is missing: {required_revision}"
    )

ancestors = {
    revision.revision
    for revision in scripts.walk_revisions(base="base", head=head)
}

if required_revision not in ancestors:
    raise SystemExit(
        f"Control head {head} does not descend from "
        f"{required_revision}. No database changes were made."
    )

print("CONTROL_HEAD:", head)
print("REQUIRED_ANCESTOR:", required_revision)
print("PHASE38_SCOPE_MIGRATION_ANCESTRY_PASSED")
'@

$verifyAncestry | & $python -

if ($LASTEXITCODE -ne 0) {
    throw "Phase 38.2 migration ancestry verification failed."
}

Write-Host ""
Write-Host "Inspecting the applied control database revision..."

& $python -m alembic -c $config current

if ($LASTEXITCODE -ne 0) {
    throw "Control database revision inspection failed."
}

Write-Host ""
Write-Host "PHASE38_2_MIGRATION_ANCESTRY_GATE_PASSED"
Write-Host "Compare the applied revision above with CONTROL_HEAD."
Write-Host "Real-database grant/access/revoke verification remains pending."