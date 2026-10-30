# WorkforceOS v3 targeted source patch

This archive is **NOT a complete auto-request implementation**.

Implemented: Windows ScreenCompanion `RemoteFramePublisher.SendAsync` treats only HTTP 403 with the exact backend message `Active employee-approved session required` as a pending-approval retry condition. It pauses retries for 5 seconds instead of terminating. HTTP 401, 404, 410 and unrelated 403 remain terminal; 409 backs off. Server authorization is not bypassed.

Not implemented: automatic owner request creation, trusted workspace-owner identity resolution from a device heartbeat, work-session/browser-close coordination, and indefinite lease renewal. Do not claim any of these work.

The existing Windows `LiveScreenInboxWorker` already polls every 15 seconds, and its current saved-consent branch auto-accepts generic consent; this needs screen-specific authorization and genuine indicator verification before production deployment.

Install with PowerShell (from C:\workforce-os):

```powershell
Expand-Archive .\WorkforceOS-AutoRequest-Integration-v3.zip -DestinationPath . -Force
powershell -NoProfile -ExecutionPolicy Bypass -File .\WorkforceOS-AutoRequest-Integration-v3\Install-WorkforceOS-AutoRequest-v3.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\WorkforceOS-AutoRequest-Integration-v3\Install-WorkforceOS-AutoRequest-v3.ps1 -Apply
```

After applying, rebuild `WorkforceOS.ScreenCompanion` using the repository's existing build/publish process, then restart only the interactive supervisor. This installer does **not** rebuild the binary.
