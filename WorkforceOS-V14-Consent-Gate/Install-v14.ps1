param([switch]$Apply)
$ErrorActionPreference = 'Stop'
$root = 'C:\workforce-os'
$agent = Join-Path $root 'agent\WorkforceOS.Agent\LiveScreen\LiveScreenInboxWorker.cs'
$backend = Join-Path $root 'backend\app\modules\devices\agent_router.py'
foreach ($f in @($agent, $backend)) { if (!(Test-Path $f)) {throw "Missing source: $f"} }
$agentText = [System.IO.File]::ReadAllText($agent)
$backendText = [System.IO.File]::ReadAllText($backend)
$old = @'
var decision = inbox.ConsentGranted
                                ? "accept"
                                : await CompanionRequestNotifier.RequestDecisionAsync(
                                    item.SessionId, item.ExpiresAt, stoppingToken);
'@
$new = @'
// Monitoring disclosure is not persistent permission for screen capture.
                            // Require a session-specific employee decision until an explicit,
                            // independently revocable screen-sharing grant is implemented.
                            var decision = await CompanionRequestNotifier.RequestDecisionAsync(
                                item.SessionId, item.ExpiresAt, stoppingToken);
'@
$already = $agentText.Contains('Monitoring disclosure is not persistent permission for screen capture.')
if (!$already -and !$agentText.Contains($old)) { throw 'Agent source conflict: expected V8 code not found; no changes made.' }
if (!$backendText.Contains('consent_granted=consent_granted,') -and !$backendText.Contains('consent_granted=False,')) { throw 'Backend source conflict; no changes made.' }
Write-Host 'PREFLIGHT PASS: source anchors verified. No live binaries touched.'
if (!$Apply) { Write-Host 'DRY RUN ONLY. Re-run with -Apply.'; exit 0 }
$backup = Join-Path $root ('WorkforceOS-v14-backup-'+(Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Force -Path $backup | Out-Null
Copy-Item -LiteralPath $agent -Destination (Join-Path $backup 'LiveScreenInboxWorker.cs')
Copy-Item -LiteralPath $backend -Destination (Join-Path $backup 'agent_router.py')
if (!$already) { $agentText=$agentText.Replace($old,$new) }
# Do not expose generic monitoring consent as screen-sharing approval.
$backendText=$backendText.Replace('consent_granted=consent_granted,','consent_granted=False,')
[System.IO.File]::WriteAllText($agent,$agentText,[System.Text.UTF8Encoding]::new($false))
[System.IO.File]::WriteAllText($backend,$backendText,[System.Text.UTF8Encoding]::new($false))
if (!( [System.IO.File]::ReadAllText($agent).Contains('Monitoring disclosure is not persistent permission for screen capture.'))) {throw 'Agent verify failed'}
Write-Host "V14 SOURCE GATE APPLIED. Backup: $backup"
Write-Host 'Not deployed. Build Agent to staging; backend restart and runtime checks required.'
