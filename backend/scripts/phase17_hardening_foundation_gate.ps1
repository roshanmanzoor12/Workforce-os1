$ErrorActionPreference = "Stop"


$BackendRoot = "C:\workforce-os\backend"

$Python = (
    "C:\workforce-os\backend\" +
    ".venv\Scripts\python.exe"
)


Set-Location $BackendRoot


Write-Host "================================================="
Write-Host " WorkforceOS Phase 17 Hardening Foundation Gate"
Write-Host "================================================="
Write-Host ""


# =========================================================
# REQUIRED FILES
# =========================================================

$RequiredFiles = @(
    ".\app\modules\channels\hardening\__init__.py",
    ".\app\modules\channels\hardening\config.py",
    ".\app\modules\channels\hardening\ticket_store.py",
    ".\app\modules\channels\hardening\access.py",
    ".\app\modules\channels\hardening\rate_limit.py",
    ".\app\modules\channels\hardening\presence_guard.py",
    ".\app\modules\channels\hardening\read_state_upsert.py",
    ".\app\modules\channels\hardening\observability.py",
    ".\app\modules\channels\hardening\attachment_access.py"
)


Write-Host "[1/8] Required files..."


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
# COMPILE
# =========================================================

Write-Host "[2/8] Compiling hardening package..."


& $Python `
    -m compileall `
    ".\app\modules\channels\hardening" `
    -q


if ($LASTEXITCODE -ne 0)
{
    throw "Hardening package compile failed."
}


Write-Host "PASS compile"
Write-Host ""


# =========================================================
# IMPORT
# =========================================================

Write-Host "[3/8] Import gate..."


$ImportCheck = @'
from app.modules.channels.hardening import (
    AtomicRealtimeTicketStore,
    ChannelAccessGuard,
    ChannelAttachmentAccessGuard,
    ChannelRateLimiter,
    ChannelReadStateUpserter,
    PresenceLifetimeGuard,
    channel_realtime_metrics,
    get_channel_hardening_settings,
)

settings = get_channel_hardening_settings()

assert settings.ticket_ttl_seconds > 0
assert settings.replay_batch_size > 0
assert settings.replay_max_events >= settings.replay_batch_size

guard = PresenceLifetimeGuard(
    online_ttl_seconds=90,
    idle_after_seconds=60,
    typing_ttl_seconds=8,
)

assert guard.online_ttl_seconds == 90

print("PASS hardening imports")
'@


$ImportCheck |
    & $Python -


if ($LASTEXITCODE -ne 0)
{
    throw "Hardening import gate failed."
}


Write-Host "PASS imports"
Write-Host ""


# =========================================================
# CONFIG
# =========================================================

Write-Host "[4/8] Configuration contract..."


$ConfigCheck = @'
from app.modules.channels.hardening.config import (
    ChannelHardeningSettings,
)

settings = ChannelHardeningSettings.from_environment()

assert settings.ticket_ttl_seconds > 0
assert settings.websocket_connect_limit > 0
assert settings.websocket_connect_window_seconds > 0
assert settings.message_event_limit > 0
assert settings.typing_event_limit > 0
assert settings.heartbeat_limit > 0
assert settings.presence_online_ttl_seconds > 0
assert settings.presence_idle_after_seconds > 0
assert settings.typing_ttl_seconds > 0
assert settings.replay_batch_size > 0
assert settings.replay_max_events > 0

print("PASS hardening config")
'@


$ConfigCheck |
    & $Python -


if ($LASTEXITCODE -ne 0)
{
    throw "Hardening config gate failed."
}


Write-Host "PASS configuration"
Write-Host ""


# =========================================================
# PRESENCE
# =========================================================

Write-Host "[5/8] Presence lifetime rules..."


$PresenceCheck = @'
from datetime import (
    datetime,
    timedelta,
    timezone,
)

from app.modules.channels.hardening.presence_guard import (
    PresenceLifetimeGuard,
)

guard = PresenceLifetimeGuard(
    online_ttl_seconds=90,
    idle_after_seconds=60,
    typing_ttl_seconds=8,
)

now = datetime.now(timezone.utc)

online = guard.evaluate(
    last_seen_at=(
        now - timedelta(seconds=10)
    ),
    now=now,
)

idle = guard.evaluate(
    last_seen_at=(
        now - timedelta(seconds=70)
    ),
    now=now,
)

offline = guard.evaluate(
    last_seen_at=(
        now - timedelta(seconds=100)
    ),
    now=now,
)

assert online.status == "online"
assert idle.status == "idle"
assert offline.status == "offline"

assert guard.typing_is_active(
    typing_started_at=(
        now - timedelta(seconds=3)
    ),
    now=now,
)

assert not guard.typing_is_active(
    typing_started_at=(
        now - timedelta(seconds=20)
    ),
    now=now,
)

print("PASS presence lifetime")
'@


$PresenceCheck |
    & $Python -


if ($LASTEXITCODE -ne 0)
{
    throw "Presence guard gate failed."
}


Write-Host "PASS presence lifetime"
Write-Host ""


# =========================================================
# ATOMIC TICKET CONTRACT
# =========================================================

Write-Host "[6/8] Atomic ticket contract..."


$TicketPath = (
    ".\app\modules\channels\" +
    "hardening\ticket_store.py"
)

$TicketSource = Get-Content `
    $TicketPath `
    -Raw


$RequiredTicketTokens = @(
    "getdel",
    "_ATOMIC_GETDEL_LUA",
    "redis.call",
    "DEL",
    "consume"
)


foreach ($Token in $RequiredTicketTokens)
{
    if (
        $TicketSource.IndexOf(
            $Token,
            [System.StringComparison]::OrdinalIgnoreCase
        ) -lt 0
    )
    {
        throw (
            "Atomic ticket contract missing token: " +
            $Token
        )
    }
}


Write-Host "PASS atomic ticket contract"
Write-Host ""


# =========================================================
# MEMBERSHIP / ATTACHMENT CONTRACT
# =========================================================

Write-Host "[7/8] Membership lifecycle contract..."


$AccessSource = Get-Content `
    ".\app\modules\channels\hardening\access.py" `
    -Raw

$AttachmentSource = Get-Content `
    ".\app\modules\channels\hardening\attachment_access.py" `
    -Raw


if (
    $AccessSource.IndexOf(
        "left_at",
        [System.StringComparison]::Ordinal
    ) -lt 0
)
{
    throw (
        "Channel access guard must use left_at."
    )
}


if (
    $AttachmentSource.IndexOf(
        "left_at",
        [System.StringComparison]::Ordinal
    ) -lt 0
)
{
    throw (
        "Attachment access guard must use left_at."
    )
}


$AttachmentAccessPath = (
    Resolve-Path `
        ".\app\modules\channels\hardening\attachment_access.py"
).Path

& ".\.venv\Scripts\python.exe" `
    -c `
    "import ast,pathlib,sys; p=pathlib.Path(r'$AttachmentAccessPath'); t=ast.parse(p.read_text(encoding='utf-8', errors='ignore')); bad=[n.lineno for n in ast.walk(t) if isinstance(n,ast.Attribute) and n.attr=='is_active' and isinstance(n.value,ast.Name) and n.value.id=='WorkspaceChannelMember']; print('PASS attachment membership AST contract' if not bad else 'BAD WorkspaceChannelMember.is_active at lines: ' + ', '.join(map(str,bad))); sys.exit(1 if bad else 0)"

if ($LASTEXITCODE -ne 0)
{
    throw (
        "Attachment access guard still uses " +
        "WorkspaceChannelMember.is_active."
    )
}


Write-Host "PASS membership lifecycle contract"
Write-Host ""


# =========================================================
# READ STATE UPSERT
# =========================================================

Write-Host "[8/8] Read-state UPSERT contract..."


$ReadStateSource = Get-Content `
    ".\app\modules\channels\hardening\read_state_upsert.py" `
    -Raw


$RequiredReadStateTokens = @(
    "insert(",
    "on_conflict_do_update",
    "channel_id",
    "user_id",
    "last_read_message_id"
)


foreach ($Token in $RequiredReadStateTokens)
{
    if (
        $ReadStateSource.IndexOf(
            $Token,
            [System.StringComparison]::Ordinal
        ) -lt 0
    )
    {
        throw (
            "Read-state UPSERT contract missing: " +
            $Token
        )
    }
}


Write-Host "PASS read-state UPSERT contract"
Write-Host ""


Write-Host "================================================="
Write-Host " PHASE 17 HARDENING FOUNDATION: PASS"
Write-Host "================================================="
Write-Host "Required files:                  PASS"
Write-Host "Python compile:                  PASS"
Write-Host "Import safety:                   PASS"
Write-Host "Configuration:                   PASS"
Write-Host "Presence lifetime:               PASS"
Write-Host "Atomic ticket foundation:        PASS"
Write-Host "Membership lifecycle:            PASS"
Write-Host "Read-state UPSERT foundation:    PASS"
Write-Host "================================================="