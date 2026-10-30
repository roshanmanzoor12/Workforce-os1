#!/usr/bin/env python3
"""Workforce OS workspace colors patch. Run with backend venv Python from project root."""
from __future__ import annotations
import pathlib, re, sys, datetime, shutil, ast
ROOT = pathlib.Path(sys.argv[1] if len(sys.argv)>1 else r'C:\workforce-os')
BASE = {
    'models':'backend/app/modules/workspaces/models.py',
    'schemas':'backend/app/modules/workspaces/schemas.py',
    'service':'backend/app/modules/workspaces/service.py',
    'types':'apps/web/types/workspace.ts',
    'api':'apps/web/services/workspaces.service.ts',
    'page':'apps/web/app/(workspace)/settings/workspace/page.tsx',
    'header':'apps/web/components/app-shell/app-header.tsx',
    'sidebar':'apps/web/components/app-shell/app-sidebar.tsx',
}
MIGRATION='backend/migrations/control/versions/ws_theme_20261021_01.py'

def replace(text, needle, replacement, label):
    n=text.count(needle)
    if n!=1: raise RuntimeError(f'{label}: expected 1 match; got {n}. Nothing written.')
    return text.replace(needle,replacement)

def modify(key, text):
    if key=='models':
        return replace(text, '''    logo_url: Mapped[str | None] = mapped_column(
        String(2048),
        nullable=True,
    )''', '''    logo_url: Mapped[str | None] = mapped_column(
        String(2048),
        nullable=True,
    )
    primary_color: Mapped[str] = mapped_column(
        String(7), nullable=False, default="#2563EB", server_default="#2563EB",
    )
    accent_color: Mapped[str] = mapped_column(
        String(7), nullable=False, default="#F59E0B", server_default="#F59E0B",
    )''', 'model workspace colors')
    if key=='schemas':
        pre, separator, post = text.partition('class WorkspaceUpdateRequest(WorkspaceSchema):')
        if not separator: raise RuntimeError('Missing update schema')
        text=replace(post,'    logo_url: str | None = Field(\n        default=None,\n        max_length=2048,\n    )\n\n    @field_validator("name")', '''    logo_url: str | None = Field(
        default=None,
        max_length=2048,
    )
    primary_color: str | None = None
    accent_color: str | None = None

    @field_validator("primary_color", "accent_color")
    @classmethod
    def validate_theme_color(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not re.fullmatch(r"#[0-9a-fA-F]{6}", value):
            raise ValueError("Theme colors must be #RRGGBB hex values.")
        return value.upper()

    @field_validator("name")''','update request color fields')
        text = pre + separator + text
        text=replace(text, '    timezone: str\n    logo_url: str | None = None\n\n    created_at:', '''    timezone: str
    logo_url: str | None = None
    primary_color: str = "#2563EB"
    accent_color: str = "#F59E0B"

    created_at:''','public response color fields')
        return text
    if key=='service':
        return replace(text, '''            await self.session.commit()

        except Exception:
            await self.session.rollback()
            raise

        return WorkspaceDetailResponse(''', '''            if request.primary_color is not None:
                workspace.primary_color = request.primary_color
            if request.accent_color is not None:
                workspace.accent_color = request.accent_color
            await self.session.commit()

        except Exception:
            await self.session.rollback()
            raise

        return WorkspaceDetailResponse(''', 'workspace update transaction colors')
    if key=='types':
        return replace(text, '''  logo_url:
    string | null;

  created_at:''', '''  logo_url:
    string | null;
  primary_color: string;
  accent_color: string;

  created_at:''','workspace TS response colors')
    if key=='api':
        return replace(text, '''      logo_url?: string | null;
    },
  ) {''', '''      logo_url?: string | null;
      primary_color?: string;
      accent_color?: string;
    },
  ) {''','workspace service update types')
    if key=='page':
        text=replace(text, '  const [logoUrl, setLogoUrl] = useState("");', '''  const [logoUrl, setLogoUrl] = useState("");
  const [primaryColor, setPrimaryColor] = useState("#2563EB");
  const [accentColor, setAccentColor] = useState("#F59E0B");''', 'page color states')
        text=replace(text, '    setLogoUrl(workspace?.logo_url ?? "");', '''    setLogoUrl(workspace?.logo_url ?? "");
    setPrimaryColor(workspace?.primary_color ?? "#2563EB");
    setAccentColor(workspace?.accent_color ?? "#F59E0B");''','page load colors')
        text=replace(text, '  }, [workspaceId, workspace?.name, workspace?.logo_url]);', '''  }, [workspaceId, workspace?.name, workspace?.logo_url, workspace?.primary_color, workspace?.accent_color]);''','page useEffect dependencies')
        text=replace(text, '''        logo_url: nextLogo,
      });''', '''        logo_url: nextLogo,
        primary_color: primaryColor,
        accent_color: accentColor,
      });''','page save colors')
        text=replace(text, '''      <section className="rounded-xl border p-5">
        <h2 className="font-semibold">Company theme colors</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          Workspace-wide theme colors are not available in the current backend schema. They require dedicated persisted color fields and an authorized update API. Your personal appearance settings remain separate.
        </p>
      </section>''', '''      <section className="rounded-xl border p-5 space-y-4">
        <h2 className="font-semibold">Company theme colors</h2>
        <p className="text-sm text-muted-foreground">
          These colors belong to this workspace, not your personal profile. Save the form above to apply changes.
        </p>
        <div className="grid gap-4 sm:grid-cols-2">
          <label className="flex items-center justify-between gap-3 rounded-lg border p-3">
            <span className="text-sm">Primary color</span>
            <input aria-label="Primary color" type="color" value={primaryColor}
              disabled={!canEdit || saving} onChange={(event) => setPrimaryColor(event.target.value)} />
          </label>
          <label className="flex items-center justify-between gap-3 rounded-lg border p-3">
            <span className="text-sm">Accent color</span>
            <input aria-label="Accent color" type="color" value={accentColor}
              disabled={!canEdit || saving} onChange={(event) => setAccentColor(event.target.value)} />
          </label>
        </div>
        <div className="flex overflow-hidden rounded-lg border" aria-label="Workspace color preview">
          <span className="flex-1 p-4 text-center text-sm font-medium text-white" style={{ backgroundColor: primaryColor }}>Primary</span>
          <span className="flex-1 p-4 text-center text-sm font-medium text-black" style={{ backgroundColor: accentColor }}>Accent</span>
        </div>
      </section>''', 'appearance page theme section')
        return text
    if key=='header':
        return replace(text, '''        borderBottom: "1px solid var(--color-border)",''', '''        borderBottom: `2px solid ${mode === "workspace" ? (workspace?.primary_color ?? "#2563EB") : "var(--color-border)"}`,''', 'header workspace theme line')
    if key=='sidebar':
        return replace(text, '''          <span
            className={styles.workspaceMark}
          >''', '''          <span
            className={styles.workspaceMark}
            style={{ backgroundColor: workspace?.primary_color ?? "#2563EB", color: "#FFFFFF" }}
          >''','sidebar workspace picker theme') if False else text
    raise RuntimeError(key)

MIGRATION_CODE='''"""Persist independent workspace theme colors.

Revision ID: ws_theme_20261021_01
Revises: ws_type_20261020_01
"""
from alembic import op
import sqlalchemy as sa

revision = "ws_theme_20261021_01"
down_revision = "ws_type_20261020_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("workspaces", sa.Column("primary_color", sa.String(7), nullable=False, server_default="#2563EB"))
    op.add_column("workspaces", sa.Column("accent_color", sa.String(7), nullable=False, server_default="#F59E0B"))
    op.create_check_constraint("ck_workspaces_primary_color_format", "workspaces", "primary_color ~ '^#[0-9A-Fa-f]{6}$'")
    op.create_check_constraint("ck_workspaces_accent_color_format", "workspaces", "accent_color ~ '^#[0-9A-Fa-f]{6}$'")


def downgrade() -> None:
    op.drop_constraint("ck_workspaces_accent_color_format", "workspaces", type_="check")
    op.drop_constraint("ck_workspaces_primary_color_format", "workspaces", type_="check")
    op.drop_column("workspaces", "accent_color")
    op.drop_column("workspaces", "primary_color")
'''

def main():
    changes={}
    for key,rel in BASE.items():
        if key=='sidebar':continue
        path=ROOT/rel
        if not path.is_file():raise RuntimeError(f'Missing {path}; nothing written')
        original=path.read_text(encoding='utf-8')
        updated=modify(key,original)
        if updated==original:raise RuntimeError(f'No change in {rel}')
        changes[path]=(original,updated)
    mig=ROOT/MIGRATION
    if mig.exists():raise RuntimeError(f'Migration already exists: {mig}; nothing written')
    ast.parse(changes[ROOT/BASE['models']][1]);ast.parse(changes[ROOT/BASE['schemas']][1]);ast.parse(changes[ROOT/BASE['service']][1]);ast.parse(MIGRATION_CODE)
    backup=ROOT/'backups'/('workspace-theme-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S'))
    for path,(before,after) in changes.items():
        dest=backup/path.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,dest)
    written=[]
    try:
        for path,(before,after) in changes.items():
            path.write_text(after,encoding='utf-8');written.append(path)
        mig.parent.mkdir(parents=True,exist_ok=True);mig.write_text(MIGRATION_CODE,encoding='utf-8')
    except Exception:
        for path in written:shutil.copy2(backup/path.relative_to(ROOT),path)
        raise
    print('APPLIED',len(changes),'source files and one migration. Backup:',backup)
    print('NEXT: verify Alembic head before migration, then run upgrade and tsc.')
if __name__=='__main__':main()
