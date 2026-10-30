# WorkforceOS V10 - Consent and Device Decision Reliability

## Implemented (limited scope)
- Fixes `None.id` backend error in authenticated device decision and activation when desktop device mapping is missing; returns 404 instead.
- Removes the false assertion that generic `MonitoringConsent` means the employee has already approved a screen-sharing session. Agent now requests the employee Accept/Decline decision via interactive Companion.
- Keeps V8 accepted-session recovery, existing permissions, and V9 Stop Sharing code untouched.

## NOT implemented
This patch does NOT implement one automatic request per login, saved **screen-specific** approval, login session binding, bounded renewal, logout cleanup, or browser/app-close detection. These require explicit account-session records and an approved owner scope; never treat background heartbeat as a browser login.

## Usage
Extract this directory at `C:\workforce-os`, then in Administrator PowerShell:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\WorkforceOS-Consent-Reliability-v10\Install-v10.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\WorkforceOS-Consent-Reliability-v10\Install-v10.ps1 -Apply
python -m py_compile .\backend\app\modules\devices\agent_router.py
dotnet publish .\agent\WorkforceOS.Agent\WorkforceOS.Agent.csproj -c Release -r win-x64 --self-contained false -o .\artifacts\agent-v10-staging
```

Restart the backend using its existing launch/supervision procedure and deploy the staging Agent only with the service safely stopped. Do not overwrite a running DLL. This ZIP does not install binaries or restart processes.

### Limitations
Indicator verification is **not** implemented: the existing Agent decision payload reports `visible_indicator_shown=accepted` without evidence. Do not treat acceptance as proof a visible capture indicator has actually been rendered. A production-ready flow needs a Companion-to-backend verified indicator-ready handshake plus a revocable saved screen-specific grant.
