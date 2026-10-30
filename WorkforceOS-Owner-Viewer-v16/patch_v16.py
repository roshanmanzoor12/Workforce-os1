#!/usr/bin/env python3
"""Guarded owner Live Screen inline viewer patch for the V15 source baseline.

Preflight is read-only. Apply backs up both modified files before any write,
performs all transformations in memory, and refuses unknown layouts.
"""
import argparse
import datetime
import pathlib
import sys
import shutil

ROOT_DIR=pathlib.Path(__file__).resolve().parent
BACKEND='backend/app/modules/live_monitoring/router.py'
FRONTEND='apps/web/app/(workspace)/monitoring/live-screen/page.tsx'

ENDPOINT='''# V16_OWNER_INLINE_VIEWER: owner-scoped discovery of an existing, approved screen session.
# This endpoint NEVER requests or activates screen capture. It does not expose
# frames: the existing native-frame endpoint performs its own authorization.
from sqlalchemy import select as _viewer_select
from app.modules.live_monitoring.access import can_access_employee as _viewer_can_access_employee
from app.modules.live_monitoring.models import LiveScreenSession as _ViewerLiveScreenSession
from datetime import datetime as _viewer_datetime, timezone as _viewer_timezone

@router.get("/current-session")
async def current_live_screen_for_owner(
    workspace_id: uuid.UUID,
    employee_id: uuid.UUID,
    device_id: uuid.UUID,
    context: TenantContext,
):
    access = await _access(workspace_id=workspace_id, context=context)
    if not access.can_request_live_screen or not _viewer_can_access_employee(
        access=access, employee_id=employee_id,
    ):
        raise HTTPException(status_code=403, detail="Not authorized to view this employee")
    # The existing /live-sessions/{id}/native-frame route requires the requester
    # to be the same owner: we return only sessions that same owner can view.
    now = _viewer_datetime.now(_viewer_timezone.utc)
    query = (
        _viewer_select(_ViewerLiveScreenSession)
        .where(
            _ViewerLiveScreenSession.employee_id == employee_id,
            _ViewerLiveScreenSession.device_id == device_id,
            _ViewerLiveScreenSession.requested_by_user_id == access.actor_user_id,
            _ViewerLiveScreenSession.status.in_(("requested", "accepted", "active")),
            _ViewerLiveScreenSession.expires_at > now,
        )
        .order_by(_ViewerLiveScreenSession.requested_at.desc())
        .limit(1)
    )
    current = await context.tenant_session.scalar(query)
    if current is None:
        return {"session": None}
    return {"session": {
        "session_id": str(current.id),
        "employee_id": str(current.employee_id),
        "device_id": str(current.device_id),
        "status": current.status,
    }}

'''

VIEWER_EFFECT='''  // V16_OWNER_INLINE_VIEWER: selecting an employee only attaches their existing
  // owner-authorized session. Employee login / native consent creates the request.
  // This page never starts another capture or opens a separate viewer window.
  useEffect(() => {
    if (!workspaceId || !allowed || !employeeId || !desktopDeviceId) {
      setSession(null);
      setSessionStatusError("");
      return;
    }
    let disposed = false;
    let inFlight = false;
    const loadCurrent = async () => {
      if (disposed || inFlight) return;
      inFlight = true;
      try {
        const current = await api.get<CurrentOwnerSessionResponse>(
          `/workspaces/${workspaceId}/live-monitoring/current-session?employee_id=${encodeURIComponent(employeeId)}&device_id=${encodeURIComponent(desktopDeviceId)}`,
        );
        if (disposed) return;
        setSession(current.session ? {
          sessionId: current.session.session_id,
          employeeId: current.session.employee_id,
          deviceId: current.session.device_id,
          status: current.session.status,
        } : null);
        setSessionStatusError("");
      } catch (cause) {
        if (!disposed) {
          setSession(null); // never show stale frames from a different employee
          setSessionStatusError(messageFromError(cause));
        }
      } finally {
        inFlight = false;
      }
    };
    void loadCurrent();
    const timer = window.setInterval(() => void loadCurrent(), 3000);
    return () => { disposed = true; window.clearInterval(timer); };
  }, [workspaceId, allowed, employeeId, desktopDeviceId]);

'''

def one_replace(text, old, new, desc):
    count=text.count(old)
    if count != 1:
        raise RuntimeError(f'SOURCE CONFLICT: {desc}; found {count} anchors, expected 1. No changes made.')
    return text.replace(old,new,1)

def patch_backend(s):
    if 'V16_OWNER_INLINE_VIEWER' in s:
        return s
    anchor='@router.get(\n    "/live-sessions/{session_id}",'
    return one_replace(s, anchor, ENDPOINT+anchor, 'backend before parameterized session route')

def patch_frontend(s):
    if 'V16_OWNER_INLINE_VIEWER' in s:
        return s
    s=one_replace(s, '  Play,\n', '', 'unused Play icon import')
    s=one_replace(s, '''type SessionInfo = {
  sessionId: string;
  employeeId: string;
  deviceId: string;
  status: string;
};''', '''type SessionInfo = {
  sessionId: string;
  employeeId: string;
  deviceId: string;
  status: string;
};

type CurrentOwnerSessionResponse = {
  session: {
    session_id: string;
    employee_id: string;
    device_id: string;
    status: string;
  } | null;
};''', 'SessionInfo structure')
    s=one_replace(s, '  const autoRequestKeyRef = useRef<string>("");\n', '', 'old auto-request ref')
    s=one_replace(s, '  const [requesting, setRequesting] = useState(false);\n', '', 'obsolete page-local request state')
    start='  // The API reports authorization/session state, NOT actual decoded video.\n'
    end='  const sessionEnded = session !== null && [\n'
    start_idx=s.find(start)
    end_idx=s.find(end,start_idx+len(start))
    if start_idx<0 or end_idx<0 or s.count(start)!=1 or s.count(end)!=1:
        raise RuntimeError('SOURCE CONFLICT: session polling block not recognized')
    s=s[:start_idx]+VIEWER_EFFECT+s[end_idx:]
    start='  const canRequest = Boolean(\n'
    end='  async function endSession() {\n'
    start_idx=s.find(start)
    end_idx=s.find(end,start_idx+len(start))
    if start_idx<0 or end_idx<0 or s.count(start)!=1 or s.count(end)!=1:
        raise RuntimeError('SOURCE CONFLICT: manual request block not recognized')
    s=s[:start_idx]+s[end_idx:]
    s=one_replace(s, '''disabled={Boolean(session && !sessionEnded)} onChange={(e) => {
                setEmployeeId(e.target.value); setDesktopDeviceId(""); setDeviceId(""); autoRequestKeyRef.current = ""; setViewPaused(false); setSuccess("");''','''onChange={(e) => {
                setSession(null); setEmployeeId(e.target.value); setDesktopDeviceId(""); setDeviceId(""); setViewPaused(false); setSuccess("");''', 'employee picker')
    s=one_replace(s, '''disabled={!employeeId || Boolean(session && !sessionEnded)} onChange={(e) => {''', '''disabled={!employeeId} onChange={(e) => {''', 'device picker disabled')
    s=one_replace(s, '''setDeviceId(registered?.id || ""); autoRequestKeyRef.current = ""; setViewPaused(false);''','''setSession(null); setDeviceId(registered?.id || ""); setViewPaused(false);''', 'device picker selection')
    s=one_replace(s, '''            <button type="button" className="ls-request" disabled={!canRequest} onClick={() => void requestSession()}>
              <Play size={17}/>Request session
            </button>''', '''            <div className="ls-auto-status" role="status">Auto view: employee login and approval required</div>''', 'manual request button')
    s=one_replace(s, '''<p>Request an employee-approved live screen session for the selected employee.</p>''', '''<p>Select an employee. Their already-authorized active screen appears below automatically, without opening a separate owner viewer.</p>''', 'page description')
    s=one_replace(s, '''<p>Select an online enrolled Windows Agent device and request a session. The employee must approve in the Windows Screen Companion before frames can appear.</p>''', '''<p>{!selectedDesktopAgent ? "Select an employee and an assigned Windows Agent device." : session?.status === "requested" ? "Automatic request delivered. Waiting for the employee's screen-sharing decision." : session?.status === "accepted" ? "Employee approved. Waiting for backend activation and native frames." : "No active employee-approved sharing session. The employee must be logged in with their assigned Agent online; native Companion approval and the sharing indicator are required."}</p>''', 'empty viewer message')
    s=one_replace(s, '''<strong>{selectedDesktopAgent ? `Viewer Â· ${selectedDesktopAgent.device_name}` : "Select an employee to view their screen"}</strong>''', '''<strong>{selectedDesktopAgent ? `Viewer · ${selectedDesktopAgent.device_name}` : "Select an employee to view their screen"}</strong>''', 'viewer label mojibake')
    s=one_replace(s, '''{d.device_name} Â· {isDesktopOnline(d) ? "Online" : "Offline"}''', '''{d.device_name} · {isDesktopOnline(d) ? "Online" : "Offline"}''', 'device option mojibake')
    s=one_replace(s, '''<div className="ls-devicecard''', '''<div className="ls-devicecard''', 'dummy') if False else s
    s=one_replace(s, '''.ls-request{height:40px;display:inline-flex;align-items:center;justify-content:center;gap:10px;background:#101923;color:white;border:1px solid #101923;border-radius:7px;padding:0 16px;font-weight:700;white-space:nowrap;cursor:pointer}''', '''.ls-auto-status{padding:9px 12px;background:#edf8f1;color:#17683f;border:1px solid #bfe6cd;border-radius:7px;font-size:12px;max-width:220px;line-height:1.3}''', 'manual button css')
    # Do not leave stale viewer when clicking another assigned device card.
    s=one_replace(s, '''setDesktopDeviceId(agent?.id || ""); setViewPaused(false);''', '''setSession(null); setDesktopDeviceId(agent?.id || ""); setViewPaused(false);''', 'other device card')
    return s

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--root',required=True)
    p.add_argument('--apply',action='store_true')
    args=p.parse_args()
    root=pathlib.Path(args.root)
    files={BACKEND:patch_backend, FRONTEND:patch_frontend}
    transformed={}
    for rel, fn in files.items():
        path=root/rel
        if not path.is_file():
            raise RuntimeError('SOURCE MISSING: '+str(path))
        old=path.read_text(encoding='utf-8-sig')
        new=fn(old)
        if new==old:
            print('ALREADY PATCHED:',rel)
        else:
            print('SOURCE PASS:',rel)
        transformed[rel]=(path,old,new)
    # Only write after every transformation has succeeded.
    if not args.apply:
        print('V16 PREFLIGHT PASS. No source, binary or DB changes. Rerun with -Apply.')
        return
    changed=[(rel, *item) for rel,item in transformed.items() if item[1]!=item[2]]
    if not changed:
        print('V16 ALREADY APPLIED. Nothing changed.')
        return
    timestamp=datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    backup=root/f'WorkforceOS-v16-backup-{timestamp}'
    for rel,path,old,new in changed:
        backup_path=backup/rel
        backup_path.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(path,backup_path)
    for rel,path,old,new in changed:
        path.write_text(new,encoding='utf-8')
        print('UPDATED:',rel)
    print('V16 SOURCE PATCH APPLIED. Backup:', backup)
    print('Backend restart / frontend build still required. No screen capture was started.')

if __name__=='__main__':
    try: main()
    except Exception as e:
        print(e,file=sys.stderr)
        sys.exit(1)
