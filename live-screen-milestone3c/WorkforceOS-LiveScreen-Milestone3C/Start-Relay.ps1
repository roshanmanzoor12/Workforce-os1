$ErrorActionPreference = 'Stop'
$root = 'C:\workforce-os'
$secretFile = Join-Path $root 'tools\live-screen-dev\secrets.clixml'
if (!(Test-Path $secretFile)) { throw 'Run Setup.ps1 first.' }
$cfg = Import-Clixml -LiteralPath $secretFile
$env:WFOS_DEVICE_ID = $cfg.Device
$env:WFOS_SEND_TOKEN = [System.Net.NetworkCredential]::new('', $cfg.SendToken).Password
$env:WFOS_VIEW_TOKEN = [System.Net.NetworkCredential]::new('', $cfg.ViewToken).Password
$relay = Join-Path $root 'live-screen-milestone3b'
Set-Location $relay
Write-Host 'Starting dev-only relay at 127.0.0.1:8769. Keep this window open.'
python -m uvicorn relay.server:app --host 127.0.0.1 --port 8769
