param(
    [string]$Root = 'C:\workforce-os',
    [int]$MaxFileMB = 2
)
$ErrorActionPreference = 'Stop'
$Root = (Resolve-Path -LiteralPath $Root).Path.TrimEnd('\')
$utf8 = New-Object System.Text.UTF8Encoding($false)
$excludedDirs = @('.git','.next','node_modules','.venv','venv','env','__pycache__','.pytest_cache','.mypy_cache','.ruff_cache','.turbo','dist','build','coverage','.idea','.vscode','logs','tmp','temp','vendor','target','.cache','playwright-report','test-results','uploads','media','staticfiles','migrations')
$excludedNames = @('.env','.env.local','.env.production','.env.development','.env.test','id_rsa','id_ed25519','credentials.json','service-account.json','secrets.json','package-lock.json','pnpm-lock.yaml','yarn.lock','poetry.lock','uv.lock','bun.lockb','bun.lock')
$allowedExt = @('.ts','.tsx','.js','.jsx','.mjs','.cjs','.json','.css','.scss','.sass','.html','.py','.sql','.prisma','.graphql','.gql','.yaml','.yml','.toml','.ini','.cfg','.md','.txt','.sh','.ps1','.dockerignore','.gitignore')
$rootFiles = @('package.json','pnpm-workspace.yaml','turbo.json','docker-compose.yml','docker-compose.yaml','compose.yml','compose.yaml','README.md','pyproject.toml','requirements.txt','alembic.ini','Dockerfile','Makefile')
function Is-Excluded([System.IO.FileInfo]$file) {
    $relative = $file.FullName.Substring($Root.Length).TrimStart('\','/')
    $segments = $relative -split '[\\/]'
    foreach ($segment in $segments[0..($segments.Length - 2)]) { if ($excludedDirs -contains $segment.ToLowerInvariant()) { return $true } }
    $name = $file.Name.ToLowerInvariant()
    if ($excludedNames -contains $name -or $name -like '.env.*' -or $name -like '*.pem' -or $name -like '*.key' -or $name -like '*.p12' -or $name -like '*.pfx' -or $name -like '*.sqlite*' -or $name -like '*.db' -or $name -like '*secret*' -or $name -like '*credential*') { return $true }
    if ($name -like '*full_context*' -or $name -like '*integration*export*' -or $name -like '*.min.js' -or $name -like '*.map') { return $true }
    if ($file.Length -gt ($MaxFileMB * 1MB)) { return $true }
    return (($allowedExt -contains $file.Extension.ToLowerInvariant()) -or ($rootFiles -contains $file.Name))
}
function Classify([string]$relative) {
    $r = $relative.Replace('\','/').ToLowerInvariant()
    if ($r -match '^(apps/web|frontend|client|web)/') { return 'frontend' }
    if ($r -match '^(apps/api|apps/backend|backend|server|api|services/api)/') { return 'backend' }
    if ($r -match '(^|/)(next\.config\.|tailwind\.config\.|postcss\.config\.|tsconfig\.json$)' -and $r -notmatch '^(apps/api|backend|server)/') { return 'frontend' }
    if ($r -match '(^|/)(requirements[^/]*\.txt|pyproject\.toml|alembic\.ini|manage\.py|main\.py)$') { return 'backend' }
    return 'shared'
}
$files = @(Get-ChildItem -LiteralPath $Root -File -Recurse -Force | Where-Object { Is-Excluded $_ } | Sort-Object FullName)
$records = @($files | ForEach-Object {
    $rel = $_.FullName.Substring($Root.Length).TrimStart('\','/').Replace('\','/')
    [pscustomobject]@{ File = $_; Relative = $rel; Area = (Classify $rel) }
})
foreach ($area in @('frontend','backend')) {
    $outName = if ($area -eq 'frontend') { 'FRONTEND_FULL_CONTEXT.md' } else { 'BACKEND_FULL_CONTEXT.md' }
    $outPath = Join-Path $Root $outName
    $selected = @($records | Where-Object { $_.Area -eq $area -or $_.Area -eq 'shared' })
    $writer = New-Object System.IO.StreamWriter($outPath, $false, $utf8)
    try {
        $writer.WriteLine("# WorkforceOS $($area.ToUpperInvariant()) - CURRENT PROJECT CONTEXT")
        $writer.WriteLine('Generated: ' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'))
        $writer.WriteLine('Project root: C:\workforce-os')
        $writer.WriteLine('This is a source snapshot, not an automatically verified architecture specification.')
        $writer.WriteLine('Sensitive files, dependencies, generated output, and files above the size limit are excluded.')
        $writer.WriteLine('IMPORTANT: Review for secrets and personal data before uploading or sharing.')
        $writer.WriteLine('')
        $writer.WriteLine('## COMPLETE INCLUDED FILE PATH INDEX')
        foreach ($item in $selected) { $writer.WriteLine('- ' + $item.Relative) }
        $writer.WriteLine('')
        $writer.WriteLine('## SOURCE FILES (CURRENT ON DISK)')
        foreach ($item in $selected) {
            $writer.WriteLine('')
            $writer.WriteLine('---')
            $writer.WriteLine('### FILE: ' + $item.Relative)
            $writer.WriteLine('Area: ' + $item.Area)
            $writer.WriteLine('```' + $item.File.Extension.TrimStart('.'))
            try {
                $content = [System.IO.File]::ReadAllText($item.File.FullName)
                # Mask common inline assignments; still manually review exports before sharing.
                $content = [regex]::Replace($content, '(?im)^([ \t]*(?:[A-Za-z_][A-Za-z0-9_]*(?:SECRET|TOKEN|PASSWORD|API_KEY|PRIVATE_KEY)[A-Za-z0-9_]*|(?:secret|token|password|api_key|private_key))[ \t]*[:=][ \t]*)([^\r\n]+)', '$1[REDACTED]')
                $writer.WriteLine($content)
            } catch { $writer.WriteLine('[READ ERROR: ' + $_.Exception.Message + ']') }
            $writer.WriteLine('```')
        }
    } finally { $writer.Dispose() }
    $sizeMB = [math]::Round((Get-Item -LiteralPath $outPath).Length / 1MB, 2)
    Write-Host "Created $outPath ($sizeMB MB; $($selected.Count) files)" -ForegroundColor Green
}
Write-Host 'Done. Check both exports for sensitive data before uploading.' -ForegroundColor Yellow
