"""Patch only precisely verified anchors of a V8/V9/V12 current source tree.
Preflight is read-only; -Apply writes only after *all* transforms are validated.
Never uses PowerShell case-insensitive variables to pass code as file paths.
"""
from __future__ import annotations
import argparse, ast, datetime, pathlib, re, shutil, sys, tempfile

PKG = pathlib.Path(__file__).resolve().parent
BASE_FILES = PKG / 'files'
SOURCES = [
 'backend/app/main.py',
 'backend/app/modules/live_monitoring/login_lifecycle.py',
 'backend/app/modules/devices/agent_router.py',
 'agent/WorkforceOS.Agent/LiveScreen/LiveScreenInboxWorker.cs',
 'agent/WorkforceOS.Agent/LiveScreen/CompanionRequestNotifier.cs',
 'agent/WorkforceOS.ScreenCompanion/IncomingRequestPipe.cs',
 'agent/WorkforceOS.ScreenCompanion/Program.cs',
 'agent/WorkforceOS.ScreenCompanion/RemoteFramePublisher.cs',
 'apps/web/app/(workspace)/layout.tsx',
 'apps/web/services/auth.service.ts',
]
ADDED = [
 'backend/app/modules/live_monitoring/auto_flow_router.py',
 'backend/app/modules/live_monitoring/auto_lease.py',
 'apps/web/components/monitoring/live-screen-auto-flow.tsx',
 'apps/web/services/live-screen-auto-flow.service.ts',
]

class SourceConflict(RuntimeError):
    pass

def must(text, fragment, name):
    if fragment not in text: raise SourceConflict(f'{name}: expected source anchor absent; no changes made')
    return text

def once_replace(text, old, new, name):
    must(text, old, name)
    if text.count(old) != 1: raise SourceConflict(f'{name}: ambiguous source anchor')
    return text.replace(old, new, 1)

def main_patch(source):
    if 'from app.modules.live_monitoring.auto_flow_router import router as live_auto_flow_router' in source:
        return source
    source=once_replace(source, 'from app.modules.devices.agent_router import router as device_agent_router',
      'from app.modules.devices.agent_router import router as device_agent_router\nfrom app.modules.live_monitoring.auto_flow_router import router as live_auto_flow_router', 'backend main router import')
    pat='app.include_router(\n    device_agent_router,\n    prefix=settings.api_v1_prefix,\n)'
    return once_replace(source,pat,pat+'\n\napp.include_router(\n    live_auto_flow_router,\n    prefix=settings.api_v1_prefix,\n)','backend main router registration')

def login_lifecycle_patch(source):
    if 'last_ping_at)' in source: return source
    old = """(login_id, desktop_device_id, employee_id, owner_user_id, live_session_id, state)
            VALUES (:login,:device,:employee,:owner,:screen,'requested')"""
    new = """(login_id, desktop_device_id, employee_id, owner_user_id, live_session_id, state, last_ping_at)
            VALUES (:login,:device,:employee,:owner,:screen,'requested',now())"""
    return once_replace(source, old, new, 'atomic creation with browser lease')

def backend_patch(source):
    if 'WFOS_V15_NATIVE_AUTO_LEASE' in source:
        return source
    # The authentication-mapped desktop may legitimately be absent; 404, not AttributeError.
    pattern=r'\(await _desktop_id_for_authenticated_device\(session, authenticated_device\)\)\.id'
    # In case V10 is already applied, these calls may already be protected with a different lookup.
    # Leave unchanged rather than guessing how that logic works.
    must(source, 'async def native_frame_from_device(', 'native frame gateway')
    source=source.replace('from app.modules.monitoring.models import MonitoringConsent', 'from app.modules.monitoring.models import MonitoringConsent\nfrom sqlalchemy import text as _wfos_sql_text')
    start=source.index('        consent_granted = False', source.index('async def get_device_live_screen_inbox('))
    end=source.index('        return DeviceLiveInboxResponse(',start)
    source=source[:start]+'''        # A disclosure toggle is NOT a screen-sharing grant. Only this explicit,
        # separately revocable, screen-specific approval can enable auto-accept.
        monitoring_disclosure_valid = bool(await session.scalar(select(MonitoringConsent.id).where(
            MonitoringConsent.user_id == desktop.user_id,
            MonitoringConsent.granted.is_(True),
            MonitoringConsent.revoked_at.is_(None),
        )))
        consent_granted = monitoring_disclosure_valid and bool(await session.scalar(_wfos_sql_text(''' + "'''" + '''
            SELECT granted FROM live_screen_saved_approvals
            WHERE user_id=:user AND employee_id=:employee AND revoked_at IS NULL
        ''' + "'''" + '''), {'user': desktop.user_id, 'employee': desktop.employee_id}))
        from app.modules.live_monitoring.auto_lease import enforce_auto_lease
        items = [item for item in items if await enforce_auto_lease(
            session, workspace_id=authenticated_device.workspace_id, live_session_id=item.id
        )]
''' +source[end:]
    # Do not hide a nonexistent desktop behind an AttributeError.
    for name in ('decide_device_live_screen(', 'activate_device_live_screen('):
        start=source.index('async def '+name)
        stop=source.index('\n@router.',start+1) if '\n@router.' in source[start+1:] else len(source)
        piece=source[start:stop]
        original='''        item = await session.scalar(select(LiveScreenSession).where(
            LiveScreenSession.id == session_id,
            LiveScreenSession.device_id == (await _desktop_id_for_authenticated_device(session, authenticated_device)).id,
        ))'''
        replacement='''        desktop = await _desktop_id_for_authenticated_device(session, authenticated_device)
        if desktop is None:
            raise HTTPException(status_code=404, detail="Assigned desktop agent not found")
        item = await session.scalar(select(LiveScreenSession).where(
            LiveScreenSession.id == session_id,
            LiveScreenSession.device_id == desktop.id,
        ))'''
        if original in piece:
            piece=piece.replace(original,replacement,1)
        elif 'desktop is None' not in piece:
            raise SourceConflict(f'{name}: unsupported device lookup baseline')
        source=source[:start]+piece+source[stop:]
    marker='''        if item is None or item.status != "active" or item.expires_at <= now or item.accepted_at is None:
            raise _NativeHTTPException(status_code=403, detail="Active employee-approved session required")'''
    replacement='''        # WFOS_V15_NATIVE_AUTO_LEASE: employee logout/closed browser blocks uploads.
        if item is not None:
            from app.modules.live_monitoring.auto_lease import enforce_auto_lease
            valid_lease = await enforce_auto_lease(tenant,
                workspace_id=authenticated_device.workspace_id, live_session_id=session_id)
            if not valid_lease:
                raise _NativeHTTPException(status_code=410, detail="Employee work session ended")
        if item is None or item.status in ("ended", "denied", "expired"):
            raise _NativeHTTPException(status_code=410, detail="Live-screen session ended")
        if item.status != "active" or item.expires_at <= now or item.accepted_at is None:
            raise _NativeHTTPException(status_code=403, detail="Active employee-approved session required")'''
    return once_replace(source,marker,replacement,'native upload authorization')

def agent_worker_patch(source):
    if 'PrepareIndicatorAsync' in source: return source
    # Match either V8's generic consent auto-accept or V14's always-prompt branch.
    needle=re.compile(r'var decision\s*=\s*(?:inbox\.ConsentGranted\s*\?\s*"accept"\s*:\s*)?await CompanionRequestNotifier\.RequestDecisionAsync\(\s*item\.SessionId,\s*item\.ExpiresAt,\s*stoppingToken\);',re.S)
    hits=list(needle.finditer(source))
    if len(hits)!=1: raise SourceConflict('Agent inbox: decision assignment not unique (V14 conflict fixed by syntax-aware anchor)')
    new='''// Explicit saved screen-only approval must be paired with a real visible Companion indicator.
                            // Otherwise ask the employee to Accept/Decline for this request.
                            var prepared = inbox.ConsentGranted && await CompanionRequestNotifier.PrepareIndicatorAsync(
                                item.SessionId, stoppingToken);
                            var decision = prepared ? "accept" : await CompanionRequestNotifier.RequestDecisionAsync(
                                item.SessionId, item.ExpiresAt, stoppingToken);'''
    return needle.sub(lambda _:new,source,count=1)

def notifier_patch(source):
    if 'PrepareIndicatorAsync' in source: return source
    marker='    public static async Task<bool> StartCaptureAsync('
    method='''    public static async Task<bool> PrepareIndicatorAsync(Guid sessionId, CancellationToken cancellationToken)
    {
        if (sessionId == Guid.Empty) return false;
        try
        {
            using var pipe = new NamedPipeClientStream(".", PipeName, PipeDirection.InOut, PipeOptions.Asynchronous);
            using var timeout = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
            timeout.CancelAfter(TimeSpan.FromSeconds(8));
            await pipe.ConnectAsync(timeout.Token);
            await pipe.WriteAsync(Encoding.UTF8.GetBytes($"prepare|{sessionId:D}\\n"), timeout.Token);
            await pipe.FlushAsync(timeout.Token);
            using var reader = new StreamReader(pipe, Encoding.UTF8, false, 256, leaveOpen: true);
            return await reader.ReadLineAsync(timeout.Token) == "ready";
        }
        catch (Exception ex) when (ex is IOException or TimeoutException or OperationCanceledException or UnauthorizedAccessException)
        {
            return false; // fail closed; the employee popup will be used instead.
        }
    }

'''
    return once_replace(source,marker,method+marker,'Companion indicator handshake client')

def pipe_patch(source):
    if 'parts[0] == "prepare"' in source: return source
    source=once_replace(source,
      '    private readonly Func<Guid, string, string, string, CancellationToken, Task>? _start;',
      '    private readonly Func<Guid, string, string, string, CancellationToken, Task>? _start;\n    private readonly Func<Guid, Task<bool>>? _prepare;', 'pipe indicator callback')
    source=once_replace(source,
      'Func<Guid, string, string, string, CancellationToken, Task>? start = null)',
      'Func<Guid, string, string, string, CancellationToken, Task>? start = null,\n        Func<Guid, Task<bool>>? prepare = null)', 'pipe constructor args')
    source=once_replace(source,'        _start = start;','        _start = start;\n        _prepare = prepare;', 'pipe constructor assignment')
    marker='                if (parts.Length == 5 && parts[0] == "start"'
    code='''                if (parts.Length == 2 && parts[0] == "prepare" &&
                    Guid.TryParse(parts[1], out var prepareId) && prepareId != Guid.Empty && _prepare is not null)
                {
                    var ready = await _prepare(prepareId);
                    await server.WriteAsync(Encoding.UTF8.GetBytes(ready ? "ready\\n" : "unavailable\\n"), stop);
                    await server.FlushAsync(stop);
                    continue;
                }
'''
    return once_replace(source,marker,code+marker,'pipe prepare command')

def companion_patch(source):
    if 'private Task<bool> PrepareIndicatorAsync' in source:return source
    must(source,'WFOS_V9_EMPLOYEE_STOP_REVOCATION','V9 Companion Stop Sharing implementation')
    # Add a saved-approval indicator acknowledgement callback to the existing pipe.
    head=source.index('_requestPipe = new IncomingRequestPipe(')
    tail=source.index('    private void StartRemoteSession(',head)
    before=source[:head]; block=source[head:tail]; after=source[tail:]
    ix=block.rfind('        });')
    if ix<0:raise SourceConflict('Companion IncomingRequestPipe constructor closure missing')
    block=block[:ix] + block[ix:].replace('        });', '        }, id => PrepareIndicatorAsync(id));',1)
    source=before+block+after
    # Popup confirmation makes the pending employee-visible sharing indicator real.
    source=once_replace(source,
      'completion.TrySetResult(answer == DialogResult.Yes ? "accept" : "decline");',
      '''if (answer == DialogResult.Yes) ShowPendingIndicator(sessionId);
                    completion.TrySetResult(answer == DialogResult.Yes ? "accept" : "decline");''', 'employee decision indicator')
    helper='''    private void ShowPendingIndicator(Guid sessionId)
    {
        OpenControls();
        _status.Text = "SCREEN SHARING APPROVED - STARTING (Stop Sharing will be available when active)";
        _status.ForeColor = Color.DarkRed;
        _tray.Text = "WorkforceOS screen sharing approved / starting";
        CompanionDiagnostics.Log($"employee indicator ready session={sessionId:D}");
    }

    private Task<bool> PrepareIndicatorAsync(Guid sessionId)
    {
        var completion = new TaskCompletionSource<bool>(TaskCreationOptions.RunContinuationsAsynchronously);
        try
        {
            _uiContext.Post(_ =>
            {
                if (IsDisposed) { completion.TrySetResult(false); return; }
                ShowPendingIndicator(sessionId);
                completion.TrySetResult(Visible && _tray.Visible);
            }, null);
        }
        catch { completion.TrySetResult(false); }
        return completion.Task.WaitAsync(TimeSpan.FromSeconds(6));
    }

'''
    source=once_replace(source,'    private void StartRemoteSession(',helper+'    private void StartRemoteSession(','Companion indicator preparation')
    # Never revoke the SAME session merely because the Agent repeats its start command.
    source=once_replace(source,'        if (_sharing) StopPreview();\n        _publisher?.Dispose();',
      '''        if (_sharing && _remoteSessionId == sessionId)
        {
            if (_publisher?.IsRunning == true) return;
            _timer.Stop();
            _publisher?.Dispose();
            _publisher = null;
            _sharing = false;
            _remoteSessionId = Guid.Empty;
        }
        else if (_sharing) StopPreview();
        _publisher?.Dispose();''', 'Companion reconnect same session')
    source=once_replace(source,
      'new RemoteFramePublisher(apiBase, sessionId, deviceUuid, deviceSecret);',
      '''new RemoteFramePublisher(apiBase, sessionId, deviceUuid, deviceSecret,
            terminalId => _uiContext.Post(_ =>
            {
                if (!IsDisposed && _sharing && _remoteSessionId == terminalId) StopPreview();
            }, null));''', 'Companion terminal publisher callback')
    return source

def publisher_patch(source):
    if 'Action<Guid>? _onTerminal' in source:return source
    source=once_replace(source,'    private readonly Guid _sessionId;',
      '    private readonly Guid _sessionId;\n    private readonly Action<Guid>? _onTerminal;','publisher terminal callback field')
    source=once_replace(source,
      'public RemoteFramePublisher(string apiBase, Guid sessionId, string deviceUuid, string deviceSecret)',
      'public RemoteFramePublisher(string apiBase, Guid sessionId, string deviceUuid, string deviceSecret, Action<Guid>? onTerminal = null)',
      'publisher constructor')
    source=once_replace(source,'        _sessionId = sessionId;',
      '        _sessionId = sessionId;\n        _onTerminal = onTerminal;', 'publisher constructor body')
    source=once_replace(source,'    public async Task SendAsync(Image source)',
      '    public bool IsRunning => Volatile.Read(ref _stopped) == 0;\n\n    public async Task SendAsync(Image source)', 'publisher running property')
    source=once_replace(source,
      '            if ((int)response.StatusCode is 401 or 403 or 404 or 410) Stop();',
      '''            if ((int)response.StatusCode is 401 or 403 or 404 or 410)
            {
                Stop();
                _onTerminal?.Invoke(_sessionId); // notify UI to stop local capture too
            }''', 'terminal publisher response')
    return source

def frontend_layout_patch(source):
    if '<LiveScreenAutoFlow />' in source:return source
    source=once_replace(source,'import { MonitoringConsentGate } from "@/components/monitoring/monitoring-consent-gate";',
      'import { MonitoringConsentGate } from "@/components/monitoring/monitoring-consent-gate";\nimport { LiveScreenAutoFlow } from "@/components/monitoring/live-screen-auto-flow";', 'workspace layout import')
    return once_replace(source,'      <EmployeeScreenShareInbox />',
      '      <EmployeeScreenShareInbox />\n      <LiveScreenAutoFlow />', 'workspace layout mount')

def auth_service_patch(source):
    if 'endLiveScreenLoginOnLogout' in source:return source
    must(source,'async function logout()', 'frontend logout hook')
    source=once_replace(source,'import {\n  clearAuthSession,',
       'import { endLiveScreenLoginOnLogout } from "@/services/live-screen-auto-flow.service";\n\nimport {\n  clearAuthSession,', 'logout helper import')
    marker='''  try {
    return await api.post<LogoutResponse>(
      "/auth/logout",'''
    added='''  try {
    // Revoke backend auto-requested sharing BEFORE revoking the browser token.
    // If offline, the server's short lease rejects capture after its TTL.
    const workspaceId = typeof window !== "undefined"
      ? window.localStorage.getItem("workforce_current_workspace_id") : null;
    if (workspaceId) {
      try { await endLiveScreenLoginOnLogout(workspaceId); }
      catch (error) { console.warn("Live-screen logout revocation deferred to lease expiry", error); }
    }
    return await api.post<LogoutResponse>(
      "/auth/logout",'''
    source = once_replace(source,marker,added,'frontend logout revocation')
    return once_replace(source,
        '''async function logoutAll():
  Promise<LogoutAllResponse> {
  try {
    return await api.post<LogoutAllResponse>(
      "/auth/logout-all",''',
        '''async function logoutAll():
  Promise<LogoutAllResponse> {
  try {
    const workspaceId = typeof window !== "undefined"
      ? window.localStorage.getItem("workforce_current_workspace_id") : null;
    if (workspaceId) {
      try { await endLiveScreenLoginOnLogout(workspaceId); }
      catch (error) { console.warn("Live-screen logout-all revocation deferred to lease expiry", error); }
    }
    return await api.post<LogoutAllResponse>(
      "/auth/logout-all",''', 'frontend logout-all revocation')

TRANSFORMS={
 SOURCES[0]:main_patch, SOURCES[1]:login_lifecycle_patch, SOURCES[2]:backend_patch,
 SOURCES[3]:agent_worker_patch, SOURCES[4]:notifier_patch, SOURCES[5]:pipe_patch,
 SOURCES[6]:companion_patch, SOURCES[7]:publisher_patch,
 SOURCES[8]:frontend_layout_patch, SOURCES[9]:auth_service_patch,
}

def apply(root:pathlib.Path, do_apply:bool):
    changed={}
    for rel,transform in TRANSFORMS.items():
        path=root/rel
        if not path.is_file():raise SourceConflict(f'Missing source: {rel}')
        old=path.read_text(encoding='utf-8-sig')
        new=transform(old.replace('\r\n','\n'))
        changed[rel]=(old,new)
        print('PASS source anchor:',rel)
    for rel in ADDED:
        original=root/rel
        if original.exists() and original.read_bytes()!=(BASE_FILES/rel).read_bytes():
            raise SourceConflict(f'Already has different module: {rel} (review manually)')
    # V12 transaction patch is mandatory, and V9 Stop Sharing must be applied.
    service=(root/'backend/app/modules/live_monitoring/service.py').read_text(encoding='utf-8-sig')
    coordinator=(root/'backend/app/modules/live_monitoring/login_lifecycle.py').read_text(encoding='utf-8-sig')
    if 'commit: bool = True' not in service or 'commit=False' not in coordinator:
        raise SourceConflict('V12 atomic request transaction is not applied')
    if 'WFOS_V9_EMPLOYEE_STOP_REVOCATION' not in changed['backend/app/modules/devices/agent_router.py'][0]:
        raise SourceConflict('V9 backend Stop Sharing patch not found')
    # Validate generated Python prior to any writes, without importing application modules.
    for rel,(old,new) in changed.items():
        if rel.endswith('.py'):ast.parse(new,filename=rel)
    for rel in ADDED:
        if rel.endswith('.py'):ast.parse((BASE_FILES/rel).read_text(encoding='utf-8'),filename=rel)
    print('PREFLIGHT PASS — no database or running process changed')
    if not do_apply:
        print('DRY RUN ONLY. Rerun installer with -Apply after reviewing README.')
        return
    backup=root/('WorkforceOS-v15-backup-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S'))
    backup.mkdir(parents=True,exist_ok=False)
    # Capture all original source bytes BEFORE writing any modified files.
    for rel in changed:
        destination=backup/rel
        destination.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(root/rel,destination)
    written=[]
    try:
        for rel,(_,new) in changed.items():
            dst=root/rel
            # Preserve Windows newline style when source used CRLF.
            orig=dst.read_bytes()
            crlf=b'\r\n' in orig
            blob=(new.replace('\n','\r\n') if crlf else new).encode('utf-8')
            dst.write_bytes(blob)
            written.append(rel)
        for rel in ADDED:
            dst=root/rel
            dst.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(BASE_FILES/rel,dst)
        print('V15 SOURCE PATCH APPLIED. Backup:',backup)
        print('No tenant migrations or binary deployments were performed.')
    except Exception:
        for rel in written:shutil.copy2(backup/rel,root/rel)
        raise

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',default=r'C:\workforce-os')
    parser.add_argument('--apply',action='store_true')
    args=parser.parse_args()
    try:apply(pathlib.Path(args.root),args.apply)
    except Exception as exc:
        print('SOURCE CONFLICT / INSTALL STOPPED:',exc,file=sys.stderr)
        sys.exit(1)
