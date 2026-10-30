param([switch]$Apply,[switch]$Rollback)
$ErrorActionPreference='Stop'
$Root='C:\workforce-os'
$Here=Split-Path -Parent $MyInvocation.MyCommand.Path
$Page=Join-Path $Root 'apps\web\app\(workspace)\monitoring\live-screen\page.tsx'
$Viewer=Join-Path $Root 'apps\web\components\monitoring\native-session-frame-viewer.tsx'
$Source=Join-Path $Here 'patch\apps\web\components\monitoring\native-session-frame-viewer.tsx'
$Marker=Join-Path $Here 'last-backup.txt'
$Utf8=New-Object System.Text.UTF8Encoding($false)
if($Rollback){
 if(!(Test-Path -LiteralPath $Marker)){throw 'Backup pointer missing'}
 $B=(Get-Content -LiteralPath $Marker -Raw).Trim()
 if(!(Test-Path -LiteralPath (Join-Path $B 'page.tsx'))){throw 'Page backup missing'}
 Copy-Item -LiteralPath (Join-Path $B 'page.tsx') -Destination $Page -Force
 $Prior=Join-Path $B 'native-session-frame-viewer.tsx'
 if(Test-Path -LiteralPath $Prior){Copy-Item -LiteralPath $Prior -Destination $Viewer -Force}else{Remove-Item -LiteralPath $Viewer -Force -ErrorAction SilentlyContinue}
 Write-Host "ROLLBACK COMPLETE: $B";exit 0
}
if(!(Test-Path -LiteralPath $Page) -or !(Test-Path -LiteralPath $Source)){throw 'Required source missing'}
$Content=Get-Content -LiteralPath $Page -Raw
if($Content.Contains('NativeSessionFrameViewer')){throw 'Viewer already installed; aborting safely'}
if(!$Content.Contains('const authorizedSessionActive =') -or !$Content.Contains('import { WorkspaceRequired }')){throw 'Current Live Screen page is incompatible'}
$Pattern='(?s)(<div className="ls-screen" ref=\{viewerRef\}>\s*)(<BrowserScreenSharePanel\b[^>]*/>)(\s*</div>)'
$Match=[regex]::Match($Content,$Pattern)
if(!$Match.Success){throw 'Viewer location mismatch: no supported BrowserScreenSharePanel in main ls-screen. No changes made.'}
$Import='import NativeSessionFrameViewer from "@/components/monitoring/native-session-frame-viewer";'
$Content=$Content.Replace('import { WorkspaceRequired }',$Import+"`r`n"+'import { WorkspaceRequired }')
$Content=[regex]::Replace($Content,$Pattern,{
 param($m)
 $prefix=$m.Groups[1].Value
 $browser=$m.Groups[2].Value
 $suffix=$m.Groups[3].Value
 return $prefix+'{authorizedSessionActive && workspaceId && session?.sessionId ? ('+"`r`n"+
   '  <NativeSessionFrameViewer workspaceId={workspaceId} sessionId={session.sessionId} paused={viewPaused} />'+"`r`n"+
   ') : ('+"`r`n"+'  '+$browser+"`r`n"+')}' +$suffix
},1)
if(!$Content.Contains('<NativeSessionFrameViewer workspaceId=')){throw 'Viewer insertion failed; no files changed'}
if(!$Apply){Write-Host 'DRY RUN PASSED: V2 viewer compatible with current single-viewer layout.';Write-Host 'WARNING: This does not create native sessions, backend gateway, or Windows capture.';exit 0}
$B=Join-Path $Root ('workforce-patch-backups\native-viewer-v2-'+(Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Force -Path $B | Out-Null
Copy-Item -LiteralPath $Page -Destination (Join-Path $B 'page.tsx') -Force
if(Test-Path -LiteralPath $Viewer){Copy-Item -LiteralPath $Viewer -Destination (Join-Path $B 'native-session-frame-viewer.tsx') -Force}
[IO.File]::WriteAllText($Page,$Content,$Utf8)
Copy-Item -LiteralPath $Source -Destination $Viewer -Force
Set-Content -LiteralPath $Marker -Value $B
Write-Host "VIEWER V2 INSTALLED. Backup: $B"
Write-Host 'WARNING: Native media publishing and production gateway NOT enabled by this patch.'
