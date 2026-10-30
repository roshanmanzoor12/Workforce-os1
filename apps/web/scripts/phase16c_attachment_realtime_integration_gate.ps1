$ErrorActionPreference = "Stop"


Write-Host ""
Write-Host "================================================="
Write-Host " WorkforceOS Phase 16C Attachment Realtime Gate"
Write-Host "================================================="
Write-Host ""


$WebRoot =
    Split-Path `
        -Parent `
        $PSScriptRoot


Set-Location $WebRoot


$HookFile =
    ".\hooks\use-channel-realtime.ts"


$ObserverFile =
    ".\lib\realtime\channel-realtime-event-observer.ts"


$AttachmentEventsFile =
    ".\lib\realtime\channel-attachment-events.ts"


$MessageItemFile =
    ".\components\channels\channel-message-item.tsx"


$RoomFile =
    ".\components\channels\text-channel-room.tsx"


$RealtimeClientFile =
    ".\lib\realtime\channel-realtime-client.ts"


function Fail-Gate {
    param(
        [string]$Message
    )


    Write-Host ""
    Write-Host `
        "FAIL: $Message" `
        -ForegroundColor Red

    Write-Host ""

    exit 1
}


function Pass-Step {
    param(
        [string]$Message
    )


    Write-Host `
        "PASS: $Message" `
        -ForegroundColor Green
}


Write-Host "[1/9] Required files..."


foreach (
    $File in @(
        $HookFile,
        $ObserverFile,
        $AttachmentEventsFile,
        $MessageItemFile,
        $RoomFile,
        $RealtimeClientFile
    )
)
{
    if (
        -not (
            Test-Path $File
        )
    )
    {
        Fail-Gate `
            "Missing required file: $File"
    }
}


Pass-Step `
    "Required files present"


Write-Host ""
Write-Host "[2/9] Backend event name frontend contract..."


if (
    -not (
        Select-String `
            -Path $AttachmentEventsFile `
            -Pattern `
            'channel\.attachment\.bound' `
            -Quiet
    )
)
{
    Fail-Gate `
        "channel.attachment.bound frontend event contract missing."
}


Pass-Step `
    "channel.attachment.bound contract"


Write-Host ""
Write-Host "[3/9] Receive-path observer integration..."


if (
    -not (
        Select-String `
            -Path $HookFile `
            -Pattern `
            'observeChannelRealtimeEvent' `
            -Quiet
    )
)
{
    Fail-Gate `
        "use-channel-realtime does not observe received events."
}


Pass-Step `
    "Realtime receive observer wired"


Write-Host ""
Write-Host "[4/9] Observer forwards attachment event..."


if (
    -not (
        Select-String `
            -Path $ObserverFile `
            -Pattern `
            'forwardChannelAttachmentRealtimeEvent' `
            -Quiet
    )
)
{
    Fail-Gate `
        "Realtime observer does not forward attachment events."
}


Pass-Step `
    "Attachment event forwarded"


Write-Host ""
Write-Host "[5/9] Message targeted subscription..."


if (
    -not (
        Select-String `
            -Path $MessageItemFile `
            -Pattern `
            'subscribeToChannelAttachmentBound' `
            -Quiet
    )
)
{
    Fail-Gate `
        "ChannelMessageItem realtime attachment subscription missing."
}


if (
    -not (
        Select-String `
            -Path $MessageItemFile `
            -Pattern `
            'payload\.message_id' `
            -Quiet
    )
)
{
    Fail-Gate `
        "Attachment refresh is not targeted by message ID."
}


Pass-Step `
    "Targeted message refresh"


Write-Host ""
Write-Host "[6/9] Canonical attachment refetch..."


if (
    -not (
        Select-String `
            -Path $MessageItemFile `
            -Pattern `
            'listChannelAttachments' `
            -Quiet
    )
)
{
    Fail-Gate `
        "Message item does not refetch canonical attachments."
}


Pass-Step `
    "Canonical attachment GET refresh"


Write-Host ""
Write-Host "[7/9] Legacy polling removed..."


if (
    Select-String `
        -Path $RoomFile `
        -Pattern `
        'setInterval' `
        -Quiet
)
{
    Fail-Gate `
        "Legacy TextChannelRoom polling still exists."
}


Pass-Step `
    "Legacy channel polling absent"


Write-Host ""
Write-Host "[8/9] TypeScript..."


& npx `
    tsc `
    --noEmit `
    --pretty false


if (
    $LASTEXITCODE -ne 0
)
{
    Fail-Gate `
        "TypeScript failed."
}


Pass-Step `
    "TypeScript"


Write-Host ""
Write-Host "[9/9] Production build..."


& npm `
    run build


if (
    $LASTEXITCODE -ne 0
)
{
    Fail-Gate `
        "Production build failed."
}


Pass-Step `
    "Production build"


Write-Host ""
Write-Host "================================================="
Write-Host " PHASE 16C ATTACHMENT REALTIME FRONTEND PASS"
Write-Host "================================================="
Write-Host ""
Write-Host "Backend event contract            PASS"
Write-Host "Realtime receive observer         PASS"
Write-Host "Attachment invalidation event     PASS"
Write-Host "Targeted message subscription     PASS"
Write-Host "Canonical attachment refresh      PASS"
Write-Host "Legacy polling removed            PASS"
Write-Host "TypeScript                        PASS"
Write-Host "Production build                  PASS"
Write-Host ""
Write-Host "Remote attachment refresh certified."
Write-Host "================================================="
Write-Host ""