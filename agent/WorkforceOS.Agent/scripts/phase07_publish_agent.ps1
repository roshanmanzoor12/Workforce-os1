#Requires -Version 5.1

$ErrorActionPreference =
    "Stop"

$ProjectDirectory =
    Split-Path `
        -Parent `
        $PSScriptRoot

$ArtifactsRoot =
    "C:\workforce-os\artifacts\agent\win-x64"

Write-Host ""
Write-Host "============================================"
Write-Host " WorkforceOS Phase 07 Agent Publish"
Write-Host "============================================"
Write-Host ""

Push-Location `
    $ProjectDirectory

try
{
    Write-Host "Project:"
    Write-Host $ProjectDirectory
    Write-Host ""

    Write-Host "Building Release configuration..."

    dotnet build `
        --configuration Release

    if (
        $LASTEXITCODE -ne 0
    )
    {
        throw (
            "Release build failed."
        )
    }

    Write-Host ""
    Write-Host "Cleaning Phase 07 publish directory..."

    if (
        Test-Path $ArtifactsRoot
    )
    {
        Remove-Item `
            $ArtifactsRoot `
            -Recurse `
            -Force
    }

    New-Item `
        -ItemType Directory `
        -Path $ArtifactsRoot `
        -Force `
        | Out-Null

    Write-Host ""
    Write-Host "Publishing win-x64..."

    dotnet publish `
        --configuration Release `
        --runtime win-x64 `
        --self-contained false `
        --output $ArtifactsRoot

    if (
        $LASTEXITCODE -ne 0
    )
    {
        throw (
            "Agent publish failed."
        )
    }

    $Executable =
        Join-Path `
            $ArtifactsRoot `
            "WorkforceOS.Agent.exe"

    if (
        -not (
            Test-Path $Executable
        )
    )
    {
        throw (
            "Published WorkforceOS.Agent.exe was not found."
        )
    }

    $ExecutableInfo =
        Get-Item $Executable

    if (
        $ExecutableInfo.Length
        -le 0
    )
    {
        throw (
            "Published WorkforceOS.Agent.exe is empty."
        )
    }

    Write-Host ""
    Write-Host "Published executable:"
    Write-Host $Executable

    Write-Host ""
    Write-Host "Executable size:"
    Write-Host $ExecutableInfo.Length

    Write-Host ""
    Write-Host "============================================"
    Write-Host " PHASE 07 AGENT PUBLISH: PASS"
    Write-Host "============================================"
    Write-Host ""
}
finally
{
    Pop-Location
}