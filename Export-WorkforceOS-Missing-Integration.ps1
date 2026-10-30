# Collect source required to wire authenticated workspace-open and logout to Live Screen.
# Run from C:\workforce-os; the script excludes configs, credentials, build artifacts, and .env files.
$ErrorActionPreference = 'Stop'
$Root = 'C:\workforce-os'
if (-not (Test-Path $Root)) { throw "Project root not found: $Root" }
$Output = Join-Path $Root 'WorkforceOS-Missing-Integration-Source.zip'
$Temp = Join-Path $env:TEMP ('workforce-missing-' + [guid]::NewGuid().ToString('N'))
$Directories = @(
  'backend\app\modules\auth', 'backend\app\modules\device_agent',
  'backend\app\modules\desktop_agent', 'backend\app\modules\devices',
  'backend\app\modules\employees', 'backend\app\modules\live_monitoring',
  'backend\app\modules\work_sessions', 'backend\app\modules\workspaces',
  'backend\app\modules\workspace_access', 'backend\app\modules\workspace_permissions',
  'backend\app\modules\workspace_members',
  'backend\app\api', 'backend\app\core',
  'apps\web\app\(auth)', 'apps\web\app\(workspace)',
  'apps\web\contexts', 'apps\web\services', 'apps\web\lib\auth',
  'apps\web\components\app-shell',
  'agent\WorkforceOS.Agent\LiveScreen', 'agent\WorkforceOS.ScreenCompanion'
)
$Allowed = @('.py','.ts','.tsx','.cs','.sql')
$Exclude = '(\\|/)(node_modules|\.next[^\\/]*|\.git|\.venv|venv|__pycache__|dist|build|bin|obj|artifacts|logs|migrations)(\\|/)' 
try {
  New-Item -ItemType Directory -Force -Path $Temp | Out-Null
  $copied=0
  foreach($dir in $Directories){
    $folder=Join-Path $Root $dir
    if(-not (Test-Path -LiteralPath $folder)){ continue }
    Get-ChildItem -LiteralPath $folder -File -Recurse -ErrorAction SilentlyContinue | ForEach-Object {
      $file=$_
      if($file.FullName -match $Exclude -or $file.Extension -notin $Allowed -or $file.Length -gt 250KB -or $file.Name -match '(?i)(secret|credential|token|private|password|\.env)'){return}
      $relative=$file.FullName.Substring($Root.Length).TrimStart('\')
      $dest=Join-Path $Temp $relative
      $parent=Split-Path $dest -Parent
      New-Item -ItemType Directory -Force -Path $parent | Out-Null
      Copy-Item -LiteralPath $file.FullName -Destination $dest
      $script:copied++
    }
  }
  if($copied -eq 0){throw 'No source files found. Confirm project root.'}
  if(Test-Path $Output){Remove-Item $Output -Force}
  Compress-Archive -Path (Join-Path $Temp '*') -DestinationPath $Output -CompressionLevel Optimal
  Write-Host "CREATED: $Output" -ForegroundColor Green
  Write-Host "FILES: $copied"
  Write-Host 'Review ZIP for secrets or proprietary information before uploading.' -ForegroundColor Yellow
} finally { if(Test-Path $Temp){ Remove-Item $Temp -Recurse -Force } }
