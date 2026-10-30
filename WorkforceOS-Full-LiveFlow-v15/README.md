# WorkforceOS V15 — Integrated Live Screen lifecycle (development implementation)

This package is based on the user's two `WorkforceOS-...Current.zip` source exports, V8 Agent, V9 Stop Sharing patch, V11 coordinator, V12 atomic transaction patch, and V13 tenant migration draft. It is an integrated source implementation, **not a tested guarantee that a complete Windows / tenant production runtime will work**. It deliberately requires a verified V9/V12 baseline and fails closed on other unexpected source layouts. It does not bypass employee consent.

## Implemented code paths

1. The **authenticated employee workspace layout** periodically invokes `POST /workspaces/{workspace_id}/live-monitoring/auto-flow/ping` using the real browser authorization token. Global `auth/login` alone is never mistaken for workspace access.
2. The backend confirms the current control-plane refresh session is active, follows refresh-token rotation to the original login ID, and resolves the employee from the tenant database.
3. It selects **exactly one** matching online, non-disabled DesktopAgentDevice from the employee's verified user ID + employee ID (fresh 90s heartbeat). Multiple candidates require explicit selection rather than guessing.
4. It resolves an active owner membership through the current membership-access resolver (including bans and effective permissions), requiring both live-screen and employees-all permissions. It does not impersonate an owner from device credentials.
5. V11/V12's coordinator uses an advisory transaction lock and per-login/device association and creates at most one owner request. Declined/stopped entries stay terminal for the same login ID. The first lifecycle ping time is included in the same transaction.
6. Agent inbox uses **explicit saved screen-specific approval**, never generic MonitoringConsent alone. Future auto-approval is an explicit user action in the workspace, with revoke control. Generic monitoring disclosure must also remain granted. Without valid saved approval, employee receives the Companion Accept/Decline popup.
7. If saved screen approval exists, Agent asks interactive Companion to show its visible sharing indicator and receives an acknowledgement **before** sending Accept. No Companion/indicator => no auto acceptance; popup fallback. Companion sends `ready` through named pipe only when its tray and controls are visible.
8. Backend activate -> Companion start uses the existing authenticated Agent. Same-session repeated start does not revoke it. A terminal 410 authorization response stops the publisher and signals UI to stop local capture.
9. Browser pings every 25s, extending a bounded 120s active capture lease. Native frame upload and Agent inbox check the lease and generic monitoring disclosure. Loss of authorization/closed browser stops streaming within the bounded lease window.
10. Explicit browser logout/logout-all calls authenticated auto-flow stop before global logout. Companion Stop Sharing uses the V9 device-authenticated backend revocation and rejects subsequent frames. Next genuinely new login gets a fresh root session ID and new request. Browser refresh does not revoke the session.

## Limitations and safeguards

- **App crash/browser close cannot be distinguished reliably from refresh**: no immediate logout signal can be guaranteed. A 120s bounded backend lease is used. Long sleep / tab throttling may expire a live session; this is fail-closed, not unbounded 20h sharing.
- Saved approval is a **new explicit opt-in**; the old `Allow live-screen requests` setting alone does not automatically accept screen capture. UI includes explanatory text and explicit revocation.
- The browser lifecycle is the authenticated **web work lease**, not the independent activity-based `WorkSession` record.
- Agent heartbeat alone NEVER starts a request. No request is created without a real browser workspace ping and verified online device mapping.
- V13 migration is mandatory first. The included V15 tenant SQL is a follow-up migration. Register both with your real Alembic migration history for future tenant provisioning; running SQL ad-hoc on one tenant does NOT handle other tenants automatically.
- No interactive Windows .NET compilation or tenant database integration tests could run in this environment. `dotnet publish`, frontend typechecking and a real PostgreSQL integration test are **required before rollout**. Source patch simulation, Python compilation, TypeScript transpilation and six static/contract tests passed locally.
- The named pipe is local to the employee's interactive session. Windows supervisor and Agent service must each use the updated binaries; deploying only one component is insufficient.
- Frame relay is in-process/single-worker; scaling to multiple backend workers needs shared relay infrastructure and is not part of this patch.
- The authorization middleware and owner membership in the target live repo may have changed since the uploaded export. Preflight refuses unsupported anchors. No hidden override switches are provided.

## 1. Source preflight and apply (nothing deployed)

From **Administrator PowerShell**, after extracting the ZIP into `C:\workforce-os`:

```powershell
cd C:\workforce-os
powershell -NoProfile -ExecutionPolicy Bypass -File .\WorkforceOS-Full-LiveFlow-v15\Install-v15.ps1
# Only after PREFLIGHT PASS:
powershell -NoProfile -ExecutionPolicy Bypass -File .\WorkforceOS-Full-LiveFlow-v15\Install-v15.ps1 -Apply
powershell -NoProfile -ExecutionPolicy Bypass -File .\WorkforceOS-Full-LiveFlow-v15\Verify-v15.ps1
```

The installer makes a timestamped backup of every changed source file. **V14 is not required** and its previous source-conflict should not be forced or overwritten.

## 2. Tenant schema — must be deliberate

Use your existing validated PostgreSQL tenant migration runner, ideally under Alembic with a real revision/down_revision. Apply V13 first (if not already applied), then this package's `migration.sql` against each intended **TENANT database**, not the control-plane database. Review backup, current `alembic_version`, and the database name before running. Do not supply production credentials in chat or command history. No migration is run automatically by installer.

The tenant schema adds `last_ping_at` and the explicit `live_screen_saved_approvals` table. `live_screen_login_lifecycle` from V13 is required.

## 3. Compile all three applications

```powershell
cd C:\workforce-os
dotnet publish .\agent\WorkforceOS.Agent\WorkforceOS.Agent.csproj -c Release -r win-x64 --self-contained false -o .\artifacts\agent-v15-staging
if ($LASTEXITCODE -ne 0) { throw 'Agent build failed' }
dotnet publish .\agent\WorkforceOS.ScreenCompanion\WorkforceOS.ScreenCompanion.csproj -c Release -r win-x64 --self-contained false -o .\artifacts\screen-companion-v15-staging
if ($LASTEXITCODE -ne 0) { throw 'Companion build failed' }
# In apps/web: use the repository's actual package manager / lockfile and scripts to run typecheck and build.
```

## 4. Live Windows deployment (ONLY after DB + builds + backups)

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\WorkforceOS-Full-LiveFlow-v15\Deploy-v15.ps1 -Agent
powershell -NoProfile -ExecutionPolicy Bypass -File .\WorkforceOS-Full-LiveFlow-v15\Deploy-v15.ps1 -Agent -Apply
```

For Companion, **employee must stop sharing** and you must pause the interactive Companion supervisor first. `Deploy-v15.ps1 -Companion -Apply` deliberately refuses a running Companion and never kills its supervisor. Restart your existing supervisor afterward. Restart backend and frontend using your existing commands **after** migrating and verifying they build. Never deploy older V6 binaries over the V15 Companion.

## 5. End-to-end acceptance tests on Windows

- Employee logs in and enters workspace, Agent online: exactly **one** requested session should appear, with authorized owner in `requested_by_user_id`.
- Owner manual request not required; a second browser heartbeat and refresh do not create a second session.
- With saved screen approval **OFF**, employee gets native Accept/Decline. Decline is terminal for the current browser login.
- With separate saved screen approval **ON** (explicitly opted in, monitoring disclosure still granted), Companion visibly acknowledges indicator first, then Agent sends Accept, activation becomes active, owner sees changing JPEG frames.
- Stop Sharing ends backend session and causes Agent not to restart it in the same login.
- Explicit logout/logout-all ends the session and publisher; a browser refresh without logout keeps the same login association.
- Unexpected browser closure/network failure ends streaming within the 120s lease (not necessarily instantly). A genuinely new login becomes eligible for one new request.
- Test transient backend restart/reconnect, device timeout, monitoring-consent revocation, owner permission removal, and two simultaneously online devices (fail closed).

## 6. What was actually tested here

- Source transformation preflight and apply on a simulated V8 + V9 + V12 tree: PASS.
- Python source compile + six patch/security contract tests: PASS.
- TypeScript transpilation/syntax check for new component and patched frontend files: PASS.
- PowerShell scripts, .NET compiler, PostgreSQL migrations and real Windows Agent-to-Companion-to-owner streaming: NOT EXECUTED in this environment.

**Do not call the full flow production-ready before the Windows and PostgreSQL acceptance tests pass.**

### Bundled migration files and verification

This archive also includes `migration-v13.sql` (the prerequisite lifecycle table), `migration.sql` (V15 incremental changes), and `verify-tenant.sql`. **V13 was only preflighted in your last logs, not applied**. Verify that your correct tenant database is selected before running either SQL file. If the schema already exists, do not blindly reapply migrations without checking migration history. The installer does not run these migrations.

Run `Smoke-v15.ps1` after restarting the backend to verify the new routes are registered. This only verifies OpenAPI registration; it does not prove streaming.
