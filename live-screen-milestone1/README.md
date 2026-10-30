# WorkforceOS — Native Live Screen, Milestone 1

**Implemented:** Standalone employee-visible Windows Forms interactive companion. User explicitly starts a real primary-desktop capture **local preview** and sees a persistent red 'SCREEN PREVIEW ACTIVE' banner, tray state, and prominent STOP SHARING control. On close/capture exception, capture stops and cached preview frames are disposed.

**Not implemented:** Authentication, saved monitoring preference lookup, Windows Agent integration, streaming/encoding/WebRTC, FastAPI signaling, browser viewer. This package does **NOT** cause the owner's `/monitoring/live-screen` page to show video. It does not change production backend/frontend or Windows service. Do not use it as a production monitoring installer.

## Install (Windows PowerShell)
Extract the zip to any directory; run `powershell -NoProfile -ExecutionPolicy Bypass -File .\INSTALL.ps1` from the extracted directory. Requires .NET 8 SDK and existing `C:\workforce-os\agent\WorkforceOS.Agent\WorkforceOS.Agent.csproj`.

## Run
As the **interactive employee Windows login** (not the Windows service):
`dotnet run --project C:\workforce-os\agent\WorkforceOS.ScreenCompanion\WorkforceOS.ScreenCompanion.csproj -c Release --no-build`

## Next milestones
1. Reuse workspace/employee/device identity and consent checks, plus employee per-session authorization.
2. Establish authenticated signaling and real WebRTC media transport from the companion.
3. Replace the test browser iframe with `<video>` inside original Live Screen page and enforce revocation.
4. Run multi-account end-to-end tests on Windows hardware.
