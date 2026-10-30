#Requires -Version 5.1
$ErrorActionPreference = 'Stop'
$Root = 'C:\workforce-os'
$Project = Join-Path $Root 'agent\WorkforceOS.ScreenCompanion\WorkforceOS.ScreenCompanion.csproj'
$Exe = Join-Path $Root 'agent\WorkforceOS.ScreenCompanion\bin\Release\net8.0-windows\WorkforceOS.ScreenCompanion.exe'
$RunKey = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run'
$ValueName = 'WorkforceOSScreenCompanion'
if (-not (Test-Path -LiteralPath $Project)) { throw "Missing Milestone 1 companion: $Project. Install Milestone 1 first." }
$Dotnet = Get-Command dotnet -ErrorAction SilentlyContinue
if (-not $Dotnet) { throw 'dotnet SDK is not available on PATH.' }
& dotnet build $Project --configuration Release
if ($LASTEXITCODE -ne 0) { throw 'Companion build failed. Auto-launch was not registered.' }
if (-not (Test-Path -LiteralPath $Exe)) { throw "Built companion executable not found: $Exe" }
# Current-user auto-launch only: never a service/Session 0, never automatic capture.
New-Item -Path $RunKey -Force | Out-Null
$Old = (Get-ItemProperty -Path $RunKey -Name $ValueName -ErrorAction SilentlyContinue).$ValueName
$BackupFile = Join-Path $PSScriptRoot 'previous-run-value.txt'
if ($null -ne $Old) { [IO.File]::WriteAllText($BackupFile, [string]$Old) }
New-ItemProperty -Path $RunKey -Name $ValueName -PropertyType String -Value ('"' + $Exe + '"') -Force | Out-Null
Write-Host 'PASS: Companion builds and launches for THIS Windows user at next Windows sign-in.' -ForegroundColor Green
Write-Host 'No screen capture or remote streaming starts automatically.'
Write-Host 'Use the companion Start local preview button for an explicitly authorized local preview.'
Write-Host 'Existing WorkforceOSAgent service was not changed.'
