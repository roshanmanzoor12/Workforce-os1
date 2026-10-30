# WorkforceOS Native Frame Upload Client (incremental implementation)

Adds a device-authenticated HTTP JPEG sender for the **existing** `/api/v1/device-agent/live-screen/{session_id}/native-frame` endpoint.

This intentionally belongs in the LocalSystem Agent, NOT the employee Screen Companion, because device secrets must never be shared with the interactive user process.

**Not an all-in-one streaming patch.** This client is not wired into the Agent host or started automatically. A secure Windows IPC protocol needs to deliver explicitly approved frames from the interactive Companion to the Agent. Native popup, session approval/activation and Stop Sharing propagation remain to be implemented and tested. Employee approval MUST be verified server-side before any frame acceptance. Gateway must be tested in single-worker development before enabling.

The method returns `false` on revoked or missing sessions and invalid frames. It does not handle retries or streaming cadence: calling code must stop capture on denial/revocation.

Apply: `powershell -NoProfile -ExecutionPolicy Bypass -File .\Apply.ps1` then `... -Apply`. From repo root run `dotnet build agent\WorkforceOS.Agent\WorkforceOS.Agent.csproj -c Release`. Revert: `... -Rollback`.

No Agent service restart/deployment is performed by this installer; existing enrollment and tracking untouched.
