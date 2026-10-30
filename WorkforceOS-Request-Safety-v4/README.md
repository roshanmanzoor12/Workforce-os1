# WorkforceOS v4: request idempotency foundation

This package adds **row-locked deduplication** to existing authorized owner `request_live_screen`. It does **not** connect device login/heartbeat to owner auto-request. It never fabricates employee consent or screen indicator evidence. It does not affect the deployed ScreenCompanion.

**Limitations:** The uploaded `heartbeat_router.py` authenticates the device but carries no authorized owner principal and has no verified mapping between a browser workspace-login session and device heartbeat. A trustworthy owner authorization/profile binding and session-lifecycle listener are necessary before online→auto-request can be enabled. Don't configure a hard-coded owner UUID or accept it from device payload.

Installation:
```powershell
cd C:\workforce-os
Expand-Archive .\WorkforceOS-Request-Safety-v4.zip -DestinationPath . -Force
powershell -NoProfile -ExecutionPolicy Bypass -File .\WorkforceOS-Request-Safety-v4\Install-v4.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\WorkforceOS-Request-Safety-v4\Install-v4.ps1 -Apply
python -m compileall -q .\backend\app\modules\live_monitoring
```

No database migration. Keeps manual request creation and approval. If an existing unexpired open session exists for same DesktopAgentDevice and employee, returns it rather than creating another. Concurrent requests are serialized on device row. An existing session owned by another requester blocks duplicate creation but is never returned to the caller.

**Not complete:** Online auto-request, login-close detection, 20-hour rolling session, native agent install/restart, and end-to-end testing.
