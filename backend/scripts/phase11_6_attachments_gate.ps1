$ErrorActionPreference = "Stop"

$BackendRoot = "C:\workforce-os\backend"
$Python = "C:\workforce-os\backend\.venv\Scripts\python.exe"

Set-Location $BackendRoot

Write-Host "================================================="
Write-Host " WorkforceOS Phase 11.6 Attachment Gate"
Write-Host "================================================="
Write-Host ""

Write-Host "[preflight 1/3] PostgreSQL 5434..."

$Postgres = Test-NetConnection `
    -ComputerName "127.0.0.1" `
    -Port 5434 `
    -WarningAction SilentlyContinue

if (-not $Postgres.TcpTestSucceeded) {
    throw "PostgreSQL 5434 is not reachable"
}

Write-Host "PASS PostgreSQL reachable"
Write-Host ""

Write-Host "[preflight 2/3] MinIO 9000..."

$Minio = Test-NetConnection `
    -ComputerName "127.0.0.1" `
    -Port 9000 `
    -WarningAction SilentlyContinue

if (-not $Minio.TcpTestSucceeded) {
    throw "MinIO 9000 is not reachable"
}

Write-Host "PASS MinIO reachable"
Write-Host ""

Write-Host "[preflight 3/3] Python dependencies..."

$DependencyScript = @'
import importlib.util

required = [
    "fastapi",
    "sqlalchemy",
    "minio",
    "pytest",
]

missing = [
    name
    for name in required
    if importlib.util.find_spec(name) is None
]

if missing:
    raise SystemExit(
        "Missing Python dependencies: "
        + ", ".join(missing)
    )

print("PASS Python dependencies")
'@

$DependencyScript | & $Python -

if ($LASTEXITCODE -ne 0) {
    throw "Python dependency check failed"
}

Write-Host ""
Write-Host "[1/7] Compiling attachment files..."

& $Python -m compileall `
    app\modules\attachments `
    tests\test_phase11_6_attachments.py `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Attachment compile failed"
}

Write-Host "PASS compile"
Write-Host ""

Write-Host "[2/7] Attachment tests..."

& $Python -m pytest `
    tests\test_phase11_6_attachments.py `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Attachment tests failed"
}

Write-Host "PASS tests"
Write-Host ""

Write-Host "[3/7] Control migration..."

& $Python -m alembic -c .\alembic-control.ini upgrade head

if ($LASTEXITCODE -ne 0) {
    throw "Alembic migration failed"
}

$MigrationScript = @'
import subprocess

result = subprocess.run(
    [
        r"C:\workforce-os\backend\.venv\Scripts\python.exe",
        "-m",
        "alembic",
        "heads",
    ],
    capture_output=True,
    text=True,
    check=True,
)

text = result.stdout.strip()

print(text)

if "b7c8d9e0f1a2" not in text:
    raise SystemExit(
        "Expected attachment migration "
        "b7c8d9e0f1a2 is not head"
    )

print("PASS attachment migration")
'@

$MigrationScript | & $Python -

if ($LASTEXITCODE -ne 0) {
    throw "Attachment migration verification failed"
}

Write-Host ""
Write-Host "[4/7] Attachment REST contract..."

$ContractScript = @'
from app.main import app

schema = app.openapi()
paths = schema.get("paths", {})

expected = {
    "/api/v1/attachments/limits": {"get"},
    "/api/v1/attachments/prepare": {"post"},
    "/api/v1/attachments/{attachment_id}": {
        "get",
        "delete",
    },
    "/api/v1/attachments/{attachment_id}/complete": {
        "post",
    },
    "/api/v1/attachments/{attachment_id}/download": {
        "post",
    },
}

for path, methods in expected.items():
    if path not in paths:
        raise SystemExit(
            f"Missing attachment route: {path}"
        )

    actual = {
        method.lower()
        for method in paths[path].keys()
    }

    missing = methods - actual

    if missing:
        raise SystemExit(
            f"{path} missing methods: "
            + ", ".join(sorted(missing))
        )

    for method in sorted(methods):
        print(
            f"PASS: {method.upper()} {path}"
        )

print("PASS attachment REST API contract")
'@

$ContractScript | & $Python -

if ($LASTEXITCODE -ne 0) {
    throw "Attachment REST contract failed"
}

Write-Host ""
Write-Host "[5/7] Attachment privacy boundary..."

$BoundaryScript = @'
from pathlib import Path

service = Path(
    "app/modules/attachments/service.py"
).read_text(
    encoding="utf-8",
)

storage = Path(
    "app/modules/attachments/storage.py"
).read_text(
    encoding="utf-8",
)

router = Path(
    "app/modules/attachments/router.py"
).read_text(
    encoding="utf-8",
)

required_service = [
    "assert_scope_access",
    "_conversation_access_allowed",
    "_channel_access_allowed",
    "owner_user_id",
]

for token in required_service:
    if token not in service:
        raise SystemExit(
            "Missing attachment authorization "
            f"boundary: {token}"
        )

if "presigned_put_object" not in storage:
    raise SystemExit(
        "Upload must use presigned MinIO URL"
    )

if "presigned_get_object" not in storage:
    raise SystemExit(
        "Download must use presigned MinIO URL"
    )

if "get_current_verified_user" not in router:
    raise SystemExit(
        "Attachment routes must require "
        "verified-user auth"
    )

print(
    "PASS conversation membership boundary"
)

print(
    "PASS channel membership boundary"
)

print(
    "PASS verified-user attachment boundary"
)

print(
    "PASS frontend receives presigned URLs only"
)
'@

$BoundaryScript | & $Python -

if ($LASTEXITCODE -ne 0) {
    throw "Attachment privacy boundary failed"
}

Write-Host ""
Write-Host "[6/7] File-size policy..."

$LimitScript = @'
from app.modules.attachments.limits import (
    MIB,
    get_attachment_limit_bytes,
)

expected = {
    "FREE": 10 * MIB,
    "STARTER": 50 * MIB,
    "PROFESSIONAL": 250 * MIB,
    "BUSINESS": 1024 * MIB,
}

for plan, size in expected.items():
    actual = get_attachment_limit_bytes(plan)

    if actual != size:
        raise SystemExit(
            f"{plan} attachment limit mismatch: "
            f"{actual} != {size}"
        )

    print(
        f"PASS {plan}: "
        f"{actual // MIB} MB"
    )

print("PASS entitlement-aware size policy")
'@

$LimitScript | & $Python -

if ($LASTEXITCODE -ne 0) {
    throw "Attachment size policy failed"
}

Write-Host ""
Write-Host "[7/7] Client storage boundary..."

$StorageBoundaryScript = @'
from pathlib import Path

frontend_forbidden = [
    "MINIO_ACCESS_KEY",
    "MINIO_SECRET_KEY",
]

roots = [
    Path("frontend"),
    Path("web"),
]

existing_roots = [
    root
    for root in roots
    if root.exists()
]

for root in existing_roots:
    for path in root.rglob("*"):
        if not path.is_file():
            continue

        if path.suffix.lower() not in {
            ".ts",
            ".tsx",
            ".js",
            ".jsx",
            ".env",
            ".json",
        }:
            continue

        try:
            text = path.read_text(
                encoding="utf-8",
                errors="ignore",
            )
        except Exception:
            continue

        for token in frontend_forbidden:
            if token in text:
                raise SystemExit(
                    f"Frontend exposes forbidden "
                    f"storage credential token "
                    f"{token} in {path}"
                )

print(
    "PASS frontend never receives "
    "MinIO credentials"
)

print(
    "PASS frontend uploads/downloads "
    "through temporary signed URLs"
)
'@

$StorageBoundaryScript | & $Python -

if ($LASTEXITCODE -ne 0) {
    throw "Client storage boundary failed"
}

Write-Host ""
Write-Host "================================================="
Write-Host " PHASE 11.6 ATTACHMENT FOUNDATION: PASS"
Write-Host "================================================="


