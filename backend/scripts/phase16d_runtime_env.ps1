# =========================================================
# WorkforceOS Phase 16D Runtime Environment
# =========================================================


# ---------------------------------------------------------
# API
# ---------------------------------------------------------

if (
    [string]::IsNullOrWhiteSpace(
        $env:WF_API_BASE
    )
)
{
    $env:WF_API_BASE = (
        "http://127.0.0.1:8001/api/v1"
    )
}


# ---------------------------------------------------------
# WEBSOCKET BASE
# ---------------------------------------------------------

if (
    [string]::IsNullOrWhiteSpace(
        $env:WF_WS_BASE
    )
)
{
    $env:WF_WS_BASE = (
        "ws://127.0.0.1:8001"
    )
}


# ---------------------------------------------------------
# WEBSOCKET CHANNEL PATH
# ---------------------------------------------------------

if (
    [string]::IsNullOrWhiteSpace(
        $env:WF_CHANNEL_WS_PATH
    )
)
{
    $env:WF_CHANNEL_WS_PATH = (
        "/api/v1/workspaces/{workspace_id}" +
        "/channels/{channel_id}/realtime/ws"
    )
}


# ---------------------------------------------------------
# WORKSPACE
# ---------------------------------------------------------

if (
    [string]::IsNullOrWhiteSpace(
        $env:WF_WORKSPACE_ID
    )
)
{
    $env:WF_WORKSPACE_ID = (
        "34527ffb-e094-4e5e-89ee-4cab97244fc3"
    )
}


# ---------------------------------------------------------
# CHANNEL
# ---------------------------------------------------------

if (
    [string]::IsNullOrWhiteSpace(
        $env:WF_CHANNEL_ID
    )
)
{
    $env:WF_CHANNEL_ID = (
        "58672c60-400d-428a-bdca-f4e611e3d845"
    )
}


# ---------------------------------------------------------
# OPTIONAL MESSAGE
# ---------------------------------------------------------

if ($null -eq $env:WF_MESSAGE_ID)
{
    $env:WF_MESSAGE_ID = ""
}


# ---------------------------------------------------------
# TIMEOUTS
# ---------------------------------------------------------

if (
    [string]::IsNullOrWhiteSpace(
        $env:WF_WS_TIMEOUT_SECONDS
    )
)
{
    $env:WF_WS_TIMEOUT_SECONDS = "12"
}


if (
    [string]::IsNullOrWhiteSpace(
        $env:WF_REPLAY_TIMEOUT_SECONDS
    )
)
{
    $env:WF_REPLAY_TIMEOUT_SECONDS = "15"
}


if (
    [string]::IsNullOrWhiteSpace(
        $env:WF_READ_UNREAD_POLL_SECONDS
    )
)
{
    $env:WF_READ_UNREAD_POLL_SECONDS = "8"
}


# ---------------------------------------------------------
# IMPORTANT
# ---------------------------------------------------------
#
# Do NOT assign WF_TOKEN_A or WF_TOKEN_B here.
#
# They are intentionally preserved from the current shell.
# Fresh authentication tokens should be supplied separately.
#
# ---------------------------------------------------------


Write-Host ""
Write-Host "Phase 16D environment loaded."
Write-Host ""