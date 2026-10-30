param(
    [string]$FrontendRoot = "C:\workforce-os\apps\web",
    [string]$OutputFile = "C:\workforce-os\WORKFORCE_FRONTEND_MASTER_HANDOFF.txt"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $FrontendRoot)) {
    throw "Frontend root not found: $FrontendRoot"
}

$FrontendRoot = (
    Resolve-Path -LiteralPath $FrontendRoot
).Path.TrimEnd("\")

$OutputDirectory = Split-Path -Parent $OutputFile

if (
    $OutputDirectory `
    -and `
    -not (Test-Path -LiteralPath $OutputDirectory)
) {
    New-Item `
        -ItemType Directory `
        -Force `
        -Path $OutputDirectory |
        Out-Null
}


function Write-Line {
    param(
        [string]$Text = ""
    )

    Add-Content `
        -LiteralPath $OutputFile `
        -Value $Text `
        -Encoding UTF8
}


function Write-Section {
    param(
        [string]$Title
    )

    Write-Line ""
    Write-Line "======================================================================"
    Write-Line $Title
    Write-Line "======================================================================"
}


function Get-RelativePathSafe {
    param(
        [string]$FullPath
    )

    if (
        $FullPath.StartsWith(
            $FrontendRoot,
            [System.StringComparison]::OrdinalIgnoreCase
        )
    ) {
        return (
            $FullPath
            .Substring(
                $FrontendRoot.Length
            )
            .TrimStart("\")
        )
    }

    return $FullPath
}


function Test-ExcludedPath {
    param(
        [string]$FullPath
    )

    $normalized = (
        $FullPath `
        -replace "/",
        "\"
    ).ToLowerInvariant()

    $excludedParts = @(
        "\node_modules\",
        "\.next\",
        "\.git\",
        "\coverage\",
        "\dist\",
        "\build\",
        "\out\",
        "\.turbo\",
        "\storybook-static\"
    )

    foreach ($part in $excludedParts) {
        if (
            $normalized.Contains(
                $part
            )
        ) {
            return $true
        }
    }

    return $false
}


function Test-SourceFile {
    param(
        [System.IO.FileInfo]$File
    )

    if (
        Test-ExcludedPath `
            -FullPath $File.FullName
    ) {
        return $false
    }

    $allowedExtensions = @(
        ".ts",
        ".tsx",
        ".js",
        ".jsx",
        ".mjs",
        ".cjs",
        ".css",
        ".scss",
        ".json",
        ".md",
        ".mdx",
        ".yml",
        ".yaml"
    )

    if (
        $allowedExtensions `
        -notcontains `
        $File.Extension.ToLowerInvariant()
    ) {
        return $false
    }

    $excludedNames = @(
        "package-lock.json",
        "pnpm-lock.yaml",
        "yarn.lock",
        "tsconfig.tsbuildinfo"
    )

    if (
        $excludedNames `
        -contains `
        $File.Name
    ) {
        return $false
    }

    return $true
}


function Write-FileContent {
    param(
        [System.IO.FileInfo]$File
    )

    $relative = (
        Get-RelativePathSafe `
            -FullPath $File.FullName
    )

    Write-Line ""
    Write-Line "----------------------------------------------------------------------"
    Write-Line "FILE: $relative"
    Write-Line "FULL_PATH: $($File.FullName)"
    Write-Line "SIZE_BYTES: $($File.Length)"
    Write-Line "LAST_WRITE: $($File.LastWriteTime.ToString('yyyy-MM-dd HH:mm:ss'))"
    Write-Line "----------------------------------------------------------------------"

    try {
        $lineNumber = 0

        Get-Content `
            -LiteralPath $File.FullName |
            ForEach-Object {
                $lineNumber++

                Write-Line (
                    "{0:D5}: {1}" -f `
                    $lineNumber,
                    $_
                )
            }
    }
    catch {
        Write-Line (
            "ERROR_READING_FILE: " `
            + $_.Exception.Message
        )
    }
}


function Get-AllSourceFiles {
    return @(
        Get-ChildItem `
            -LiteralPath $FrontendRoot `
            -Recurse `
            -File `
            -Force |
        Where-Object {
            Test-SourceFile `
                -File $_
        } |
        Sort-Object FullName
    )
}


function Write-SourceFolder {
    param(
        [string]$Title,
        [string]$RelativeFolder
    )

    Write-Section $Title

    $folder = Join-Path `
        $FrontendRoot `
        $RelativeFolder

    if (
        -not (
            Test-Path `
                -LiteralPath $folder
        )
    ) {
        Write-Line "MISSING_FOLDER: $RelativeFolder"
        return
    }

    Get-ChildItem `
        -LiteralPath $folder `
        -Recurse `
        -File `
        -Force |
    Where-Object {
        Test-SourceFile `
            -File $_
    } |
    Sort-Object FullName |
    ForEach-Object {
        Write-FileContent `
            -File $_
    }
}


Set-Content `
    -LiteralPath $OutputFile `
    -Value "" `
    -Encoding UTF8


Write-Line "======================================================================"
Write-Line " WORKFORCEOS FRONTEND MASTER HANDOFF"
Write-Line "======================================================================"
Write-Line ""
Write-Line "PURPOSE:"
Write-Line "Complete current frontend snapshot for continuing WorkforceOS in a new AI chat."
Write-Line ""
Write-Line "IMPORTANT:"
Write-Line "- UI existence does not automatically mean API connection works."
Write-Line "- API service existence does not automatically mean a page uses it."
Write-Line "- Realtime presence does not automatically mean runtime certification passed."
Write-Line "- Environment secret VALUES are intentionally excluded."
Write-Line ""
Write-Line "FRONTEND_ROOT: $FrontendRoot"
Write-Line "GENERATED_AT: $((Get-Date).ToString('yyyy-MM-dd HH:mm:ss zzz'))"


Write-Section "1. FRONTEND DIRECTORY TREE"

Get-ChildItem `
    -LiteralPath $FrontendRoot `
    -Recurse `
    -Force |
Where-Object {
    -not (
        Test-ExcludedPath `
            -FullPath $_.FullName
    )
} |
Sort-Object FullName |
ForEach-Object {
    $relative = (
        Get-RelativePathSafe `
            -FullPath $_.FullName
    )

    if ($_.PSIsContainer) {
        Write-Line "DIR  $relative"
    }
    else {
        Write-Line "FILE $relative"
    }
}


Write-Section "2. NEXT.JS ROUTE / PAGE INVENTORY"

$AppRoot = Join-Path `
    $FrontendRoot `
    "app"

if (Test-Path -LiteralPath $AppRoot) {
    Get-ChildItem `
        -LiteralPath $AppRoot `
        -Recurse `
        -File `
        -Force |
    Where-Object {
        $_.Name -in @(
            "page.tsx",
            "page.ts",
            "layout.tsx",
            "layout.ts",
            "loading.tsx",
            "loading.ts",
            "error.tsx",
            "error.ts",
            "not-found.tsx",
            "not-found.ts"
        )
    } |
    Sort-Object FullName |
    ForEach-Object {
        Write-Line (
            Get-RelativePathSafe `
                -FullPath $_.FullName
        )
    }
}


Write-Section "3. PAGE API / REALTIME STATUS EVIDENCE"

if (Test-Path -LiteralPath $AppRoot) {
    $pages = @(
        Get-ChildItem `
            -LiteralPath $AppRoot `
            -Recurse `
            -File `
            -Force |
        Where-Object {
            $_.Name -in @(
                "page.tsx",
                "page.ts"
            )
        } |
        Sort-Object FullName
    )

    foreach ($page in $pages) {
        $relative = (
            Get-RelativePathSafe `
                -FullPath $page.FullName
        )

        $content = Get-Content `
            -LiteralPath $page.FullName `
            -Raw

        $hasServiceImport = (
            $content -match "@/services/" `
            -or `
            $content -match "/services/" `
            -or `
            $content -match "Service\." `
            -or `
            $content -match "service\."
        )

        $hasDirectApi = (
            $content -match "fetch\(" `
            -or `
            $content -match "apiClient" `
            -or `
            $content -match "/api/v1"
        )

        $hasRealtime = (
            $content -match "WebSocket" `
            -or `
            $content -match "realtime" `
            -or `
            $content -match "/ws"
        )

        $hasWorkspace = (
            $content -match "useWorkspace" `
            -or `
            $content -match "workspaceId" `
            -or `
            $content -match "WorkspaceContext"
        )

        $hasLoading = (
            $content -match "loading" `
            -or `
            $content -match "isLoading"
        )

        $hasError = (
            $content -match "error" `
            -or `
            $content -match "setError"
        )

        $status = "UI_ONLY_OR_WRAPPER"

        if (
            $hasServiceImport `
            -or `
            $hasDirectApi
        ) {
            $status = "API_EVIDENCE_PRESENT"
        }

        if (
            $hasRealtime `
            -and `
            (
                $hasServiceImport `
                -or `
                $hasDirectApi
            )
        ) {
            $status = "API_AND_REALTIME_EVIDENCE_PRESENT"
        }

        Write-Line ""
        Write-Line "PAGE: $relative"
        Write-Line "STATUS_EVIDENCE: $status"
        Write-Line "SERVICE_OR_API_REFERENCE: $hasServiceImport"
        Write-Line "DIRECT_API_REFERENCE: $hasDirectApi"
        Write-Line "REALTIME_REFERENCE: $hasRealtime"
        Write-Line "WORKSPACE_CONTEXT_REFERENCE: $hasWorkspace"
        Write-Line "LOADING_STATE_REFERENCE: $hasLoading"
        Write-Line "ERROR_STATE_REFERENCE: $hasError"
        Write-Line "NOTE: Static evidence only. Runtime/API success must still be certified."
    }
}


Write-SourceFolder `
    -Title "4. FULL NEXT.JS APP / PAGE SOURCE" `
    -RelativeFolder "app"

Write-SourceFolder `
    -Title "5. FULL API SERVICES SOURCE" `
    -RelativeFolder "services"

Write-SourceFolder `
    -Title "6. FULL CONTEXT SOURCE" `
    -RelativeFolder "contexts"

Write-SourceFolder `
    -Title "7. FULL HOOK SOURCE" `
    -RelativeFolder "hooks"

Write-SourceFolder `
    -Title "8. FULL LIB / API CLIENT SOURCE" `
    -RelativeFolder "lib"

Write-SourceFolder `
    -Title "9. FULL TYPE DEFINITIONS" `
    -RelativeFolder "types"

Write-SourceFolder `
    -Title "10. FULL COMPONENT SOURCE" `
    -RelativeFolder "components"

Write-SourceFolder `
    -Title "11. FRONTEND SCRIPTS" `
    -RelativeFolder "scripts"


Write-Section "12. PROJECT CONFIGURATION"

$ConfigFiles = @(
    "package.json",
    "tsconfig.json",
    "next.config.ts",
    "next.config.js",
    "next.config.mjs",
    "eslint.config.js",
    "eslint.config.mjs",
    "postcss.config.js",
    "postcss.config.mjs",
    "tailwind.config.ts",
    "tailwind.config.js",
    "next-env.d.ts"
)

foreach ($ConfigName in $ConfigFiles) {
    $ConfigPath = Join-Path `
        $FrontendRoot `
        $ConfigName

    if (
        Test-Path `
            -LiteralPath $ConfigPath
    ) {
        Write-FileContent `
            -File (
                Get-Item `
                    -LiteralPath $ConfigPath
            )
    }
}


Write-Section "13. ENVIRONMENT VARIABLE NAMES - VALUES REDACTED"

Get-ChildItem `
    -LiteralPath $FrontendRoot `
    -File `
    -Force |
Where-Object {
    $_.Name -like ".env*"
} |
ForEach-Object {
    Write-Line ""
    Write-Line "ENV_FILE: $($_.Name)"

    Get-Content `
        -LiteralPath $_.FullName |
    ForEach-Object {
        $line = $_.Trim()

        if (
            $line `
            -and `
            -not $line.StartsWith("#") `
            -and `
            $line.Contains("=")
        ) {
            $name = (
                $line.Split(
                    "=",
                    2
                )[0]
            ).Trim()

            Write-Line "$name=<REDACTED>"
        }
    }
}


Write-Section "14. API / NETWORK / REALTIME USAGE INDEX"

$SearchFiles = Get-AllSourceFiles

$SearchPatterns = @(
    "fetch\(",
    "axios",
    "apiClient",
    "Service\.",
    "service\.",
    "WebSocket",
    "new WebSocket",
    "EventSource",
    "NEXT_PUBLIC_",
    "WF_API",
    "WF_WS",
    "/api/v1",
    "realtime",
    "/ws",
    "Authorization",
    "Bearer"
)

foreach ($Pattern in $SearchPatterns) {
    Write-Line ""
    Write-Line "### PATTERN: $Pattern"

    $SearchFiles |
        Select-String `
            -Pattern $Pattern `
            -ErrorAction SilentlyContinue |
        ForEach-Object {
            $relative = (
                Get-RelativePathSafe `
                    -FullPath $_.Path
            )

            Write-Line (
                "{0}:{1}: {2}" -f `
                $relative,
                $_.LineNumber,
                $_.Line.Trim()
            )
        }
}


Write-Section "15. PAGE -> SERVICE IMPORT INDEX"

if (Test-Path -LiteralPath $AppRoot) {
    Get-ChildItem `
        -LiteralPath $AppRoot `
        -Recurse `
        -File `
        -Force |
    Where-Object {
        $_.Extension -in @(
            ".ts",
            ".tsx"
        )
    } |
    Select-String `
        -Pattern `
        "@/services/",
        "/services/" `
        -ErrorAction SilentlyContinue |
    ForEach-Object {
        $relative = (
            Get-RelativePathSafe `
                -FullPath $_.Path
        )

        Write-Line (
            "{0}:{1}: {2}" -f `
            $relative,
            $_.LineNumber,
            $_.Line.Trim()
        )
    }
}


Write-Section "16. PAGE -> COMPONENT IMPORT INDEX"

if (Test-Path -LiteralPath $AppRoot) {
    Get-ChildItem `
        -LiteralPath $AppRoot `
        -Recurse `
        -File `
        -Force |
    Where-Object {
        $_.Extension -in @(
            ".ts",
            ".tsx"
        )
    } |
    Select-String `
        -Pattern `
        "@/components/" `
        -ErrorAction SilentlyContinue |
    ForEach-Object {
        $relative = (
            Get-RelativePathSafe `
                -FullPath $_.Path
        )

        Write-Line (
            "{0}:{1}: {2}" -f `
            $relative,
            $_.LineNumber,
            $_.Line.Trim()
        )
    }
}


Write-Section "17. WORKSPACE / AUTH / PERMISSION / CAPABILITY INDEX"

$SearchFiles |
Select-String `
    -Pattern `
    "useWorkspace",
    "WorkspaceContext",
    "workspaceId",
    "useAuth",
    "AuthContext",
    "currentUser",
    "permissions",
    "capabilities",
    "403",
    "forbidden" `
    -ErrorAction SilentlyContinue |
ForEach-Object {
    $relative = (
        Get-RelativePathSafe `
            -FullPath $_.Path
    )

    Write-Line (
        "{0}:{1}: {2}" -f `
        $relative,
        $_.LineNumber,
        $_.Line.Trim()
    )
}


Write-Section "18. LOADING / ERROR / EMPTY / OFFLINE / RETRY STATE INDEX"

$SearchFiles |
Select-String `
    -Pattern `
    "loading",
    "isLoading",
    "error",
    "setError",
    "empty",
    "offline",
    "reconnect",
    "retry",
    "not configured",
    "stale" `
    -ErrorAction SilentlyContinue |
ForEach-Object {
    $relative = (
        Get-RelativePathSafe `
            -FullPath $_.Path
    )

    Write-Line (
        "{0}:{1}: {2}" -f `
        $relative,
        $_.LineNumber,
        $_.Line.Trim()
    )
}


Write-Section "19. TODO / MOCK / PLACEHOLDER / FAKE DATA INDEX"

$SearchFiles |
Select-String `
    -Pattern `
    "TODO",
    "FIXME",
    "mock",
    "placeholder",
    "fake",
    "dummy",
    "hardcoded",
    "sampleData",
    "demoData" `
    -ErrorAction SilentlyContinue |
ForEach-Object {
    $relative = (
        Get-RelativePathSafe `
            -FullPath $_.Path
    )

    Write-Line (
        "{0}:{1}: {2}" -f `
        $relative,
        $_.LineNumber,
        $_.Line.Trim()
    )
}


Write-Section "20. SOURCE COUNTS"

$AllSourceFiles = Get-AllSourceFiles

Write-Line (
    "TOTAL_SOURCE_FILES={0}" -f `
    $AllSourceFiles.Count
)

if (Test-Path -LiteralPath $AppRoot) {
    $PageCount = @(
        Get-ChildItem `
            -LiteralPath $AppRoot `
            -Recurse `
            -File `
            -Force |
        Where-Object {
            $_.Name -in @(
                "page.tsx",
                "page.ts"
            )
        }
    ).Count

    Write-Line (
        "PAGE_COUNT={0}" -f `
        $PageCount
    )
}

$ServicesRoot = Join-Path `
    $FrontendRoot `
    "services"

if (
    Test-Path `
        -LiteralPath $ServicesRoot
) {
    $ServiceCount = @(
        Get-ChildItem `
            -LiteralPath $ServicesRoot `
            -Recurse `
            -File `
            -Force |
        Where-Object {
            $_.Extension -in @(
                ".ts",
                ".tsx"
            )
        }
    ).Count

    Write-Line (
        "SERVICE_FILE_COUNT={0}" -f `
        $ServiceCount
    )
}


Write-Section "21. HANDOFF INSTRUCTIONS FOR NEXT AI"

Write-Line "When uploaded into a new chat:"
Write-Line "1. Treat this as current frontend source-of-truth."
Write-Line "2. Read actual page/component/service code before saying a page works."
Write-Line "3. Distinguish UI, API wiring, realtime wiring, and runtime certification."
Write-Line "4. Do not invent endpoints."
Write-Line "5. Preserve WorkspaceContext and authenticated API client."
Write-Line "6. Backend 403 remains authoritative."
Write-Line "7. Never expose device or agent secrets in browser code."
Write-Line "8. Realtime is freshness only; persisted backend is authoritative."
Write-Line "9. Continue from current files instead of rebuilding completed pages."
Write-Line ""
Write-Line "STATUS LABELS:"
Write-Line "WORKING_API"
Write-Line "API_EVIDENCE_PRESENT"
Write-Line "PARTIAL_API"
Write-Line "REALTIME_CONNECTED"
Write-Line "UI_ONLY"
Write-Line "MISSING"
Write-Line "NEEDS_CERTIFICATION"


Write-Line ""
Write-Line "======================================================================"
Write-Line " END WORKFORCEOS FRONTEND MASTER HANDOFF"
Write-Line "======================================================================"

Write-Host ""
Write-Host "PASS Frontend master handoff generated"
Write-Host "OUTPUT: $OutputFile"

$Info = Get-Item `
    -LiteralPath $OutputFile

Write-Host "SIZE   :" $Info.Length
Write-Host "UPDATED:" $Info.LastWriteTime
