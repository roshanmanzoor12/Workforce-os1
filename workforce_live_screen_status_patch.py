#!/usr/bin/env python3
"""Non-destructive patch for Workforce OS Live Screen session status UI.

Usage: python workforce_live_screen_status_patch.py C:\\workforce-os
"""
from pathlib import Path
import sys, shutil, datetime

ROOT = Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve()
PAGE = ROOT/'apps/web/app/(workspace)/monitoring/live-screen/page.tsx'
if not PAGE.is_file(): raise SystemExit(f'Missing: {PAGE}')
src=PAGE.read_text(encoding='utf-8-sig')
original=src

def change(old, new, desc):
    global src
    count=src.count(old)
    if count!=1: raise SystemExit(f'Cannot apply {desc}: expected 1 match, found {count}. No files modified.')
    src=src.replace(old,new,1)

change('  deviceId: string;\n};\n\nfunction messageFromError', '  deviceId: string;\n  status: string;\n};\n\nfunction messageFromError','session status field')
change('  const [session, setSession] =\n    useState<SessionInfo | null>(null);', '''  const [session, setSession] =
    useState<SessionInfo | null>(null);
  const [sessionStatusError, setSessionStatusError] = useState("");''','session status error')
change('    setSession(null);\n    setAllowed(false);', '    setSession(null);\n    setSessionStatusError("");\n    setAllowed(false);','workspace switch reset')
change('  const selectedEmployee = useMemo(', '''  // The API reports authorization/session state, NOT actual decoded video.
  // Avoid displaying a fake LIVE badge until a media transport is attached.
  useEffect(() => {
    if (!workspaceId || !session?.sessionId || !allowed) return;
    let cancelled = false;
    let inFlight = false;
    const poll = async () => {
      if (inFlight || cancelled) return;
      inFlight = true;
      try {
        const latest = await monitoringService.getLiveSession(workspaceId, session.sessionId);
        if (cancelled) return;
        setSessionStatusError("");
        setSession((existing) => existing?.sessionId === latest.id
          ? { ...existing, status: latest.status }
          : existing);
      } catch (cause) {
        if (!cancelled) setSessionStatusError(messageFromError(cause));
      } finally {
        inFlight = false;
      }
    };
    void poll();
    const timer = window.setInterval(() => void poll(), 5000);
    return () => { cancelled = true; window.clearInterval(timer); };
  }, [workspaceId, session?.sessionId, allowed]);

  const sessionEnded = session !== null && [
    "ended", "expired", "denied", "rejected", "cancelled", "failed",
  ].includes(session.status.toLowerCase());

  const selectedEmployee = useMemo(''','polling effect')
change('    !session,\n  );', '     (!session || sessionEnded),\n  );','request flag')
change('      setSession({\n        sessionId: response.session_id,\n        employeeId: selectedEmployee.id,\n        deviceId: selectedDevice.id,\n      });','''      setSession({
        sessionId: response.session_id,
        employeeId: selectedEmployee.id,
        deviceId: selectedDevice.id,
        status: response.status,
      });
      setSessionStatusError("");''','new request state')
change('    if (!workspaceId || !session || stopping) return;', '    if (!workspaceId || !session || stopping || sessionEnded) return;','end request guard')
change('        {success && (', '''        {sessionStatusError && (
          <div className="wls-alert" role="alert">
            <AlertCircle size={18} />
            <span>Session status could not be refreshed: {sessionStatusError}</span>
          </div>
        )}

        {success && (''','visible status error')
change('''                  disabled={Boolean(session)}
                  onChange''','''                  disabled={Boolean(session && !sessionEnded)}
                  onChange''','employee select unlock')
change('disabled={!employeeId || Boolean(session)}','disabled={!employeeId || Boolean(session && !sessionEnded)}','device select unlock')
change('''                    {session
                      ? "Session requested"
                      : "No active live video"}''','''                    {session
                      ? `Session: ${session.status} (video not connected)`
                      : "No active live video"}''','actual status display')
change('''                    {session && (
                      <button''','''                    {session && !sessionEnded && (
                      <button''','end button for active only')
change('''                      {session
                        ? "Waiting for authorized video"
                        : "No active screen stream"}''','''                      {sessionEnded
                        ? "Session ended"
                        : session
                          ? "Waiting for authorized video"
                          : "No active screen stream"}''','viewer state')
change('''                      {session
                        ? "The session request was created, but a live " +''','''                      {sessionEnded
                        ? "The backend reports that this session is no longer active. You can request a new session."
                        : session
                          ? "The session request was created, but a live " +''','viewer ended help')
change('''                      {session
                        ? "Request created"
                        : "Not connected"}''','''                      {session
                        ? `${session.status} — media disconnected`
                        : "Not connected"}''','details status')
# Keep device selection usable after a terminal backend session.
change('''disabled={Boolean(session)}
                        onClick''','''disabled={Boolean(session && !sessionEnded)}
                        onClick''','device card unlock')
if src==original: raise SystemExit('No changes generated')
backup = ROOT/'backups'/('live-screen-status-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S'))/'apps/web/app/(workspace)/monitoring/live-screen/page.tsx'
backup.parent.mkdir(parents=True, exist_ok=True)
shutil.copy2(PAGE,backup)
PAGE.write_text(src,encoding='utf-8')
print('PATCHED', PAGE)
print('BACKUP', backup)
print('NOTE: Polls session state; does not create WebRTC media or enable desktop screen capture.')
