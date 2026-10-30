# WorkforceOS Safe Fix v2 — limited backend patch

This bundle is **not a complete end-to-end implementation**. The latest provided attachment contains search matches, not full C# source code, so applying guessed fixes to Companion or agent would be unsafe.

## What it safely changes

- Control-plane device heartbeat *response* advertises 10 seconds (the Windows service must honor this on its side; not modified here).
- When an already employee-accepted live-screen session is activated, replaces the **120-second request deadline** with a **bounded 900-second active deadline**. The 120-second approval-request deadline remains unchanged. Existing consent, employee-owner authorization, visible indicator checks, and server-side frame authorization remain in place. A 900-second session will end unless the application implements an authorized renewal procedure, which is NOT provided here.
- Installer performs **all** source preflight checks before writing files, keeps a timestamped backup, and is idempotent.

## What it does not change

- Existing desktop presence bridge (your current 164-line bridge is more complete than old ZIP).
- No automatic owner request creation: trusted owner principal, device identity match, and concurrency controls are unverified.
- No automatic acceptance from generic monitoring consent: employee-specific live-screen authorization and actual visible sharing indicator are necessary.
- No 403 Companion recovery: full `RemoteFramePublisher.cs`, `NativeFrameUploadClient.cs`, and control-flow files weren't uploaded.
- No Windows service binary rebuild, 10-second agent scheduler, frontend changes, or claimed browser live-stream fix. User's latest grep shows 5-second live-screen polling and 900ms native-frame polling already exist.
- No changes to relay ticket duration or multi-worker in-memory behavior.

## Windows installation

Put ZIP into `C:\workforce-os\`, unzip into `C:\workforce-os\WorkforceOS-Safe-Fix-v2\`.

Preview without editing:

```powershell
cd C:\workforce-os
powershell -NoProfile -ExecutionPolicy Bypass -File .\WorkforceOS-Safe-Fix-v2\Install-WorkforceOS-Fix.ps1
```

Apply only after review:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\WorkforceOS-Safe-Fix-v2\Install-WorkforceOS-Fix.ps1 -Apply
```

Backup path is printed in PowerShell output. Deploy/restart backend only after testing with your application dependencies and database. Do not restart the WorkforceOSAgent Windows service as a substitute for backend deployment.

## Verification

- Confirm endpoint heartbeat returns `next_heartbeat_seconds: 10`, and *actual* Windows service sends authenticated heartbeat at this rate.
- Create a session, wait for **real employee approval + visible indicator**, activate, confirm `expires_at` is approximately 15 minutes beyond activation. Verify 120-second pending request still expires.
- Confirm owner live-frame route returns frames and session ends on employee stop/owner end/real timeout. Confirm inactive sessions cannot publish.
- The 15-minute maximum is an interim safety boundary, not continuous indefinite streaming.

## To finish the full requested flow

Provide the **full** contents of `agent/WorkforceOS.ScreenCompanion/RemoteFramePublisher.cs`, `agent/WorkforceOS.Agent/LiveScreen/NativeFrameUploadClient.cs`, `agent/WorkforceOS.Agent/LiveScreen/LiveScreenInboxClient.cs`, the device-agent native upload FastAPI route, the actual `apps/web/app/(workspace)/monitoring/live-screen/page.tsx`, and device registration identity code. A search-match listing cannot verify control flow.
