# Milestone 3C — local end-to-end test launcher

This package does **not** implement WorkforceOS production auth, automatic employee selection or silent capture. It automates the existing Milestone 3B *same-Windows-PC development demo*: separate sender/viewer credentials, relay environment, interactive companion launch, Next.js env config, and relay health inspection.

## Install

Use the usual Expand-Archive command and run INSTALL.ps1. Then in PowerShell:

```powershell
$Tools = 'C:\workforce-os\tools\live-screen-dev'
powershell -NoProfile -ExecutionPolicy Bypass -File "$Tools\Setup.ps1"
```

Run these in separate PowerShell windows:

1. Relay: `powershell -NoProfile -ExecutionPolicy Bypass -File C:\workforce-os\tools\live-screen-dev\Start-Relay.ps1`
2. Companion: `powershell -NoProfile -ExecutionPolicy Bypass -File C:\workforce-os\tools\live-screen-dev\Start-Companion.ps1`
3. Viewer config: `powershell -NoProfile -ExecutionPolicy Bypass -File C:\workforce-os\tools\live-screen-dev\Configure-Viewer.ps1`

Then restart Next.js dev server, paste the two sessionStorage commands printed by Configure-Viewer.ps1 into the trusted owner's browser devtools console on `/monitoring/live-screen`, and use **Start local preview / remote sharing confirmation** in the employee companion. Verify with `Check.ps1`. Stop Sharing terminates sender.

**Privacy/security:** the employee must explicitly authorize each remote-sharing session; active indicator and Stop Sharing remain visible. All tokens are for localhost dev only. DPAPI CLIXML is protected for current Windows user, but console/sessionStorage expose viewer credential; never use on production/public networks. Avoid running Setup under administrator's different identity if user sessions differ. This is not multi-PC streaming and not a final production fix.

## Known limitations

The relay runs as a separate development server (not FastAPI auth integration), and the viewer uses JPEG `<img>` frames instead of WebRTC `<video>`. It cannot enforce WorkforceOS organization RBAC, user login events, or persistent workplace consent. Browser and companion must both run on this PC. Do not expose port 8769 externally.
