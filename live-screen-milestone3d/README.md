# WorkforceOS Live Screen Milestone 3D — no DevTools local viewer setup

This is a **local development** UI improvement, not secure production auto-enrollment. Prerequisites: 3B native sender + relay, 3C Setup, original Live Screen page containing 3B viewer.

1. Extract ZIP (flat: INSTALL.ps1 at ZIP root) to C:\workforce-os\live-screen-milestone3d.
2. Run PowerShell `powershell -NoProfile -ExecutionPolicy Bypass -File C:\workforce-os\live-screen-milestone3d\INSTALL.ps1`.
3. Ensure relay is running, employee has approved active sharing, and 3C Configure-Viewer.ps1 has set NEXT_PUBLIC_WFOS_SCREEN_RELAY_URL in apps\web\.env.local; restart frontend.
4. In PowerShell for the original Windows user, run `powershell -NoProfile -ExecutionPolicy Bypass -File C:\workforce-os\live-screen-milestone3d\COPY-VIEWER-TOKEN.ps1`.
5. On the trusted owner Chrome profile, open http://localhost:3001/monitoring/live-screen and select `clickronix llc` and `DESKTOP-F726TKR` under **Desktop monitoring enrollment**; paste token with Ctrl+V into the **on-page** field, press Connect viewer. No DevTools required. Viewer token remains in that tab's sessionStorage until cleared.
6. Run tools\live-screen-dev\Check.ps1 and confirm Viewer connections is 1 and recent frames true.

The token is a powerful local demo secret; clipboard and sessionStorage are not appropriate production credentials. Use employee-visible and explicitly authorized sharing only. The earlier local test relay has ONE device only; this UI does not add multi-device remote streaming. Preserve the original Windows user running setup, as DPAPI secrets are per-user. To rollback, restore page.tsx and native-jpeg-stream.tsx from the printed backup directory. Token is never printed by COPY-VIEWER-TOKEN.ps1.
