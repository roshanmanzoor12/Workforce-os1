param([switch]$Apply, [switch]$Rollback)
$ErrorActionPreference='Stop'
$Root='C:\workforce-os'
$Here=Split-Path -Parent $MyInvocation.MyCommand.Path
$Page=Join-Path $Root 'apps\web\app\(workspace)\monitoring\live-screen\page.tsx'
$Viewer=Join-Path $Root 'apps\web\components\monitoring\native-session-frame-viewer.tsx'
$Source=Join-Path $Here 'patch\apps\web\components\monitoring\native-session-frame-viewer.tsx'
$Marker=Join-Path $Here 'last-backup.txt'
if($Rollback){
 if(!(Test-Path -LiteralPath $Marker)){throw 'Backup manifest missing'}
 $B=(Get-Content -LiteralPath $Marker -Raw).Trim()
 Copy-Item -LiteralPath (Join-Path $B 'page.tsx') -Destination $Page -Force
 $Prior=Join-Path $B 'native-session-frame-viewer.tsx'
 if(Test-Path $Prior){Copy-Item -LiteralPath $Prior -Destination $Viewer -Force}else{Remove-Item -LiteralPath $Viewer -Force -ErrorAction SilentlyContinue}
 Write-Host "Rolled back frontend native viewer from $B"; exit 0
}
if(!(Test-Path -LiteralPath $Page) -or !(Test-Path -LiteralPath $Source)){throw 'Required source missing'}
$Content=Get-Content -LiteralPath $Page -Raw
if($Content.Contains('NativeSessionFrameViewer')){throw 'Native viewer already installed; no changes applied'}
if(!$Content.Contains('const authorizedSessionActive =')){throw 'Unexpected Live Screen file: session state missing'}
$Needle='<div className="ls-screenempty" role="status" aria-live="polite">'
if(!$Content.Contains($Needle)){throw 'Unexpected Live Screen layout: placeholder missing'}
if(!$Content.Contains('const viewerRef = useRef')){throw 'Unexpected Live Screen page: viewer ref missing'}
if(!$Content.Contains('import { WorkspaceRequired }')){throw 'Unexpected Live Screen imports'}
if(!$Apply){Write-Host 'DRY RUN PASSED: native viewer integration only. Does not implement Companion capture.';exit 0}
$B=Join-Path $Root ('workforce-patch-backups\native-viewer-'+(Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Force -Path $B | Out-Null
Copy-Item -LiteralPath $Page -Destination (Join-Path $B 'page.tsx')
if(Test-Path -LiteralPath $Viewer){Copy-Item -LiteralPath $Viewer -Destination (Join-Path $B 'native-session-frame-viewer.tsx')}
$Import='import NativeSessionFrameViewer from "@/components/monitoring/native-session-frame-viewer";'
$Content=$Content.Replace('import { WorkspaceRequired }', $Import+"`r`n"+'import { WorkspaceRequired }')
# Use native stream exclusively for active, approved native sessions, otherwise preserve page message.
$Content=$Content.Replace($Needle, '{authorizedSessionActive && workspaceId && session?.sessionId ? <NativeSessionFrameViewer workspaceId={workspaceId} sessionId={session.sessionId} paused={viewPaused} /> : ('+"`r`n"+$Needle)
$EndNeedle='</div>'+"`r`n"+'              </div>'+"`r`n"+'              <div className="ls-foot">'
if(!$Content.Contains($EndNeedle)){$EndNeedle='</div>'+"`n"+'              </div>'+"`n"+'              <div className="ls-foot">'}
if(!$Content.Contains($EndNeedle)){throw 'Cannot find viewer placeholder closing boundary; source unchanged'}
$Content=$Content.Replace($EndNeedle,'</div>'+"`r`n"+'                )}'+"`r`n"+'              </div>'+"`r`n"+'              <div className="ls-foot">')
$Utf8=New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($Page,$Content,$Utf8)
Copy-Item -LiteralPath $Source -Destination $Viewer -Force
Set-Content -LiteralPath $Marker -Value $B
Write-Host "NATIVE VIEWER INSTALLED. Backup: $B"
Write-Host 'No backend endpoints installed and no native Windows Companion changes.'
