$ErrorActionPreference = 'Stop'
$root = 'C:\workforce-os'
$cfg = Import-Clixml -LiteralPath (Join-Path $root 'tools\live-screen-dev\secrets.clixml')
$token = [System.Net.NetworkCredential]::new('', $cfg.ViewToken).Password
$frontend = Join-Path $root 'apps\web'
$envFile = Join-Path $frontend '.env.local'
$line = 'NEXT_PUBLIC_WFOS_SCREEN_RELAY_URL=http://127.0.0.1:8769'
if (Test-Path $envFile) {
 $raw = Get-Content $envFile -Raw
 if ($raw -match '(?m)^NEXT_PUBLIC_WFOS_SCREEN_RELAY_URL=') {
   $raw = [regex]::Replace($raw, '(?m)^NEXT_PUBLIC_WFOS_SCREEN_RELAY_URL=.*$', $line)
 } else { $raw = $raw.TrimEnd("`r","`n") + "`r`n" + $line + "`r`n" }
 Copy-Item $envFile ($envFile + '.before-live-screen-3c.bak') -Force
} else { $raw = $line + "`r`n" }
Set-Content -LiteralPath $envFile -Value $raw -Encoding utf8
Write-Host 'Next.js dev env configured. Restart frontend dev server before opening /monitoring/live-screen.'
Write-Host 'IN YOUR TRUSTED OWNER BROWSER tab, open DevTools Console and paste BOTH lines below:'
Write-Host ('sessionStorage.setItem(''wfos_screen_view_token'', ' + (ConvertTo-Json $token -Compress) + ');')
Write-Host ('sessionStorage.setItem(''wfos_screen_device_id'', ' + (ConvertTo-Json $cfg.Device -Compress) + '); location.reload();')
Write-Warning 'The viewer token will appear in console and sessionStorage. This is a LOCAL DEVELOPMENT DEMO only.'
