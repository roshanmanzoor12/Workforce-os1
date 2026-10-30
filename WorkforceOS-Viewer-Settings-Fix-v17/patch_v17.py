#!/usr/bin/env python3
"""WorkforceOS V17: fix inline owner-session SQL sort, consolidate saved-approval
control inside existing Monitoring settings, and replace recursive native preview
with an employee-visible compact indicator and Stop Sharing control.

Performs all edits in memory before touching disk. Idempotent, backup-first,
strictly rejects source layouts not checked by the script.
"""
from __future__ import annotations
import argparse
import datetime
import pathlib
import re
import shutil
import sys

BACKEND = 'backend/app/modules/live_monitoring/router.py'
VIEWER = 'apps/web/app/(workspace)/monitoring/live-screen/page.tsx'
AUTO = 'apps/web/components/monitoring/live-screen-auto-flow.tsx'
MODAL = 'apps/web/components/monitoring/monitoring-consent-gate.tsx'
SETTING = 'apps/web/components/monitoring/saved-screen-sharing-setting.tsx'
COMPANION = 'agent/WorkforceOS.ScreenCompanion/Program.cs'

HEARTBEAT = '''"use client";

import { useEffect } from "react";
import { useWorkspace } from "@/contexts/workspace-context";
import { getAuthSession } from "@/lib/auth/session";
import { api } from "@/lib/api/client";

/** Keep an authenticated browser-workspace lease alive. UI for explicit future
 * screen-sharing approval lives inside Employee monitoring settings, not a
 * floating card. Browser refresh does not revoke; logout uses backend stop.
 */
export function LiveScreenAutoFlow() {
  const { workspaceId, mode, user } = useWorkspace();
  useEffect(() => {
    if (!workspaceId || !user || mode !== "workspace") return;
    let disposed = false;
    const ping = async () => {
      if (disposed || !getAuthSession()) return;
      try {
        await api.post(`/workspaces/${workspaceId}/live-monitoring/auto-flow/ping`, {});
      } catch {
        // Ping failures must not automatically create duplicate capture requests.
      }
    };
    void ping();
    const interval = window.setInterval(() => void ping(), 25000);
    return () => { disposed = true; window.clearInterval(interval); };
  }, [workspaceId, mode, user?.id]);
  return null;
}
'''

SETTING_COMPONENT = '''"use client";

import { useEffect, useState } from "react";
import { useWorkspace } from "@/contexts/workspace-context";
import { api } from "@/lib/api/client";

type SavedApproval = { granted: boolean };

/** Employee's separate, revocable consent for *future automatic approval*.
 * Generic monitoring disclosure or "Allow live-screen requests" does NOT
 * grant this permission. This control is shown within Monitoring Settings.
 */
export function SavedScreenSharingSetting() {
  const { workspaceId, user, mode } = useWorkspace();
  const [granted, setGranted] = useState<boolean | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!workspaceId || !user || mode !== "workspace") { setGranted(null); return; }
    let cancelled = false;
    setGranted(null);
    setError("");
    void api.get<SavedApproval>(`/workspaces/${workspaceId}/live-monitoring/auto-flow/saved-approval`)
      .then(v => { if (!cancelled) setGranted(Boolean(v.granted)); })
      .catch(() => { if (!cancelled) setError("Screen-sharing approval could not be loaded."); });
    return () => { cancelled = true; };
  }, [workspaceId, user?.id, mode]);

  const changeApproval = async (checked: boolean) => {
    if (!workspaceId || busy || granted === null) return;
    setBusy(true);
    setError("");
    try {
      const result = await api.request<SavedApproval>(
        `/workspaces/${workspaceId}/live-monitoring/auto-flow/saved-approval`,
        { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ granted: checked }) },
      );
      setGranted(Boolean(result.granted));
    } catch {
      setError("Unable to update approval. Please try again.");
    } finally {
      setBusy(false);
    }
  };

  if (!workspaceId || mode !== "workspace" || !user) return null;
  return (
    <div data-wfos-screen-approval="v17" style={{ marginTop: 12, paddingTop: 12, borderTop: "1px solid #e7e9ed" }}>
      <label style={{ display: "flex", alignItems: "center", gap: 10, cursor: busy ? "wait" : "pointer", fontWeight: 600, fontSize: 13 }}>
        <input
          type="checkbox"
          checked={granted === true}
          disabled={busy || granted === null}
          onChange={e => void changeApproval(e.target.checked)}
          aria-label="Automatically approve future live screen-sharing requests"
        />
        Automatically approve future screen-sharing requests
      </label>
      <p style={{ margin: "6px 0 0", fontSize: 12, lineHeight: 1.45, color: "#62718a" }}>
        Separate, optional screen-sharing consent. This approval is used only with a
        visible WorkforceOS Companion sharing indicator and Stop Sharing control.
        Turn this off any time to revoke saved approval and end associated sharing.
      </p>
      {error && <p role="alert" style={{ color: "#b42318", fontSize: 12 }}>{error}</p>}
    </div>
  );
}
'''

def replace_one(s, old, new, what):
    n = s.count(old)
    if n != 1:
        raise ValueError(f'SOURCE CONFLICT: {what}: found {n}, expected 1')
    return s.replace(old,new,1)

def backend_patch(s):
    if 'V16_OWNER_INLINE_VIEWER' not in s:
        raise ValueError('V16 current-session endpoint not installed')
    if '.order_by(_ViewerLiveScreenSession.created_at.desc()' in s:
        return s
    return replace_one(s,
        '.order_by(_ViewerLiveScreenSession.requested_at.desc())',
        '.order_by(_ViewerLiveScreenSession.created_at.desc(), _ViewerLiveScreenSession.id.desc())',
        'nonexistent requested_at field')

def viewer_patch(s):
    if 'V16_OWNER_INLINE_VIEWER' not in s:
        raise ValueError('V16 inline viewer page not installed')
    old = 'setSessionStatusError(messageFromError(cause));'
    new = 'setSessionStatusError("Unable to load this employee\\\'s Live Screen status. Please retry.");'
    # Do not expose raw internal FastAPI stack traces to the owner UI.
    if new in s: return s
    return replace_one(s,old,new,'viewer raw exception disclosure')

def auto_patch(s):
    if 'export function LiveScreenAutoFlow()' not in s or 'auto-flow' not in s or 'ping' not in s:
        raise ValueError('V15 auto-flow heartbeat component not found')
    if 'data-wfos-screen-approval' in s: raise ValueError('Unexpected approval UI in heartbeat source')
    return HEARTBEAT if s != HEARTBEAT else s

def modal_patch(s):
    if 'V17_SAVED_APPROVAL_IN_MODAL' in s: return s
    if 'Allow live-screen requests' not in s or 'Employee monitoring settings' not in s:
        raise ValueError('Monitoring settings modal string anchors missing. No files changed; current modal source required.')
    if 'SavedScreenSharingSetting' in s:
        raise ValueError('SavedScreenSharingSetting already appears in modal, inspect manually')
    if not s.lstrip().startswith('"use client"') and not s.lstrip().startswith("'use client'"):
        raise ValueError('Monitoring settings source is not a client component')
    # Place the new setting after the existing *toggle row*, not inside its
    # label or its switch. The guard rejects unrecognized JSX containers.
    label = 'Allow live-screen requests'
    at = s.index(label)
    div_matches = re.finditer(r'</?div\b[^>]*>', s, re.I)
    stack = []
    possible_rows = []
    for match in div_matches:
        tag = match.group(0)
        if tag.startswith('</'):
            if not stack:
                continue
            opened = stack.pop()
            if opened < at < match.start():
                interior = s[opened:match.end()]
                if len(interior) < 4500 and re.search(r'(type\s*=\s*["\']checkbox|role\s*=\s*["\']switch|onChange\s*=|onClick\s*=)', interior):
                    possible_rows.append((len(interior), match.end()))
        elif not tag.endswith('/>'):
            stack.append(match.start())
    if not possible_rows:
        raise ValueError('Cannot safely locate the complete monitoring-permission toggle row. No files changed.')
    _, insert_at = min(possible_rows)
    s=s[:insert_at]+'\n                    {/* V17_SAVED_APPROVAL_IN_MODAL */}\n                    <SavedScreenSharingSetting />'+s[insert_at:]
    marker = 'import { SavedScreenSharingSetting } from "@/components/monitoring/saved-screen-sharing-setting";\n'
    use_client = re.search(r'^[ \t]*["\']use client["\'];?[ \t]*$',s,re.M)
    if not use_client: raise ValueError('Cannot find client directive')
    s = s[:use_client.end()]+'\n'+marker+s[use_client.end():]
    return s

def companion_patch(s):
    if 'WFOS_V9_EMPLOYEE_STOP_REVOCATION' not in s or 'PrepareIndicatorAsync' not in s:
        raise ValueError('V15 Companion indicator/stop code required')
    if 'WFOS_V17_COMPACT_INDICATOR' in s: return s
    s=replace_one(s,
      '''        Width = 940;
        Height = 690;
        MinimumSize = new Size(640, 480);
        StartPosition = FormStartPosition.CenterScreen;
        FormBorderStyle = FormBorderStyle.Sizable;''',
      '''        // WFOS_V17_COMPACT_INDICATOR: a persistent employee-visible indicator,
        // not a recursive desktop preview or a second owner's viewer.
        Width = 520;
        Height = 140;
        MinimumSize = new Size(520, 140);
        MaximumSize = new Size(520, 140);
        TopMost = true;
        StartPosition = FormStartPosition.Manual;
        var work = Screen.PrimaryScreen?.WorkingArea ?? new Rectangle(0, 0, 1024, 768);
        Location = new Point(Math.Max(work.Left, work.Right - Width - 18), work.Top + 18);
        FormBorderStyle = FormBorderStyle.FixedDialog;
        MaximizeBox = false;''','big recursive Preview window dimensions')
    s=replace_one(s,
      '        controlRow.Controls.Add(_start);\n        controlRow.Controls.Add(_stop);',
      '''        _start.Visible = false; // Remote sharing starts only after employee authorization.
        controlRow.Controls.Add(_stop);''','local preview start control')
    s=replace_one(s,
      '''        Controls.Add(_preview);
        Controls.Add(controlRow);''',
      '''        // The native capture continues to send frames to the authorized backend.
        // Never render the desktop inside the employee indicator (recursive mirror).
        Controls.Add(controlRow);''','embedded recursive preview')
    s=replace_one(s,
      '''            var old = _preview.Image;
            _preview.Image = (Image)bitmap.Clone();
            old?.Dispose();''',
      '''            // No local preview cloning: frames are only published to backend.''','capture recursive preview')
    # Hiding when sharing ended eliminates the unnecessary persistent OFF window.
    marker='''        _stop.Enabled = false;
        var old = _preview.Image;'''
    s=replace_one(s,marker,
      '''        _stop.Enabled = false;
        // Keep the tray control available while idle; visible mini-indicator
        // is always shown while active/pending and cannot be silently dismissed.
        Hide();
        ShowInTaskbar = false;
        _allowDisplay = false;
        var old = _preview.Image;''','hide idle indicator after stop')
    # Closing the indicator counts as Stop Sharing, and the tray icon remains.
    return s

TRANSFORMS = {BACKEND:backend_patch,VIEWER:viewer_patch,AUTO:auto_patch,
              MODAL:modal_patch,COMPANION:companion_patch}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',required=True)
    parser.add_argument('--apply',action='store_true')
    args=parser.parse_args()
    root=pathlib.Path(args.root)
    originals={}
    outputs={}
    for rel,fn in TRANSFORMS.items():
        path=root/rel
        if not path.is_file(): raise ValueError(f'SOURCE MISSING: {rel}')
        old=path.read_text(encoding='utf-8-sig')
        new=fn(old)
        originals[rel]=old
        outputs[rel]=new
        print(('ALREADY PATCHED' if old==new else 'SOURCE PASS') + ': '+rel)
    if (root/SETTING).exists():
        original=(root/SETTING).read_text(encoding='utf-8-sig')
        if original!=SETTING_COMPONENT:
            raise ValueError('SOURCE CONFLICT: existing saved approval component differs')
        originals[SETTING]=original
    else:
        originals[SETTING]=None
    outputs[SETTING]=SETTING_COMPONENT
    if not args.apply:
        print('V17 PREFLIGHT PASS: no source, DB, or process changed')
        return
    changes=[rel for rel in outputs if originals[rel]!=outputs[rel]]
    if not changes:
        print('V17 ALREADY APPLIED: no changes')
        return
    ts=datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    backup=root/f'WorkforceOS-v17-backup-{ts}'
    # Backup every existing change before writing anything.
    for rel in changes:
        if originals[rel] is not None:
            dst=backup/rel
            dst.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(root/rel,dst)
    written=[]
    try:
        for rel in changes:
            dst=root/rel
            dst.parent.mkdir(parents=True,exist_ok=True)
            dst.write_text(outputs[rel],encoding='utf-8')
            written.append(rel)
            print('UPDATED:',rel)
    except BaseException:
        for rel in reversed(written):
            if originals[rel] is None: (root/rel).unlink(missing_ok=True)
            else: (root/rel).write_text(originals[rel],encoding='utf-8')
        raise
    print('V17 SOURCE PATCH APPLIED. BACKUP:',backup)
    print('Build backend/frontend/Companion and deploy safely; no running process restarted.')

if __name__ == '__main__':
    try: main()
    except Exception as exc:
        print('V17 FAILED:',exc,file=sys.stderr)
        sys.exit(1)
