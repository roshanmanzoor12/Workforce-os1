#!/usr/bin/env python3
"""Guarded WorkforceOS Companion-only patch: remove recursive preview and
replace bulky employee-side window with a small always-visible Stop Sharing bar.
Supports known V15 and V17 Program.cs shapes; never changes consent decisions.
"""
from __future__ import annotations
import argparse
import datetime
from pathlib import Path
import shutil
import sys

REL = Path('agent/WorkforceOS.ScreenCompanion/Program.cs')
V15_WIN = '''        Width = 940;
        Height = 690;
        MinimumSize = new Size(640, 480);
        StartPosition = FormStartPosition.CenterScreen;
        FormBorderStyle = FormBorderStyle.Sizable;'''
V17_WIN = '''        // WFOS_V17_COMPACT_INDICATOR: a persistent employee-visible indicator,
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
        MaximizeBox = false;'''
V18_WIN = '''        // WFOS_V18_MINI_SHARING_OVERLAY: employee-visible status + Stop Sharing.
        // No separate desktop preview. The authorized owner uses the web viewer.
        Width = 410;
        Height = 102;
        MinimumSize = new Size(410, 102);
        MaximumSize = new Size(410, 102);
        TopMost = true;
        ShowInTaskbar = false;
        FormBorderStyle = FormBorderStyle.None;
        StartPosition = FormStartPosition.Manual;
        BackColor = Color.FromArgb(255, 246, 243);
        var work = Screen.PrimaryScreen?.WorkingArea ?? new Rectangle(0, 0, 1024, 768);
        Location = new Point(Math.Max(work.Left, work.Right - Width - 18), work.Top + 18);'''
V15_ROW = '''        controlRow.Controls.Add(_start);
        controlRow.Controls.Add(_stop);'''
V17_ROW = '''        _start.Visible = false; // Remote sharing starts only after employee authorization.
        controlRow.Controls.Add(_stop);'''
V15_PREVIEW = '''        Controls.Add(_preview);
        Controls.Add(controlRow);'''
V17_PREVIEW = '''        // The native capture continues to send frames to the authorized backend.
        // Never render the desktop inside the employee indicator (recursive mirror).
        Controls.Add(controlRow);'''
V15_CLONE = '''            var old = _preview.Image;
            _preview.Image = (Image)bitmap.Clone();
            old?.Dispose();'''
V17_CLONE = '''            // No local preview cloning: frames are only published to backend.'''
V15_STOP = '''        _stop.Enabled = false;
        var old = _preview.Image;'''
V17_STOP = '''        _stop.Enabled = false;
        // Keep the tray control available while idle; visible mini-indicator
        // is always shown while active/pending and cannot be silently dismissed.
        Hide();
        ShowInTaskbar = false;
        _allowDisplay = false;
        var old = _preview.Image;'''
V18_STOP = '''        _stop.Enabled = false;
        // Idle: large app window stays hidden; employee can reopen controls in tray.
        Hide();
        _allowDisplay = false;
        var old = _preview.Image;'''


def once(source: str, old: str, new: str, label: str) -> str:
    n = source.count(old)
    if n != 1:
        raise ValueError(f'SOURCE CONFLICT: {label}: expected 1, found {n}')
    return source.replace(old, new, 1)


def transform(s: str) -> str:
    if 'WFOS_V18_MINI_SHARING_OVERLAY' in s:
        return s
    required = ['WFOS_V9_EMPLOYEE_STOP_REVOCATION', 'PrepareIndicatorAsync',
                'IncomingRequestPipe', 'SetVisibleCore', 'OpenControls()',
                'CaptureFrame()', 'StopPreview()']
    for token in required:
        if token not in s:
            raise ValueError(f'SOURCE CONFLICT: missing V15 prerequisite {token}')
    if V17_WIN in s:
        s = once(s, V17_WIN, V18_WIN, 'V17 window')
        s = once(s, V17_ROW, '''        _start.Visible = false;
        controlRow.Controls.Add(_stop);''', 'V17 controls')
        s = once(s, V17_PREVIEW, '''        // Never create a second desktop preview in the employee UI.
        Controls.Add(controlRow);''', 'V17 preview')
        s = once(s, V17_CLONE, '''            // No employee-side image rendering: publisher handles authorized frames.''', 'V17 image clone')
        s = once(s, V17_STOP, V18_STOP, 'V17 stop visibility')
    elif V15_WIN in s:
        s = once(s, V15_WIN, V18_WIN, 'V15 window')
        s = once(s, V15_ROW, '''        _start.Visible = false;
        controlRow.Controls.Add(_stop);''', 'V15 controls')
        s = once(s, V15_PREVIEW, '''        // Never create a second desktop preview in the employee UI.
        Controls.Add(controlRow);''', 'V15 preview')
        s = once(s, V15_CLONE, '''            // No employee-side image rendering: publisher handles authorized frames.''', 'V15 image clone')
        s = once(s, V15_STOP, V18_STOP, 'V15 stop visibility')
    else:
        raise ValueError('SOURCE CONFLICT: neither known V15 nor V17 Companion window found')

    s = once(s,
        '''        ShowInTaskbar = true;
        Show();
        WindowState = FormWindowState.Normal;
        Activate();''',
        '''        ShowInTaskbar = false; // Mini indicator is not a separate taskbar app.
        WindowState = FormWindowState.Normal;
        Show();
        if (IsHandleCreated && !SetWindowDisplayAffinity(Handle, 0x00000011))
        {
            // Capture exclusion is best-effort on supported Windows builds.
            // Employee-visible indicator and Stop Sharing remain available.
            CompanionDiagnostics.Log("mini indicator frame exclusion unavailable");
        }''',
        'OpenControls mini indicator')

    s = once(s,
        '''    private bool _allowDisplay;
    protected override void SetVisibleCore''',
        '''    private bool _allowDisplay;
    // Keep the employee-visible bar unobtrusive without hiding sharing state.
    protected override bool ShowWithoutActivation => true;
    [System.Runtime.InteropServices.DllImport("user32.dll", SetLastError = true)]
    private static extern bool SetWindowDisplayAffinity(IntPtr hwnd, uint affinity);
    protected override void SetVisibleCore''',
        'Win32 display affinity')

    s = once(s,
        '''        _status.Height = 35;''',
        '''        _status.Height = 42;''',
        'status height')
    s = once(s,
        '''        _status.Font = new Font(Font.FontFamily, 11, FontStyle.Bold);''',
        '''        _status.Font = new Font(Font.FontFamily, 10, FontStyle.Bold);''',
        'status font')
    s = once(s,
        '''        _stop.Width = 180;''',
        '''        _stop.Width = 170;''',
        'stop button width')
    s = once(s,
        '''        _status.Text = "● SCREEN SHARING ACTIVE — STOP SHARING to end capture";''',
        '''        _status.Text = "● SCREEN SHARING ACTIVE - Employee can stop anytime";''',
        'active status')
    s = once(s,
        '''        _sharing = true;
        _status.Text = "● SCREEN SHARING ACTIVE - Employee can stop anytime";''',
        '''        // A previous remote session may have hidden the bar in StopPreview().
        // Reopen it only after the replacement session is ready.
        OpenControls();
        _sharing = true;
        _status.Text = "● SCREEN SHARING ACTIVE - Employee can stop anytime";''',
        'start indicator')
    s = once(s,
        '''                    if (answer == DialogResult.Yes) ShowPendingIndicator(sessionId);
                    completion.TrySetResult(answer == DialogResult.Yes ? "accept" : "decline");''',
        '''                    if (answer == DialogResult.Yes) ShowPendingIndicator(sessionId);
                    else if (!_sharing) { Hide(); _allowDisplay = false; }
                    completion.TrySetResult(answer == DialogResult.Yes ? "accept" : "decline");''',
        'declined request')
    # Distinctive source assertion used by installer and tests.
    if 'Controls.Add(_preview)' in s:
        raise ValueError('preview control remains attached to form')
    return s


def main() -> int:
    p=argparse.ArgumentParser()
    p.add_argument('--root', required=True)
    p.add_argument('--apply', action='store_true')
    args=p.parse_args()
    root=Path(args.root)
    file=root/REL
    if not file.exists(): raise ValueError(f'SOURCE MISSING: {file}')
    src=file.read_text(encoding='utf-8-sig')
    dst=transform(src)
    if src == dst:
        print('V18 ALREADY INSTALLED IN SOURCE')
        return 0
    if not args.apply:
        print('V18 PREFLIGHT PASS: safe companion-only patch; no files changed')
        return 0
    timestamp=datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    backup=root/f'WorkforceOS-v18-backup-{timestamp}'/REL
    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(file,backup)
    try:
        file.write_text(dst,encoding='utf-8')
    except BaseException:
        shutil.copy2(backup,file)
        raise
    print('V18 SOURCE PATCH APPLIED; BACKUP:',backup)
    print('No running Companion changed. Rebuild to staging and deploy safely.')
    return 0

if __name__=='__main__':
    try: sys.exit(main())
    except Exception as exc:
        print('V18 PATCH FAILED:',exc,file=sys.stderr)
        sys.exit(1)
