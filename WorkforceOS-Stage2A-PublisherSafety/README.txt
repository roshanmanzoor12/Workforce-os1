WorkforceOS Stage 2A — Companion publisher stop/cancellation safety

THIS IS NOT THE COMPLETE LIVE-SCREEN FIX. The backend currently advertises
live_screen=false; agent inbox is read-only; no authorized owner frame transport exists.
This patch only prevents in-flight publisher operations from initiating/retrying
transmission after employee Stop. It does not enable screen capture on a device.

Safe review:
  powershell -NoProfile -ExecutionPolicy Bypass -File .\Apply-Stage2A.ps1

Source-only application (requires audited original file hash):
  powershell -NoProfile -ExecutionPolicy Bypass -File .\Apply-Stage2A.ps1 -Apply

Build on Windows with .NET 8 SDK, review results before deploy:
  dotnet build C:\workforce-os\agent\WorkforceOS.ScreenCompanion\WorkforceOS.ScreenCompanion.csproj -c Release

No automatic binary replacement, service restart, credential change,
assignment change or capability enablement. Backup path printed by installer.
If test fails, copy backup over patched source. Then rebuild.

Remaining work for live screen: backend workspace-scoped request/approval,
consent-bound publisher credentials, verified device/session identity, secured
media relay, viewer authorization, revocation/expiry, and end-to-end tests.
