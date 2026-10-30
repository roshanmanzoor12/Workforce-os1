param([switch]$Apply)
$ErrorActionPreference = 'Stop'
$Package = Split-Path -Parent $MyInvocation.MyCommand.Path
$Root = Split-Path -Parent $Package
$Paths = @(
 'backend\app\modules\devices\agent_router.py',
 'agent\WorkforceOS.Agent\LiveScreen\LiveScreenInboxWorker.cs'
)
foreach($rel in $Paths) {
 $dest=Join-Path $Root $rel
 $baseline=Join-Path (Join-Path $Package 'baseline') $rel
 $replacement=Join-Path (Join-Path $Package 'files') $rel
 if(!(Test-Path $dest)){ throw "Missing: $dest" }
 $actual=(Get-FileHash $dest -Algorithm SHA256).Hash
 $expected=(Get-FileHash $baseline -Algorithm SHA256).Hash
 $updated=(Get-FileHash $replacement -Algorithm SHA256).Hash
 if($actual -ne $expected -and $actual -ne $updated){ throw "SOURCE CONFLICT: $rel differs from V8 baseline. No changes made." }
 Write-Host "BASELINE PASS: $rel"
}
if(!$Apply){ Write-Host 'PREFLIGHT PASS. Re-run -Apply to modify source only.';exit 0 }
$backup=Join-Path $Root ('WorkforceOS-v10-backup-'+(Get-Date -Format yyyyMMdd-HHmmss))
foreach($rel in $Paths){
 $dest=Join-Path $Root $rel
 $b=Join-Path $backup $rel
 New-Item -ItemType Directory -Force -Path (Split-Path $b -Parent)|Out-Null
 Copy-Item $dest $b -Force
}
try {
 foreach($rel in $Paths){
  $dest=Join-Path $Root $rel
  $replacement=Join-Path (Join-Path $Package 'files') $rel
  Copy-Item $replacement $dest -Force
  if((Get-FileHash $replacement).Hash -ne (Get-FileHash $dest).Hash){throw "Verify failed: $rel"}
  Write-Host "APPLIED: $rel"
 }
} catch {
 foreach($rel in $Paths){Copy-Item (Join-Path $backup $rel) (Join-Path $Root $rel) -Force}
 throw
}
Write-Host "PATCH VERIFIED. Backup: $backup" -ForegroundColor Green
Write-Host 'Restart backend and build/deploy Agent separately after reviewing README.'
