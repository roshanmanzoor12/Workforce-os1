from pathlib import Path
import datetime, shutil, sys
root=Path(sys.argv[1])
pkg=Path(__file__).parent
program=root/'agent/WorkforceOS.ScreenCompanion/Program.cs'
page=root/'apps/web/app/(workspace)/monitoring/live-screen/page.tsx'
if not program.is_file() or not page.is_file(): raise SystemExit('ERROR: Existing Program.cs or Live Screen page missing')
p=program.read_text(encoding='utf-8-sig'); ui=page.read_text(encoding='utf-8-sig')
if 'WFOS_3B_NATIVE_PUBLISHER' in p or 'WFOS_3B_NATIVE_VIEWER' in ui: raise SystemExit('ALREADY INSTALLED (no changes)')
if 'private void CaptureFrame()' not in p or '_preview.Image = (Image)bitmap.Clone();' not in p: raise SystemExit('ERROR: Milestone1 capture pattern changed; no patch applied')
if 'import NativeLiveVideo from' not in ui or '<NativeLiveVideo stream={null}' not in ui: raise SystemExit('ERROR: Milestone2C component not found in original Live Screen page; no patch applied')
# Prep all writes first: refuse if there are existing custom component files.
files={
 root/'agent/WorkforceOS.ScreenCompanion/RemoteFramePublisher.cs': pkg/'agent/WorkforceOS.ScreenCompanion/RemoteFramePublisher.cs',
 root/'apps/web/components/monitoring/native-jpeg-stream.tsx': pkg/'apps/web/components/monitoring/native-jpeg-stream.tsx',
}
for dst,src in files.items():
 if dst.exists() and dst.read_bytes()!=src.read_bytes(): raise SystemExit(f'ERROR: Existing custom file would be overwritten: {dst}')
p=p.replace('private bool _sharing;', '''private bool _sharing;
    // WFOS_3B_NATIVE_PUBLISHER: sender exists only while employee-authorized sharing is active.
    private RemoteFramePublisher? _publisher;
    private readonly string _remoteUrl = Environment.GetEnvironmentVariable("WFOS_SCREEN_SEND_URL") ?? "";''',1)
p=p.replace('''"Start employee-visible LOCAL desktop preview? This milestone does NOT transmit frames to the owner or backend. You can stop any time.",''','''(_remoteUrl.Length > 0 ? "Start employee-visible REMOTE screen sharing to the configured WorkforceOS relay? Your screen will be transmitted to authorized viewers. STOP SHARING ends capture and transmission." : "Start employee-visible LOCAL desktop preview? No remote relay is configured. You can stop any time."),''',1)
p=p.replace('''_sharing = true;
        _status.Text''','''_sharing = true;
        if (_remoteUrl.Length > 0) _publisher = new RemoteFramePublisher(_remoteUrl);
        _status.Text''',1)
p=p.replace('''_preview.Image = (Image)bitmap.Clone();
            old?.Dispose();''','''_preview.Image = (Image)bitmap.Clone();
            old?.Dispose();
            if (_publisher is not null)
            {
                // Bitmap clone survives CaptureFrame return; publishing never blocks UI thread.
                var remoteFrame = (Image)bitmap.Clone();
                var publisher = _publisher;
                _ = System.Threading.Tasks.Task.Run(async () =>
                {
                    try { if (publisher is not null) await publisher.SendAsync(remoteFrame); }
                    finally { remoteFrame.Dispose(); }
                });
            }''',1)
p=p.replace('''_timer.Stop();
        _sharing = false;''','''_timer.Stop();
        _sharing = false;
        _publisher?.Stop();
        _publisher = null;''',1)
ui=ui.replace('import NativeLiveVideo from "@/components/monitoring/native-live-video";', 'import NativeJpegStream from "@/components/monitoring/native-jpeg-stream";',1)
import re
ui,n=re.subn(r'<NativeLiveVideo stream=\{null\}[^\n]*?/>', '<NativeJpegStream endpoint={process.env.NEXT_PUBLIC_WFOS_SCREEN_RELAY_URL || ""} token={typeof window !== "undefined" ? window.sessionStorage.getItem("wfos_screen_view_token") || "" : ""} deviceId={typeof window !== "undefined" ? window.sessionStorage.getItem("wfos_screen_device_id") || "" : ""} />',ui,count=1)
if n!=1: raise SystemExit('ERROR: Receiver element unexpected; no changes')
# Dashboard setup for dev tokens is manual, never embed secrets in NEXT_PUBLIC vars.
ui=ui.replace('''<NativeJpegStream endpoint={''','''{/* WFOS_3B_NATIVE_VIEWER: developer sets sessionStorage keys after authenticating separately; NOT production tenancy authorization. */}
                <NativeJpegStream endpoint={''',1)
backupdir=root/'artifacts/backups/live-screen-3b'/datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
backupdir.mkdir(parents=True,exist_ok=True)
for src in (program,page):
 dest=backupdir/src.relative_to(root); dest.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dest)
for dest,src in files.items(): dest.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dest)
program.write_text(p,encoding='utf-8'); page.write_text(ui,encoding='utf-8')
print('PATCH INSTALLED. Backup:', backupdir)
print('Native JPEG relay must be configured; this is a DEVELOPMENT transport only.')
