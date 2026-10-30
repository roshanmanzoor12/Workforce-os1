from pathlib import Path
from datetime import datetime
import shutil, sys
root=Path(sys.argv[1]); target=root/'apps/web/app/(workspace)/monitoring/live-screen/page.tsx'
if not target.is_file(): sys.exit(f'MISSING: {target}')
s=target.read_text(encoding='utf-8-sig')
marker='WFOS_BROWSER_SHARE_EMBED_V1'
if marker not in s:
    if 'WFOS_NATIVE_PLAYER_PENDING_V2B' in s:
        print('ALREADY PATCHED'); sys.exit(0)
    sys.exit('SKIPPED: legacy browser iframe marker is not present; no changes made.')
start=s.find('                {/* WFOS_BROWSER_SHARE_EMBED_V1')
end=s.find('<div className="wls-video-footer">',start)
if start<0 or end<0: sys.exit('SKIPPED: precise iframe block not found; no changes made.')
chunk=s[start:end]
if '<iframe' not in chunk or 'src="/browser-screen-share"' not in chunk: sys.exit('SKIPPED: unexpected video block; no changes made.')
replacement='''                {/* WFOS_NATIVE_PLAYER_PENDING_V2B: do not show a nested browser demo as native video */}
                <div className="wls-video" style={{ minHeight: 420, display: "flex", alignItems: "center", justifyContent: "center", textAlign: "center", padding: 28 }}>
                  <div style={{ maxWidth: 420, color: "#fff" }} role="status">
                    <Monitor size={44} style={{ margin: "0 auto 14px" }} />
                    <strong style={{ display: "block", fontSize: 17, marginBottom: 8 }}>No native live video connected</strong>
                    <p style={{ lineHeight: 1.6, margin: 0 }}>
                      The Windows companion currently supports employee-approved local preview only.
                      A secure native media sender and authorized viewer transport must be installed before video can appear here.
                    </p>
                  </div>
                </div>
                '''
backup=target.with_name(target.name+'.backup-'+datetime.now().strftime('%Y%m%d-%H%M%S'))
shutil.copy2(target,backup)
updated=s[:start]+replacement+s[end:]
target.write_text(updated,encoding='utf-8')
print('PATCH APPLIED:',target)
print('BACKUP:',backup)
print('No screen transmission or permission model was changed.')
