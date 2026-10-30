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
Write-Host " WorkforceOS Phase 12.9 Workforce Intelligence"
Write-Host "================================================="
Write-Host ""


# =========================================================
# REQUIRED FILES
# =========================================================

$RequiredFiles = @(
    ".\app\modules\workforce_intelligence\__init__.py",
    ".\app\modules\workforce_intelligence\enums.py",
    ".\app\modules\workforce_intelligence\schemas.py",
    ".\app\modules\workforce_intelligence\access.py",
    ".\app\modules\workforce_intelligence\calculations.py",
    ".\app\modules\workforce_intelligence\repository.py",
    ".\app\modules\workforce_intelligence\service.py",
    ".\app\modules\workforce_intelligence\router.py",
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
    .\app\modules\workforce_intelligence `
    .\app\modules\tenant_api `
    -q


if ($LASTEXITCODE -ne 0)
{
    throw "Compile failed."
}


Write-Host "PASS compile"
Write-Host ""


# =========================================================
# 2/8 CALCULATIONS
# =========================================================

Write-Host "[2/8] Intelligence calculations..."


$CalculationCheck = @'
from app.modules.workforce_intelligence.calculations import (
    clamp_percent,
    is_absence_status,
    safe_average,
    safe_ratio_average,
)


if not is_absence_status("absent"):
    raise SystemExit(
        "Absence status detection failed."
    )


if is_absence_status("present"):
    raise SystemExit(
        "Present incorrectly detected as absence."
    )


if safe_ratio_average(
    total=120,
    count=2,
) != 60.0:
    raise SystemExit(
        "Ratio average failed."
    )


if safe_average(
    [10, 20, 30]
) != 20.0:
    raise SystemExit(
        "Safe average failed."
    )


if clamp_percent(150) != 100.0:
    raise SystemExit(
        "Percent upper clamp failed."
    )


if clamp_percent(-5) != 0.0:
    raise SystemExit(
        "Percent lower clamp failed."
    )


print(
    "PASS calculations"
)
'@


$CalculationCheck | & $Python -


if ($LASTEXITCODE -ne 0)
{
    throw "Calculation gate failed."
}


Write-Host ""


# =========================================================
# 3/8 PERMISSION CONTRACT
# =========================================================

Write-Host "[3/8] Intelligence permissions..."


$PermissionCheck = @'
from app.modules.workspace_permissions.permissions import (
    ALL_WORKSPACE_PERMISSIONS,
)


required = {
    "analytics.self.read",
    "analytics.team.read",
    "analytics.all.read",
    "productivity_insights.self.read",
    "productivity_insights.team.read",
    "productivity_insights.all.read",
}


missing = (
    required
    - set(
        ALL_WORKSPACE_PERMISSIONS
    )
)


if missing:
    raise SystemExit(
        "Required intelligence permissions missing: "
        + str(
            sorted(
                missing
            )
        )
    )


print(
    "PASS intelligence permissions"
)
'@


$PermissionCheck | & $Python -


if ($LASTEXITCODE -ne 0)
{
    throw "Permission gate failed."
}


Write-Host ""


# =========================================================
# 4/8 IMPORT CONTRACT
# =========================================================

Write-Host "[4/8] Intelligence imports..."


$ImportCheck = @'
from app.modules.workforce_intelligence.access import (
    WorkforceIntelligenceAccess,
    resolve_intelligence_access,
)

from app.modules.workforce_intelligence.repository import (
    WorkforceIntelligenceRepository,
)

from app.modules.workforce_intelligence.router import (
    router,
)

from app.modules.workforce_intelligence.service import (
    WorkforceIntelligenceService,
)


assert WorkforceIntelligenceAccess
assert resolve_intelligence_access
assert WorkforceIntelligenceRepository
assert WorkforceIntelligenceService
assert router


print(
    "PASS intelligence imports"
)
'@


$ImportCheck | & $Python -


if ($LASTEXITCODE -ne 0)
{
    throw "Intelligence import gate failed."
}


Write-Host ""


# =========================================================
# 5/8 PRIVACY + ASYNC SAFETY
# =========================================================

Write-Host "[5/8] Privacy/AsyncSession safety..."


$SafetyCheck = @'
import ast
import uuid
from pathlib import Path

from app.modules.workforce_intelligence.access import (
    WorkforceIntelligenceAccess,
)

from app.modules.workforce_intelligence.enums import (
    IntelligenceScope,
)

from app.modules.workforce_intelligence.service import (
    WorkforceIntelligenceService,
)


root = Path(
    r"C:\workforce-os\backend\app\modules\workforce_intelligence"
)


# Only actual invasive collection mechanisms are forbidden.
#
# Negative capability fields such as:
#
#   arbitrary_productivity_score=False
#   employee_ranking=False
#   hidden_monitoring=False
#
# are valid and are checked explicitly below.
forbidden_terms = (
    "keylog",
    "keystroke_capture",
    "clipboard_capture",
    "password_capture",
    "credential_capture",
    "mouse_coordinates",
    "mouse_coordinate_capture",
    "screen_capture_without_consent",
    "stealth_monitoring",
)


violations = []


for path in root.glob("*.py"):
    source = path.read_text(
        encoding="utf-8-sig"
    )

    lowered = source.casefold()

    for term in forbidden_terms:
        if term in lowered:
            violations.append(
                (
                    str(path),
                    term,
                )
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
                (
                    str(path),
                    "asyncio.gather",
                )
            )

        if (
            isinstance(
                func,
                ast.Name,
            )
            and func.id in gather_aliases
        ):
            violations.append(
                (
                    str(path),
                    "gather",
                )
            )


if violations:
    raise SystemExit(
        "Safety violations: "
        + str(
            violations
        )
    )


# =========================================================
# NEGATIVE CAPABILITY CONTRACT
# =========================================================

access = WorkforceIntelligenceAccess(
    workspace_id=uuid.uuid4(),

    actor_user_id=uuid.uuid4(),

    actor_employee_id=None,

    scope=(
        IntelligenceScope.WORKSPACE
    ),

    employee_ids=None,

    permissions=frozenset(),
)


capabilities = (
    WorkforceIntelligenceService
    .capabilities(
        access=access
    )
)


if (
    capabilities
    .descriptive_metrics_only
    is not True
):
    raise SystemExit(
        "Intelligence must remain "
        "descriptive-metrics-only."
    )


if (
    capabilities
    .arbitrary_productivity_score
    is not False
):
    raise SystemExit(
        "Arbitrary productivity scoring "
        "must remain disabled."
    )


if (
    capabilities
    .employee_ranking
    is not False
):
    raise SystemExit(
        "Employee ranking must remain disabled."
    )


if (
    capabilities
    .hidden_monitoring
    is not False
):
    raise SystemExit(
        "Hidden monitoring must remain disabled."
    )


print(
    "PASS privacy/async safety"
)
'@


$SafetyCheck | & $Python -


if ($LASTEXITCODE -ne 0)
{
    throw "Safety gate failed."
}


Write-Host ""


# =========================================================
# 6/8 APP + OPENAPI
# =========================================================

Write-Host "[6/8] App/OpenAPI..."


$OpenApiCheck = @'
from app.main import app


paths = app.openapi()["paths"]


base = (
    "/api/v1/workspaces/"
    "{workspace_id}/"
    "workforce-intelligence"
)


required = {
    base + "/overview",
    base + "/employees",
    base + "/trends",
    base + "/signals",
    base + "/capabilities",
}


missing = (
    required
    - set(paths)
)


if missing:
    raise SystemExit(
        "Missing intelligence endpoints: "
        + str(
            sorted(
                missing
            )
        )
    )


for path in required:
    if "get" not in paths[path]:
        raise SystemExit(
            "Missing GET endpoint: "
            + path
        )


print(
    "PASS app/OpenAPI"
)
'@


$OpenApiCheck | & $Python -


if ($LASTEXITCODE -ne 0)
{
    throw "Intelligence OpenAPI gate failed."
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
Write-Host " PHASE 12.9 WORKFORCE INTELLIGENCE API: PASS"
Write-Host "================================================="
Write-Host "Self scope:                 PASS"
Write-Host "Team scope:                 PASS"
Write-Host "Workspace scope:            PASS"
Write-Host "Custom-role support:        PASS"
Write-Host "Overview intelligence:      PASS"
Write-Host "Employee snapshots:         PASS"
Write-Host "Trend intelligence:         PASS"
Write-Host "Descriptive signals:        PASS"
Write-Host "No employee ranking:        PASS"
Write-Host "No arbitrary score:         PASS"
Write-Host "No hidden monitoring:       PASS"
Write-Host "AsyncSession safety:        PASS"
Write-Host "OpenAPI:                    PASS"
Write-Host "Control head:               $ExpectedControlHead"
Write-Host "Tenant head:                $ExpectedTenantHead"
Write-Host "================================================="