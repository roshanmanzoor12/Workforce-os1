# WorkforceOS v6 — targeted Companion transient reconnect fix

Addresses the log-proven issue: `RemoteFramePublisher.SendAsync` permanently calls `Stop()` after 8 network failures, so backend restart or transient outage can leave a running Companion process without a publisher. This patch removes only that terminal stop for exceptions; subsequent frame callbacks can retry. **It does not modify server-side authentication and does not auto-start new approved sessions.** For denied/ended/expired sessions the backend must continue to reject frames; the Companion's preexisting terminal authorization handling remains unchanged.

The source patch is dry-run by default and creates a backup on `-Apply`. **Verify actual compiled DLL deployment**, not just EXE hashes: .NET apphost EXE may remain identical while assembly DLL differs.

This patch does not implement: login-driven owner requests, work-session lifecycle, heartbeat device mapping, rolling authorization leases, 500 server traceback repair, or screen sharing without employee approval. It is not a full end-to-end fix.

## Use

Copy zip to `C:\workforce-os`, extract under root, then:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\WorkforceOS-Reconnect-v6\Install-v6.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\WorkforceOS-Reconnect-v6\Install-v6.ps1 -Apply

dotnet publish .\agent\WorkforceOS.ScreenCompanion\WorkforceOS.ScreenCompanion.csproj -c Release -r win-x64 --self-contained false -o .\artifacts\screen-companion-v6
```

Stop employee screen sharing before deploying the published output via your **existing interactive supervisor release process**. Do not hot-copy over a running binary. Start the supervisor, and then validate manual request / employee acceptance / frame uploads and forced temporary backend downtime in a safe test environment. Never test real monitoring on uninformed users.

## Next architecture phase

A genuine login-triggered auto-request requires authenticated work-session events, device-to-DesktopAgent mapping, an authorized owner resolver and database uniqueness across requests. No owner identity may be guessed from a device heartbeat. Active sharing needs bounded rolling leases with employee-visible indication and explicit revocation on logout/consent withdrawal; a 24-hour fixed expiration is not the same thing.
