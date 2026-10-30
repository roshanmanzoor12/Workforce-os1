# WorkforceOS Live Screen — Milestone 2A: Employee companion sign-in launch

**Status: Windows login launch integration, NOT remote video streaming.**

This package builds the existing Milestone 1 `.NET 8` WinForms screen preview and adds current-user Windows sign-in startup via HKCU Run. It will launch in the interactive desktop session rather than Windows service Session 0. It intentionally does **not** automatically start screen capture, transmit screen pixels, modify monitoring consent, modify the owner player, or set `live_screen: true`.

It makes it easier for employees to access visible sharing controls after Windows sign-in. WorkforceOS web login and Windows login are independent; opening the WorkforceOS website does not start the companion.

## Installation

Extract the ZIP to a folder and run the `INSTALL.ps1` script **as the Windows employee account that should use the companion**, in that account's interactive PowerShell window. Do not run as a different admin account. Requires Milestone 1 installed at `C:\workforce-os\agent\WorkforceOS.ScreenCompanion` and the .NET 8 SDK.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\INSTALL.ps1
```

## Rollback

Run `ROLLBACK.ps1` under the same Windows account.

## Next engineering milestone

- Employee-controlled active session authorization bound to employee/device/workspace.
- Windows native encoded video sender, ICE/SDP signaling and authenticated viewer transport.
- Server checks workspace membership, device binding, current consent and session validity.
- Replace old browser demo iframe with direct video player in original Monitoring / Live Screen.
- Stop and revoke must cut off video server-side.

The existing local preview proves frame acquisition only. Do not claim native remote streaming works until complete Windows end-to-end verification succeeds.
