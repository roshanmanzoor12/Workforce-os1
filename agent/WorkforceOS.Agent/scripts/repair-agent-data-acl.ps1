#Requires -RunAsAdministrator
#Requires -Version 5.1

$ErrorActionPreference = "Stop"

$AgentDataDirectory =
    "C:\ProgramData\WorkforceOS\Agent"

$CredentialFile =
    Join-Path `
        $AgentDataDirectory `
        "device-credentials.dat"

$AgentIdFile =
    Join-Path `
        $AgentDataDirectory `
        "agent-id"

Write-Host ""
Write-Host "============================================="
Write-Host " WorkforceOS Agent Data ACL Repair"
Write-Host "============================================="
Write-Host ""

if (-not (Test-Path $AgentDataDirectory))
{
    throw (
        "WorkforceOS Agent data directory does not exist: " +
        $AgentDataDirectory
    )
}

# =========================================================
# DIRECTORY
# =========================================================

icacls `
    $AgentDataDirectory `
    /inheritance:r `
    /grant:r `
    "SYSTEM:(OI)(CI)F" `
    "BUILTIN\Administrators:(OI)(CI)F"

if ($LASTEXITCODE -ne 0)
{
    throw "Unable to secure WorkforceOS Agent data directory."
}

# =========================================================
# AGENT ID
# =========================================================

if (Test-Path $AgentIdFile)
{
    takeown `
        /F $AgentIdFile `
        /A `
        | Out-Null

    if ($LASTEXITCODE -ne 0)
    {
        throw "Unable to take ownership of WorkforceOS agent-id."
    }

    icacls `
        $AgentIdFile `
        /inheritance:r `
        /grant:r `
        "SYSTEM:F" `
        "BUILTIN\Administrators:F"

    if ($LASTEXITCODE -ne 0)
    {
        throw "Unable to secure WorkforceOS agent-id."
    }
}

# =========================================================
# DEVICE CREDENTIALS
# =========================================================

if (Test-Path $CredentialFile)
{
    takeown `
        /F $CredentialFile `
        /A `
        | Out-Null

    if ($LASTEXITCODE -ne 0)
    {
        throw "Unable to take ownership of device credentials."
    }

    icacls `
        $CredentialFile `
        /inheritance:r `
        /grant:r `
        "SYSTEM:F" `
        "BUILTIN\Administrators:F"

    if ($LASTEXITCODE -ne 0)
    {
        throw "Unable to secure device credentials."
    }
}

Write-Host ""
Write-Host "Agent data directory:"
icacls $AgentDataDirectory

if (Test-Path $AgentIdFile)
{
    Write-Host ""
    Write-Host "Agent ID:"
    icacls $AgentIdFile
}

if (Test-Path $CredentialFile)
{
    Write-Host ""
    Write-Host "Device credentials:"
    icacls $CredentialFile
}

Write-Host ""
Write-Host "============================================="
Write-Host " WORKFORCEOS AGENT DATA ACL: PASS"
Write-Host "============================================="
Write-Host ""