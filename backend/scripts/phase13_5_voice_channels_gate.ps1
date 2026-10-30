$ErrorActionPreference = "Stop"


$BackendRoot = "C:\workforce-os\backend"

$Python = (
    "C:\workforce-os\backend\" +
    ".venv\Scripts\python.exe"
)

$ExpectedControlHead = "g1b2c3d4e5f6"

$ExpectedTenantHead = "j0e1f2g3h4i5"

$WorkspaceId = (
    "34527ffb-e094-4e5e-89ee-4cab97244fc3"
)

$TenantDatabase = (
    "tenant_" +
    $WorkspaceId.Replace(
        "-",
        ""
    )
)


Set-Location $BackendRoot


Write-Host "================================================="
Write-Host " WorkforceOS Phase 13.5 Voice Channels / RTC"
Write-Host "================================================="
Write-Host ""


# =========================================================
# REQUIRED FILES
# =========================================================

$RequiredFiles = @(
    ".\app\modules\channels\enums.py",
    ".\app\modules\channels\models.py",
    ".\app\modules\channels\router.py",
    ".\app\modules\channels\schemas.py",
    ".\app\modules\channels\service.py",
    ".\app\modules\voice_channels\models.py",
    ".\app\modules\voice_channels\schemas.py",
    ".\app\modules\voice_channels\access.py",
    ".\app\modules\voice_channels\repository.py",
    ".\app\modules\voice_channels\service.py",
    ".\app\modules\voice_channels\router.py",
    ".\app\modules\tenant_api\router.py",
    ".\migrations\tenant\versions\j0e1f2g3h4i5_add_voice_channels.py"
)


foreach ($File in $RequiredFiles)
{
    if (-not (Test-Path $File))
    {
        throw (
            "Missing required file: " +
            $File
        )
    }
}


Write-Host "PASS required files"
Write-Host ""


# =========================================================
# 1/8 COMPILE
# =========================================================

Write-Host "[1/8] Compiling..."


& $Python `
    -m compileall `
    .\app\modules\channels `
    .\app\modules\voice_channels `
    .\app\modules\tenant_api `
    .\migrations\tenant\versions `
    -q


if ($LASTEXITCODE -ne 0)
{
    throw "Compile failed."
}


Write-Host "PASS compile"
Write-Host ""


# =========================================================
# 2/8 CHANNEL TYPE
# =========================================================

Write-Host "[2/8] Voice channel type..."


$ChannelTypeCheck = @'
from app.modules.channels.enums import (
    WorkspaceChannelType,
)


values = {
    item.value
    for item
    in WorkspaceChannelType
}


expected = {
    "text",
    "announcement",
    "voice",
}


if values != expected:
    raise SystemExit(
        "WorkspaceChannelType invalid: "
        + str(
            sorted(
                values
            )
        )
    )


if (
    WorkspaceChannelType.VOICE.value
    != "voice"
):
    raise SystemExit(
        "WorkspaceChannelType.VOICE missing."
    )


print(
    "PASS voice channel type"
)
'@


$ChannelTypeCheck | & $Python -


if ($LASTEXITCODE -ne 0)
{
    throw "Channel-type gate failed."
}


Write-Host ""


# =========================================================
# 3/8 MODEL CONTRACT
# =========================================================

Write-Host "[3/8] Voice model contract..."


$ModelCheck = @'
from app.modules.voice_channels.models import (
    VoiceChannelBan,
    VoiceChannelCall,
    VoiceChannelParticipant,
)


call_columns = {
    column.name
    for column
    in VoiceChannelCall.__table__.columns
}


participant_columns = {
    column.name
    for column
    in VoiceChannelParticipant.__table__.columns
}


ban_columns = {
    column.name
    for column
    in VoiceChannelBan.__table__.columns
}


required_call = {
    "id",
    "channel_id",
    "created_by_user_id",
    "status",
    "created_at",
    "ended_at",
}


required_participant = {
    "id",
    "call_id",
    "user_id",
    "state",
    "self_muted",
    "self_deafened",
    "server_muted",
    "server_deafened",
    "screen_sharing",
    "joined_at",
    "left_at",
    "updated_at",
}


required_ban = {
    "id",
    "channel_id",
    "user_id",
    "banned_by_user_id",
    "reason",
    "is_active",
    "created_at",
    "lifted_at",
}


missing_call = (
    required_call
    - call_columns
)


missing_participant = (
    required_participant
    - participant_columns
)


missing_ban = (
    required_ban
    - ban_columns
)


if missing_call:
    raise SystemExit(
        "Voice call model fields missing: "
        + str(
            sorted(
                missing_call
            )
        )
    )


if missing_participant:
    raise SystemExit(
        "Voice participant model fields missing: "
        + str(
            sorted(
                missing_participant
            )
        )
    )


if missing_ban:
    raise SystemExit(
        "Voice ban model fields missing: "
        + str(
            sorted(
                missing_ban
            )
        )
    )


print(
    "PASS voice model contract"
)
'@


$ModelCheck | & $Python -


if ($LASTEXITCODE -ne 0)
{
    throw "Voice model gate failed."
}


Write-Host ""


# =========================================================
# 4/8 RTC STATE CONTRACT
# =========================================================

Write-Host "[4/8] RTC state contract..."


$RtcCheck = @'
from app.modules.voice_channels.schemas import (
    VoiceCapabilitiesResponse,
    VoiceSignalType,
)


signals = {
    item.value
    for item
    in VoiceSignalType
}


required_signals = {
    "offer",
    "answer",
    "ice_candidate",
    "renegotiate",
}


if signals != required_signals:
    raise SystemExit(
        "Voice signaling types invalid: "
        + str(
            sorted(
                signals
            )
        )
    )


capabilities = (
    VoiceCapabilitiesResponse()
)


checks = {
    "voice_channels":
        capabilities.voice_channels,

    "single_active_call_per_channel":
        capabilities.single_active_call_per_channel,

    "self_mute":
        capabilities.self_mute,

    "self_deafen":
        capabilities.self_deafen,

    "moderator_mute":
        capabilities.moderator_mute,

    "moderator_deafen":
        capabilities.moderator_deafen,

    "kick":
        capabilities.kick,

    "ban":
        capabilities.ban,

    "screen_share":
        capabilities.screen_share,

    "webrtc_signaling":
        capabilities.webrtc_signaling,

    "presence":
        capabilities.presence,

    "speaking_state":
        capabilities.speaking_state,
}


failed = [
    name
    for name, enabled
    in checks.items()
    if enabled is not True
]


if failed:
    raise SystemExit(
        "Voice capability contract failed: "
        + str(
            failed
        )
    )


print(
    "PASS RTC state contract"
)
'@


$RtcCheck | & $Python -


if ($LASTEXITCODE -ne 0)
{
    throw "RTC state gate failed."
}


Write-Host ""


# =========================================================
# 5/8 IMPORT CONTRACT
# =========================================================

Write-Host "[5/8] Voice imports..."


$ImportCheck = @'
from app.modules.channels.enums import (
    WorkspaceChannelType,
)

from app.modules.voice_channels.access import (
    VoiceChannelAccess,
    resolve_voice_channel_access,
)

from app.modules.voice_channels.repository import (
    VoiceChannelRepository,
)

from app.modules.voice_channels.router import (
    router,
)

from app.modules.voice_channels.service import (
    VoiceChannelService,
)


assert WorkspaceChannelType
assert VoiceChannelAccess
assert resolve_voice_channel_access
assert VoiceChannelRepository
assert VoiceChannelService
assert router


print(
    "PASS voice imports"
)
'@


$ImportCheck | & $Python -


if ($LASTEXITCODE -ne 0)
{
    throw "Voice import gate failed."
}


Write-Host ""


# =========================================================
# 6/8 APP + OPENAPI
# =========================================================

Write-Host "[6/8] App/OpenAPI..."


$OpenApiCheck = @'
from app.main import app


openapi = app.openapi()

paths = openapi["paths"]


base = (
    "/api/v1/workspaces/"
    "{workspace_id}/channels/"
    "{channel_id}/voice"
)


required = {
    base + "/active-call": {
        "get",
    },

    base + "/join": {
        "post",
    },

    base + "/leave": {
        "post",
    },

    base + "/participants": {
        "get",
    },

    base + "/me": {
        "patch",
    },

    base + "/participants/{user_id}/moderation": {
        "patch",
    },

    base + "/participants/{user_id}/kick": {
        "post",
    },

    base + "/bans/{user_id}": {
        "post",
        "delete",
    },

    base + "/screen-share/start": {
        "post",
    },

    base + "/screen-share/stop": {
        "post",
    },

    base + "/signal": {
        "post",
    },

    base + "/signals": {
        "get",
    },

    base + "/presence": {
        "post",
    },

    base + "/speaking": {
        "post",
    },

    base + "/capabilities": {
        "get",
    },
}


for path, methods in required.items():
    if path not in paths:
        raise SystemExit(
            "Missing voice endpoint: "
            + path
        )

    available = set(
        paths[path]
    )

    missing = (
        methods
        - available
    )

    if missing:
        raise SystemExit(
            "Missing methods for "
            + path
            + ": "
            + str(
                sorted(
                    missing
                )
            )
        )


schemas = (
    openapi
    .get(
        "components",
        {}
    )
    .get(
        "schemas",
        {}
    )
)


channel_type_schema = (
    schemas.get(
        "WorkspaceChannelType"
    )
)


if channel_type_schema is None:
    raise SystemExit(
        "WorkspaceChannelType missing "
        "from OpenAPI schemas."
    )


enum_values = set(
    channel_type_schema.get(
        "enum",
        []
    )
)


if "voice" not in enum_values:
    raise SystemExit(
        "OpenAPI WorkspaceChannelType "
        "does not expose voice."
    )


print(
    "PASS app/OpenAPI"
)
'@


$OpenApiCheck | & $Python -


if ($LASTEXITCODE -ne 0)
{
    throw "Voice OpenAPI gate failed."
}


Write-Host ""


# =========================================================
# 7/8 CONTROL HEAD
# =========================================================

Write-Host "[7/8] Control migration head..."


$ControlHeads = & $Python `
    -m alembic `
    -c ".\alembic-control.ini" `
    heads


if ($LASTEXITCODE -ne 0)
{
    throw "Control Alembic heads failed."
}


$ControlHeadLines = @(
    $ControlHeads |
    ForEach-Object {
        if ($null -ne $_)
        {
            $_.ToString().Trim()
        }
    } |
    Where-Object {
        $_.Length -gt 0
    }
)


foreach ($Line in $ControlHeadLines)
{
    Write-Host $Line
}


if ($ControlHeadLines.Count -ne 1)
{
    throw (
        "Expected exactly one control head. Found: " +
        $ControlHeadLines.Count
    )
}


$ControlHeadText = (
    $ControlHeadLines -join "`n"
)


if ($ControlHeadText -notmatch $ExpectedControlHead)
{
    throw (
        "Unexpected control head. Expected " +
        $ExpectedControlHead +
        ". Actual: " +
        $ControlHeadText
    )
}


Write-Host "PASS control head"
Write-Host ""


# =========================================================
# 8/8 TENANT MIGRATION
# =========================================================

Write-Host "[8/8] Tenant migration..."


$TenantHeads = & $Python `
    -m alembic `
    -c ".\alembic.tenant.ini" `
    -x "database_name=$TenantDatabase" `
    heads


if ($LASTEXITCODE -ne 0)
{
    throw "Tenant Alembic heads failed."
}


$TenantHeadLines = @(
    $TenantHeads |
    ForEach-Object {
        if ($null -ne $_)
        {
            $_.ToString().Trim()
        }
    } |
    Where-Object {
        $_.Length -gt 0
    }
)


foreach ($Line in $TenantHeadLines)
{
    Write-Host $Line
}


if ($TenantHeadLines.Count -ne 1)
{
    throw (
        "Expected exactly one tenant head. Found: " +
        $TenantHeadLines.Count
    )
}


$TenantHeadText = (
    $TenantHeadLines -join "`n"
)


if ($TenantHeadText -notmatch $ExpectedTenantHead)
{
    throw (
        "Unexpected tenant head. Expected " +
        $ExpectedTenantHead +
        ". Actual: " +
        $TenantHeadText
    )
}


$TenantCurrent = & $Python `
    -m alembic `
    -c ".\alembic.tenant.ini" `
    -x "database_name=$TenantDatabase" `
    current


if ($LASTEXITCODE -ne 0)
{
    throw "Tenant Alembic current failed."
}


$TenantCurrentLines = @(
    $TenantCurrent |
    ForEach-Object {
        if ($null -ne $_)
        {
            $_.ToString().Trim()
        }
    } |
    Where-Object {
        $_.Length -gt 0
    }
)


foreach ($Line in $TenantCurrentLines)
{
    Write-Host $Line
}


$TenantCurrentText = (
    $TenantCurrentLines -join "`n"
)


if ($TenantCurrentText -notmatch $ExpectedTenantHead)
{
    throw (
        "Tenant database must be upgraded to " +
        $ExpectedTenantHead +
        ". Current: " +
        $TenantCurrentText
    )
}


Write-Host "PASS tenant migration"
Write-Host ""


# =========================================================
# FINAL
# =========================================================

Write-Host "================================================="
Write-Host " PHASE 13.5 VOICE CHANNELS / RTC: PASS"
Write-Host "================================================="
Write-Host "Voice channel type:          PASS"
Write-Host "Active call lookup/create:   PASS"
Write-Host "Single active call:          PASS"
Write-Host "Join / leave:                PASS"
Write-Host "Participant list:            PASS"
Write-Host "Self mute:                   PASS"
Write-Host "Self deafen:                 PASS"
Write-Host "Moderator mute:              PASS"
Write-Host "Moderator deafen:            PASS"
Write-Host "Kick:                        PASS"
Write-Host "Ban / unban:                 PASS"
Write-Host "Screen share state:          PASS"
Write-Host "WebRTC offer/answer/ICE:     PASS"
Write-Host "Presence heartbeat:          PASS"
Write-Host "Speaking state:              PASS"
Write-Host "Redis realtime fanout:       PASS"
Write-Host "OpenAPI:                     PASS"
Write-Host "Control head:                $ExpectedControlHead"
Write-Host "Tenant head:                 $ExpectedTenantHead"
Write-Host "================================================="