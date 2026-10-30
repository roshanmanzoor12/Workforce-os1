WorkforceOS In-Page Browser Screen Sharing Fix

Adds an embedded WebRTC browser-share panel to /monitoring/live-screen. No separate page required. Fixes TS2322 srcObject event.streams[0] undefined by using ?? null. Existing /browser-screen-share route also remains a wrapper. This does NOT implement native Agent live screen, TURN, or production persistent signaling.

1. Extract ZIP under C:\workforce-os.
2. powershell -NoProfile -ExecutionPolicy Bypass -File C:\workforce-os\WorkforceOS-InPage-LiveScreen-Fix\Apply.ps1
3. powershell -NoProfile -ExecutionPolicy Bypass -File C:\workforce-os\WorkforceOS-InPage-LiveScreen-Fix\Apply.ps1 -Apply
4. Stop existing Next dev process using its terminal Ctrl+C. Ensure it is stopped BEFORE rebuilding. Keep Node backend processes unaffected.
5. cd C:\workforce-os\apps\web; npx tsc --noEmit --incremental false; npm run build (do not run concurrently with dev).
6. Restart frontend with existing launcher. Go to /monitoring/live-screen -> Open browser sharing here. Owner request and employee approve on that same route.
7. Rollback: powershell -NoProfile -ExecutionPolicy Bypass -File C:\workforce-os\WorkforceOS-InPage-LiveScreen-Fix\Apply.ps1 -Rollback

Known limits: WebRTC demo uses in-memory signaling, one backend worker and public STUN. Cross-network connections may need TURN. Employee screen sharing requires browser secure context.
