# WorkforceOS Native Screen — Milestone 3B (development transport, NOT production)

## What this really implements

Employee-triggered Start Sharing -> Windows capture -> compressed JPEG frames -> WebSocket relay -> same original owner Live Screen page. No iframe, Chrome screen picker, or fake MediaStream. The publisher sends frames ONLY after the companion user explicitly accepts a remote-sharing dialog; STOP SHARING closes the publisher. The component compiles in the existing .NET 8 Windows project (must be verified on Windows).

**Important limitations:** This is a LAN/dev demo using capability tokens, not integrated with WorkforceOS user authentication, employee selection, consent database, audit, or TLS provisioning. Do NOT expose the relay to the internet or deploy for employee surveillance. Device selection and viewer token are currently entered manually for testing. The captured images are not WebRTC and the relay is in-memory and single-device. Owner page uses an `<img>` receiver, not the previous `<video>` MediaStream component.

## Install

Extract ZIP into `C:\workforce-os\live-screen-milestone3b` and run `powershell -NoProfile -ExecutionPolicy Bypass -File C:\workforce-os\live-screen-milestone3b\INSTALL.ps1`. It makes backups at `C:\workforce-os\artifacts\backups\live-screen-3b\<timestamp>` and builds the C# companion.

## Test on same Windows machine only

1. Open PowerShell. Generate **two different** long secrets and remember the displayed values:

```powershell
$SendToken = [Convert]::ToHexString([Security.Cryptography.RandomNumberGenerator]::GetBytes(32))
$ViewToken = [Convert]::ToHexString([Security.Cryptography.RandomNumberGenerator]::GetBytes(32))
$Device = 'DESKTOP-F726TKR'
$env:WFOS_SEND_TOKEN = $SendToken
$env:WFOS_VIEW_TOKEN = $ViewToken
$env:WFOS_DEVICE_ID = $Device
cd C:\workforce-os\live-screen-milestone3b
python -m pip install -r .\relay\requirements.txt
python -m uvicorn relay.server:app --host 127.0.0.1 --port 8769
```

2. In a **different employee PowerShell**, set `WFOS_SCREEN_SEND_URL` to `ws://127.0.0.1:8769/ws/send/DESKTOP-F726TKR?token=<SendToken>` using the real generated `$SendToken`, then **launch the companion from that PowerShell** using `dotnet run --project C:\workforce-os\agent\WorkforceOS.ScreenCompanion\WorkforceOS.ScreenCompanion.csproj -c Release --no-build`. The Windows-sign-in autostart companion will NOT inherit this temporary environment variable. Close the previous companion process before testing.

3. Set `NEXT_PUBLIC_WFOS_SCREEN_RELAY_URL=http://127.0.0.1:8769` in the Next.js dev server environment, then restart Next.js. In **owner browser devtools console**, only on your trusted local test machine:

```javascript
sessionStorage.setItem('wfos_screen_view_token', '<ViewToken>');
sessionStorage.setItem('wfos_screen_device_id', 'DESKTOP-F726TKR');
location.reload();
```

4. Navigate to `/monitoring/live-screen`. In companion, press **Start local preview (consent)** and approve the new **remote sharing** dialog. Frames should appear in the original page. **Stop Sharing** should clear them.

The viewer token is stored only in tab sessionStorage for this demo; the network relay uses an unencrypted ws:// connection bound to localhost. Production requires backend-issued short-lived tokens, app RBAC/tenant consent, TLS (wss://), audit trails, reliable session cleanup, and native video codec/streaming.

## Revert

Restore the two source files from the backup folder recorded during install, and remove the new RemoteFramePublisher.cs and native-jpeg-stream.tsx files. Restart frontend and rebuild companion.
