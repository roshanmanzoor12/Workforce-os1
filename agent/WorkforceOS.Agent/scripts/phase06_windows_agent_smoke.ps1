#Requires -RunAsAdministrator

$ErrorActionPreference = "Stop"

$ServiceName =
    "WorkforceOSAgent"

$ExpectedServiceIdentity =
    "LocalSystem"

$ProjectDirectory =
    Split-Path `
        -Parent `
        $PSScriptRoot

$RepositoryRoot =
    Resolve-Path `
        (
            Join-Path `
                $ProjectDirectory `
                "..\..\"
        )

$PublishDirectory =
    Join-Path `
        $RepositoryRoot `
        "artifacts\agent\win-x64"

$ExecutablePath =
    Join-Path `
        $PublishDirectory `
        "WorkforceOS.Agent.exe"

$ProgramDataDirectory =
    Join-Path `
        $env:ProgramData `
        "WorkforceOS\Agent"

$CredentialFile =
    Join-Path `
        $ProgramDataDirectory `
        "device-credentials.dat"

$AgentIdentifierFile =
    Join-Path `
        $ProgramDataDirectory `
        "agent-id"


function Write-Step
{
    param(
        [Parameter(Mandatory = $true)]
        [string] $Message
    )

    Write-Host ""
    Write-Host "==> $Message"
}


function Assert-True
{
    param(
        [Parameter(Mandatory = $true)]
        [bool] $Condition,

        [Parameter(Mandatory = $true)]
        [string] $Message
    )

    if (
        -not $Condition
    )
    {
        throw $Message
    }
}


function Wait-ServiceRunning
{
    param(
        [Parameter(Mandatory = $true)]
        [string] $Name,

        [int] $TimeoutSeconds = 30
    )

    $Deadline =
        (Get-Date).AddSeconds(
            $TimeoutSeconds
        )

    while (
        (Get-Date) -lt $Deadline
    )
    {
        $Service =
            Get-Service `
                -Name $Name `
                -ErrorAction Stop

        if (
            $Service.Status `
                -eq "Running"
        )
        {
            return
        }

        Start-Sleep `
            -Milliseconds 500
    }

    throw (
        "Service '$Name' did not enter Running state " +
        "within $TimeoutSeconds seconds."
    )
}


Write-Host ""
Write-Host "=========================================="
Write-Host " WorkforceOS Phase 06 Windows Agent Smoke "
Write-Host "=========================================="
Write-Host ""


# =========================================================
# 1. PUBLISHED AGENT
# =========================================================

Write-Step "Checking published WorkforceOS Agent"

Assert-True `
    -Condition (
        Test-Path `
            $ExecutablePath
    ) `
    -Message (
        "Published WorkforceOS.Agent.exe was not found: " +
        $ExecutablePath
    )

$PublishedExecutable =
    Get-Item `
        $ExecutablePath

Assert-True `
    -Condition (
        $PublishedExecutable.Length -gt 0
    ) `
    -Message "Published WorkforceOS.Agent.exe is empty."

Write-Host "Published executable:"
Write-Host $ExecutablePath


# =========================================================
# 2. WINDOWS SERVICE EXISTS
# =========================================================

Write-Step "Checking Windows Service"

$Service =
    Get-Service `
        -Name $ServiceName `
        -ErrorAction Stop

Assert-True `
    -Condition (
        $null -ne $Service
    ) `
    -Message "WorkforceOSAgent service does not exist."

Write-Host "Service found:"
Write-Host $Service.DisplayName


# =========================================================
# 3. SERVICE CONFIGURATION
# =========================================================

Write-Step "Checking Windows Service configuration"

$ServiceConfiguration =
    Get-CimInstance `
        Win32_Service `
        -Filter "Name='$ServiceName'"

Assert-True `
    -Condition (
        $null -ne $ServiceConfiguration
    ) `
    -Message "Unable to read WorkforceOSAgent service configuration."

Assert-True `
    -Condition (
        $ServiceConfiguration.StartMode `
            -eq "Auto"
    ) `
    -Message (
        "WorkforceOSAgent startup mode is not Automatic. " +
        "Actual: $($ServiceConfiguration.StartMode)"
    )

Assert-True `
    -Condition (
        $ServiceConfiguration.StartName `
            -eq $ExpectedServiceIdentity
    ) `
    -Message (
        "WorkforceOSAgent is not running as LocalSystem. " +
        "Actual identity: $($ServiceConfiguration.StartName)"
    )

$NormalizedServicePath =
    $ServiceConfiguration.PathName.Trim(
        '"'
    )

Assert-True `
    -Condition (
        $NormalizedServicePath `
            -eq $ExecutablePath
    ) `
    -Message (
        "WorkforceOSAgent executable path does not match " +
        "the published agent. Actual: " +
        $ServiceConfiguration.PathName
    )

Write-Host "Startup mode: Automatic"
Write-Host "Service identity: LocalSystem"
Write-Host "Executable path verified"


# =========================================================
# 4. PROGRAMDATA FILES
# =========================================================

Write-Step "Checking persistent agent data"

Assert-True `
    -Condition (
        Test-Path `
            $ProgramDataDirectory
    ) `
    -Message (
        "WorkforceOS ProgramData directory does not exist: " +
        $ProgramDataDirectory
    )

Assert-True `
    -Condition (
        Test-Path `
            $CredentialFile
    ) `
    -Message (
        "Device credential file does not exist: " +
        $CredentialFile
    )

Assert-True `
    -Condition (
        Test-Path `
            $AgentIdentifierFile
    ) `
    -Message (
        "Agent identifier file does not exist: " +
        $AgentIdentifierFile
    )

$CredentialFileInfo =
    Get-Item `
        $CredentialFile

$AgentIdentifierFileInfo =
    Get-Item `
        $AgentIdentifierFile

Assert-True `
    -Condition (
        $CredentialFileInfo.Length -gt 0
    ) `
    -Message "Device credential file is empty."

Assert-True `
    -Condition (
        $AgentIdentifierFileInfo.Length -gt 0
    ) `
    -Message "Agent identifier file is empty."

Write-Host "Credential file exists and is non-empty"
Write-Host "Persistent agent identifier file exists and is non-empty"


# =========================================================
# 5. PROGRAMDATA ACL
# =========================================================

Write-Step "Checking ProgramData protection"

$DirectoryAcl =
    Get-Acl `
        $ProgramDataDirectory

Assert-True `
    -Condition (
        $DirectoryAcl.AreAccessRulesProtected
    ) `
    -Message (
        "WorkforceOS ProgramData ACL still inherits permissions. " +
        "Expected inheritance to be disabled."
    )

$SystemRuleFound =
    $false

$AdministratorsRuleFound =
    $false

foreach (
    $Rule
    in $DirectoryAcl.Access
)
{
    $Identity =
        $Rule.IdentityReference.Value

    if (
        $Identity `
            -eq "NT AUTHORITY\SYSTEM"
    )
    {
        $SystemRuleFound =
            $true
    }

    if (
        $Identity `
            -eq "BUILTIN\Administrators"
    )
    {
        $AdministratorsRuleFound =
            $true
    }
}

Assert-True `
    -Condition $SystemRuleFound `
    -Message (
        "SYSTEM permission is missing from " +
        "WorkforceOS ProgramData ACL."
    )

Assert-True `
    -Condition $AdministratorsRuleFound `
    -Message (
        "BUILTIN\Administrators permission is missing from " +
        "WorkforceOS ProgramData ACL."
    )

Write-Host "ACL inheritance disabled"
Write-Host "SYSTEM access present"
Write-Host "Administrators access present"


# =========================================================
# 6. SERVICE RUNNING
# =========================================================

Write-Step "Checking service runtime"

$Service =
    Get-Service `
        -Name $ServiceName

if (
    $Service.Status `
        -ne "Running"
)
{
    Start-Service `
        -Name $ServiceName

    Wait-ServiceRunning `
        -Name $ServiceName `
        -TimeoutSeconds 30
}

$Service =
    Get-Service `
        -Name $ServiceName

Assert-True `
    -Condition (
        $Service.Status `
            -eq "Running"
    ) `
    -Message "WorkforceOSAgent service is not running."

Write-Host "Service is running"


# =========================================================
# 7. SERVICE PROCESS
# =========================================================

Write-Step "Checking WorkforceOS Agent service process"

$ServiceConfiguration =
    Get-CimInstance `
        Win32_Service `
        -Filter "Name='$ServiceName'"

Assert-True `
    -Condition (
        $ServiceConfiguration.ProcessId -gt 0
    ) `
    -Message (
        "WorkforceOSAgent does not have a running process."
    )

$AgentProcess =
    Get-Process `
        -Id $ServiceConfiguration.ProcessId `
        -ErrorAction Stop

Assert-True `
    -Condition (
        $null -ne $AgentProcess
    ) `
    -Message (
        "Unable to resolve the WorkforceOS Agent process."
    )

Write-Host (
    "Service process running with PID: " +
    $ServiceConfiguration.ProcessId
)


# =========================================================
# 8. RESTART PERSISTENCE
# =========================================================

Write-Step "Testing Windows Service restart persistence"

$CredentialLengthBeforeRestart =
    (
        Get-Item `
            $CredentialFile
    ).Length

$AgentIdentifierLengthBeforeRestart =
    (
        Get-Item `
            $AgentIdentifierFile
    ).Length

Restart-Service `
    -Name $ServiceName `
    -Force

Wait-ServiceRunning `
    -Name $ServiceName `
    -TimeoutSeconds 30

Start-Sleep `
    -Seconds 3

$Service =
    Get-Service `
        -Name $ServiceName

Assert-True `
    -Condition (
        $Service.Status `
            -eq "Running"
    ) `
    -Message (
        "WorkforceOSAgent did not remain Running " +
        "after restart."
    )

Assert-True `
    -Condition (
        Test-Path `
            $CredentialFile
    ) `
    -Message (
        "Device credential file disappeared " +
        "after service restart."
    )

Assert-True `
    -Condition (
        Test-Path `
            $AgentIdentifierFile
    ) `
    -Message (
        "Agent identifier file disappeared " +
        "after service restart."
    )

$CredentialLengthAfterRestart =
    (
        Get-Item `
            $CredentialFile
    ).Length

$AgentIdentifierLengthAfterRestart =
    (
        Get-Item `
            $AgentIdentifierFile
    ).Length

Assert-True `
    -Condition (
        $CredentialLengthAfterRestart `
            -eq $CredentialLengthBeforeRestart
    ) `
    -Message (
        "Device credential file changed unexpectedly " +
        "during service restart."
    )

Assert-True `
    -Condition (
        $AgentIdentifierLengthAfterRestart `
            -eq $AgentIdentifierLengthBeforeRestart
    ) `
    -Message (
        "Agent identifier file changed unexpectedly " +
        "during service restart."
    )

Write-Host "Service restart: PASS"
Write-Host "Credential persistence: PASS"
Write-Host "Agent identifier persistence: PASS"


# =========================================================
# 9. POST-RESTART PROCESS
# =========================================================

Write-Step "Checking service process after restart"

$PostRestartConfiguration =
    Get-CimInstance `
        Win32_Service `
        -Filter "Name='$ServiceName'"

Assert-True `
    -Condition (
        $PostRestartConfiguration.ProcessId -gt 0
    ) `
    -Message (
        "WorkforceOSAgent does not have a running " +
        "process after restart."
    )

$PostRestartProcess =
    Get-Process `
        -Id $PostRestartConfiguration.ProcessId `
        -ErrorAction Stop

Assert-True `
    -Condition (
        $null -ne $PostRestartProcess
    ) `
    -Message (
        "Unable to resolve WorkforceOS Agent process " +
        "after restart."
    )

Write-Host (
    "Post-restart service PID: " +
    $PostRestartConfiguration.ProcessId
)


# =========================================================
# 10. SERVICE STABILITY
# =========================================================

Write-Step "Checking short service stability window"

Start-Sleep `
    -Seconds 5

$StableService =
    Get-Service `
        -Name $ServiceName

Assert-True `
    -Condition (
        $StableService.Status `
            -eq "Running"
    ) `
    -Message (
        "WorkforceOSAgent stopped during the " +
        "service stability window."
    )

Write-Host "Service stability: PASS"


# =========================================================
# FINAL RESULT
# =========================================================

Write-Host ""
Write-Host "=========================================="
Write-Host " PHASE 06 WINDOWS AGENT SMOKE TEST: PASS "
Write-Host "=========================================="
Write-Host ""

Write-Host "Validated:"
Write-Host "- Published win-x64 executable"
Write-Host "- Windows Service exists"
Write-Host "- Automatic startup"
Write-Host "- LocalSystem service identity"
Write-Host "- Correct published executable path"
Write-Host "- Persistent agent identifier file"
Write-Host "- Persistent protected credential file"
Write-Host "- Restricted ProgramData ACL"
Write-Host "- Running Windows Service process"
Write-Host "- Windows Service restart"
Write-Host "- Credential persistence after restart"
Write-Host "- Agent identifier persistence after restart"
Write-Host "- Post-restart process recovery"
Write-Host "- Service stability"
Write-Host ""