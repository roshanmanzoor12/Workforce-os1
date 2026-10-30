# Read-only Windows diagnostics for WorkforceOS. No credentials exported.
$ErrorActionPreference = 'Continue'
$Root = 'C:\workforce-os'
$Out = Join-Path $Root ('workforce-diagnostics-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Force -Path $Out | Out-Null
function Save-Text($File, $Data) { $Data | Out-File -LiteralPath (Join-Path $Out $File) -Encoding utf8 }
Save-Text 'service.txt' (Get-CimInstance Win32_Service | Where-Object { $_.Name -like '*Workforce*' -or $_.DisplayName -like '*Workforce*' } | Select-Object Name,DisplayName,State,StartMode,ProcessId | Format-List | Out-String)
Save-Text 'process.txt' (Get-Process | Where-Object { $_.ProcessName -like '*Workforce*' } | Select-Object ProcessName,Id,StartTime | Format-Table -AutoSize | Out-String)
Save-Text 'runtime.txt' (("OS: " + [Environment]::OSVersion.VersionString), ("PowerShell: " + $PSVersionTable.PSVersion), ("Dotnet available: " + [bool](Get-Command dotnet -ErrorAction SilentlyContinue)))
Save-Text 'ports.txt' (Get-NetTCPConnection -ErrorAction SilentlyContinue | Where-Object { $_.LocalPort -in @(3000,3001,8001,5434,6381) } | Select-Object LocalAddress,LocalPort,State,OwningProcess | Format-Table -AutoSize | Out-String)
Save-Text 'files-present.txt' (@('agent\WorkforceOS.Agent\program.cs','agent\WorkforceOS.ScreenCompanion\Program.cs','apps\web\components\monitoring\native-jpeg-stream.tsx','backend\app\modules\devices\service.py') | ForEach-Object { "$_ = $(Test-Path (Join-Path $Root $_))" })
Write-Host "Diagnostics saved to: $Out" -ForegroundColor Green
Write-Host 'Review files before uploading. This script made no project changes.' -ForegroundColor Yellow
