param([switch]$Apply)
$ErrorActionPreference = 'Stop'
$Root = 'C:\workforce-os'
$Relative = 'agent\WorkforceOS.ScreenCompanion\RemoteFramePublisher.cs'
$Target = Join-Path $Root $Relative
if (!(Test-Path -LiteralPath $Target)) { throw "Missing source: $Target" }
$Current = [System.IO.File]::ReadAllText($Target)
$Old = '            if (failures >= 8) Stop();'
$New = '            // Temporary backend disconnects/timeouts must not permanently stop the publisher.\n            // The backend still authorizes every upload; explicit Stop() remains terminal.\n            // The next frame callback retries after the backend recovers.'
$New = $New.Replace('\n', "`r`n")
if ($Current.Contains($New)) { Write-Host 'ALREADY APPLIED: transient network failure no longer stops publisher'; exit 0 }
$Count = ([regex]::Matches($Current, [regex]::Escape($Old))).Count
if ($Count -ne 1) { throw "PREFLIGHT FAILED: expected exactly one eight-failure Stop() block; found $Count. No files changed." }
# Must be running version with dedicated terminal authorization handling; avoid modifying older/unknown variants.
if (!$Current.Contains('response.StatusCode') -or !$Current.Contains('Stop()')) { throw 'PREFLIGHT FAILED: unexpected source structure' }
Write-Host 'PREFLIGHT PASS: transient network/timeout publisher recovery'
if (!$Apply) { Write-Host 'DRY RUN ONLY: use -Apply'; exit 0 }
$BackupDir = Join-Path $Root ('WorkforceOS-v6-backup-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
Copy-Item -LiteralPath $Target -Destination (Join-Path $BackupDir 'RemoteFramePublisher.cs') -Force
$Updated = $Current.Replace($Old, $New)
[System.IO.File]::WriteAllText($Target, $Updated, [System.Text.UTF8Encoding]::new($false))
Write-Host "APPLIED: $Target"
Write-Host "BACKUP: $BackupDir"
Write-Host 'NEXT: publish ScreenCompanion to a STAGING directory, then switch it when employee capture is stopped.'
