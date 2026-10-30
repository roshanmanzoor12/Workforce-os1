from pathlib import Path
import datetime, shutil, sys
root=Path(sys.argv[1])
page=root/'apps/web/app/(workspace)/monitoring/live-screen/page.tsx'
component=root/'apps/web/components/monitoring/native-live-video.tsx'
source=Path(__file__).with_name('native-live-video.tsx')
if not page.is_file(): sys.exit(f'ERROR: existing page missing: {page}')
s=page.read_text(encoding='utf-8-sig')
if 'WFOS_NATIVE_VIDEO_RECEIVER_V2C' in s:
    print('ALREADY INSTALLED'); sys.exit(0)
start=s.find('{/* WFOS_NATIVE_PLAYER_PENDING_V2B')
end=s.find('<div className="wls-video-footer">',start)
if start<0 or end<0: sys.exit('ERROR: Milestone 2B marker absent; refusing uncertain modification. Install 2B first.')
chunk=s[start:end]
if 'No native live video connected' not in chunk: sys.exit('ERROR: unexpected player block; no changes.')
anchor='"use client";'
if anchor not in s[:200]: sys.exit('ERROR: client component header missing')
# Keep a null stream until a genuine authorized media session is supplied.
# This is intentional: never fabricate an active stream.
replacement='''{/* WFOS_NATIVE_VIDEO_RECEIVER_V2C: direct HTML video receiver; no iframe, no fabricated stream */}
                <NativeLiveVideo stream={null} employeeName={selectedEmployee?.full_name || "employee"} />
                '''
# Avoid assumptions about selectedEmployee shape; no typed dependency required.
replacement=replacement.replace('selectedEmployee?.full_name || "employee"', '"selected employee"')
s=s[:start]+replacement+s[end:]
s=s.replace(anchor,anchor+'\nimport NativeLiveVideo from "@/components/monitoring/native-live-video";',1)
if component.exists() and component.read_text(encoding='utf-8-sig')!=source.read_text(encoding='utf-8'):
    sys.exit(f'ERROR: component path already exists with different content: {component}')
backup=page.with_name(page.name+'.backup-2c-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S'))
shutil.copy2(page,backup)
component.parent.mkdir(parents=True,exist_ok=True)
component.write_text(source.read_text(encoding='utf-8'),encoding='utf-8')
page.write_text(s,encoding='utf-8')
print('PASS: native video receiver component installed')
print('PASS: original page no longer uses a nested browser iframe (2B prerequisite)')
print('BACKUP:',backup)
print('NOTE: stream prop is NULL until authenticated transport is implemented; remote video is NOT active.')
