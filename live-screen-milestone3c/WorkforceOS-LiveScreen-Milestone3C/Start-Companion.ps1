$ErrorActionPreference = 'Stop'
$root = 'C:\workforce-os'
$cfg = Import-Clixml -LiteralPath (Join-Path $root 'tools\live-screen-dev\secrets.clixml')
$token = [System.Net.NetworkCredential]::new('', $cfg.SendToken).Password
$env:WFOS_SCREEN_SEND_URL = 'ws://127.0.0.1:8769/ws/send/' + [uri]::EscapeDataString($cfg.Device) + '?token=' + [uri]::EscapeDataString($token)
Write-Host 'Starting companion for LOCAL testing. Close any other already-running companion first.'
dotnet run --project "$root\agent\WorkforceOS.ScreenCompanion\WorkforceOS.ScreenCompanion.csproj" -c Release --no-build
