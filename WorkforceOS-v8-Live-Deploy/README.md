# V8 Windows Agent safe live deployment (not the seven-stage automatic-request implementation)
Run in elevated Windows PowerShell after employee stops screen sharing, and schedule a service restart window. Existing agent monitoring will temporarily pause. No backend/frontend source changes.

```powershell
cd C:\workforce-os
powershell -NoProfile -ExecutionPolicy Bypass -File .\WorkforceOS-v8-Live-Deploy\Deploy-v8-Agent.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\WorkforceOS-v8-Live-Deploy\Deploy-v8-Agent.ps1 -Apply
```

The script saves a full backup and verifies DLL SHA256 before/after, stops only `WorkforceOSAgent`, copies the published v8 staging output, then restarts. It prints a backup path. To roll back:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\WorkforceOS-v8-Live-Deploy\Deploy-v8-Agent.ps1 -Rollback -BackupPath 'C:\workforce-os\WorkforceOS-agent-live-backup-YYYYMMDD-HHMMSS'
```

This does not implement web-login triggered auto-request, session-bound authorization, or logout revocation. Test request acceptance and Companion visibility after deploy.
