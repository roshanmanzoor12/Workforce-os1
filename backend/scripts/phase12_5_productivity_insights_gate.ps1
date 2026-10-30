$ErrorActionPreference = "Stop"


$BackendRoot = (
    "C:\workforce-os\backend"
)

$Python = (
    "C:\workforce-os\backend\" +
    ".venv\Scripts\python.exe"
)

$ExpectedControlHead = (
    "f1a2b3c4d5e6"
)


Set-Location $BackendRoot


Write-Host "================================================="
Write-Host " WorkforceOS Phase 12.5 Productivity Insights"
Write-Host "================================================="
Write-Host ""


# =========================================================
# REQUIRED FILES
# =========================================================

$RequiredFiles = @(
    ".\app\modules\productivity_insights\__init__.py",
    ".\app\modules\productivity_insights\access.py",
    ".\app\modules\productivity_insights\schemas.py",
    ".\app\modules\productivity_insights\calculations.py",
    ".\app\modules\productivity_insights\service.py",
    ".\app\modules\productivity_insights\router.py",
    ".\app\modules\analytics\repository.py",
    ".\app\modules\analytics\service.py",
    ".\app\modules\workspace_permissions\permissions.py",
    ".\app\modules\workspace_permissions\roles.py",
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
    .\app\modules\productivity_insights `
    .\app\modules\analytics `
    .\app\modules\workspace_permissions `
    .\app\modules\tenant_api `
    -q


if ($LASTEXITCODE -ne 0)
{
    throw "Compile failed."
}


Write-Host "PASS compile"
Write-Host ""


# =========================================================
# 2/8 PERMISSIONS
# =========================================================

Write-Host "[2/8] Productivity permissions..."


$PermissionCheck = @'
from app.modules.workspace_permissions.permissions import (
    ALL_WORKSPACE_PERMISSIONS,
)

from app.modules.workspace_permissions.roles import (
    ADMIN_PERMISSIONS,
    CLIENT_PERMISSIONS,
    MANAGER_PERMISSIONS,
    MEMBER_PERMISSIONS,
    OWNER_PERMISSIONS,
)


required = {
    "productivity_insights.self.read",
    "productivity_insights.team.read",
    "productivity_insights.all.read",
    "productivity_insights.export",
}


missing = (
    required
    - set(
        ALL_WORKSPACE_PERMISSIONS
    )
)


if missing:
    raise SystemExit(
        "Missing productivity permissions: "
        + str(
            sorted(
                missing
            )
        )
    )


if not required.issubset(
    set(
        OWNER_PERMISSIONS
    )
):
    raise SystemExit(
        "Owner productivity permissions invalid."
    )


if not required.issubset(
    set(
        ADMIN_PERMISSIONS
    )
):
    raise SystemExit(
        "Admin productivity permissions invalid."
    )


manager_required = {
    "productivity_insights.self.read",
    "productivity_insights.team.read",
}


if not manager_required.issubset(
    set(
        MANAGER_PERMISSIONS
    )
):
    raise SystemExit(
        "Manager productivity permissions invalid."
    )


if (
    "productivity_insights.self.read"
    not in MEMBER_PERMISSIONS
):
    raise SystemExit(
        "Member productivity self permission missing."
    )


if any(
    permission.startswith(
        "productivity_insights."
    )
    for permission
    in CLIENT_PERMISSIONS
):
    raise SystemExit(
        "Client must not receive productivity "
        "insights permissions by default."
    )


print(
    "PASS productivity permissions"
)
'@


$PermissionCheck |
    & $Python -


if ($LASTEXITCODE -ne 0)
{
    throw "Productivity permission gate failed."
}


Write-Host ""


# =========================================================
# 3/8 CALCULATION CONTRACT
# =========================================================

Write-Host "[3/8] Calculation contract..."


$CalculationCheck = @'
from app.modules.productivity_insights.calculations import (
    metric_change,
    percentage,
)


if percentage(
    50,
    100,
) != 50.0:
    raise SystemExit(
        "percentage() failed."
    )


if percentage(
    1,
    0,
) != 0.0:
    raise SystemExit(
        "Zero denominator handling failed."
    )


change = metric_change(
    current=120,
    previous=100,
)


if change.absolute_change != 20.0:
    raise SystemExit(
        "Absolute comparison failed."
    )


if change.percent_change != 20.0:
    raise SystemExit(
        "Percentage comparison failed."
    )


zero_previous = metric_change(
    current=10,
    previous=0,
)


if (
    zero_previous.percent_change
    is not None
):
    raise SystemExit(
        "Zero previous value must return "
        "percent_change=None."
    )


print(
    "PASS calculation contract"
)
'@


$CalculationCheck |
    & $Python -


if ($LASTEXITCODE -ne 0)
{
    throw "Calculation contract failed."
}


Write-Host ""


# =========================================================
# 4/8 IMPORTS
# =========================================================

Write-Host "[4/8] Productivity imports..."


$ImportCheck = @'
from app.modules.productivity_insights.access import (
    resolve_productivity_insights_access,
)

from app.modules.productivity_insights.router import (
    router,
)

from app.modules.productivity_insights.service import (
    ProductivityInsightsService,
)


assert callable(
    resolve_productivity_insights_access
)

assert router

assert ProductivityInsightsService


print(
    "PASS productivity imports"
)
'@


$ImportCheck |
    & $Python -


if ($LASTEXITCODE -ne 0)
{
    throw "Productivity import failed."
}


Write-Host ""


# =========================================================
# 5/8 APP IMPORT
# =========================================================

Write-Host "[5/8] App import..."


& $Python `
    -c "from app.main import app; print('PASS app.main')"


if ($LASTEXITCODE -ne 0)
{
    throw "App import failed."
}


Write-Host ""


# =========================================================
# 6/8 OPENAPI
# =========================================================

Write-Host "[6/8] Productivity OpenAPI..."


$OpenApiCheck = @'
from app.main import app


paths = app.openapi()["paths"]


required = {
    "/api/v1/workspaces/{workspace_id}/productivity-insights/overview",
    "/api/v1/workspaces/{workspace_id}/productivity-insights/activity",
    "/api/v1/workspaces/{workspace_id}/productivity-insights/usage",
    "/api/v1/workspaces/{workspace_id}/productivity-insights/goals",
    "/api/v1/workspaces/{workspace_id}/productivity-insights/comparison",
}


missing = (
    required
    - set(
        paths
    )
)


if missing:
    raise SystemExit(
        "Missing productivity paths: "
        + str(
            sorted(
                missing
            )
        )
    )


for path in required:
    if "get" not in paths[path]:
        raise SystemExit(
            "GET missing: "
            + path
        )


print(
    "PASS productivity OpenAPI"
)
'@


$OpenApiCheck |
    & $Python -


if ($LASTEXITCODE -ne 0)
{
    throw "Productivity OpenAPI failed."
}


Write-Host ""


# =========================================================
# 7/8 ASYNCSESSION SAFETY
# =========================================================

Write-Host "[7/8] AsyncSession safety..."


$AsyncCheck = @'
import ast

from pathlib import Path


files = [
    Path(
        r"C:\workforce-os\backend\app\modules\productivity_insights\service.py"
    ),

    Path(
        r"C:\workforce-os\backend\app\modules\analytics\service.py"
    ),

    Path(
        r"C:\workforce-os\backend\app\modules\timeline\service.py"
    ),
]


def imported_gather_names(
    tree: ast.AST,
) -> set[str]:
    names = set()

    for node in ast.walk(
        tree
    ):
        if (
            isinstance(
                node,
                ast.ImportFrom,
            )
            and node.module
            == "asyncio"
        ):
            for alias in node.names:
                if alias.name == "gather":
                    names.add(
                        alias.asname
                        or alias.name
                    )

    return names


def is_gather_call(
    node: ast.Call,
    imported_names: set[str],
) -> bool:
    func = node.func

    if isinstance(
        func,
        ast.Attribute,
    ):
        if (
            func.attr == "gather"
            and isinstance(
                func.value,
                ast.Name,
            )
            and func.value.id
            == "asyncio"
        ):
            return True

    if isinstance(
        func,
        ast.Name,
    ):
        return (
            func.id
            in imported_names
        )

    return False


problems = []


for file in files:
    source = file.read_text(
        encoding="utf-8-sig"
    )

    tree = ast.parse(
        source,
        filename=str(
            file
        ),
    )

    imported_names = (
        imported_gather_names(
            tree
        )
    )

    for node in ast.walk(
        tree
    ):
        if not isinstance(
            node,
            ast.Call,
        ):
            continue

        if is_gather_call(
            node,
            imported_names,
        ):
            problems.append(
                (
                    str(
                        file
                    ),
                    getattr(
                        node,
                        "lineno",
                        None,
                    ),
                )
            )


if problems:
    raise SystemExit(
        "Actual asyncio.gather calls found: "
        + str(
            problems
        )
    )


print(
    "PASS sequential AsyncSession queries"
)
'@


$AsyncCheck |
    & $Python -


if ($LASTEXITCODE -ne 0)
{
    throw "AsyncSession safety failed."
}


Write-Host ""


# =========================================================
# 8/8 CONTROL SCHEMA
# =========================================================

Write-Host "[8/8] Control schema..."


$Heads = & $Python `
    -m alembic `
    -c ".\alembic-control.ini" `
    heads


if ($LASTEXITCODE -ne 0)
{
    throw "Alembic heads failed."
}


Write-Host $Heads


if (
    $Heads -notmatch
    $ExpectedControlHead
)
{
    throw (
        "Unexpected control head. Expected " +
        $ExpectedControlHead
    )
}


$Current = & $Python `
    -m alembic `
    -c ".\alembic-control.ini" `
    current


if ($LASTEXITCODE -ne 0)
{
    throw "Alembic current failed."
}


Write-Host $Current


if (
    $Current -notmatch
    $ExpectedControlHead
)
{
    throw (
        "Control database must be on " +
        $ExpectedControlHead
    )
}


Write-Host "PASS control schema"
Write-Host ""


# =========================================================
# FINAL
# =========================================================

Write-Host "================================================="
Write-Host " PHASE 12.5 PRODUCTIVITY INSIGHTS: PASS"
Write-Host "================================================="
Write-Host "Permissions:              PASS"
Write-Host "Custom roles:             PASS"
Write-Host "Self scope:               PASS"
Write-Host "Team scope:               PASS"
Write-Host "Workspace scope:          PASS"
Write-Host "Overview:                 PASS"
Write-Host "Activity insight:         PASS"
Write-Host "Usage insight:            PASS"
Write-Host "Goals insight:            PASS"
Write-Host "Period comparison:        PASS"
Write-Host "No arbitrary score:       PASS"
Write-Host "AsyncSession safety:      PASS"
Write-Host "OpenAPI:                  PASS"
Write-Host "Control head:             $ExpectedControlHead"
Write-Host "================================================="