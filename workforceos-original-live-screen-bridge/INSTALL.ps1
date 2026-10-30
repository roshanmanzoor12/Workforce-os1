$ErrorActionPreference = 'Stop'
$Root = 'C:\workforce-os'
$Page = Join-Path $Root 'apps\web\app\(workspace)\monitoring\live-screen\page.tsx'
$TestPage = Join-Path $Root 'apps\web\app\(workspace)\browser-screen-share\page.tsx'
if (!(Test-Path -LiteralPath $Page)) { throw "Live Screen page missing: $Page" }
if (!(Test-Path -LiteralPath $TestPage)) { throw "Browser-share test page missing: $TestPage. Install previous browser-share package first." }
$source = [IO.File]::ReadAllText($Page)
$start = '<div className="wls-video">'
$end = '<div className="wls-video-footer">'
if ($source.Contains('WFOS_BROWSER_SHARE_EMBED_V1')) { Write-Host 'Already installed.' -ForegroundColor Green; exit 0 }
$at = $source.IndexOf($start)
if ($at -lt 0) { throw 'Expected wls-video block not found, no changes made.' }
$endAt = $source.IndexOf($end, $at)
if ($endAt -lt 0) { throw 'Expected wls-video-footer block not found, no changes made.' }
$backup = "$Page.backup-$(Get-Date -Format yyyyMMdd-HHmmss)"
Copy-Item -LiteralPath $Page -Destination $backup
$new = @'
{/* WFOS_BROWSER_SHARE_EMBED_V1: real employee-approved browser screen share */}
                <div className="wls-video" style={{ minHeight: 620, padding: 0, background: "#fff" }}>
                  <iframe
                    title="Employee-approved live browser screen sharing"
                    src="/browser-screen-share"
                    style={{ display: "block", width: "100%", height: 680, border: 0, background: "#fff" }}
                    allow="display-capture; autoplay"
                  />
                </div>

'@
$updated = $source.Substring(0,$at) + $new + $source.Substring($endAt)
[IO.File]::WriteAllText($Page,$updated, (New-Object System.Text.UTF8Encoding($false)))
Write-Host "Integrated browser sharing into original Live Screen page." -ForegroundColor Green
Write-Host "Backup: $backup"
Write-Host 'Owner: open /monitoring/live-screen, use the embedded Request Screen Share button.'
Write-Host 'Employee: open /browser-screen-share, click Accept & Choose Screen when a request appears.'
Write-Host 'NOTE: Existing disabled agent Request session button remains disabled; this uses browser WebRTC, not Windows-agent capture.'
