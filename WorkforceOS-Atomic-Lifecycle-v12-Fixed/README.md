# WorkforceOS V12 — corrected installer

Fixes a PowerShell case-insensitive variable collision in the original installer: `$L` was the login_lifecycle.py *path* while `$l` was reassigned its *source contents*. PowerShell treats those as the same variable, so `Copy-Item` attempted to interpret Python source as a drive/path.

This fix only changes the installer; patch behavior is unchanged. Previous failure occurred before either `WriteAllText`, so normally no source files were modified.

From `C:\workforce-os`:

```powershell
Expand-Archive .\WorkforceOS-Atomic-Lifecycle-v12-Fixed.zip -DestinationPath . -Force
& .\WorkforceOS-Atomic-Lifecycle-v12-Fixed\Install-v12.ps1
& .\WorkforceOS-Atomic-Lifecycle-v12-Fixed\Install-v12.ps1 -Apply
```

Do not run the database migration or enable the coordinator yet. This is an atomicity source patch, not a complete login/logout integration.
