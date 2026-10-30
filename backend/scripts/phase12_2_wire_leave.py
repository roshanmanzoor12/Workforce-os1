from __future__ import annotations

from pathlib import Path


ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)


def read(
    relative: str,
) -> str:
    path = ROOT / relative

    return path.read_text(
        encoding="utf-8"
    )


def write(
    relative: str,
    content: str,
) -> None:
    path = ROOT / relative

    path.write_text(
        content,
        encoding="utf-8",
    )


def replace_once(
    content: str,
    old: str,
    new: str,
    *,
    label: str,
) -> str:
    if new in content:
        print(
            "SKIP already wired:",
            label,
        )

        return content

    if old not in content:
        raise RuntimeError(
            "Insertion point not found: "
            + label
        )

    print(
        "PATCH:",
        label,
    )

    return content.replace(
        old,
        new,
        1,
    )


# =========================================================
# PERMISSION ENUM
# =========================================================


def patch_permissions() -> None:
    relative = (
        "app/modules/"
        "workspace_permissions/"
        "permissions.py"
    )

    content = read(
        relative
    )

    if (
        "LEAVE_VIEW"
        in content
    ):
        print(
            "SKIP already wired: "
            "WorkspacePermission leave keys"
        )

        return

    class_marker = (
        "class WorkspacePermission"
    )

    class_start = content.find(
        class_marker
    )

    if class_start < 0:
        raise RuntimeError(
            "WorkspacePermission class "
            "not found."
        )

    # Insert after the existing Holidays permission family
    # when available. We locate the last HOLIDAYS_* enum
    # member instead of relying on exact formatting.
    holidays_positions = []

    search_from = class_start

    while True:
        index = content.find(
            "HOLIDAYS_",
            search_from,
        )

        if index < 0:
            break

        holidays_positions.append(
            index
        )

        search_from = (
            index
            + len("HOLIDAYS_")
        )

    if not holidays_positions:
        raise RuntimeError(
            "No HOLIDAYS_* permissions "
            "found in WorkspacePermission."
        )

    last_holiday = max(
        holidays_positions
    )

    # Find the next section divider after the last holidays
    # permission. This avoids depending on whether the enum
    # member uses one line or multiple lines.
    next_section = content.find(
        "    # ===============================",
        last_holiday,
    )

    if next_section < 0:
        # Fall back to the next obvious enum section comment.
        next_section = content.find(
            "    # ",
            last_holiday,
        )

    if next_section < 0:
        raise RuntimeError(
            "Could not locate insertion "
            "point after Holidays permissions."
        )

    leave_block = """
    # =====================================================
    # LEAVE
    # =====================================================

    LEAVE_VIEW = "leave.view"
    LEAVE_MANAGE = "leave.manage"

    LEAVE_SELF_READ = (
        "leave.self.read"
    )

    LEAVE_TEAM_READ = (
        "leave.team.read"
    )

    LEAVE_ALL_READ = (
        "leave.all.read"
    )

    LEAVE_APPROVE = (
        "leave.approve"
    )

    LEAVE_POLICY_MANAGE = (
        "leave.policy.manage"
    )

    LEAVE_BALANCE_MANAGE = (
        "leave.balance.manage"
    )

"""

    content = (
        content[:next_section]
        + leave_block
        + content[next_section:]
    )

    print(
        "PATCH: WorkspacePermission "
        "leave keys"
    )

    write(
        relative,
        content,
    )

# =========================================================
# ROLE GRANTS
# =========================================================


ADMIN_BLOCK = """
        # -------------------------------------------------
        # Phase 12.2 — Leave
        # -------------------------------------------------

        WorkspacePermission
        .LEAVE_VIEW
        .value,

        WorkspacePermission
        .LEAVE_MANAGE
        .value,

        WorkspacePermission
        .LEAVE_SELF_READ
        .value,

        WorkspacePermission
        .LEAVE_TEAM_READ
        .value,

        WorkspacePermission
        .LEAVE_ALL_READ
        .value,

        WorkspacePermission
        .LEAVE_APPROVE
        .value,

        WorkspacePermission
        .LEAVE_POLICY_MANAGE
        .value,

        WorkspacePermission
        .LEAVE_BALANCE_MANAGE
        .value,
"""


MANAGER_BLOCK = """
        # -------------------------------------------------
        # Phase 12.2 — Leave
        # -------------------------------------------------

        WorkspacePermission
        .LEAVE_VIEW
        .value,

        WorkspacePermission
        .LEAVE_SELF_READ
        .value,

        WorkspacePermission
        .LEAVE_TEAM_READ
        .value,

        WorkspacePermission
        .LEAVE_APPROVE
        .value,
"""


MEMBER_BLOCK = """
        # -------------------------------------------------
        # Phase 12.2 — Leave
        # -------------------------------------------------

        WorkspacePermission
        .LEAVE_SELF_READ
        .value,
"""


def insert_role_block(
    content: str,
    *,
    section_start: str,
    section_end: str,
    block: str,
    needle: str,
) -> str:
    start = content.find(
        section_start
    )

    end = content.find(
        section_end,
        start,
    )

    if (
        start < 0
        or end < 0
    ):
        raise RuntimeError(
            "Role section not found: "
            + section_start
        )

    section = content[
        start:end
    ]

    if needle in section:
        print(
            "SKIP already wired:",
            needle,
        )

        return content

    closing = section.rfind(
        "    }\n)"
    )

    if closing < 0:
        closing = section.rfind(
            "    }\r\n)"
        )

    if closing < 0:
        raise RuntimeError(
            "Role grant insertion point "
            "not found: "
            + section_start
        )

    absolute = (
        start
        + closing
    )

    print(
        "PATCH role:",
        section_start,
    )

    return (
        content[:absolute]
        + block
        + content[absolute:]
    )


def patch_roles() -> None:
    relative = (
        "app/modules/"
        "workspace_permissions/"
        "roles.py"
    )

    content = read(
        relative
    )

    content = insert_role_block(
        content,
        section_start=(
            "ADMIN_PERMISSIONS = "
            "frozenset"
        ),
        section_end=(
            "MANAGER_PERMISSIONS = "
            "frozenset"
        ),
        block=ADMIN_BLOCK,
        needle=".LEAVE_MANAGE",
    )

    content = insert_role_block(
        content,
        section_start=(
            "MANAGER_PERMISSIONS = "
            "frozenset"
        ),
        section_end=(
            "MEMBER_PERMISSIONS = "
            "frozenset"
        ),
        block=MANAGER_BLOCK,
        needle=".LEAVE_TEAM_READ",
    )

    content = insert_role_block(
        content,
        section_start=(
            "MEMBER_PERMISSIONS = "
            "frozenset"
        ),
        section_end=(
            "CLIENT_PERMISSIONS = "
            "frozenset"
        ),
        block=MEMBER_BLOCK,
        needle=".LEAVE_SELF_READ",
    )

    write(
        relative,
        content,
    )


# =========================================================
# TENANT API ROUTER
# =========================================================


def patch_tenant_router() -> None:
    relative = (
        "app/modules/"
        "tenant_api/router.py"
    )

    content = read(
        relative
    )

    import_marker = (
        "from app.modules.live_monitoring."
        "router import (\n"
    )

    leave_import = (
        "from app.modules.leave.router import (\n"
        "    router as leave_router,\n"
        ")\n"
        + import_marker
    )

    content = replace_once(
        content,
        import_marker,
        leave_import,
        label="Leave router import",
    )

    include_marker = (
        "router.include_router(\n"
        "    workspace_permissions_router\n"
        ")\n"
    )

    include_block = (
        include_marker
        + "\n"
        + "router.include_router(\n"
        + "    leave_router\n"
        + ")\n"
    )

    content = replace_once(
        content,
        include_marker,
        include_block,
        label="Leave router registration",
    )

    write(
        relative,
        content,
    )


# =========================================================
# ALEMBIC TENANT METADATA
# =========================================================


def patch_tenant_env() -> None:
    relative = (
        "migrations/tenant/env.py"
    )

    content = read(
        relative
    )

    marker = (
        "from app.modules.holidays import "
        "models as holiday_models"
    )

    if marker not in content:
        marker = (
            "from app.modules.holidays import ("
        )

    if (
        "app.modules.leave"
        in content
    ):
        print(
            "SKIP already wired: "
            "Leave Alembic metadata"
        )

        return

    index = content.find(
        marker
    )

    if index < 0:
        raise RuntimeError(
            "Holiday Alembic import "
            "not found."
        )

    line_end = content.find(
        "\n",
        index,
    )

    # Handle multiline import block.
    if marker.endswith(
        "import ("
    ):
        block_end = content.find(
            ")\n",
            line_end,
        )

        if block_end < 0:
            raise RuntimeError(
                "Holiday import block end "
                "not found."
            )

        line_end = block_end + 1

    insertion = (
        "\n"
        "from app.modules.leave import ("
        "  # noqa: E402,F401\n"
        "    models as leave_models,\n"
        ")\n"
    )

    content = (
        content[:line_end + 1]
        + insertion
        + content[line_end + 1:]
    )

    print(
        "PATCH: Leave Alembic metadata"
    )

    write(
        relative,
        content,
    )


# =========================================================
# SCHEMA VERSION
# =========================================================


def patch_schema_version() -> None:
    relative = (
        "app/db/"
        "tenant_initialization.py"
    )

    content = read(
        relative
    )

    old = (
        '"m3h4i5j6k7l8"'
    )

    new = (
        '"n4i5j6k7l8m9"'
    )

    if new in content:
        print(
            "SKIP already wired: "
            "tenant schema version"
        )

        return

    if old not in content:
        raise RuntimeError(
            "Expected previous tenant "
            "schema version not found."
        )

    content = content.replace(
        old,
        new,
        1,
    )

    print(
        "PATCH: tenant schema version"
    )

    write(
        relative,
        content,
    )


# =========================================================
# MAIN
# =========================================================


def main() -> None:
    patch_permissions()
    patch_roles()
    patch_tenant_router()
    patch_tenant_env()
    patch_schema_version()

    print()
    print(
        "PASS Phase 12.2 leave wiring"
    )


if __name__ == "__main__":
    main()