param(
    [string]$FrontendRoot = "C:\workforce-os\apps\web",
    [string]$OutputFile = "C:\workforce-os\WORKFORCE_FRONTEND_MASTER_HANDOFF.txt"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $FrontendRoot)) {
    throw "Frontend root not found: $FrontendRoot"
}

$FrontendRoot = (
    Resolve-Path $FrontendRoot
).Path

$OutputDirectory = Split-Path `
    -Parent `
    $OutputFile

if (
    $OutputDirectory `
    -and `
    -not (Test-Path $OutputDirectory)
) {
    New-Item `
        -ItemType Directory `
        -Force `
        $OutputDirectory |
        Out-Null
}


function Write-Line {
    param(
        [string]$Text = ""
    )

    $Text |
        Add-Content `
            -Path $OutputFile `
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


function Get-RelativePath {
    param(
        [string]$FullPath
    )

    $root = $FrontendRoot.TrimEnd(
        "\"
    )

    if (
        $FullPath.StartsWith(
            $root,
            [System.StringComparison]::OrdinalIgnoreCase
        )
    ) {
        return (
            $FullPath
                .Substring(
                    $root.Length
                )
                .TrimStart(
                    "\"
                )
        )
    }

    return $FullPath
}


function Is-ExcludedPath {
    param(
        [string]$FullPath
    )

    $normalized = (
        $FullPath
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


function Is-SourceFile {
    param(
        [System.IO.FileInfo]$File
    )

    if (
        Is-ExcludedPath `
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

    $relative = Get-RelativePath `
        -FullPath $File.FullName

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


Set-Content `
    -Path $OutputFile `
    -Value "" `
    -Encoding UTF8


Write-Line "======================================================================"
Write-Line " WORKFORCEOS FRONTEND MASTER HANDOFF"
Write-Line "======================================================================"
Write-Line ""
Write-Line "PURPOSE:"
Write-Line "This file is a complete handoff of the current WorkforceOS frontend."
Write-Line "Give this file to ChatGPT in a new conversation before continuing"
Write-Line "frontend API wiring, page implementation, debugging, or certification."
Write-Line ""
Write-Line "IMPORTANT:"
Write-Line "- Treat the source below as current frontend truth."
Write-Line "- Do not invent missing page behavior."
Write-Line "- Backend certification status must be supplied separately if newer."
Write-Line "- Environment SECRET VALUES are intentionally NOT included."
Write-Line ""
Write-Line "FRONTEND_ROOT: $FrontendRoot"
Write-Line "GENERATED_AT: $((Get-Date).ToString('yyyy-MM-dd HH:mm:ss zzz'))"


# ======================================================================
# PROJECT STRUCTURE
# ======================================================================

Write-Section "1. FRONTEND DIRECTORY TREE"

Get-ChildItem `
    -Path $FrontendRoot `
    -Recurse `
    -Force |
    Where-Object {
        -not (
            Is-ExcludedPath `
                -FullPath $_.FullName
        )
    } |
    Sort-Object FullName |
    ForEach-Object {
        $relative = Get-RelativePath `
            -FullPath $_.FullName

        if ($_.PSIsContainer) {
            Write-Line "DIR  $relative"
        }
        else {
            Write-Line "FILE $relative"
        }
    }


# ======================================================================
# NEXT ROUTES
# ======================================================================

Write-Section "2. NEXT.JS ROUTE / PAGE INVENTORY"

$AppRoot = Join-Path `
    $FrontendRoot `
    "app"

if (Test-Path $AppRoot) {
    Get-ChildItem `
        -Path $AppRoot `
        -Recurse `
        -File |
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
            $relative = Get-RelativePath `
                -FullPath $_.FullName

            Write-Line $relative
        }
}


# ======================================================================
# PAGE FILES
# ======================================================================

Write-Section "3. FULL NEXT.JS APP / PAGE SOURCE"

if (Test-Path $AppRoot) {
    Get-ChildItem `
        -Path $AppRoot `
        -Recurse `
        -File |
        Where-Object {
            Is-SourceFile $_
        } |
        Sort-Object FullName |
        ForEach-Object {
            Write-FileContent $_
        }
}


# ======================================================================
# SERVICES
# ======================================================================

Write-Section "4. FULL API SERVICES SOURCE"

$ServicesRoot = Join-Path `
    $FrontendRoot `
    "services"

if (Test-Path $ServicesRoot) {
    Get-ChildItem `
        -Path $ServicesRoot `
        -Recurse `
        -File |
        Where-Object {
            Is-SourceFile $_
        } |
        Sort-Object FullName |
        ForEach-Object {
            Write-FileContent $_
        }
}


# ======================================================================
# CONTEXTS
# ======================================================================

Write-Section "5. FULL CONTEXT SOURCE"

$ContextsRoot = Join-Path `
    $FrontendRoot `
    "contexts"

if (Test-Path $ContextsRoot) {
    Get-ChildItem `
        -Path $ContextsRoot `
        -Recurse `
        -File |
        Where-Object {
            Is-SourceFile $_
        } |
        Sort-Object FullName |
        ForEach-Object {
            Write-FileContent $_
        }
}


# ======================================================================
# HOOKS
# ======================================================================

Write-Section "6. FULL HOOK SOURCE"

$HooksRoot = Join-Path `
    $FrontendRoot `
    "hooks"

if (Test-Path $HooksRoot) {
    Get-ChildItem `
        -Path $HooksRoot `
        -Recurse `
        -File |
        Where-Object {
            Is-SourceFile $_
        } |
        Sort-Object FullName |
        ForEach-Object {
            Write-FileContent $_
        }
}


# ======================================================================
# LIB
# ======================================================================

Write-Section "7. FULL LIB / API CLIENT SOURCE"

$LibRoot = Join-Path `
    $FrontendRoot `
    "lib"

if (Test-Path $LibRoot) {
    Get-ChildItem `
        -Path $LibRoot `
        -Recurse `
        -File |
        Where-Object {
            Is-SourceFile $_
        } |
        Sort-Object FullName |
        ForEach-Object {
            Write-FileContent $_
        }
}


# ======================================================================
# TYPES
# ======================================================================

Write-Section "8. FULL TYPE DEFINITIONS"

$TypesRoot = Join-Path `
    $FrontendRoot `
    "types"

if (Test-Path $TypesRoot) {
    Get-ChildItem `
        -Path $TypesRoot `
        -Recurse `
        -File |
        Where-Object {
            Is-SourceFile $_
        } |
        Sort-Object FullName |
        ForEach-Object {
            Write-FileContent $_
        }
}


# ======================================================================
# COMPONENTS
# ======================================================================

Write-Section "9. FULL COMPONENT SOURCE"

$ComponentsRoot = Join-Path `
    $FrontendRoot `
    "components"

if (Test-Path $ComponentsRoot) {
    Get-ChildItem `
        -Path $ComponentsRoot `
        -Recurse `
        -File |
        Where-Object {
            Is-SourceFile $_
        } |
        Sort-Object FullName |
        ForEach-Object {
            Write-FileContent $_
        }
}


# ======================================================================
# SCRIPTS
# ======================================================================

Write-Section "10. FRONTEND SCRIPTS"

$ScriptsRoot = Join-Path `
    $FrontendRoot `
    "scripts"

if (Test-Path $ScriptsRoot) {
    Get-ChildItem `
        -Path $ScriptsRoot `
        -Recurse `
        -File |
        Where-Object {
            Is-SourceFile $_
        } |
        Sort-Object FullName |
        ForEach-Object {
            Write-FileContent $_
        }
}


# ======================================================================
# CONFIG FILES
# ======================================================================

Write-Section "11. PROJECT CONFIGURATION"

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

    if (Test-Path $ConfigPath) {
        Write-FileContent (
            Get-Item $ConfigPath
        )
    }
}


# ======================================================================
# ENVIRONMENT VARIABLE NAMES ONLY
# ======================================================================

Write-Section "12. ENVIRONMENT VARIABLE NAMES — VALUES REDACTED"

$EnvironmentFiles = Get-ChildItem `
    -Path $FrontendRoot `
    -File `
    -Force |
    Where-Object {
        $_.Name -like ".env*"
    }

foreach ($EnvFile in $EnvironmentFiles) {
    Write-Line ""
    Write-Line "ENV_FILE: $($EnvFile.Name)"

    Get-Content `
        -LiteralPath $EnvFile.FullName |
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


# ======================================================================
# API / NETWORK INDEX
# ======================================================================

Write-Section "13. API / NETWORK / REALTIME USAGE INDEX"

$SearchPatterns = @(
    "fetch\(",
    "axios",
    "apiClient",
    "api\.",
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

$SearchFiles = Get-ChildItem `
    -Path $FrontendRoot `
    -Recurse `
    -File |
    Where-Object {
        Is-SourceFile $_
    }

foreach ($Pattern in $SearchPatterns) {
    Write-Line ""
    Write-Line "### PATTERN: $Pattern"

    $SearchFiles |
        Select-String `
            -Pattern $Pattern `
            -ErrorAction SilentlyContinue |
        ForEach-Object {
            $relative = Get-RelativePath `
                -FullPath $_.Path

            Write-Line (
                "$relative:$($_.LineNumber): " `
                + $_.Line.Trim()
            )
        }
}


# ======================================================================
# SERVICE IMPORTS FROM PAGES
# ======================================================================

Write-Section "14. PAGE -> SERVICE IMPORT INDEX"

if (Test-Path $AppRoot) {
    Get-ChildItem `
        -Path $AppRoot `
        -Recurse `
        -File `
        -Include "*.ts","*.tsx" |
        Select-String `
            -Pattern `
            "@/services/",
            "from `"../../services",
            "from `"../services",
            "from '../../services",
            "from '../services" |
        ForEach-Object {
            $relative = Get-RelativePath `
                -FullPath $_.Path

            Write-Line (
                "$relative:$($_.LineNumber): " `
                + $_.Line.Trim()
            )
        }
}


# ======================================================================
# COMPONENT IMPORTS FROM PAGES
# ======================================================================

Write-Section "15. PAGE -> COMPONENT IMPORT INDEX"

if (Test-Path $AppRoot) {
    Get-ChildItem `
        -Path $AppRoot `
        -Recurse `
        -File `
        -Include "*.ts","*.tsx" |
        Select-String `
            -Pattern `
            "@/components/" |
        ForEach-Object {
            $relative = Get-RelativePath `
                -FullPath $_.Path

            Write-Line (
                "$relative:$($_.LineNumber): " `
                + $_.Line.Trim()
            )
        }
}


# ======================================================================
# WORKSPACE CONTEXT USAGE
# ======================================================================

Write-Section "16. WORKSPACE / AUTH CONTEXT USAGE"

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
        "capabilities" |
    ForEach-Object {
        $relative = Get-RelativePath `
            -FullPath $_.Path

        Write-Line (
            "$relative:$($_.LineNumber): " `
            + $_.Line.Trim()
        )
    }


# ======================================================================
# UI STATE INDEX
# ======================================================================

Write-Section "17. LOADING / ERROR / EMPTY / FORBIDDEN / OFFLINE STATES"

$SearchFiles |
    Select-String `
        -Pattern `
        "loading",
        "isLoading",
        "error",
        "setError",
        "empty",
        "forbidden",
        "403",
        "offline",
        "reconnect",
        "retry",
        "not configured",
        "stale" |
    ForEach-Object {
        $relative = Get-RelativePath `
            -FullPath $_.Path

        Write-Line (
            "$relative:$($_.LineNumber): " `
            + $_.Line.Trim()
        )
    }


# ======================================================================
# TODO / MOCK / PLACEHOLDER INDEX
# ======================================================================

Write-Section "18. TODO / MOCK / PLACEHOLDER / FAKE DATA INDEX"

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
        "demoData" |
    ForEach-Object {
        $relative = Get-RelativePath `
            -FullPath $_.Path

        Write-Line (
            "$relative:$($_.LineNumber): " `
            + $_.Line.Trim()
        )
    }


# ======================================================================
# PUBLIC ASSET INVENTORY
# ======================================================================

Write-Section "19. PUBLIC ASSET INVENTORY"

$PublicRoot = Join-Path `
    $FrontendRoot `
    "public"

if (Test-Path $PublicRoot) {
    Get-ChildItem `
        -Path $PublicRoot `
        -Recurse `
        -File |
        Sort-Object FullName |
        ForEach-Object {
            $relative = Get-RelativePath `
                -FullPath $_.FullName

            Write-Line (
                "$relative | " `
                + "$($_.Length) bytes"
            )
        }
}
else {
    Write-Line "No public directory found."
}


# ======================================================================
# SUMMARY COUNTS
# ======================================================================

Write-Section "20. SOURCE COUNTS"

$AllSourceFiles = Get-ChildItem `
    -Path $FrontendRoot `
    -Recurse `
    -File |
    Where-Object {
        Is-SourceFile $_
    }

Write-Line (
    "TOTAL_SOURCE_FILES=" `
    + $AllSourceFiles.Count
)

if (Test-Path $AppRoot) {
    $PageCount = (
        Get-ChildItem `
            -Path $AppRoot `
            -Recurse `
            -File `
            -Filter "page.tsx"
    ).Count

    Write-Line (
        "PAGE_TSX_COUNT=" `
        + $PageCount
    )
}

if (Test-Path $ServicesRoot) {
    $ServiceCount = (
        Get-ChildItem `
            -Path $ServicesRoot `
            -Recurse `
            -File `
            -Include "*.ts","*.tsx"
    ).Count

    Write-Line (
        "SERVICE_FILE_COUNT=" `
        + $ServiceCount
    )
}


Write-Section "21. HANDOFF INSTRUCTIONS FOR NEXT AI"

Write-Line "When this file is uploaded into a new ChatGPT conversation:"
Write-Line ""
Write-Line "1. Treat this file as the current frontend source-of-truth snapshot."
Write-Line "2. Read actual page/service/component code before claiming a page works."
Write-Line "3. Distinguish:"
Write-Line "   - UI exists"
Write-Line "   - API service exists"
Write-Line "   - page actually calls service"
Write-Line "   - realtime actually wired"
Write-Line "   - page fully certified"
Write-Line "4. Do not assume UI-only pages are backend connected."
Write-Line "5. Do not invent API endpoints."
Write-Line "6. Preserve WorkspaceContext and authenticated API-client architecture."
Write-Line "7. Backend 403 remains authoritative even if frontend hides actions."
Write-Line "8. Never expose device/agent secrets in browser code."
Write-Line "9. Realtime is for freshness; persisted backend remains authoritative."
Write-Line "10. Continue from current files instead of rebuilding completed pages."
Write-Line ""
Write-Line "Recommended status labels:"
Write-Line "WORKING_API = page directly uses real backend service/API."
Write-Line "PARTIAL_API = some functionality is real, some is incomplete."
Write-Line "REALTIME_CONNECTED = websocket/realtime integration exists."
Write-Line "UI_ONLY = page exists but no verified backend data path."
Write-Line "MISSING = route/page does not exist."
Write-Line "NEEDS_CERTIFICATION = implementation exists but final runtime gate is absent."


Write-Line ""
Write-Line "======================================================================"
Write-Line " END WORKFORCEOS FRONTEND MASTER HANDOFF"
Write-Line "======================================================================"

Write-Host ""
Write-Host "PASS Frontend master handoff generated"
Write-Host "OUTPUT: $OutputFile"

$Info = Get-Item $OutputFile

Write-Host "SIZE  :" $Info.Length
Write-Host "UPDATED:" $Info.LastWriteTime
