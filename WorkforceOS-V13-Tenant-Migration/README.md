# WorkforceOS V13 — tenant lifecycle persistence migration

This is **not** the complete automatic login-to-logout Live Screen feature.

## Implemented
- Tenant PostgreSQL `live_screen_login_lifecycle` table, per-login per-device PK, employee and session indexes, terminal state check.
- PowerShell dry-run checks for V12 source, explicit tenant DB target requirement, `psql ON_ERROR_STOP`, transaction-atomic DDL.
- `verify.sql` for post-deployment checks.

## Install
1. Extract ZIP into `C:\workforce-os`.
2. `powershell -NoProfile -ExecutionPolicy Bypass -File .\WorkforceOS-V13-Tenant-Migration\Install-v13.ps1`
3. First establish the exact intended **tenant** database. Never use the control-plane connection. Apply only with explicit `-Apply -TenantDatabaseUrl '<tenant PostgreSQL URL>'`. Avoid pasting secrets into chat or logging command lines; use your existing secrets manager or established migration runner instead where possible.
4. `psql -X -v ON_ERROR_STOP=1 --dbname '<same tenant URL>' -f '.\WorkforceOS-V13-Tenant-Migration\verify.sql'`

## Not implemented
- Authenticated browser login-to-coordinator hook; trusted owner selection; screen-specific saved consent; logout event bridging; lease renewal; app-close timeout reconciliation. Do not restart backend to assume these are wired.

## Compatibility
- V11 coordinator writes states `requested`/`ended` and uses `(login_id, desktop_device_id)` primary key.
- V12 transaction logic uses `commit=False` on live request service.
- Use the real project migration system before production rollout. `IF NOT EXISTS` cannot reconcile an incompatible existing table; inspect before apply.
