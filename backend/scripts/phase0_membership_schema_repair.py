"""Append and apply the membership repair to the control migration chain."""
from __future__ import annotations

import os
from configparser import RawConfigParser
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory


REVISION = "phase0_member_schema_01"

MIGRATION = '''"""Align membership metadata with the application model."""
from alembic import op
import sqlalchemy as sa

revision = "phase0_member_schema_01"
down_revision = "__PARENT__"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("workspace_memberships"):
        raise RuntimeError(
            "Control database membership table is missing."
        )

    columns = {
        item["name"]
        for item in inspector.get_columns("workspace_memberships")
    }

    required = {
        "role_key",
        "workspace_id",
        "user_id",
        "joined_at",
        "invited_by_user_id",
        "invited_at",
    }

    if not required.issubset(columns):
        raise RuntimeError(
            "Membership schema needs earlier migrations first."
        )

    if "source" not in columns:
        op.add_column(
            "workspace_memberships",
            sa.Column("source", sa.String(32), nullable=True),
        )

        op.execute(sa.text("""
            UPDATE workspace_memberships AS m
            SET source = CASE
                WHEN EXISTS (
                    SELECT 1
                    FROM workspaces AS w
                    WHERE w.id = m.workspace_id
                      AND w.created_by_user_id = m.user_id
                ) THEN 'CREATOR'
                WHEN m.invited_by_user_id IS NOT NULL
                  OR m.invited_at IS NOT NULL
                    THEN 'INVITATION'
                ELSE 'ADMIN'
            END
        """))

        op.alter_column(
            "workspace_memberships",
            "source",
            existing_type=sa.String(32),
            nullable=False,
        )

    if "activated_at" not in columns:
        op.add_column(
            "workspace_memberships",
            sa.Column(
                "activated_at",
                sa.DateTime(timezone=True),
                nullable=True,
            ),
        )

        op.execute(sa.text("""
            UPDATE workspace_memberships
            SET activated_at = joined_at
            WHERE joined_at IS NOT NULL
        """))


def downgrade():
    raise RuntimeError(
        "This repair preserves existing columns and is forward-only. "
        "Use a reviewed follow-up migration to reverse it."
    )
'''


def find_control_config(root: Path, control: Path) -> Config:
    matches = []

    for directory, folders, files in os.walk(root):
        folders[:] = [
            name
            for name in folders
            if name not in {
                ".venv",
                "venv",
                "node_modules",
                "repair-backups",
                ".git",
            }
        ]

        for filename in files:
            if not filename.endswith(".ini"):
                continue

            path = Path(directory) / filename
            raw = RawConfigParser()
            raw.read(path, encoding="utf-8-sig")

            for section in raw.sections():
                if not raw.has_option(section, "script_location"):
                    continue

                config = Config(
                    str(path),
                    ini_section=section,
                )

                try:
                    scripts = ScriptDirectory.from_config(config)
                except Exception:
                    continue

                if Path(scripts.dir).resolve() == control:
                    matches.append(config)

    if len(matches) != 1:
        raise RuntimeError(
            "Expected one Alembic configuration for migrations/control; "
            f"found {len(matches)}. Send the control Alembic configuration "
            "and migrations/control/env.py before applying this repair."
        )

    return matches[0]


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    os.chdir(root)

    control = (root / "migrations" / "control").resolve()

    if not (control / "versions").is_dir():
        raise RuntimeError(
            "Control migration versions directory is missing."
        )

    config = find_control_config(root, control)
    scripts = ScriptDirectory.from_config(config)
    heads = scripts.get_heads()

    if len(heads) != 1:
        raise RuntimeError(
            f"Expected one control migration head; found {heads}."
        )

    existing = next(
        (
            item
            for item in scripts.walk_revisions()
            if item.revision == REVISION
        ),
        None,
    )

    target = control / "versions" / f"{REVISION}.py"

    if existing is None:
        content = MIGRATION.replace("__PARENT__", heads[0])
        compile(content, str(target), "exec")

        with target.open(
            "x",
            encoding="utf-8",
            newline="\n",
        ) as output:
            output.write(content)

        print(f"Created migration after: {heads[0]}")

    else:
        if Path(existing.path).resolve() != target.resolve():
            raise RuntimeError(
                "Repair revision exists at an unexpected path."
            )

        if heads != [REVISION]:
            raise RuntimeError(
                "Repair has later migrations. "
                "Use the normal control migration gate."
            )

        expected_content = MIGRATION.replace(
            "__PARENT__",
            str(existing.down_revision),
        )

        if target.read_text(encoding="utf-8") != expected_content:
            raise RuntimeError(
                "Existing repair migration differs; "
                "refusing to overwrite it."
            )

        print("Reusing the existing repair migration.")

    command.upgrade(config, REVISION)
    command.current(config)

    print("PASS: control membership schema migration applied.")


if __name__ == "__main__":
    main()