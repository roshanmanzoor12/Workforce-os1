$ErrorActionPreference = 'Stop'
$root = 'C:\workforce-os'
$target = Join-Path $root 'tools\live-screen-dev'
$secretFile = Join-Path $target 'secrets.clixml'
if (Test-Path $secretFile) { throw "Secrets already exist: $secretFile. Keeping previous credentials; do not overwrite accidentally." }
$device = Read-Host 'Enter enrolled employee device name (for local test, e.g. DESKTOP-F726TKR)'
if ([string]::IsNullOrWhiteSpace($device) -or $device -notmatch '^[A-Za-z0-9_-]{1,80}$') { throw 'Device ID must use 1-80 ASCII letters, digits, _ or -.' }
$send = [Convert]::ToHexString([Security.Cryptography.RandomNumberGenerator]::GetBytes(32))
$view = [Convert]::ToHexString([Security.Cryptography.RandomNumberGenerator]::GetBytes(32))
# DPAPI protects this export for the currently signed-in Windows account.
[pscustomobject]@{
 Device = $device
 SendToken = ConvertTo-SecureString $send -AsPlainText -Force
 ViewToken = ConvertTo-SecureString $view -AsPlainText -Force
} | Export-Clixml -LiteralPath $secretFile
Write-Host "Created per-user encrypted local credentials at $secretFile"
Write-Host 'This demo assumes relay, employee companion and owner browser are on the SAME Windows PC.'
