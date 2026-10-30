#!/usr/bin/env python3
"""Workforce OS workspace logo/colors in navigation. Run from project root with Python."""
from __future__ import annotations
import pathlib, sys, datetime, shutil

ROOT=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else r'C:\workforce-os')
SIDEBAR='apps/web/components/app-shell/app-sidebar.tsx'
SWITCHER='apps/web/components/app-shell/workspace-switcher.tsx'

def once(s, old, new, label):
    n=s.count(old)
    if n!=1: raise RuntimeError(f'{label}: expected exactly one anchor, found {n}; nothing changed.')
    return s.replace(old,new)

def patch_sidebar(s):
    s=once(s,'''        <Link
          href={
            mode === "workspace"
              ? "/dashboard"
              : "/home"
          }
          className={styles.brandLink}
        >''','''        <Link
          href={
            mode === "workspace"
              ? "/dashboard"
              : "/home"
          }
          className={styles.brandLink}
          style={mode === "workspace" ? { borderLeft: `3px solid ${workspace?.accent_color ?? "#F59E0B"}`, paddingLeft: 8 } : undefined}
        >''','sidebar company accent')
    s=once(s,'''          <span
            className={styles.brandMark}
            aria-hidden="true"
          >
            W
          </span>''','''          <span
            className={styles.brandMark}
            aria-hidden="true"
            style={mode === "workspace" ? { backgroundColor: workspace?.primary_color ?? "#2563EB", color: "#FFFFFF", overflow: "hidden" } : undefined}
          >
            {mode === "workspace" && workspace?.logo_url ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={workspace.logo_url} alt="" style={{ width: "100%", height: "100%", objectFit: "cover" }} />
            ) : mode === "workspace" ? getInitials(currentWorkspaceName) : "W"}
          </span>''','sidebar brand avatar')
    s=once(s,'''        <WorkspacePicker
          name={currentWorkspaceName}''','''        <WorkspacePicker
          name={currentWorkspaceName}
          logoUrl={workspaceRecord?.logo_url ?? null}
          primaryColor={workspaceRecord?.primary_color ?? "#2563EB"}''','sidebar picker args')
    s=once(s,'''function WorkspacePicker({
  name,
  workspaces,''','''function WorkspacePicker({
  name,
  logoUrl,
  primaryColor,
  workspaces,''','sidebar picker signature')
    s=once(s,'''  name: string;
  workspaces: Array<{''','''  name: string;
  logoUrl: string | null;
  primaryColor: string;
  workspaces: Array<{''','sidebar picker props')
    s=once(s,'''        <span
          className={styles.workspaceMark}
        >
          {getInitials(name)}
        </span>''','''        <span
          className={styles.workspaceMark}
          style={{ backgroundColor: primaryColor, color: "#FFFFFF", overflow: "hidden" }}
        >
          {logoUrl ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={logoUrl} alt="" style={{ width: "100%", height: "100%", objectFit: "cover" }} />
          ) : getInitials(name)}
        </span>''','sidebar picker logo')
    return s

def patch_switcher(s):
    s=once(s,'''        <span
          style={{
            overflow:
              "hidden",
            whiteSpace:
              "nowrap",''','''        {mode === "workspace" ? (
          <span aria-hidden="true" style={{ width: 22, height: 22, borderRadius: 6, flexShrink: 0, display: "grid", placeItems: "center", overflow: "hidden", backgroundColor: workspace?.primary_color ?? "#2563EB", color: "#fff", fontSize: 10, fontWeight: 700 }}>
            {workspace?.logo_url ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={workspace.logo_url} alt="" style={{ width: "100%", height: "100%", objectFit: "cover" }} />
            ) : workspace?.name?.trim().slice(0, 2).toUpperCase() ?? "WS"}
          </span>
        ) : null}
        <span
          style={{
            overflow:
              "hidden",
            whiteSpace:
              "nowrap",''','header switcher brand')
    s=once(s,'''          border:
            "1px solid var(--color-border)",
          borderRadius:
            8,
          background:
            "#fffefa",''','''          border: mode === "workspace" ? `1px solid ${workspace?.accent_color ?? "#F59E0B"}` : "1px solid var(--color-border)",
          borderRadius:
            8,
          background:
            "#fffefa",''','header switcher accent')
    return s

def main():
    paths={SIDEBAR:patch_sidebar, SWITCHER:patch_switcher}
    updates={}
    for relative,fn in paths.items():
        path=ROOT/relative
        if not path.is_file():raise RuntimeError(f'Missing {path}; nothing changed')
        source=path.read_text(encoding='utf-8')
        updated=fn(source)
        updates[path]=updated
    backup=ROOT/'backups'/('workspace-navigation-branding-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S'))
    for path in updates:
        target=backup/path.relative_to(ROOT)
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(path,target)
    done=[]
    try:
        for path,source in updates.items():
            path.write_text(source,encoding='utf-8')
            done.append(path)
    except Exception:
        for path in done:shutil.copy2(backup/path.relative_to(ROOT),path)
        raise
    print('WORKSPACE NAVIGATION BRANDING APPLIED')
    print('Updated:')
    for path in updates:print(' ',path)
    print('Backup:',backup)
    print('Run: pnpm --dir apps/web exec tsc --noEmit')

if __name__=='__main__':main()
