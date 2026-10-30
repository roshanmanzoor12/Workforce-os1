param(
    [string]$FrontendRoot = "C:\workforce-os\frontend",
    [string]$OutputFile = "C:\workforce-os\frontend_api_pages_handoff.txt"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $FrontendRoot)) {
    throw "Frontend root not found: $FrontendRoot"
}

$Root = (Resolve-Path $FrontendRoot).Path

function Add-Line {
    param([string]$Text = "")
    Add-Content -Path $OutputFile -Value $Text -Encoding UTF8
}

function RelPath {
    param([string]$Path)
    $resolved = (Resolve-Path $Path).Path
    if ($resolved.StartsWith($Root, [System.StringComparison]::OrdinalIgnoreCase)) {
        return $resolved.Substring($Root.Length).TrimStart("\")
    }
    return $resolved
}

function Safe-Read {
    param([string]$Path)
    try {
        return Get-Content -Path $Path -Raw -ErrorAction Stop
    }
    catch {
        return ""
    }
}

function Is-ApiConnectedSource {
    param([string]$Content)

    $Patterns = @(
        '@/services/',
        '@/lib/api',
        '@/lib/api-client',
        'api\.',
        'apiClient',
        'fetch\(',
        'axios',
        'WebSocket',
        'EventSource',
        'useWorkspace',
        'workspaceId',
        'service\.',
        'Service\.',
        'useQuery',
        'useMutation'
    )

    foreach ($Pattern in $Patterns) {
        if ($Content -match $Pattern) {
            return $true
        }
    }

    return $false
}

function Extract-ApiEvidence {
    param([string]$Content)

    $Lines = $Content -split "`r?`n"
    $Evidence = New-Object System.Collections.Generic.List[string]

    foreach ($Line in $Lines) {
        if (
            $Line -match '@/services/' -or
            $Line -match '@/lib/api' -or
            $Line -match 'api\.' -or
            $Line -match 'apiClient' -or
            $Line -match 'fetch\(' -or
            $Line -match 'axios' -or
            $Line -match 'WebSocket' -or
            $Line -match 'EventSource' -or
            $Line -match 'useWorkspace' -or
            $Line -match 'workspaceId' -or
            $Line -match 'Service\.' -or
            $Line -match 'service\.'
        ) {
            $Trimmed = $Line.Trim()
            if ($Trimmed) {
                $Evidence.Add($Trimmed)
            }
        }
    }

    return $Evidence | Select-Object -Unique
}

function Get-AppRoute {
    param([string]$RelativePath)

    $normalized = $RelativePath.Replace("\", "/")

    $marker = "/app/"
    $index = $normalized.IndexOf($marker)

    if ($index -lt 0) {
        if ($normalized.StartsWith("app/")) {
            $routePart = $normalized.Substring(4)
        }
        elseif ($normalized.StartsWith("src/app/")) {
            $routePart = $normalized.Substring(8)
        }
        else {
            return "(unknown)"
        }
    }
    else {
        $routePart = $normalized.Substring($index + $marker.Length)
    }

    $routePart = $routePart -replace '/page\.(tsx|ts|jsx|js)$', ''
    $routePart = $routePart -replace '\([^/]+\)/', ''
    $routePart = $routePart -replace '^page\.(tsx|ts|jsx|js)$', ''

    if (-not $routePart) {
        return "/"
    }

    return "/" + $routePart.Trim("/")
}

Set-Content -Path $OutputFile -Value "" -Encoding UTF8

Add-Line "============================================================"
Add-Line " WorkforceOS Frontend API Pages Handoff"
Add-Line " Generated from the current local frontend source tree"
Add-Line "============================================================"
Add-Line ""
Add-Line ("Generated: " + (Get-Date).ToString("yyyy-MM-dd HH:mm:ss zzz"))
Add-Line ("Frontend root: " + $Root)
Add-Line ""
Add-Line "IMPORTANT INTERPRETATION"
Add-Line "- API_CONNECTED_SOURCE means the page/component contains source-level API/service/workspace/realtime evidence."
Add-Line "- It does NOT by itself prove runtime success. Runtime PASS should be recorded separately after browser/e2e testing."
Add-Line "- Pages without direct API imports may still be API-backed through child components; those child files are included below."
Add-Line "- Never treat sample/static UI as live unless this file shows a real service/API path."
Add-Line ""
Add-Line "CURRENT BACKEND CERTIFICATION CONTEXT"
Add-Line "- Phase 18 Productivity: 100% backend gate PASS"
Add-Line "- Phase 19 Analytics: 100% backend gate PASS"
Add-Line "- Phase 20 Reports: 100% backend gate PASS"
Add-Line "- Phase 21 Channels: certification in progress"
Add-Line "- Next after Phase 21: Voice Channels, Chat/DMs, Calls, Meetings, Goals, Notes, Knowledge, Notifications, Audit, Billing, Workspace Settings, Profile Preferences, Integrations/Apps, Recruitment/Resume Analyzer, Location if supported, final E2E certification"
Add-Line ""

# Git context if available.
try {
    $git = Get-Command git -ErrorAction Stop
    Push-Location $Root
    try {
        $branch = (& git branch --show-current 2>$null)
        $commit = (& git rev-parse HEAD 2>$null)
        if ($branch) { Add-Line ("Git branch: " + $branch) }
        if ($commit) { Add-Line ("Git commit: " + $commit) }
    }
    finally {
        Pop-Location
    }
}
catch {
}

Add-Line ""
Add-Line "============================================================"
Add-Line " PAGE INVENTORY + API CONNECTION EVIDENCE"
Add-Line "============================================================"

$PageFiles = Get-ChildItem -Path $Root -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object {
        $_.FullName -notmatch '\\node_modules\\' -and
        $_.FullName -notmatch '\\.next\\' -and
        $_.Name -match '^page\.(tsx|ts|jsx|js)$'
    } |
    Sort-Object FullName

if (-not $PageFiles) {
    Add-Line "NO PAGE FILES FOUND"
}

foreach ($File in $PageFiles) {
    $relative = RelPath $File.FullName
    $content = Safe-Read $File.FullName
    $route = Get-AppRoute $relative
    $connected = Is-ApiConnectedSource $content
    $evidence = @(Extract-ApiEvidence $content)

    Add-Line ""
    Add-Line ("PAGE: " + $route)
    Add-Line ("FILE: " + $relative)
    Add-Line ("STATUS: " + ($(if ($connected) { "API_CONNECTED_SOURCE" } else { "NO_DIRECT_API_EVIDENCE" })))

    if ($evidence.Count -gt 0) {
        Add-Line "API/SERVICE EVIDENCE:"
        foreach ($item in $evidence) {
            Add-Line ("  " + $item)
        }
    }
}

Add-Line ""
Add-Line "============================================================"
Add-Line " API-CONNECTED COMPONENT INVENTORY"
Add-Line "============================================================"

$ComponentFiles = Get-ChildItem -Path $Root -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object {
        $_.FullName -notmatch '\\node_modules\\' -and
        $_.FullName -notmatch '\\.next\\' -and
        $_.Extension -in @(".tsx", ".ts", ".jsx", ".js") -and
        (
            $_.FullName -match '\\components\\' -or
            $_.FullName -match '\\views\\' -or
            $_.FullName -match '\\features\\'
        )
    } |
    Sort-Object FullName

foreach ($File in $ComponentFiles) {
    $content = Safe-Read $File.FullName
    if (-not (Is-ApiConnectedSource $content)) {
        continue
    }

    $relative = RelPath $File.FullName
    $evidence = @(Extract-ApiEvidence $content)

    Add-Line ""
    Add-Line ("COMPONENT: " + $relative)
    Add-Line "STATUS: API_CONNECTED_SOURCE"
    if ($evidence.Count -gt 0) {
        Add-Line "EVIDENCE:"
        foreach ($item in $evidence) {
            Add-Line ("  " + $item)
        }
    }
}

Add-Line ""
Add-Line "============================================================"
Add-Line " DOMAIN SERVICE FILES"
Add-Line "============================================================"

$ServiceFiles = Get-ChildItem -Path $Root -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object {
        $_.FullName -notmatch '\\node_modules\\' -and
        $_.FullName -notmatch '\\.next\\' -and
        (
            $_.FullName -match '\\services\\' -or
            $_.Name -match '\.service\.(ts|tsx|js|jsx)$'
        ) -and
        $_.Extension -in @(".ts", ".tsx", ".js", ".jsx")
    } |
    Sort-Object FullName

foreach ($File in $ServiceFiles) {
    Add-Line ""
    Add-Line ("SERVICE FILE: " + (RelPath $File.FullName))
    Add-Line "----- BEGIN SOURCE -----"
    Add-Line (Safe-Read $File.FullName)
    Add-Line "----- END SOURCE -----"
}

Add-Line ""
Add-Line "============================================================"
Add-Line " CENTRAL API / AUTH / WORKSPACE CONTEXT FILES"
Add-Line "============================================================"

$CoreCandidates = Get-ChildItem -Path $Root -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object {
        $_.FullName -notmatch '\\node_modules\\' -and
        $_.FullName -notmatch '\\.next\\' -and
        $_.Extension -in @(".ts", ".tsx", ".js", ".jsx") -and
        (
            $_.Name -match 'api-client' -or
            $_.Name -match '^api\.' -or
            $_.Name -match '^auth\.' -or
            $_.Name -match 'workspace-context' -or
            $_.Name -match 'permission' -or
            $_.Name -match 'capabilit'
        )
    } |
    Sort-Object FullName

foreach ($File in $CoreCandidates) {
    Add-Line ""
    Add-Line ("CORE FILE: " + (RelPath $File.FullName))
    Add-Line "----- BEGIN SOURCE -----"
    Add-Line (Safe-Read $File.FullName)
    Add-Line "----- END SOURCE -----"
}

Add-Line ""
Add-Line "============================================================"
Add-Line " API ENDPOINT STRING INDEX"
Add-Line "============================================================"

$SourceFiles = Get-ChildItem -Path $Root -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object {
        $_.FullName -notmatch '\\node_modules\\' -and
        $_.FullName -notmatch '\\.next\\' -and
        $_.Extension -in @(".ts", ".tsx", ".js", ".jsx")
    }

$EndpointHits = foreach ($File in $SourceFiles) {
    Select-String -Path $File.FullName -Pattern @(
        '/api/v1/',
        '/workspaces/',
        '/workspace-channels',
        '/auth/',
        '/reports/',
        '/analytics/',
        '/productivity',
        '/payroll/',
        '/attendance/',
        '/devices',
        '/monitoring',
        '/channels',
        '/meetings',
        '/goals',
        '/notifications',
        '/audit-log'
    ) -SimpleMatch -ErrorAction SilentlyContinue |
    ForEach-Object {
        [PSCustomObject]@{
            File = RelPath $_.Path
            Line = $_.LineNumber
            Text = $_.Line.Trim()
        }
    }
}

foreach ($Hit in ($EndpointHits | Sort-Object File, Line)) {
    Add-Line ("{0}:{1} {2}" -f $Hit.File, $Hit.Line, $Hit.Text)
}

Add-Line ""
Add-Line "============================================================"
Add-Line " ENVIRONMENT VARIABLE NAMES (VALUES REDACTED)"
Add-Line "============================================================"

$EnvFiles = Get-ChildItem -Path $Root -Force -File -ErrorAction SilentlyContinue |
    Where-Object {
        $_.Name -like ".env*" -or
        $_.Name -match 'env\.'
    }

foreach ($File in $EnvFiles) {
    Add-Line ("ENV FILE: " + (RelPath $File.FullName))

    $lines = Get-Content $File.FullName -ErrorAction SilentlyContinue
    foreach ($line in $lines) {
        if ($line -match '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=') {
            Add-Line ("  " + $Matches[1] + "=<REDACTED>")
        }
    }
}

Add-Line ""
Add-Line "============================================================"
Add-Line " FULL SOURCE OF API-CONNECTED PAGE FILES"
Add-Line "============================================================"

foreach ($File in $PageFiles) {
    $content = Safe-Read $File.FullName
    if (-not (Is-ApiConnectedSource $content)) {
        continue
    }

    Add-Line ""
    Add-Line ("FILE: " + (RelPath $File.FullName))
    Add-Line ("ROUTE: " + (Get-AppRoute (RelPath $File.FullName)))
    Add-Line "----- BEGIN SOURCE -----"
    Add-Line $content
    Add-Line "----- END SOURCE -----"
}

Add-Line ""
Add-Line "============================================================"
Add-Line " HANDOFF RULES FOR NEXT CHAT"
Add-Line "============================================================"
Add-Line "1. Treat this file as source evidence for current frontend wiring."
Add-Line "2. Do not claim a page is runtime-working merely because source imports a service."
Add-Line "3. Use STATUS/API evidence above to identify pages wired to backend."
Add-Line "4. If a page has NO_DIRECT_API_EVIDENCE, inspect its child components before calling it static."
Add-Line "5. Frontend must use central authenticated API client and WorkspaceContext; backend remains authorization authority."
Add-Line "6. Realtime improves freshness only; persisted backend API remains authoritative."
Add-Line "7. Never expose device secrets or tenant DB identifiers in browser code."
Add-Line "8. When this handoff is regenerated, newer source supersedes older chat assumptions."
Add-Line ""
Add-Line "END OF WORKFORCEOS FRONTEND API HANDOFF"

Write-Host ""
Write-Host "PASS frontend API handoff generated"
Write-Host $OutputFile
