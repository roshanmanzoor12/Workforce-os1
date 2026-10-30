param([switch]$Apply)
$ErrorActionPreference = 'Stop'
$root = 'C:\workforce-os'
$target = Join-Path $root 'apps\web\app\(workspace)\monitoring\live-wall\page.tsx'
if (-not (Test-Path -LiteralPath $target)) { throw "File not found: $target" }
$utf8 = New-Object System.Text.UTF8Encoding($false)
$before = [System.IO.File]::ReadAllText($target)
$oldCondition = 'sessions[selected.device_id] && ["requested", "pending", "accepted", "active"].includes(sessions[selected.device_id].status)'
$newCondition = 'sessions[selected.device_id] && ["requested", "pending", "accepted", "active"].includes(sessions[selected.device_id]?.status ?? "")'
$oldCallback = 'onClick={() => void stopSession(selected.device_id, sessions[selected.device_id].id)}'
$newCallback = 'onClick={() => { const currentSession = sessions[selected.device_id]; if (currentSession) void stopSession(selected.device_id, currentSession.id); }}'
foreach ($old in @($oldCondition, $oldCallback)) {
  $count = [regex]::Matches($before, [regex]::Escape($old)).Count
  if ($count -ne 1) { throw "Expected exactly one match ($count found): $old. No changes made." }
}
$after = $before.Replace($oldCondition, $newCondition).Replace($oldCallback, $newCallback)
if (-not $Apply) { Write-Host 'DRY RUN PASS: two exact Live Wall TypeScript fixes located. Use -Apply to modify.'; exit 0 }
$backup = "$target.backup-$(Get-Date -Format 'yyyyMMddTHHmmss')"
Copy-Item -LiteralPath $target -Destination $backup -ErrorAction Stop
[System.IO.File]::WriteAllText($target, $after, $utf8)
Write-Host "PATCH APPLIED: $target" -ForegroundColor Green
Write-Host "BACKUP: $backup"
Write-Host 'NEXT: cd C:\workforce-os\apps\web; npx tsc --noEmit'
