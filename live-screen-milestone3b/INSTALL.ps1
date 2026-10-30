$ErrorActionPreference = 'Stop'
$Root = 'C:\workforce-os'
$Package = Split-Path -Parent $MyInvocation.MyCommand.Path
if (!(Test-Path "$Root\agent\WorkforceOS.ScreenCompanion\Program.cs")) { throw 'Milestone 1 not installed' }
if (!(Get-Command python -ErrorAction SilentlyContinue)) { throw 'Python is required for safe source patching' }
python "$Package\patch.py" "$Root"
if ($LASTEXITCODE -ne 0) { throw 'Patch failed; review output above' }
dotnet build "$Root\agent\WorkforceOS.ScreenCompanion\WorkforceOS.ScreenCompanion.csproj" -c Release
if ($LASTEXITCODE -ne 0) { throw 'Build failed: restore backup in artifacts\backups\live-screen-3b' }
Write-Host 'PASS: Milestone 3B sender+viewer source installed and C# built.'
Write-Host 'IMPORTANT: Relay is a separate DEV service. Setup in README; no production authorization integration.'
