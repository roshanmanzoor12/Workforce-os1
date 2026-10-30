$script:Phase18BackendRoot = (
    Resolve-Path (
        Join-Path `
            $PSScriptRoot `
            ".."
    )
).Path


$script:Phase18Python = Join-Path `
    $script:Phase18BackendRoot `
    ".venv\Scripts\python.exe"


function Fail-Phase18
{
    param(
        [Parameter(Mandatory = $true)]
        [string] $Message
    )

    Write-Host ""
    Write-Host "FAIL:" $Message
    Write-Host ""

    exit 1
}


function Assert-Phase18File
{
    param(
        [Parameter(Mandatory = $true)]
        [string] $Path
    )

    if (-not (Test-Path $Path))
    {
        Fail-Phase18 (
            "Missing required file: {0}" `
                -f $Path
        )
    }
}


function Assert-Phase18Contains
{
    param(
        [Parameter(Mandatory = $true)]
        [string] $Path,

        [Parameter(Mandatory = $true)]
        [string[]] $Tokens
    )

    Assert-Phase18File `
        -Path $Path

    $Source = Get-Content `
        $Path `
        -Raw

    foreach ($Token in $Tokens)
    {
        if (
            $Source.IndexOf(
                $Token,
                [System.StringComparison]::Ordinal
            ) -lt 0
        )
        {
            Fail-Phase18 (
                "Required token '{0}' missing from {1}" `
                    -f $Token, $Path
            )
        }
    }
}


function Find-Phase18LegacyGate
{
    param(
        [Parameter(Mandatory = $true)]
        [string] $Regex
    )

    $ScriptsRoot = Join-Path `
        $script:Phase18BackendRoot `
        "scripts"

    $Candidates = @(
        Get-ChildItem `
            -Path $ScriptsRoot `
            -Filter "*.ps1" `
            -File |
        Where-Object {
            $_.Name -notlike "phase18_*"
        } |
        Sort-Object Name
    )

    foreach ($Candidate in $Candidates)
    {
        $Source = ""

        try
        {
            $Source = Get-Content `
                $Candidate.FullName `
                -Raw `
                -ErrorAction Stop
        }
        catch
        {
            continue
        }

        $SearchText = (
            $Candidate.Name +
            "`n" +
            $Source
        )

        if (
            [regex]::IsMatch(
                $SearchText,
                $Regex
            )
        )
        {
            return $Candidate.FullName
        }
    }

    return $null
}


function Invoke-Phase18LegacyGate
{
    param(
        [Parameter(Mandatory = $true)]
        [string] $Regex,

        [Parameter(Mandatory = $true)]
        [string] $Label
    )

    $Gate = Find-Phase18LegacyGate `
        -Regex $Regex

    if ($null -eq $Gate)
    {
        Fail-Phase18 (
            "Could not discover certified legacy gate for: {0}" `
                -f $Label
        )
    }

    Write-Host "Selected gate:"
    Write-Host $Gate
    Write-Host ""

    & powershell.exe `
        -NoProfile `
        -ExecutionPolicy Bypass `
        -File $Gate

    if ($LASTEXITCODE -ne 0)
    {
        Fail-Phase18 (
            "{0} failed with exit code {1}" `
                -f $Label, $LASTEXITCODE
        )
    }

    Write-Host "PASS:" $Label
}


function Invoke-Phase18Pytest
{
    param(
        [Parameter(Mandatory = $true)]
        [string[]] $Tests,

        [Parameter(Mandatory = $true)]
        [string] $Label
    )

    foreach ($Test in $Tests)
    {
        Assert-Phase18File `
            -Path $Test
    }

    & $script:Phase18Python `
        -m pytest `
        @Tests `
        -q

    if ($LASTEXITCODE -ne 0)
    {
        Fail-Phase18 (
            "{0} failed." `
                -f $Label
        )
    }

    Write-Host "PASS:" $Label
}