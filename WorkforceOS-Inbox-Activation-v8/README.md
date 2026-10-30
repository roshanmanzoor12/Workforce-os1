# WorkforceOS Inbox Activation Recovery v8

## What this actually fixes

- Re-processes backend `accepted` sessions rather than silently dropping them from the Agent inbox.
- Retries activation on an already employee-accepted session. Does NOT grant consent, auto-accept requests, or start capture before active authorization.
- Adds inbox polling logging to isolate absent requests vs decision/activation vs Companion pipe.

## What it does NOT implement

**This is NOT the complete 7-stage login-to-logout implementation.** Specifically it does not wire authenticated web login to an employee work-session, choose a trusted authorized owner, create automatic requests, implement screen-specific saved consent/indicator acknowledgements, or revoke on browser close. Existing 24-hour expiry is not a substitute for revocation and rolling leases. Those items need verified integration and testing.

## Install

Place this folder under `C:\workforce-os`, then use:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\WorkforceOS-Inbox-Activation-v8\Install-v8.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\WorkforceOS-Inbox-Activation-v8\Install-v8.ps1 -Apply
```

Build *after* applying. Do not overwrite binaries of a running service:

```powershell
dotnet publish .\agent\WorkforceOS.Agent\WorkforceOS.Agent.csproj -c Release -r win-x64 --self-contained false -o .\artifacts\agent-v8-staging
```

Caution: the current inbox worker also sends `visible_indicator_shown = accepted` on the decision API. That is not verified indicator evidence; do not enable unattended screen capture based only on generic monitoring preference. Employee acceptance / informed screen-specific authorization remains required. Back up and deploy only after reviewing diff and regression tests.
