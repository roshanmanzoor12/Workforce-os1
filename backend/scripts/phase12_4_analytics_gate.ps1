$ErrorActionPreference = "Stop"

$BackendRoot = "C:\workforce-os\backend"

$Python = (
    "C:\workforce-os\backend\" +
    ".venv\Scripts\python.exe"
)

$ExpectedControlHead = (
    "f1a2b3c4d5e6"
)


Set-Location $BackendRoot


Write-Host "================================================="
Write-Host " WorkforceOS Phase 12.4 Analytics Gate"
Write-Host "================================================="
Write-Host ""


# =========================================================
# REQUIRED FILES
# =========================================================

$RequiredFiles = @(
    ".\app\modules\analytics\__init__.py",
    ".\app\modules\analytics\schemas.py",
    ".\app\modules\analytics\access.py",
    ".\app\modules\analytics\repository.py",
    ".\app\modules\analytics\service.py",
    ".\app\modules\analytics\router.py",
    ".\app\modules\workspace_permissions\permissions.py",
    ".\app\modules\workspace_permissions\roles.py",
    ".\app\modules\tenant_api\router.py",
    ".\app\modules\timeline\service.py"
)


foreach ($File in $RequiredFiles)
{
    if (-not (Test-Path $File))
    {
        throw "Missing required file: $File"
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
    .\app\modules\analytics `
    .\app\modules\workspace_permissions `
    .\app\modules\tenant_api `
    .\app\modules\timeline `
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

Write-Host "[2/8] Analytics permissions..."


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
    "analytics.self.read",
    "analytics.team.read",
    "analytics.all.read",
    "analytics.export",
}


missing = (
    required
    - set(
        ALL_WORKSPACE_PERMISSIONS
    )
)


if missing:
    raise SystemExit(
        "Missing analytics permissions: "
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
        "Owner analytics permissions invalid."
    )


if not required.issubset(
    set(
        ADMIN_PERMISSIONS
    )
):
    raise SystemExit(
        "Admin analytics permissions invalid."
    )


manager_required = {
    "analytics.self.read",
    "analytics.team.read",
}


if not manager_required.issubset(
    set(
        MANAGER_PERMISSIONS
    )
):
    raise SystemExit(
        "Manager analytics permissions invalid."
    )


if (
    "analytics.self.read"
    not in MEMBER_PERMISSIONS
):
    raise SystemExit(
        "Member analytics.self.read missing."
    )


if any(
    permission.startswith(
        "analytics."
    )
    for permission
    in CLIENT_PERMISSIONS
):
    raise SystemExit(
        "Client must not receive analytics "
        "permission by default."
    )


print(
    "PASS analytics permissions"
)
'@


$PermissionCheck |
    & $Python -


if ($LASTEXITCODE -ne 0)
{
    throw "Analytics permissions failed."
}


Write-Host ""


# =========================================================
# 3/8 SOURCE MODEL CONTRACTS
# =========================================================

Write-Host "[3/8] Source model contracts..."


$ModelCheck = @'
from app.modules.activity.models import (
    ActivityStateEvent,
)

from app.modules.app_tracking.models import (
    AppUsageInterval,
)

from app.modules.attendance.models import (
    AttendanceRecord,
)

from app.modules.employees.models import (
    Employee,
)

from app.modules.goals.models import (
    Goal,
)

from app.modules.website_tracking.models import (
    WebsiteUsageInterval,
)


checks = [
    (Employee, "id"),
    (Employee, "user_id"),
    (Employee, "team_id"),
    (Employee, "is_active"),

    (ActivityStateEvent, "employee_id"),
    (ActivityStateEvent, "state"),
    (ActivityStateEvent, "idle_seconds"),
    (ActivityStateEvent, "observed_at"),

    (AttendanceRecord, "employee_id"),
    (AttendanceRecord, "attendance_date"),
    (AttendanceRecord, "status"),
    (AttendanceRecord, "worked_minutes"),
    (AttendanceRecord, "break_minutes"),

    (AppUsageInterval, "employee_id"),
    (AppUsageInterval, "process_name"),
    (AppUsageInterval, "started_at"),
    (AppUsageInterval, "duration_seconds"),

    (WebsiteUsageInterval, "employee_id"),
    (WebsiteUsageInterval, "normalized_domain"),
    (WebsiteUsageInterval, "started_at"),
    (WebsiteUsageInterval, "duration_seconds"),

    (Goal, "owner_employee_id"),
    (Goal, "status"),
    (Goal, "progress_percent"),
    (Goal, "created_at"),
]


for model, field in checks:
    if not hasattr(
        model,
        field,
    ):
        raise SystemExit(
            f"{model.__name__}.{field} missing"
        )


print(
    "PASS source model contracts"
)
'@


$ModelCheck |
    & $Python -


if ($LASTEXITCODE -ne 0)
{
    throw "Source model contract gate failed."
}


Write-Host ""


# =========================================================
# 4/8 ANALYTICS IMPORT
# =========================================================

Write-Host "[4/8] Analytics imports..."


$ImportCheck = @'
from app.modules.analytics.access import (
    AnalyticsAccess,
    AnalyticsScope,
)

from app.modules.analytics.repository import (
    AnalyticsRepository,
)

from app.modules.analytics.router import (
    router,
)

from app.modules.analytics.service import (
    AnalyticsService,
)


assert AnalyticsAccess
assert AnalyticsScope
assert AnalyticsRepository
assert AnalyticsService
assert router


print(
    "PASS analytics imports"
)
'@


$ImportCheck |
    & $Python -


if ($LASTEXITCODE -ne 0)
{
    throw "Analytics import failed."
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

Write-Host "[6/8] Analytics OpenAPI..."


$OpenApiCheck = @'
from app.main import app


schema = app.openapi()

paths = schema["paths"]


required = {
    "/api/v1/workspaces/{workspace_id}/analytics/overview",
    "/api/v1/workspaces/{workspace_id}/analytics/activity",
    "/api/v1/workspaces/{workspace_id}/analytics/attendance",
    "/api/v1/workspaces/{workspace_id}/analytics/productivity",
    "/api/v1/workspaces/{workspace_id}/analytics/apps",
    "/api/v1/workspaces/{workspace_id}/analytics/websites",
    "/api/v1/workspaces/{workspace_id}/analytics/goals",
    "/api/v1/workspaces/{workspace_id}/analytics/trends",
}


missing = (
    required
    - set(
        paths
    )
)


if missing:
    raise SystemExit(
        "Missing analytics routes: "
        + str(
            sorted(
                missing
            )
        )
    )


for path in required:
    if "get" not in paths[path]:
        raise SystemExit(
            "GET operation missing: "
            + path
        )


print(
    "PASS analytics OpenAPI"
)
'@


$OpenApiCheck |
    & $Python -


if ($LASTEXITCODE -ne 0)
{
    throw "Analytics OpenAPI failed."
}


Write-Host ""


# =========================================================
# 7/8 SAME SESSION SAFETY
# =========================================================

Write-Host "[7/8] AsyncSession safety..."


$AsyncCheck = @'
import ast
from pathlib import Path


files = [
    Path(
        r"C:\workforce-os\backend\app\modules\analytics\service.py"
    ),
    Path(
        r"C:\workforce-os\backend\app\modules\timeline\service.py"
    ),
]


def is_asyncio_gather_call(
    node: ast.Call,
) -> bool:
    func = node.func

    # asyncio.gather(...)
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
            and func.value.id == "asyncio"
        ):
            return True

    return False


def imported_gather_names(
    tree: ast.AST,
) -> set[str]:
    names: set[str] = set()

    for node in ast.walk(
        tree
    ):
        if not isinstance(
            node,
            ast.ImportFrom,
        ):
            continue

        if node.module != "asyncio":
            continue

        for alias in node.names:
            if alias.name != "gather":
                continue

            names.add(
                alias.asname
                or alias.name
            )

    return names


def direct_gather_call(
    node: ast.Call,
    names: set[str],
) -> bool:
    return (
        isinstance(
            node.func,
            ast.Name,
        )
        and node.func.id
        in names
    )


problems = []


for file in files:
    source = file.read_text(
        encoding="utf-8-sig"
    )

    try:
        tree = ast.parse(
            source,
            filename=str(
                file
            ),
        )

    except SyntaxError as exc:
        raise SystemExit(
            "Unable to parse "
            + str(file)
            + ": "
            + str(exc)
        ) from exc

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

        if (
            is_asyncio_gather_call(
                node
            )
            or direct_gather_call(
                node,
                imported_names,
            )
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
    formatted = [
        (
            file_name
            + ":"
            + str(
                line_number
            )
        )
        for (
            file_name,
            line_number,
        )
        in problems
    ]

    raise SystemExit(
        "Actual asyncio.gather call found: "
        + str(
            formatted
        )
    )


print(
    "PASS no executable asyncio.gather "
    "calls on shared AsyncSession services"
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
# 8/8 CONTROL MIGRATION HEAD
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
Write-Host " PHASE 12.4 ANALYTICS FOUNDATION: PASS"
Write-Host "================================================="
Write-Host "Permissions:            PASS"
Write-Host "Custom-role support:    PASS"
Write-Host "Self scope:             PASS"
Write-Host "Team scope:             PASS"
Write-Host "Workspace scope:        PASS"
Write-Host "Employees analytics:    PASS"
Write-Host "Activity analytics:     PASS"
Write-Host "Attendance analytics:   PASS"
Write-Host "Application analytics:  PASS"
Write-Host "Website analytics:      PASS"
Write-Host "Goals analytics:        PASS"
Write-Host "Timeline async fix:     PASS"
Write-Host "OpenAPI:                PASS"
Write-Host "Control head:           $ExpectedControlHead"
Write-Host "================================================="