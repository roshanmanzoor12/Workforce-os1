# WorkforceOS native backend gateway activation (PARTIAL)

Contents: code for two FastAPI endpoints, isolated relay and 2 gateway unit tests. Existing installed V2 viewer can read JPEG frames from owner endpoint if session is active and a native agent actually publishes them.

**NOT full live streaming**: The current Windows service does not securely deliver requests to the interactive Screen Companion. The Companion does not publish to the authenticated HTTP native-frame endpoint and has no native session approval integration. Never claim or toggle capability to true yet.

1. Verify against current source and backup changes: `powershell -NoProfile -ExecutionPolicy Bypass -File .\source\Apply.ps1`
2. Examine router diff before applying. The installer appends routes and overwrites the standalone gateway/core files. Ensure service downtime/maintenance and one worker for development.
3. If you explicitly want to enable backend routes in DEVELOPMENT only, run `.\source\Apply.ps1 -Apply`; restart backend with normal deployment process.
4. Validate: `python -m unittest discover -s .\source\tests -v`
5. Rollback source changes with `.\source\Apply.ps1 -Rollback`, then restart backend.

Security notes: Do not activate backend gateway on production yet; it is in-memory and single-worker. Existing screen capture and device credentials are unchanged by this installer.
