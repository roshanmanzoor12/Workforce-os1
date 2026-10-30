$ErrorActionPreference = 'Stop'
$File = 'C:\workforce-os\tools\live-screen-dev\secrets.clixml'
if (!(Test-Path -LiteralPath $File)) { throw "Missing credentials: $File. Run Setup.ps1 as original Windows user." }
$Cfg = Import-Clixml -LiteralPath $File
$Token = [System.Net.NetworkCredential]::new('', $Cfg.ViewToken).Password
if ($Token -notmatch '^[a-fA-F0-9]{64}$') { throw 'Invalid viewer token format' }
Set-Clipboard -Value $Token
Write-Host 'PASS: Local development viewer token copied to clipboard (not printed).' -ForegroundColor Green
Write-Host 'Open your trusted owner Chrome profile on /monitoring/live-screen; paste into the on-page field.'
Write-Warning 'Clipboard contains a secret. Clear clipboard after connecting (Set-Clipboard -Value "").'
