#Requires -Version 5.1
$ErrorActionPreference = 'Stop'
$RunKey = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run'
$ValueName = 'WorkforceOSScreenCompanion'
$Backup = Join-Path $PSScriptRoot 'previous-run-value.txt'
if (Test-Path -LiteralPath $Backup) {
    $Previous = [IO.File]::ReadAllText($Backup)
    New-ItemProperty -Path $RunKey -Name $ValueName -PropertyType String -Value $Previous -Force | Out-Null
    Write-Host 'Restored previous auto-launch value.'
} else {
    Remove-ItemProperty -Path $RunKey -Name $ValueName -ErrorAction SilentlyContinue
    Write-Host 'Removed WorkforceOS companion auto-launch for this user.'
}
