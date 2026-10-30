WorkforceOS Browser Screen Share Shortcut

Purpose: adds a prominent link from Monitoring > Live Screen to existing browser-to-browser WebRTC screen-share route. This is NOT Windows Agent-native screen capture or production relay.

Owner: open http://localhost:3001/browser-screen-share as an authorized owner/admin, choose a linked employee, request sharing.
Employee: sign in to the same workspace from their own desktop browser, open the same route, Accept & Choose Screen in browser chooser.
Owner: view the video; both parties have Stop control.

LIMITATIONS: browser-share server currently holds rooms in RAM, suitable for local testing with a single backend process, depends on browser WebRTC connectivity, HTTPS for remote origins, TURN for challenging networks, and role permissions. Do not represent as production compliant or always-on employee monitoring.

Install:
1. Extract the ZIP into C:\workforce-os
2. powershell -NoProfile -ExecutionPolicy Bypass -File "C:\workforce-os\WorkforceOS-BrowserShare-Shortcut\Apply.ps1"
3. If DRY RUN succeeds, rerun with -Apply
4. Restart Next.js if necessary.

Rollback: copy the backed up page.tsx printed by installer to C:\workforce-os\apps\web\app\(workspace)\monitoring\live-screen\page.tsx
