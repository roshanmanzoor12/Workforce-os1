WorkforceOS Native Live Screen Stage 2B - Read-only preflight

Run in PowerShell:
  powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\workforce-os\WorkforceOS-Native-Stage2B-Preflight\Check-NativeLiveScreen.ps1"

No services are stopped. No tokens or stored credentials are read. No files are changed.
This is NOT the end-to-end streaming implementation: secure backend frame transport,
device-bound authorization, Agent-to-Companion session delivery and owner viewer must
be implemented and tested before the native screen can appear.
