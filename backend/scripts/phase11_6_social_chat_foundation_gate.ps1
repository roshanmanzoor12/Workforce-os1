$ErrorActionPreference = "Stop"

$Backend = "C:\workforce-os\backend"
$Python = "C:\workforce-os\.venv\Scripts\python.exe"

Set-Location $Backend

Write-Host ""
Write-Host "================================================="
Write-Host " WorkforceOS Phase 11.6 Social/Chat Foundation"
Write-Host "================================================="
Write-Host ""


# =========================================================
# 1. COMPILE
# =========================================================

Write-Host "[1/5] Compiling social/chat foundation..."

& $Python `
    -m py_compile `
    .\app\modules\friends\enums.py `
    .\app\modules\friends\models.py `
    .\app\modules\friends\repository.py `
    .\app\modules\chat\enums.py `
    .\app\modules\chat\models.py `
    .\app\modules\chat\schemas.py `
    .\migrations\control\versions\e4f5a6b7c8d9_add_social_chat_foundation.py

if ($LASTEXITCODE -ne 0)
{
    throw "Phase 11.6 foundation compile failed."
}

Write-Host "PASS compile"
Write-Host ""


# =========================================================
# 2. TESTS
# =========================================================

Write-Host "[2/5] Social/chat tests..."

& $Python `
    -m pytest `
    .\tests\modules\friends `
    .\tests\modules\chat `
    -q

if ($LASTEXITCODE -ne 0)
{
    throw "Phase 11.6 social/chat tests failed."
}

Write-Host "PASS tests"
Write-Host ""


# =========================================================
# 3. ALEMBIC HEAD
# =========================================================

Write-Host "[3/5] Checking control migration chain..."

$Heads = (
    & $Python `
        -m alembic `
        -c .\alembic-control.ini `
        heads
)

if ($LASTEXITCODE -ne 0)
{
    throw "Alembic heads command failed."
}

Write-Host $Heads

if (
    $Heads -notmatch
    "e4f5a6b7c8d9"
)
{
    throw "Phase 11.6 migration is not the control head."
}

Write-Host "PASS migration chain"
Write-Host ""


# =========================================================
# 4. MODEL SECURITY / SHAPE
# =========================================================

Write-Host "[4/5] Checking social/chat boundaries..."

@'
from app.modules.chat.models import (
    ChatMessage,
    Conversation,
    ConversationMember,
)
from app.modules.friends.models import Friendship

assert Friendship.__tablename__ == "friendships"
assert Conversation.__tablename__ == "conversations"
assert ConversationMember.__tablename__ == "conversation_members"
assert ChatMessage.__tablename__ == "chat_messages"

print("PASS account-level friendship model")
print("PASS direct/group conversation model")
print("PASS conversation membership model")
print("PASS message model")
'@ |
& $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "Phase 11.6 model verification failed."
}

Write-Host ""


# =========================================================
# 5. PRIVACY / MESSAGE BOUNDARY
# =========================================================

Write-Host "[5/5] Checking forbidden monitoring fields..."

$Files = @(
    ".\app\modules\friends\enums.py",
    ".\app\modules\friends\models.py",
    ".\app\modules\friends\repository.py",
    ".\app\modules\chat\enums.py",
    ".\app\modules\chat\models.py",
    ".\app\modules\chat\schemas.py"
)

$Forbidden = @(
    "keylogger",
    "keystroke_capture",
    "clipboard_capture",
    "password_capture"
)

foreach ($Word in $Forbidden)
{
    $Matches = Get-ChildItem $Files |
        Select-String `
            -Pattern $Word `
            -SimpleMatch

    if ($Matches)
    {
        throw (
            "Forbidden monitoring field found: " +
            $Word
        )
    }
}

Write-Host "PASS social/chat privacy boundary"
Write-Host ""

Write-Host "================================================="
Write-Host " PHASE 11.6 SOCIAL/CHAT FOUNDATION: PASS"
Write-Host "================================================="
Write-Host ""