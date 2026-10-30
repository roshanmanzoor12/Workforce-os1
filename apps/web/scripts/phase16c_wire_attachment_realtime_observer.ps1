$ErrorActionPreference = "Stop"


Write-Host ""
Write-Host "================================================="
Write-Host " WorkforceOS Phase 16C Attachment Observer Wiring"
Write-Host "================================================="
Write-Host ""


$WebRoot =
    Split-Path `
        -Parent `
        $PSScriptRoot


Set-Location $WebRoot


$HookFile =
    ".\hooks\use-channel-realtime.ts"


if (
    -not (
        Test-Path $HookFile
    )
)
{
    throw "Missing file: $HookFile"
}


# =========================================================
# LOAD SOURCE
# =========================================================


$Lines =
    [System.Collections.Generic.List[string]]::new()


foreach (
    $Line in (
        Get-Content $HookFile
    )
)
{
    [void]$Lines.Add(
        $Line
    )
}


# =========================================================
# IMPORT
# =========================================================


$HasObserverImport =
    $false


foreach (
    $Line in $Lines
)
{
    if (
        $Line -match
        'channel-realtime-event-observer'
    )
    {
        $HasObserverImport =
            $true

        break
    }
}


if (
    $HasObserverImport
)
{
    Write-Host `
        "PASS: observer import already present"
}
else
{
    $ReducerImportEndIndex =
        -1


    for (
        $Index = 0;
        $Index -lt $Lines.Count;
        $Index++
    )
    {
        if (
            $Lines[$Index] -match
            'from\s+["'']@/lib/realtime/channel-event-reducer["''];?'
        )
        {
            $ReducerImportEndIndex =
                $Index

            break
        }
    }


    if (
        $ReducerImportEndIndex -lt 0
    )
    {
        throw (
            "Unable to locate channel-event-reducer import."
        )
    }


    $ImportLines =
        [string[]]@(
            "",
            'import {',
            '  observeChannelRealtimeEvent,',
            '} from "@/lib/realtime/channel-realtime-event-observer";'
        )


    $Lines.InsertRange(
        $ReducerImportEndIndex + 1,
        $ImportLines
    )


    Write-Host `
        "PASS: observer import added"
}


# =========================================================
# EVENT HANDLER CALL
# =========================================================


$HasObserverCall =
    $false


foreach (
    $Line in $Lines
)
{
    if (
        $Line -match
        '^\s*observeChannelRealtimeEvent\(\s*$'
    )
    {
        $HasObserverCall =
            $true

        break
    }
}


if (
    $HasObserverCall
)
{
    Write-Host `
        "PASS: observer call already present"
}
else
{
    $ReducerCallIndex =
        -1


    for (
        $Index = 0;
        $Index -lt $Lines.Count;
        $Index++
    )
    {
        if (
            $Lines[$Index] -match
            'reduceChannelRealtimeEvent\s*\('
        )
        {
            $ReducerCallIndex =
                $Index

            break
        }
    }


    if (
        $ReducerCallIndex -lt 0
    )
    {
        throw (
            "Unable to locate reduceChannelRealtimeEvent call."
        )
    }


    $SetStateIndex =
        -1


    for (
        $Index = $ReducerCallIndex;
        $Index -ge 0;
        $Index--
    )
    {
        if (
            $Lines[$Index] -match
            '^(\s*)setState\(\s*$'
        )
        {
            $SetStateIndex =
                $Index

            break
        }


        if (
            (
                $ReducerCallIndex -
                $Index
            ) -gt 20
        )
        {
            break
        }
    }


    if (
        $SetStateIndex -lt 0
    )
    {
        throw (
            "Unable to locate setState block for realtime reducer."
        )
    }


    $SetStateLine =
        $Lines[
            $SetStateIndex
        ]


    $Indent =
        ""


    if (
        $SetStateLine -match
        '^(\s*)'
    )
    {
        $Indent =
            $Matches[1]
    }


    $ObserverLines =
        [string[]]@(
            (
                $Indent +
                "observeChannelRealtimeEvent("
            ),
            (
                $Indent +
                "  event,"
            ),
            (
                $Indent +
                ");"
            ),
            "",
            ""
        )


    $Lines.InsertRange(
        $SetStateIndex,
        $ObserverLines
    )


    Write-Host `
        "PASS: observer call added"
}


# =========================================================
# SAVE
# =========================================================


Set-Content `
    -Path $HookFile `
    -Value $Lines `
    -Encoding utf8


# =========================================================
# VALIDATE SAVED SOURCE
# =========================================================


$SavedContent =
    Get-Content `
        $HookFile `
        -Raw


if (
    $SavedContent -notmatch
    'channel-realtime-event-observer'
)
{
    throw (
        "Observer import missing after write."
    )
}


if (
    $SavedContent -notmatch
    'observeChannelRealtimeEvent\s*\(\s*event\s*,?\s*\)'
)
{
    throw (
        "Observer call missing after write."
    )
}


if (
    $SavedContent -notmatch
    'reduceChannelRealtimeEvent\s*\('
)
{
    throw (
        "Existing realtime reducer was unexpectedly lost."
    )
}


Write-Host ""
Write-Host "PASS: existing realtime reducer preserved"
Write-Host "PASS: attachment observer wired"
Write-Host ""
Write-Host "Updated:"
Write-Host "  $HookFile"
Write-Host ""
Write-Host "================================================="
Write-Host " ATTACHMENT OBSERVER WIRING COMPLETE"
Write-Host "================================================="
Write-Host ""