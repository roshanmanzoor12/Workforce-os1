$ErrorActionPreference = "Stop"


$BaseUrl = "http://127.0.0.1:8001"


if (
    [string]::IsNullOrWhiteSpace(
        $env:WORKFORCE_TEST_WORKSPACE_ID
    )
)
{
    throw (
        "Set WORKFORCE_TEST_WORKSPACE_ID " +
        "before running this script."
    )
}


if (
    [string]::IsNullOrWhiteSpace(
        $env:WORKFORCE_TEST_TOKEN
    )
)
{
    throw (
        "Set WORKFORCE_TEST_TOKEN before " +
        "running this script."
    )
}


$WorkspaceId = (
    $env:WORKFORCE_TEST_WORKSPACE_ID
)


$Headers = @{
    Authorization = (
        "Bearer " +
        $env:WORKFORCE_TEST_TOKEN
    )
}


$Paths = @(
    "overview",
    "activity",
    "attendance",
    "productivity",
    "apps",
    "websites",
    "goals",
    "trends"
)


Write-Host "================================================="
Write-Host " WorkforceOS Phase 12.4 Runtime Smoke"
Write-Host "================================================="
Write-Host ""

Write-Host (
    "Workspace: " +
    $WorkspaceId
)

Write-Host ""


foreach ($Path in $Paths)
{
    $Uri = (
        $BaseUrl +
        "/api/v1/workspaces/" +
        $WorkspaceId +
        "/analytics/" +
        $Path
    )

    Write-Host (
        "[GET] " +
        $Uri
    )

    try
    {
        $Response = Invoke-RestMethod `
            -Method Get `
            -Uri $Uri `
            -Headers $Headers `
            -ContentType "application/json"

        if ($null -eq $Response)
        {
            throw (
                "Empty analytics response: " +
                $Path
            )
        }

        Write-Host (
            "PASS " +
            $Path
        )
    }
    catch
    {
        Write-Host ""
        Write-Host (
            "FAIL " +
            $Path
        )

        Write-Host (
            $_.Exception.Message
        )

        throw
    }

    Write-Host ""
}


Write-Host "================================================="
Write-Host " PHASE 12.4 ANALYTICS RUNTIME SMOKE: PASS"
Write-Host "================================================="
Write-Host "Overview:       PASS"
Write-Host "Activity:       PASS"
Write-Host "Attendance:     PASS"
Write-Host "Productivity:   PASS"
Write-Host "Apps:           PASS"
Write-Host "Websites:       PASS"
Write-Host "Goals:          PASS"
Write-Host "Trends:         PASS"
Write-Host "================================================="