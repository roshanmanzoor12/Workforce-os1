$ErrorActionPreference = "Stop"

$ProjectDirectory =
    Split-Path `
        -Parent `
        $PSScriptRoot

$ProjectFile =
    Join-Path `
        $ProjectDirectory `
        "WorkforceOS.Agent.csproj"

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

Write-Host ""
Write-Host "WorkforceOS Agent Publish"
Write-Host "========================="
Write-Host ""

if (
    -not (
        Test-Path `
            $ProjectFile
    )
)
{
    throw "WorkforceOS.Agent.csproj was not found."
}

$DotNet =
    Get-Command `
        dotnet `
        -ErrorAction Stop

Write-Host "dotnet:"
Write-Host $DotNet.Source
Write-Host ""

Write-Host "Stopping interactive WorkforceOS Agent process if running..."

Stop-Process `
    -Name "WorkforceOS.Agent" `
    -Force `
    -ErrorAction SilentlyContinue

Write-Host "Cleaning publish directory..."

if (
    Test-Path `
        $PublishDirectory
)
{
    Remove-Item `
        -Recurse `
        -Force `
        $PublishDirectory
}

New-Item `
    -ItemType Directory `
    -Force `
    $PublishDirectory |
    Out-Null

Write-Host ""
Write-Host "Building Release configuration..."

Push-Location `
    $ProjectDirectory

try
{
    dotnet build `
        $ProjectFile `
        --configuration Release

    if (
        $LASTEXITCODE -ne 0
    )
    {
        throw "Release build failed."
    }

    Write-Host ""
    Write-Host "Publishing win-x64 agent..."

    dotnet publish `
        $ProjectFile `
        --configuration Release `
        --runtime win-x64 `
        --self-contained false `
        --output $PublishDirectory `
        --no-build

    if (
        $LASTEXITCODE -ne 0
    )
    {
        throw "Agent publish failed."
    }
}
finally
{
    Pop-Location
}

$ExecutablePath =
    Join-Path `
        $PublishDirectory `
        "WorkforceOS.Agent.exe"

if (
    -not (
        Test-Path `
            $ExecutablePath
    )
)
{
    throw "Published WorkforceOS.Agent.exe was not found."
}

Write-Host ""
Write-Host "Publish completed successfully."
Write-Host ""
Write-Host "Executable:"
Write-Host $ExecutablePath
Write-Host ""

Get-ChildItem `
    $PublishDirectory |
    Select-Object `
        Name,
        Length