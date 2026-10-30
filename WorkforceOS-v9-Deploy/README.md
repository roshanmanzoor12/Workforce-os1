# V9 Companion live deployment (not full automatic workflow)

1. Confirm V9 `Install-v9.ps1 -Apply` completed and `dotnet publish` staged `artifacts/screen-companion-v9`.
2. Employee stops sharing. Pause the *verified interactive Companion supervisor* (do not stop background WorkforceOSAgent service).
3. Run `Deploy-v9-Companion.ps1` for preflight and `Deploy-v9-Companion.ps1 -Apply` after Companion no longer appears as a process.
4. Restart the existing Companion supervisor through its original command and restart backend via existing launch procedure to load changed `agent_router.py`.
5. Test explicit Stop Sharing on a fresh employee-approved live session, check backend status `ended`, and ensure Agent does not restart capture.

This does not implement login-triggered requests, work-session binding, saved screen-specific auto-approval, or logout reconciliation. Do not assume v9 solves those. If request fails while offline, server status can remain active; this requires a durable revocation mechanism in the next implementation.
