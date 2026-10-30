# WorkforceOS V16 — Owner Inline Live Screen Viewer

**Purpose:** The owner should select an employee and see that employee's **existing employee-approved active native screen-sharing session directly in the black Live Screen panel**. No second owner viewer/window and no manual `Request session` are needed.

**Employee privacy:** This patch does NOT grant consent, start capture, remove the employee's Companion indicator, or bypass the employee's Stop Sharing control. `Monitoring disclosure` / `Allow live-screen requests` is not an automatic screen capture approval. The existing V15 screen-specific saved approval or employee Accept/Decline remains the gate.

## What changed

- `backend/app/modules/live_monitoring/router.py`: adds authenticated `GET /workspaces/{workspace_id}/live-monitoring/current-session?employee_id=<UUID>&device_id=<UUID>`. It finds only non-expired `requested`, `accepted`, or `active` sessions **created for the currently authenticated owner**. It validates the owner's live-screen permission and employee access scope, and returns only session metadata. Existing `/native-frame` route still validates authorization per frame.
- `apps/web/app/(workspace)/monitoring/live-screen/page.tsx`: selection of an employee and assigned DesktopAgentDevice automatically polls this endpoint every 3 seconds; if a session becomes `active`, the existing `NativeSessionFrameViewer` is rendered within the black panel. Switching employee resets previous session immediately. Removes the page-local automatic request effect, and replaces the manual Request Session button with read-only automatic-viewing status.

## Installation

Place the ZIP at `C:\workforce-os` and use **PowerShell**:

```powershell
cd C:\workforce-os
Expand-Archive -Path '.\WorkforceOS-Owner-Viewer-v16.zip' -DestinationPath '.' -Force
powershell -NoProfile -ExecutionPolicy Bypass -File '.\WorkforceOS-Owner-Viewer-v16\Install-v16.ps1'
if ($LASTEXITCODE -ne 0) { throw 'V16 source preflight failed' }
# Only after preflight passes:
powershell -NoProfile -ExecutionPolicy Bypass -File '.\WorkforceOS-Owner-Viewer-v16\Install-v16.ps1' -Apply
if ($LASTEXITCODE -ne 0) { throw 'V16 source patch failed' }
```

Installer is guarded; unexpected source changes produce `SOURCE CONFLICT` instead of replacing files. All target files are backed up to `C:\workforce-os\WorkforceOS-v16-backup-<timestamp>` before any changes. No binaries, database tables, credentials or services are touched.

## Validate and activate

```powershell
cd C:\workforce-os
& .\.venv\Scripts\python.exe -m py_compile '.\backend\app\modules\live_monitoring\router.py'
cd .\apps\web
npm run typecheck
# next build may still fail on existing unrelated ESLint errors; do not confuse with TypeScript failure.
npm run build
```

Restart the existing backend **after Python import validation**, and restart the frontend using its established process. If using `next dev` then refreshed source can be picked up automatically, but a production frontend requires a successful build. The earlier owner page's production build was blocked by unrelated lint errors in AI/chat/devices components; this patch does not fix those errors.

Read-only route check:

```powershell
$spec = Invoke-RestMethod 'http://127.0.0.1:8001/openapi.json'
if (-not $spec.paths.PSObject.Properties.Name.Contains('/api/v1/workspaces/{workspace_id}/live-monitoring/current-session')) {
  throw 'V16 route not registered in the running backend'
}
'V16 owner session route is registered'
```

## Acceptance test

1. Employee logs into workspace on the assigned Windows machine. The V15 auto-flow sends one owner request (verify backend event; V16 does not create requests).
2. If explicit, saved screen-specific approval is valid and the employee Companion visibly signals sharing, Agent auto-accepts. Otherwise employee receives Accept/Decline. Do not interpret the generic monitoring toggle as capture approval.
3. In owner UI, select that employee; if multiple devices select correct DesktopAgentDevice. A `requested` or `accepted` session shows waiting status; an `active` session starts existing `NativeSessionFrameViewer` inside the page.
4. Switching employees must never show previous employee frames. Stop Sharing or logout causes the backend active session to end, and viewer clears on next poll.
5. A separate **employee-side** Companion sharing indicator/window is still visible/accessible to the employee by design. It is **not a separate owner viewer**. If owner and employee are testing on the same physical desktop, screen-within-screen recursion in the native preview is normal.

## Known limitations

- If backend session is **ended** or assigned Agent is **offline/stale** (as in provided screenshots), no safe owner-side UI patch can display live frames. Device heartbeat, session approval, and actual native frame upload must all work; this patch does not forge them.
- Only the owner that the backend records as `requested_by_user_id` can view frames, matching the current native-frame endpoint. Other privileged owners require an explicit authorized-sharing design, not a bypass.
- The persistent floating **“Live Screen Sharing — employee control”** opt-in from V15 is **not merged into the modern “Employee monitoring settings” dialog by this patch**. The uploaded frontend source snapshot does not include the screenshot's newer modal implementation. Do not remove the explicit saved-approval control before moving it into a source-verified employee settings component.
- Backend REST, live tenant DB and actual Windows production streaming were not exercised in this environment. Guarded source transformation, Python syntax compile, TSX syntax parse and static access/UX contract checks passed against the provided V15 simulation tree.
