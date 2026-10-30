# =========================================================
# WorkforceOS Phase 16D Runtime Certification Environment
# =========================================================
#
# Copy this file to:
#
#   phase16d_runtime_env.ps1
#
# Then fill the values from your local test accounts.
#
# DO NOT commit real bearer tokens.
# =========================================================


$env:WF_API_BASE =
    "http://127.0.0.1:8000/api/v1"


$env:WF_WS_BASE =
    "ws://127.0.0.1:8000"


# ---------------------------------------------------------
# Authenticated user A
# ---------------------------------------------------------

$env:WF_TOKEN_A =
    ""


# ---------------------------------------------------------
# Authenticated user B
#
# Must be a different authenticated user who is also
# permitted to access the test workspace/channel.
# ---------------------------------------------------------

$env:WF_TOKEN_B =
    ""


# ---------------------------------------------------------
# Workspace/channel under test
# ---------------------------------------------------------

$env:WF_WORKSPACE_ID =
    ""


$env:WF_CHANNEL_ID =
    ""


# ---------------------------------------------------------
# Optional known message.
#
# Leave blank for tests that create their own message.
# ---------------------------------------------------------

$env:WF_MESSAGE_ID =
    ""


# ---------------------------------------------------------
# Runtime timings
# ---------------------------------------------------------

$env:WF_WS_TIMEOUT_SECONDS =
    "12"


$env:WF_REPLAY_TIMEOUT_SECONDS =
    "15"


Write-Host ""
Write-Host "Phase 16D environment loaded."
Write-Host ""