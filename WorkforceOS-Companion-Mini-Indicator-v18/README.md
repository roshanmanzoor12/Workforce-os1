# WorkforceOS V18 — No large companion preview; mini employee indicator

**Goal:** Remove the large, recursive **WorkforceOS Employee Screen Sharing** preview app from the desktop and taskbar. The owner watches the employee's *authorized* screen in the existing Live Screen browser viewer. The employee gets a small 410×102 always-on-top **SCREEN SHARING ACTIVE / STOP SHARING** indicator in the corner during sharing; it remains visible and stoppable, with a tray menu for opening controls and Exit. The whole Companion app cannot be silently hidden while capture is active.

**Extra best-effort behavior:** `SetWindowDisplayAffinity(Handle, WDA_EXCLUDEFROMCAPTURE)` asks supported Windows builds to exclude the employee-facing mini indicator from captured images, so it doesn't appear recursively in the owner stream. If unsupported, the employee indicator remains visible and may appear in owner video. No screen-authorisation, saved-consent decision, device credential, or backend protocol changes are made.

## Source compatibility

Patch supports both installed **V15** and source-patched **V17** `agent/WorkforceOS.ScreenCompanion/Program.cs`. It modifies **only this file**, refuses unknown baselines, creates a timestamped backup, and supports re-running idempotently.

## PowerShell — preflight, apply, stage build

Put ZIP in `C:\workforce-os`, extract and run:

```powershell
cd C:\workforce-os
Expand-Archive .\WorkforceOS-Companion-Mini-Indicator-v18.zip -DestinationPath . -Force
powershell -NoProfile -ExecutionPolicy Bypass -File .\WorkforceOS-Companion-Mini-Indicator-v18\Install-v18.ps1
# If preflight passes:
powershell -NoProfile -ExecutionPolicy Bypass -File .\WorkforceOS-Companion-Mini-Indicator-v18\Install-v18.ps1 -Apply
powershell -NoProfile -ExecutionPolicy Bypass -File .\WorkforceOS-Companion-Mini-Indicator-v18\Verify-v18.ps1

dotnet publish .\agent\WorkforceOS.ScreenCompanion\WorkforceOS.ScreenCompanion.csproj -c Release -r win-x64 --self-contained false -o .\artifacts\screen-companion-v18-staging
if ($LASTEXITCODE -ne 0) { throw 'Companion build FAILED' }
```

## Safe live deployment

Employee must first click **Stop Sharing**. Preflight:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\WorkforceOS-Companion-Mini-Indicator-v18\Deploy-v18-Companion.ps1
```

For a verified single Companion under the interactive PowerShell supervisor used by WorkforceOS, this command temporarily pauses **only that supervisor**, safely terminates that Companion, backs up its deployed binaries, copies the staged build, verifies DLL SHA256, and restarts the supervisor:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\WorkforceOS-Companion-Mini-Indicator-v18\Deploy-v18-Companion.ps1 -Apply -PauseAndRestartSupervisor
if ($LASTEXITCODE -ne 0) { throw 'Companion deployment FAILED' }
```

It refuses unfamiliar supervisors or multiple Companion processes. If you already paused the supervisor and no Companion is running, use just `-Apply` and restart your own supervisor afterwards. The script does not stop Agent, backend, Docker, or frontend.

## Verify behavior

1. Employee shares with valid approval, visible corner indicator and accessible **STOP SHARING**. No large separate recursive preview window or taskbar button.
2. Owner selects the same employee in the web Live Screen page. If session is `active` and Agent frames are arriving, they show **in the page viewer**. This patch does **not** repair backend `requested/ended` state, offline Agent, or failed frame uploads.
3. Employee clicks **STOP SHARING**: local publisher terminates, revocation path remains, small bar hides.
4. Test fallback if Windows can't exclude mini bar from capture: owner may see a tiny indicator in video, **not** the large recursive mirror.

**Testing disclaimer:** Local transforms were tested on V15/V17 source snapshots. This Linux tool environment cannot compile the .NET Windows UI or confirm Win32 capture exclusion; validate with `dotnet publish` and a real employee/owner session before production use.
