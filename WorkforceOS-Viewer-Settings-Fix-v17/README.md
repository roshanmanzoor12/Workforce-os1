# WorkforceOS V17 — Owner viewer crash + unified consent settings + compact Companion indicator

This patch targets the V15 + V16 source state. This is **not** a fix for device heartbeat `offline/stale`, an `ended/requested` backend session, failed native uploads, or an employee who has not authorized viewing. Those require separate runtime diagnosis.

## Changes

1. Fixes the V16 `/current-session` SQLAlchemy `AttributeError` by sorting `LiveScreenSession` using the real `created_at` model field (then `id`), instead of nonexistent `requested_at`.
2. Keeps the owner viewer embedded in the Live Screen page. Converts raw traceback display for the V16 current-session API into a generic error message.
3. Removes V15's floating saved-approval panel but keeps authenticated workspace `auto-flow/ping` heartbeat.
4. Inserts a **separate, explicit, revocable** future screen-sharing auto-approval checkbox in the existing **Employee monitoring settings** dialog, immediately after the `Allow live-screen requests` toggle row. Uses the existing V15 `/auto-flow/saved-approval` API and database state. `Allow live-screen requests` is not itself auto-approval.
5. Replaces the Companion's large recursive desktop preview window with a small, **topmost, employee-visible** active-sharing indicator and Stop Sharing button. Tray menu and revocation remain; owner sees frames only in the existing browser viewer. While idle, the mini indicator hides. No local desktop preview is shown.

## Safe installation

Put this ZIP in `C:\workforce-os`. Extract:

```powershell
cd C:\workforce-os
Expand-Archive .\WorkforceOS-Viewer-Settings-Fix-v17.zip -DestinationPath . -Force
powershell -NoProfile -ExecutionPolicy Bypass -File .\WorkforceOS-Viewer-Settings-Fix-v17\Install-v17.ps1
```

**Only on preflight PASS:**

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\WorkforceOS-Viewer-Settings-Fix-v17\Install-v17.ps1 -Apply
powershell -NoProfile -ExecutionPolicy Bypass -File .\WorkforceOS-Viewer-Settings-Fix-v17\Verify-v17.ps1
```

The installer transforms all six files in memory first and refuses unknown source layouts, including a Monitoring dialog whose markup is different from the pattern recognized by this patch. Before writing, it backs up every modified existing file to `WorkforceOS-v17-backup-<timestamp>`. It does **not** modify SQL, services, or running executables.

## Builds and deployment

Run frontend typecheck from `apps\web` using `npm run typecheck`; run `npm run build` and fix unrelated lint failures before deploying production frontend. Publish Screen Companion into `artifacts\screen-companion-v17-staging` using your existing `dotnet publish` command. Let employee stop sharing first, pause the verified interactive supervisor, and deploy using your existing V15 Companion deploy procedure **only after using a staging path matching that procedure**. Do not overwrite a running DLL. Restart the existing backend Uvicorn worker to load the route change, and restart frontend.

## Acceptance tests

- Open Live Screen owner page and choose employee and verified assigned device. `current-session` must return HTTP 200, no `requested_at` traceback. If session is `active`, native frames display inline in black viewer; if `requested/ended` or device stale, diagnose that separately.
- Open Employee monitoring settings. See `Allow live-screen requests` plus separate `Automatically approve future screen-sharing requests`. No floating approval card. Turning auto-approval on/off persists through existing endpoint.
- Start employee-approved sharing. Employee sees compact topmost active indicator with **STOP SHARING**, not the large recursive mirror. Owner sees frames on web page, not a native owner window. Stop Sharing ends capture and triggers backend revoke.

**Test limitations:** Python syntax, transformation against V15/V16 test baseline, and idempotency verified locally. Actual current Monitoring dialog source was not in the uploaded exports; V17 preflight will reject a different markup. .NET compilation, frontend typecheck/build, and Windows runtime are not verified here.
