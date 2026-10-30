WorkforceOS Live Screen Stage 1 - UI correctness / fail-closed behavior

Scope: ONE frontend file. Removes local development viewer token prompt from Live Screen.
Ensures no fake stream is shown when there is no production media transport.
Displays clear agent/readiness/employee authorization/session states.

NOT a completed live-screen streaming implementation. Does not alter backend, agent,
credentials, database, assignments or monitoring collection.

Installation:
1) Extract ZIP into C:\workforce-os\WorkforceOS-LiveScreen-Stage1
2) From PowerShell:
   powershell -NoProfile -ExecutionPolicy Bypass -File 'C:\workforce-os\WorkforceOS-LiveScreen-Stage1\Apply-Stage1.ps1'
3) Restart/rebuild your frontend as normally deployed.

The installer REFUSES to change a file whose SHA256 differs from the uploaded
2026-10-26 source snapshot. Backup path is printed. Restore backup page.tsx
if you need to roll back.

Unverified: Frontend typecheck/build, runtime browser behavior and end-to-end streaming.
