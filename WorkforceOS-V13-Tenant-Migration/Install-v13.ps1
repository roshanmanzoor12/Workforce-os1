[CmdletBinding()]
param([switch]$Apply, [string]$TenantDatabaseUrl)
$ErrorActionPreference = 'Stop'
$base = $PSScriptRoot
$project = 'C:\workforce-os'
$coordinator = Join-Path $project 'backend\app\modules\live_monitoring\login_lifecycle.py'
$service = Join-Path $project 'backend\app\modules\live_monitoring\service.py'
if (!(Test-Path $coordinator) -or !(Test-Path $service)) { throw 'V11/V12 backend source missing' }
$life = Get-Content $coordinator -Raw
$svc = Get-Content $service -Raw
if ($life -notmatch 'commit=False' -or $svc -notmatch 'commit: bool = True') { throw 'V12 atomic patch not detected' }
if (!(Get-Command python -ErrorAction SilentlyContinue)) {throw 'python command not found'}
& python -m py_compile $coordinator $service
if ($LASTEXITCODE -ne 0) {throw 'Python syntax verification failed'}
Write-Host 'PREFLIGHT PASS: V12 coordinator and transaction patch present.' -ForegroundColor Green
if (!$Apply) { Write-Host 'DRY RUN ONLY. No database changed.'; exit 0 }
if ([string]::IsNullOrWhiteSpace($TenantDatabaseUrl)) {throw 'Explicit -TenantDatabaseUrl required; auto-discovery is deliberately disabled.'}
if ($TenantDatabaseUrl -notmatch '^postgres(ql)?://') {throw 'Expected PostgreSQL URL for the TENANT database.'}
# Use psql only when explicitly passed the tenant URL. Suppress command output containing credentials.
$psql = Get-Command psql -ErrorAction SilentlyContinue
if (!$psql) { throw 'psql is not on PATH; nothing applied. Install PostgreSQL client or use your tenant migration runner.' }
Write-Host 'CONFIRM: This URL must target a tenant DB, NOT control-plane. Press Ctrl+C if unsure.' -ForegroundColor Yellow
$env:PGCONNECT_TIMEOUT = '5'
& $psql.Source '-X' '-v' 'ON_ERROR_STOP=1' '--dbname' $TenantDatabaseUrl '-f' (Join-Path $base 'migration.sql')
if ($LASTEXITCODE -ne 0) {throw 'Tenant migration failed'}
Write-Host 'V13 MIGRATION APPLIED. Verify against same tenant database using verify.sql.' -ForegroundColor Green
