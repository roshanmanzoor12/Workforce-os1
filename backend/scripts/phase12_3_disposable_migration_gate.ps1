$ErrorActionPreference = "Stop"

$BackendRoot = "C:\workforce-os\backend"

Set-Location $BackendRoot


Write-Host ""
Write-Host "================================================"
Write-Host " WorkforceOS Phase 12.3 Migration Certificate"
Write-Host "================================================"


# =========================================================
# PYTHON IMPORT ROOT
# =========================================================
#
# Direct execution of:
#
#     scripts\phase12_3_disposable_tenant_cert.py
#
# normally places backend\scripts on sys.path.
#
# WorkforceOS application packages live under:
#
#     backend\app
#
# Therefore explicitly expose backend as PYTHONPATH for this
# certification process.
#
# Preserve any pre-existing PYTHONPATH and restore it at the end.
# =========================================================


$PreviousPythonPath = $env:PYTHONPATH


if (
    [string]::IsNullOrWhiteSpace(
        $PreviousPythonPath
    )
) {
    $env:PYTHONPATH = $BackendRoot
}
else {
    $env:PYTHONPATH = (
        $BackendRoot +
        [System.IO.Path]::PathSeparator +
        $PreviousPythonPath
    )
}


try {

    # =====================================================
    # 1. COMPILE
    # =====================================================

    Write-Host ""
    Write-Host "[1/4] Compile certificate..."

    & ".\.venv\Scripts\python.exe" `
        -m py_compile `
        ".\scripts\phase12_3_disposable_tenant_cert.py"

    if ($LASTEXITCODE -ne 0) {
        throw "Certificate compile failed."
    }

    Write-Host "PASS compile"


    # =====================================================
    # 2. IMPORT ENVIRONMENT
    # =====================================================

    Write-Host ""
    Write-Host "[2/4] Verify backend import environment..."

    & ".\.venv\Scripts\python.exe" `
        -c "import app; from app.db.tenant_provisioning import create_postgres_admin_engine, quote_postgres_identifier; print('PASS backend imports')"

    if ($LASTEXITCODE -ne 0) {
        throw "Backend import environment failed."
    }


    # =====================================================
    # 3. MIGRATION GRAPH
    # =====================================================

    Write-Host ""
    Write-Host "[3/4] Migration graph head..."

    $HeadOutput = & ".\.venv\Scripts\python.exe" `
        -m alembic `
        -c ".\alembic.tenant.ini" `
        heads

    if ($LASTEXITCODE -ne 0) {
        throw "Tenant migration graph failed."
    }

    $HeadOutput


    if (
        $HeadOutput `
        -notmatch "p6k7l8m9n0o1"
    ) {
        throw (
            "Unexpected tenant migration head. " +
            "Expected p6k7l8m9n0o1."
        )
    }

    Write-Host "PASS migration graph"


    # =====================================================
    # 4. REAL DISPOSABLE DATABASE CERTIFICATE
    # =====================================================

    Write-Host ""
    Write-Host "[4/4] Disposable DB upgrade/down/upgrade..."

    & ".\.venv\Scripts\python.exe" `
        ".\scripts\phase12_3_disposable_tenant_cert.py"

    if ($LASTEXITCODE -ne 0) {
        throw (
            "Disposable migration certificate failed."
        )
    }


    # =====================================================
    # COMPLETE
    # =====================================================

    Write-Host ""
    Write-Host "================================================"
    Write-Host " Phase 12.3 Migration Certificate PASS"
    Write-Host "================================================"
}
finally {

    # =====================================================
    # RESTORE PYTHONPATH
    # =====================================================

    if (
        [string]::IsNullOrWhiteSpace(
            $PreviousPythonPath
        )
    ) {
        Remove-Item `
            Env:PYTHONPATH `
            -ErrorAction SilentlyContinue
    }
    else {
        $env:PYTHONPATH = (
            $PreviousPythonPath
        )
    }
}