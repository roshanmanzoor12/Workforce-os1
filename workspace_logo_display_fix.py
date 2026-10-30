#!/usr/bin/env python3
"""Fix workspace-logo URLs behind Next.js /backend proxy, add clickable avatar.

Preflight all anchors, back up before writing, no database modifications.
"""
from __future__ import annotations
from pathlib import Path
from datetime import datetime
import shutil, sys

ROOT=Path(sys.argv[1] if len(sys.argv)>1 else r'C:\workforce-os')
SIDE=Path('apps/web/components/app-shell/app-sidebar.tsx')
SWITCH=Path('apps/web/components/app-shell/workspace-switcher.tsx')
PAGE=Path('apps/web/app/(workspace)/settings/workspace/page.tsx')
UPLOAD=Path('apps/web/components/workspace/workspace-logo-upload.tsx')
HELPER=Path('apps/web/lib/workspace/logo-url.ts')

def once(src, a, b, name):
    n=src.count(a)
    if n!=1: raise RuntimeError(f'{name}: expected one anchor, found {n}; nothing changed')
    return src.replace(a,b,1)

def main():
    sources={}
    for p in (SIDE,SWITCH,PAGE,UPLOAD):
        f=ROOT/p
        if not f.is_file():raise RuntimeError(f'Missing {p}; nothing changed')
        sources[p]=f.read_text(encoding='utf-8-sig')
    if (ROOT/HELPER).exists():raise RuntimeError(f'{HELPER} already exists; no changes')
    side=sources[SIDE]
    side=once(side,'import styles from "./app-sidebar.module.css";', 'import { workspaceLogoSrc } from "@/lib/workspace/logo-url";\n\nimport styles from "./app-sidebar.module.css";', 'sidebar helper import')
    side=once(side,'<img src={logoUrl} alt=""', '<img src={workspaceLogoSrc(logoUrl)} alt=""', 'sidebar logo src')
    sw=sources[SWITCH]
    sw=once(sw,'import {\n  useWorkspace,\n} from "@/contexts/workspace-context";', 'import {\n  useWorkspace,\n} from "@/contexts/workspace-context";\nimport { workspaceLogoSrc } from "@/lib/workspace/logo-url";', 'switcher helper import')
    sw=once(sw,'<img src={workspace.logo_url} alt=""', '<img src={workspaceLogoSrc(workspace.logo_url)} alt=""', 'switcher logo src')
    page=sources[PAGE]
    page=once(page,'import { WorkspaceLogoUpload } from "@/components/workspace/workspace-logo-upload";', 'import { WorkspaceLogoUpload } from "@/components/workspace/workspace-logo-upload";\nimport { workspaceLogoSrc } from "@/lib/workspace/logo-url";', 'page import')
    page=once(page,'const previewValid = /^https?:\\/\\//i.test(preview);','const previewValid = /^https?:\\/\\//i.test(preview) || preview.startsWith("/api/v1/workspaces/logos/") || preview.startsWith("/backend/workspaces/logos/");','page preview validation')
    page=once(page,'<img src={preview} alt=', '<img src={workspaceLogoSrc(preview)} alt=', 'page preview URL')
    page=once(page,'<div style={{ width: 76, height: 76, borderRadius: 15, background: primaryColor, color: "#fff", display: "grid", placeItems: "center", fontSize: 24, fontWeight: 750, overflow: "hidden", flexShrink: 0 }}>', '<label htmlFor="workspace-logo-file" title={canEdit ? "Click to upload company logo" : "Company logo"} style={{ width: 76, height: 76, borderRadius: 15, background: primaryColor, color: "#fff", display: "grid", placeItems: "center", fontSize: 24, fontWeight: 750, overflow: "hidden", flexShrink: 0, cursor: canEdit ? "pointer" : "default" }}>', 'page clickable preview open')
    page=once(page, '            ) : initialsOf(name || workspace.name)}\n          </div>', '            ) : initialsOf(name || workspace.name)}\n          </label>', 'page clickable preview close')
    page=once(page,'const url = new URL(trimmed);','if (trimmed.startsWith("/api/v1/workspaces/logos/") || trimmed.startsWith("/backend/workspaces/logos/")) return trimmed;\n    const url = new URL(trimmed);','page allow stored image path')
    upload=sources[UPLOAD]
    upload=once(upload,'<input ref={inputRef} type="file"', '<input id="workspace-logo-file" ref={inputRef} type="file"', 'upload input id')
    helper='''/** Workspace logo stored under FastAPI's /api/v1 is served through Next.js /backend rewrite. */
export function workspaceLogoSrc(value: string | null | undefined): string {
  if (!value) return "";
  if (value.startsWith("/api/v1/workspaces/logos/")) {
    return "/backend/" + value.slice("/api/v1/".length);
  }
  if (value.startsWith("/backend/workspaces/logos/")) return value;
  if (/^https?:\\/\\//i.test(value)) return value;
  return "";
}
'''
    changes={SIDE:side, SWITCH:sw, PAGE:page, UPLOAD:upload, HELPER:helper}
    backup=ROOT/'backups'/('workspace-logo-display-'+datetime.now().strftime('%Y%m%d-%H%M%S'))
    for p in sources:
        dst=backup/p;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/p,dst)
    written=[]
    try:
        for p,contents in changes.items():
            out=ROOT/p;out.parent.mkdir(parents=True,exist_ok=True)
            out.write_text(contents,encoding='utf-8')
            written.append(p)
    except Exception:
        for p in written:
            if p in sources:shutil.copy2(backup/p,ROOT/p)
            else:(ROOT/p).unlink(missing_ok=True)
        raise
    print('WORKSPACE LOGO DISPLAY FIX APPLIED')
    for p in changes:print(' ',p)
    print('BACKUP:',backup)

if __name__=='__main__':
    try:main()
    except Exception as exc:print('ERROR:',exc,file=sys.stderr);sys.exit(1)
