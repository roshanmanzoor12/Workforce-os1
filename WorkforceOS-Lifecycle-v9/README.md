# WorkforceOS V9 — Employee Stop Sharing revocation (partial lifecycle patch)

This is NOT the entire seven-step automatic-login implementation. It closes a concrete security/lifecycle defect in the current sources: pressing Stop Sharing stopped the local capture, but left the backend session `active`, allowing the Agent inbox to restart it.

Changes:
- `backend/app/modules/devices/agent_router.py`: credential-authenticated `POST /api/v1/device-agent/live-screen/{session_id}/stop`, device-bound lookup, idempotent ended state and native relay revocation.
- `agent/WorkforceOS.ScreenCompanion/Program.cs`: synchronous local capture stop, best-effort backend revocation using the current authenticated device's credentials. No secrets logged.

Limitations: network failure while stopping can leave the server session open until its normal expiry. Backend must reject uploads (already status-checked). A durable retry queue, work-session binding, auto-request trusted-owner resolution, saved screen-specific consent and logout/app-close reconciliation remain pending. Do not deploy assuming the entire automatic-login flow works.

Installation: run `Install-v9.ps1` (dry-run), then `Install-v9.ps1 -Apply`. Existing files are backed up. Restart backend and publish/deploy ScreenCompanion using your existing supervisor-safe procedure. Test explicit Stop Sharing; check session status `ended` and that frames cease. Do not restart the Agent service for this patch.
