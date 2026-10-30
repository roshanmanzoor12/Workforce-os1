param(
    [ValidateSet('Stage','Deploy','Verify')]
    [string]$Mode = 'Stage',
    [string]$Root = 'C:\workforce-os'
)
$ErrorActionPreference = 'Stop'
$dotnet = 'C:\Program Files\dotnet\dotnet.exe'
$project = Join-Path $Root 'agent\WorkforceOS.Agent\WorkforceOS.Agent.csproj'
$tests = Join-Path $Root 'agent\WorkforceOS.Agent.Tests\WorkforceOS.Agent.Tests.csproj'
$installed = Join-Path $Root 'artifacts\agent\win-x64'
$staged = Join-Path $Root 'artifacts\agent\staged-win-x64'
$backups = Join-Path $Root 'backups'
function Assert-Success($label) { if ($LASTEXITCODE -ne 0) { throw "$label failed ($LASTEXITCODE)" } }
function Hash-Agent($folder) {
    $dll = Join-Path $folder 'WorkforceOS.Agent.dll'
    if (Test-Path $dll) { (Get-FileHash -LiteralPath $dll -Algorithm SHA256).Hash } else { 'DLL missing' }
}
if ($Mode -eq 'Stage') {
    if (-not (Test-Path $dotnet)) { throw 'Install .NET 8 SDK first.' }
    & $dotnet test $tests --configuration Release; Assert-Success 'Agent tests'
    # Publish to a NEW directory: do not modify installed executable or credentials.
    if (Test-Path $staged) { Remove-Item $staged -Recurse -Force }
    & $dotnet publish $project --configuration Release --runtime win-x64 --no-self-contained --output $staged
    Assert-Success 'Agent publish'
    Write-Host "STAGED: $staged" -ForegroundColor Green
    Write-Host "Staged DLL SHA256: $(Hash-Agent $staged)"
    Write-Host "Installed DLL SHA256: $(Hash-Agent $installed)"
    Write-Host 'No running agent processes or installed files were changed.'
    exit 0
}
if ($Mode -eq 'Deploy') {
    $principal = [Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
    if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { throw 'Run PowerShell as Administrator for Deploy.' }
    if (-not (Test-Path (Join-Path $staged 'WorkforceOS.Agent.dll'))) { throw 'Run -Mode Stage first.' }
    $service = Get-Service WorkforceOSAgent -ErrorAction Stop
    if ($service.Status -ne 'Stopped') { throw 'Stop the Windows service before deployment.' }
    $processes = @(Get-CimInstance Win32_Process | Where-Object {
        $_.Name -in @('WorkforceOS.Agent.exe', 'WorkforceOS.WebsiteNativeHost.exe')
    })
    if ($processes.Count -gt 0) {
        $processes | Select-Object ProcessId,ParentProcessId,Name,ExecutablePath | Format-Table -AutoSize
        throw 'Agent or Native Host running: close native-host/browser session and stop Agent safely, then rerun Deploy. No processes were killed.'
    }
    if (-not (Test-Path $installed)) { throw "Install directory missing: $installed" }
    $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
    $backup = Join-Path $backups "agent-deploy-$stamp"
    New-Item -ItemType Directory -Path $backup -Force | Out-Null
    foreach ($item in (Get-ChildItem -LiteralPath $installed -Force)) { Copy-Item -LiteralPath $item.FullName -Destination $backup -Recurse -Force -ErrorAction Stop }
    # Preserve deployed environment-specific configuration, and avoid resetting enrollment.
    $items = Get-ChildItem -LiteralPath $staged -Force | Where-Object {
        $_.Name -notin @('appsettings.json','appsettings.Development.json')
    }
    foreach ($item in $items) { Copy-Item -LiteralPath $item.FullName -Destination $installed -Recurse -Force }
    Write-Host "BACKUP: $backup" -ForegroundColor Green
    Write-Host "INSTALLED SHA256: $(Hash-Agent $installed)"
    Write-Host "STAGED SHA256: $(Hash-Agent $staged)"
    Write-Host 'Deploy complete. Service was NOT auto-started; start it after validating its intended runtime identity.'
    exit 0
}
if ($Mode -eq 'Verify') {
    Write-Host "Installed DLL SHA256: $(Hash-Agent $installed)"
    Write-Host "Staged DLL SHA256: $(Hash-Agent $staged)"
    Get-CimInstance Win32_Service -Filter "Name='WorkforceOSAgent'" | Select-Object Name,State,StartMode,StartName,ProcessId
    Get-CimInstance Win32_Process | Where-Object { $_.Name -in @('WorkforceOS.Agent.exe','WorkforceOS.WebsiteNativeHost.exe') } | Select-Object ProcessId,ParentProcessId,Name,ExecutablePath
    exit 0
}
