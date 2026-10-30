# WorkforceOS V12 — Atomic Login Lifecycle Source Fix

This is a **targeted transaction-safety patch** for staged V11, NOT the full automatic-login workflow.

## Changes
- `LiveMonitoringService.request_live_screen(..., commit=True)` keeps manual caller behavior.
- V11 coordinator uses `commit=False`; request insert is flushed, then the per-login mapping is inserted, then one commit occurs while advisory lock remains active.
- Guarded, idempotent PowerShell installer creates timestamped backups and Python syntax-checks.

## Install
From `C:\workforce-os` after extracting ZIP:

```
powershell -NoProfile -ExecutionPolicy Bypass -File .\WorkforceOS-Atomic-Lifecycle-v12\Install-v12.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\WorkforceOS-Atomic-Lifecycle-v12\Install-v12.ps1 -Apply
```

## NOT READY for live auto-request
Do NOT run V11 migration or enable coordinator until: authenticated browser login ID and employee identity are validated; trusted owner access is resolved; real login/logout routes invoke coordinator; device/employee records are verified; screen-specific consent and actual visible indicator are integrated; capture renew/revoke is tested. This patch itself does NOT create automatic requests.
