$ErrorActionPreference = "Stop"

$Backend = "C:\workforce-os\backend"

$Path = Join-Path `
    $Backend `
    "app\modules\workspaces\service.py"

if (-not (Test-Path $Path))
{
    throw "Workspace service file missing."
}

$Text = Get-Content `
    $Path `
    -Raw


# =========================================================
# IMPORT
# =========================================================

if (
    $Text -notmatch
    "app\.modules\.billing\.workspace_access"
)
{
    $Anchor = @'
from app.modules.auth.models import User
'@

    $Replacement = @'
from app.modules.auth.models import User
from app.modules.billing.exceptions import (
    WorkspaceEntitlementDeniedError,
)
from app.modules.billing.workspace_access import (
    WorkspaceEntitlementAccess,
)
'@

    if (-not $Text.Contains($Anchor))
    {
        throw "Workspace service import anchor missing."
    }

    $Text = $Text.Replace(
        $Anchor,
        $Replacement
    )

    Write-Host "PASS billing entitlement imports inserted"
}
else
{
    Write-Host "Billing entitlement imports already present"
}


# =========================================================
# CREATE WORKSPACE GUARD
# =========================================================

if (
    $Text -notmatch
    "require_workspace_creation\("
)
{
    $Anchor = @'
        slug = await self._allocate_workspace_slug(
            requested_slug=request.slug,
            workspace_name=request.name,
        )
'@

    $Replacement = @'
        entitlement_access = WorkspaceEntitlementAccess(
            self.session
        )

        try:
            await entitlement_access.require_workspace_creation(
                user_id=user.id
            )

        except WorkspaceEntitlementDeniedError as exc:
            raise ValidationError(
                str(exc)
            ) from exc

        slug = await self._allocate_workspace_slug(
            requested_slug=request.slug,
            workspace_name=request.name,
        )
'@

    if (-not $Text.Contains($Anchor))
    {
        throw (
            "Workspace create slug anchor missing. " +
            "No source changes were written."
        )
    }

    $Text = $Text.Replace(
        $Anchor,
        $Replacement
    )

    Write-Host "PASS workspace entitlement guard inserted"
}
else
{
    Write-Host "Workspace entitlement guard already present"
}


Set-Content `
    -Path $Path `
    -Value $Text `
    -Encoding UTF8

Write-Host ""
Write-Host "PASS Phase 11.5 workspace entitlement wiring"