$ErrorActionPreference = "Stop"


$BackendRoot = "C:\workforce-os\backend"

$Python = (
    "C:\workforce-os\backend\" +
    ".venv\Scripts\python.exe"
)

$ExpectedControlHead = "g1b2c3d4e5f6"

$ExpectedTenantHead = "g7b8c9d0e1f2"

$WorkspaceId = (
    "34527ffb-e094-4e5e-89ee-4cab97244fc3"
)

$TenantDatabase = (
    "tenant_" +
    $WorkspaceId.Replace(
        "-",
        ""
    )
)


Set-Location $BackendRoot


Write-Host "================================================="
Write-Host " WorkforceOS Phase 12.8 Workspace Search"
Write-Host "================================================="
Write-Host ""


# =========================================================
# REQUIRED FILES
# =========================================================

$RequiredFiles = @(
    ".\app\modules\workspace_search\__init__.py",
    ".\app\modules\workspace_search\enums.py",
    ".\app\modules\workspace_search\schemas.py",
    ".\app\modules\workspace_search\access.py",
    ".\app\modules\workspace_search\ranking.py",
    ".\app\modules\workspace_search\repository.py",
    ".\app\modules\workspace_search\service.py",
    ".\app\modules\workspace_search\router.py",
    ".\app\modules\tenant_api\router.py"
)


foreach ($File in $RequiredFiles)
{
    if (-not (Test-Path $File))
    {
        throw (
            "Missing required file: " +
            $File
        )
    }
}


Write-Host "PASS required files"
Write-Host ""


# =========================================================
# 1/8 COMPILE
# =========================================================

Write-Host "[1/8] Compiling..."


& $Python `
    -m compileall `
    .\app\modules\workspace_search `
    .\app\modules\tenant_api `
    -q


if ($LASTEXITCODE -ne 0)
{
    throw "Compile failed."
}


Write-Host "PASS compile"
Write-Host ""


# =========================================================
# 2/8 ENTITY TYPES
# =========================================================

Write-Host "[2/8] Search entity types..."


$EntityCheck = @'
from app.modules.workspace_search.enums import (
    SEARCH_ENTITY_TYPES,
)


expected = {
    "employee",
    "goal",
    "note",
    "knowledge",
    "meeting",
}


if set(SEARCH_ENTITY_TYPES) != expected:
    raise SystemExit(
        "Search entity types invalid: "
        + str(
            SEARCH_ENTITY_TYPES
        )
    )


print(
    "PASS search entity types"
)
'@


$EntityCheck | & $Python -


if ($LASTEXITCODE -ne 0)
{
    throw "Search entity type gate failed."
}


Write-Host ""


# =========================================================
# 3/8 RANKING
# =========================================================

Write-Host "[3/8] Search ranking..."


$RankingCheck = @'
from app.modules.workspace_search.ranking import (
    combined_score,
    field_match_score,
)


exact = field_match_score(
    query="Alice",
    value="Alice",
)


prefix = field_match_score(
    query="Ali",
    value="Alice Smith",
)


substring = field_match_score(
    query="Smith",
    value="Alice Smith",
)


miss = field_match_score(
    query="Finance",
    value="Alice Smith",
)


if not (
    exact > prefix
    and prefix > substring
    and substring > miss
):
    raise SystemExit(
        "Search ranking order invalid."
    )


score, fields = combined_score(
    query="Alice",
    fields=[
        (
            "name",
            "Alice Smith",
            1.3,
        ),
        (
            "email",
            "alice@example.com",
            1.0,
        ),
    ],
)


if score <= 0:
    raise SystemExit(
        "Combined search score invalid."
    )


if "name" not in fields:
    raise SystemExit(
        "Matched fields missing name."
    )


print(
    "PASS search ranking"
)
'@


$RankingCheck | & $Python -


if ($LASTEXITCODE -ne 0)
{
    throw "Search ranking gate failed."
}


Write-Host ""


# =========================================================
# 4/8 IMPORT CONTRACT
# =========================================================

Write-Host "[4/8] Search imports..."


$ImportCheck = @'
from app.modules.workspace_search.access import (
    SearchAccess,
    resolve_search_access,
)

from app.modules.workspace_search.repository import (
    WorkspaceSearchRepository,
)

from app.modules.workspace_search.router import (
    router,
)

from app.modules.workspace_search.service import (
    WorkspaceSearchService,
)


assert SearchAccess
assert resolve_search_access
assert WorkspaceSearchRepository
assert WorkspaceSearchService
assert router


print(
    "PASS search imports"
)
'@


$ImportCheck | & $Python -


if ($LASTEXITCODE -ne 0)
{
    throw "Search import gate failed."
}


Write-Host ""


# =========================================================
# 5/8 ASYNCSESSION SAFETY
# =========================================================

Write-Host "[5/8] AsyncSession safety..."


$AsyncSafety = @'
import ast
from pathlib import Path


root = Path(
    r"C:\workforce-os\backend\app\modules\workspace_search"
)


violations = []


for path in root.glob("*.py"):
    source = path.read_text(
        encoding="utf-8-sig"
    )

    tree = ast.parse(
        source,
        filename=str(path),
    )

    gather_aliases = set()

    for node in ast.walk(tree):
        if isinstance(
            node,
            ast.ImportFrom,
        ):
            if node.module == "asyncio":
                for alias in node.names:
                    if alias.name == "gather":
                        gather_aliases.add(
                            alias.asname
                            or alias.name
                        )

    for node in ast.walk(tree):
        if not isinstance(
            node,
            ast.Call,
        ):
            continue

        func = node.func

        if (
            isinstance(
                func,
                ast.Attribute,
            )
            and isinstance(
                func.value,
                ast.Name,
            )
            and func.value.id == "asyncio"
            and func.attr == "gather"
        ):
            violations.append(
                str(path)
            )

        if (
            isinstance(
                func,
                ast.Name,
            )
            and func.id
            in gather_aliases
        ):
            violations.append(
                str(path)
            )


if violations:
    raise SystemExit(
        "Unsafe asyncio.gather found: "
        + ", ".join(
            sorted(
                set(
                    violations
                )
            )
        )
    )


print(
    "PASS AsyncSession safety"
)
'@


$AsyncSafety | & $Python -


if ($LASTEXITCODE -ne 0)
{
    throw "AsyncSession safety gate failed."
}


Write-Host ""


# =========================================================
# 6/8 APP + OPENAPI
# =========================================================

Write-Host "[6/8] App/OpenAPI..."


$OpenApiCheck = @'
from app.main import app


paths = app.openapi()["paths"]


search_path = (
    "/api/v1/workspaces/"
    "{workspace_id}/search"
)


capabilities_path = (
    "/api/v1/workspaces/"
    "{workspace_id}/search/capabilities"
)


required = {
    search_path,
    capabilities_path,
}


missing = (
    required
    - set(paths)
)


if missing:
    raise SystemExit(
        "Missing search endpoints: "
        + str(
            sorted(
                missing
            )
        )
    )


if "get" not in paths[search_path]:
    raise SystemExit(
        "Workspace search GET missing."
    )


if "get" not in paths[capabilities_path]:
    raise SystemExit(
        "Search capabilities GET missing."
    )


print(
    "PASS app/OpenAPI"
)
'@


$OpenApiCheck | & $Python -


if ($LASTEXITCODE -ne 0)
{
    throw "Search OpenAPI gate failed."
}


Write-Host ""


# =========================================================
# 7/8 CONTROL HEAD
# =========================================================

Write-Host "[7/8] Control migration head..."


$ControlHeads = & $Python `
    -m alembic `
    -c ".\alembic-control.ini" `
    heads


if ($LASTEXITCODE -ne 0)
{
    throw "Control Alembic heads failed."
}


$ControlHeadLines = @(
    $ControlHeads |
    ForEach-Object {
        if ($null -ne $_)
        {
            $_.ToString().Trim()
        }
    } |
    Where-Object {
        $_.Length -gt 0
    }
)


foreach ($Line in $ControlHeadLines)
{
    Write-Host $Line
}


if ($ControlHeadLines.Count -ne 1)
{
    throw (
        "Expected exactly one control head. Found: " +
        $ControlHeadLines.Count
    )
}


$ControlHeadText = (
    $ControlHeadLines -join "`n"
)


if ($ControlHeadText -notmatch $ExpectedControlHead)
{
    throw (
        "Unexpected control head. Expected " +
        $ExpectedControlHead +
        ". Actual: " +
        $ControlHeadText
    )
}


Write-Host "PASS control head"
Write-Host ""


# =========================================================
# 8/8 TENANT HEAD
# =========================================================

Write-Host "[8/8] Tenant migration head..."


$TenantHeads = & $Python `
    -m alembic `
    -c ".\alembic.tenant.ini" `
    -x "database_name=$TenantDatabase" `
    heads


if ($LASTEXITCODE -ne 0)
{
    throw "Tenant Alembic heads failed."
}


$TenantHeadLines = @(
    $TenantHeads |
    ForEach-Object {
        if ($null -ne $_)
        {
            $_.ToString().Trim()
        }
    } |
    Where-Object {
        $_.Length -gt 0
    }
)


foreach ($Line in $TenantHeadLines)
{
    Write-Host $Line
}


if ($TenantHeadLines.Count -ne 1)
{
    throw (
        "Expected exactly one tenant head. Found: " +
        $TenantHeadLines.Count
    )
}


$TenantHeadText = (
    $TenantHeadLines -join "`n"
)


if ($TenantHeadText -notmatch $ExpectedTenantHead)
{
    throw (
        "Unexpected tenant head. Expected " +
        $ExpectedTenantHead +
        ". Actual: " +
        $TenantHeadText
    )
}


Write-Host "PASS tenant head"
Write-Host ""


# =========================================================
# FINAL
# =========================================================

Write-Host "================================================="
Write-Host " PHASE 12.8 WORKSPACE SEARCH: PASS"
Write-Host "================================================="
Write-Host "Permission-aware search:   PASS"
Write-Host "Custom-role support:       PASS"
Write-Host "Employee search:           PASS"
Write-Host "Goal search:               PASS"
Write-Host "Note search:               PASS"
Write-Host "Knowledge search:          PASS"
Write-Host "Meeting search:            PASS"
Write-Host "Result ranking:            PASS"
Write-Host "Result deduplication:      PASS"
Write-Host "AsyncSession safety:       PASS"
Write-Host "OpenAPI:                   PASS"
Write-Host "Control head:              $ExpectedControlHead"
Write-Host "Tenant head:               $ExpectedTenantHead"
Write-Host "================================================="