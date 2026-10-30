param([switch]$Apply)
$ErrorActionPreference = 'Stop'
$Root = 'C:\workforce-os'
$Package = Split-Path -Parent $MyInvocation.MyCommand.Path
$Relative = 'agent\WorkforceOS.ScreenCompanion\RemoteFramePublisher.cs'
$Source = Join-Path $Package ('payload\' + $Relative)
$Target = Join-Path $Root $Relative
$ExpectedSHA = '01e02af0f757e1fa0ee1ba18b65966003184ae789477ab2b77ab1fc7974d79c1'
if (!(Test-Path -LiteralPath $Source) -or !(Test-Path -LiteralPath $Target)) { throw 'Required source file not found.' }
$TargetSha = (Get-FileHash -LiteralPath $Target -Algorithm SHA256).Hash.ToLowerInvariant()
$SourceSha = (Get-FileHash -LiteralPath $Source -Algorithm SHA256).Hash.ToLowerInvariant()
if ($TargetSha -eq $SourceSha) { Write-Host 'ALREADY APPLIED'; exit 0 }
if ($TargetSha -ne $ExpectedSHA) { throw 'Source mismatch. Your C# file differs from the uploaded snapshot. No changes made.' }
Write-Host 'PREFLIGHT PASS: Companion 403 recovery patch' -ForegroundColor Green
if (!$Apply) { Write-Host 'DRY RUN ONLY. Use -Apply to update.'; exit 0 }
$Backup = Join-Path $Root ('WorkforceOS-v3-backup-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
$BackupFile = Join-Path $Backup $Relative
New-Item -Path (Split-Path -Parent $BackupFile) -ItemType Directory -Force | Out-Null
Copy-Item -LiteralPath $Target -Destination $BackupFile -Force
Copy-Item -LiteralPath $Source -Destination $Target -Force
Write-Host "APPLIED. Backup: $Backup" -ForegroundColor Green
Write-Host 'Rebuild the Windows ScreenCompanion project before testing.' -ForegroundColor Yellow
