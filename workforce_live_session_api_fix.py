from pathlib import Path
import sys, shutil, datetime, re
root = Path(sys.argv[1] if len(sys.argv)>1 else r'C:\workforce-os')
relative = Path('apps/web/services/monitoring.service.ts')
file = root/relative
if not file.exists(): raise SystemExit(f'Missing: {file}')
src=file.read_text(encoding='utf-8-sig')
needle='''  requestLiveSession(workspaceId: string, deviceId: string) {
    return api.post<{ session_id: string }>(path(workspaceId, "live-sessions"), { device_id: deviceId });
  },
  stopLiveSession(workspaceId: string, sessionId: string) {
    return api.post(path(workspaceId, `live-sessions/${sessionId}/stop`));
  },'''
replacement='''  // Match the real FastAPI live_monitoring router rather than /monitoring/*.
  requestLiveSession(workspaceId: string, deviceId: string) {
    return api.post<{ id: string; device_id: string; employee_id: string; status: string }>(
      `/workspaces/${workspaceId}/live-monitoring/live-sessions`,
      { device_id: deviceId },
    ).then((result) => ({ ...result, session_id: result.id }));
  },
  getLiveSession(workspaceId: string, sessionId: string) {
    return api.get<{ id: string; device_id: string; employee_id: string; status: string; session_channel: string | null }>(
      `/workspaces/${workspaceId}/live-monitoring/live-sessions/${sessionId}`,
    );
  },
  stopLiveSession(workspaceId: string, sessionId: string) {
    return api.post(
      `/workspaces/${workspaceId}/live-monitoring/live-sessions/${sessionId}/end`,
      { reason: "Stopped by authorized viewer" },
    );
  },'''
if needle not in src:
 if 'live-monitoring/live-sessions' in src: raise SystemExit('Already patched or changed; no files modified.')
 raise SystemExit('Expected service source differs; no files modified. Export latest monitoring.service.ts.')
new=src.replace(needle,replacement)
backup=root/'backups'/('live-session-api-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S'))/relative
backup.parent.mkdir(parents=True,exist_ok=True)
shutil.copy2(file,backup)
file.write_text(new,encoding='utf-8')
print('PATCHED',file)
print('BACKUP',backup)
print('NOTE: Fixes request/status/end API contracts; does NOT implement WebRTC.')
