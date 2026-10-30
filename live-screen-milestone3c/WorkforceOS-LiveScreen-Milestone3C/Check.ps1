$ErrorActionPreference = 'Stop'
try {
 $h = Invoke-RestMethod -Uri 'http://127.0.0.1:8769/health' -TimeoutSec 4
 Write-Host "Relay running: $($h.relay)"
 Write-Host "Sender connected: $($h.sender_connected)"
 Write-Host "Viewer connections: $($h.viewers)"
 Write-Host "Recent frames: $($h.frame_fresh)"
 if ($h.sender_connected -and $h.frame_fresh) { Write-Host 'PASS: Native sender is delivering fresh image frames to relay.' }
 else { Write-Warning 'No fresh remote frames. Start companion and authorize sharing.' }
} catch { throw "Relay not reachable at localhost:8769. Start-Relay.ps1 first. $($_.Exception.Message)" }
