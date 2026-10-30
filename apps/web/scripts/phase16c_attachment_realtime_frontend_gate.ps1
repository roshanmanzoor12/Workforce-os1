$ErrorActionPreference = "Stop"


Write-Host ""
Write-Host "================================================="
Write-Host " WorkforceOS Phase 16C Attachment Frontend Gate"
Write-Host "================================================="
Write-Host ""


$WebRoot =
    Split-Path `
        -Parent `
        $PSScriptRoot


Set-Location $WebRoot


$AttachmentEvents =
    ".\lib\realtime\channel-attachment-events.ts"


$RealtimeObserver =
    ".\lib\realtime\channel-realtime-event-observer.ts"


$MessageItem =
    ".\components\channels\channel-message-item.tsx"


$AttachmentService =
    ".\services\attachments.service.ts"


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


Write-Host "[1/8] Required files..."


foreach (
    $File in @(
        $AttachmentEvents,
        $RealtimeObserver,
        $MessageItem,
        $AttachmentService
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
Write-Host "[2/8] Event contract..."


if (
    -not (
        Select-String `
            -Path $AttachmentEvents `
            -Pattern `
            'channel\.attachment\.bound' `
            -Quiet
    )
)
{
    Fail-Gate `
        "Frontend channel.attachment.bound contract missing."
}


Pass-Step `
    "Attachment event contract"


Write-Host ""
Write-Host "[3/8] Realtime observer..."


if (
    -not (
        Select-String `
            -Path $RealtimeObserver `
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
    "Realtime observer"


Write-Host ""
Write-Host "[4/8] Message subscription..."


if (
    -not (
        Select-String `
            -Path $MessageItem `
            -Pattern `
            'subscribeToChannelAttachmentBound' `
            -Quiet
    )
)
{
    Fail-Gate `
        "ChannelMessageItem does not subscribe to attachment events."
}


Pass-Step `
    "Message attachment subscription"


Write-Host ""
Write-Host "[5/8] Targeted refresh..."


if (
    -not (
        Select-String `
            -Path $MessageItem `
            -Pattern `
            'listChannelAttachments' `
            -Quiet
    )
)
{
    Fail-Gate `
        "ChannelMessageItem does not refresh attachments."
}


Pass-Step `
    "Targeted attachment refresh"


Write-Host ""
Write-Host "[6/8] Polling regression check..."


$Polling =
    Select-String `
        -Path @(
            $AttachmentEvents,
            $RealtimeObserver,
            $MessageItem
        ) `
        -Pattern `
        'setInterval|setTimeout.*listChannelAttachments' `
        -Quiet


if (
    $Polling
)
{
    Fail-Gate `
        "Polling detected in attachment realtime files."
}


Pass-Step `
    "No attachment polling"


Write-Host ""
Write-Host "[7/8] TypeScript..."


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
Write-Host "[8/8] Locate realtime receive integration..."


$IntegrationMatches =
    Get-ChildItem `
        ".\lib", `
        ".\hooks", `
        ".\components", `
        ".\app" `
        -Recurse `
        -File `
        -Include "*.ts","*.tsx" `
        -ErrorAction SilentlyContinue |
    Select-String `
        -Pattern `
        'onmessage|addEventListener\("message"|JSON\.parse\(.*data|reduceChannel|channel-event-reducer|observeChannelRealtimeEvent' `
        -Context 5,12


if (
    $IntegrationMatches
)
{
    Write-Host ""
    Write-Host `
        "Realtime receive candidates:"
    Write-Host ""

    $IntegrationMatches
}
else
{
    Write-Host `
        "[NO RECEIVE CANDIDATES FOUND]"
}


Write-Host ""
Write-Host "================================================="
Write-Host " FRONTEND ATTACHMENT CONTRACT PASS"
Write-Host "================================================="
Write-Host ""
Write-Host "Attachment event parser           PASS"
Write-Host "Browser invalidation bridge       PASS"
Write-Host "Message targeted subscription     PASS"
Write-Host "Attachment refetch                PASS"
Write-Host "Polling absent                    PASS"
Write-Host "TypeScript                        PASS"
Write-Host ""
Write-Host "Realtime receive integration location printed above."
Write-Host "================================================="
Write-Host ""