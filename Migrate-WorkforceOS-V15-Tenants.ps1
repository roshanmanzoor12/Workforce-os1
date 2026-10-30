<#
WorkforceOS V13 + V15 tenant migration for four verified local development tenants.
Defaults to read-only preflight. -Apply makes full custom-format backups for ALL
four tenants before applying either migration to any tenant.
Do not run against production without reviewing SQL and existing Alembic history.
#>
[CmdletBinding()]
param(
    [switch]$Apply,
    [string]$Root = 'C:\workforce-os',
    [string]$Container = 'workforce-os-postgres-1'
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$SqlRoot = Join-Path $Root 'WorkforceOS-Full-LiveFlow-v15'
$V13Sql = Join-Path $SqlRoot 'migration-v13.sql'
$V15Sql = Join-Path $SqlRoot 'migration.sql'
foreach ($file in @($V13Sql, $V15Sql)) {
    if (!(Test-Path -LiteralPath $file -PathType Leaf)) {
        throw "Missing SQL migration: $file"
    }
}

$ExpectedTenants = @(
    'tenant_1e4ba0b85ce3442fa0a6ed3c1a890f46',
    'tenant_34527ffbe0944e5e89ee4cab97244fc3',
    'tenant_367c0324060240259a641ecbd5a0bca9',
    'tenant_3c9792c88f1d4d0486876a4cf802699c'
)

function Assert-CommandSucceeded([string]$Operation) {
    if ($LASTEXITCODE -ne 0) { throw "$Operation failed (exit $LASTEXITCODE). STOP; do not continue." }
}

if (!(Get-Command docker -ErrorAction SilentlyContinue)) {
    throw 'Docker CLI not found. No changes made.'
}
$Active = @(& docker ps --filter "name=^/${Container}$" --format '{{.Names}}')
Assert-CommandSucceeded 'docker ps'
if ($Active.Count -ne 1 -or $Active[0] -ne $Container) {
    throw "Verified PostgreSQL container $Container is not running. No changes made."
}

$RegistrySql = "SELECT database_name FROM public.tenant_database_registry WHERE status='ready' ORDER BY database_name;"
$Registry = @(& docker exec $Container psql -U postgres -d workforce_control -X -At -v ON_ERROR_STOP=1 -c $RegistrySql)
Assert-CommandSucceeded 'tenant registry discovery'
$Registry = @($Registry | ForEach-Object { $_.Trim() } | Where-Object { $_ })
$Missing = @($ExpectedTenants | Where-Object { $_ -notin $Registry })
$Extra = @($Registry | Where-Object { $_ -notin $ExpectedTenants })
if ($Missing.Count -gt 0 -or $Extra.Count -gt 0) {
    throw "Tenant registry changed. Missing: $($Missing -join ', '); unexpected: $($Extra -join ', '). No changes made."
}

$InspectSql = @'
SELECT (to_regclass('public.live_screen_login_lifecycle') IS NOT NULL)::int,
       (to_regclass('public.live_screen_saved_approvals') IS NOT NULL)::int,
       (EXISTS (SELECT 1 FROM information_schema.columns
                WHERE table_schema='public'
                  AND table_name='live_screen_login_lifecycle'
                  AND column_name='last_ping_at'))::int;
'@

function Get-TenantStatus([string]$Tenant) {
    $Schema = @(& docker exec $Container psql -U postgres -d $Tenant -X -At -F '|' -v ON_ERROR_STOP=1 -c 'SELECT current_schema();')
    Assert-CommandSucceeded "default schema check for $Tenant"
    if ($Schema.Count -ne 1 -or $Schema[0].Trim() -ne 'public') {
        throw "$Tenant has unexpected default schema $($Schema -join ','). No migrations applied."
    }
    $Rows = @(& docker exec $Container psql -U postgres -d $Tenant -X -At -F '|' -v ON_ERROR_STOP=1 -c $InspectSql)
    Assert-CommandSucceeded "schema inspection for $Tenant"
    if ($Rows.Count -ne 1) { throw "Unexpected schema inspection rows for $Tenant : $($Rows -join '; ')" }
    $Value = $Rows[0].Trim()
    if ($Value -notin @('0|0|0','1|1|1')) {
        throw "PARTIAL/UNEXPECTED schema in $Tenant ($Value). Stop and reconcile manually."
    }
    return $Value
}

Write-Host '=== WorkforceOS V13 + V15 tenant migration preflight ===' -ForegroundColor Cyan
$Pending = @()
foreach ($Tenant in $ExpectedTenants) {
    $Status = Get-TenantStatus $Tenant
    if ($Status -eq '0|0|0') {
        $Pending += $Tenant
        Write-Host "PENDING: $Tenant (lifecycle=missing, approval=missing, lease=missing)" -ForegroundColor Yellow
    } else {
        Write-Host "COMPLETE: $Tenant (all required objects present)" -ForegroundColor Green
    }
}

if (!$Apply) {
    Write-Host "DRY RUN PASS. $($Pending.Count) of 4 tenants need migrations. No database changed." -ForegroundColor Green
    Write-Host 'Review V13/V15 SQL, then re-run this script with -Apply.'
    return
}
if ($Pending.Count -eq 0) {
    Write-Host 'All four tenants already contain the required schema. Nothing applied.' -ForegroundColor Green
    return
}

# Never modify a tenant until verified backups exist for ALL four tenants.
$Stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$BackupDir = Join-Path $Root ("WorkforceOS-V15-tenant-backups-$Stamp")
New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
Write-Host "Backing up all four tenants to $BackupDir" -ForegroundColor Cyan

foreach ($Tenant in $ExpectedTenants) {
    $DumpName = "${Tenant}-${Stamp}.dump"
    $RemoteDump = "/tmp/$DumpName"
    $LocalDump = Join-Path $BackupDir $DumpName
    try {
        & docker exec $Container pg_dump -U postgres -d $Tenant -Fc --file=$RemoteDump
        Assert-CommandSucceeded "pg_dump $Tenant"
        & docker exec $Container pg_restore --list $RemoteDump | Out-Null
        Assert-CommandSucceeded "pg_restore --list $Tenant"
        & docker cp "${Container}:${RemoteDump}" $LocalDump
        Assert-CommandSucceeded "docker cp backup $Tenant"
        if (!(Test-Path -LiteralPath $LocalDump -PathType Leaf) -or (Get-Item -LiteralPath $LocalDump).Length -lt 1024) {
            throw "Backup file missing or suspiciously small for $Tenant : $LocalDump"
        }
        Write-Host "BACKUP OK: $Tenant" -ForegroundColor Green
    } finally {
        & docker exec $Container rm -f $RemoteDump | Out-Null
    }
}

# SQL scripts execute in PostgreSQL container, avoiding Windows psql PATH and text re-encoding.
# Each file has BEGIN/COMMIT and ON_ERROR_STOP=1: a failing migration halts immediately.
$RemoteV13 = "/tmp/wfos-v13-${Stamp}.sql"
$RemoteV15 = "/tmp/wfos-v15-${Stamp}.sql"
try {
    & docker cp $V13Sql "${Container}:${RemoteV13}"
    Assert-CommandSucceeded 'copy V13 SQL to container'
    & docker cp $V15Sql "${Container}:${RemoteV15}"
    Assert-CommandSucceeded 'copy V15 SQL to container'

    foreach ($Tenant in $Pending) {
        Write-Host "=== Applying V13 to $Tenant ===" -ForegroundColor Cyan
        & docker exec $Container psql -U postgres -d $Tenant -X -v ON_ERROR_STOP=1 -f $RemoteV13
        Assert-CommandSucceeded "V13 migration for $Tenant"
        Write-Host "=== Applying V15 to $Tenant ===" -ForegroundColor Cyan
        & docker exec $Container psql -U postgres -d $Tenant -X -v ON_ERROR_STOP=1 -f $RemoteV15
        Assert-CommandSucceeded "V15 migration for $Tenant"
        $Status = Get-TenantStatus $Tenant
        if ($Status -ne '1|1|1') { throw "POST-MIGRATION VALIDATION FAILED for ${Tenant}: $Status" }
        Write-Host "MIGRATION VERIFIED: $Tenant" -ForegroundColor Green
    }
} finally {
    & docker exec $Container rm -f $RemoteV13 $RemoteV15 | Out-Null
}

Write-Host 'V13 + V15 SCHEMA VERIFIED FOR ALL FOUR TENANTS.' -ForegroundColor Green
Write-Host "Database backups retained at $BackupDir" -ForegroundColor Cyan
Write-Host 'Next: register equivalent Alembic migrations for future tenants, then backend/frontend compile + runtime tests.'
