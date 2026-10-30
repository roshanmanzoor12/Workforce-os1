# WorkforceOS Lifecycle Core v11 — DEVELOPMENT PATCH, NOT END-TO-END DEPLOYABLE

This package implements **a reusable backend persistence/coordinator module** for:
- One request record per verified browser login and assigned desktop device.
- Employee/device heartbeat freshness checks.
- Owner live-monitoring permission and employee-scope checks.
- Explicit per-login revocation on logout/app close/stop/revocation.
- No re-request after an existing login lifecycle row exists.

## NOT IMPLEMENTED / DO NOT DEPLOY AS A COMPLETE FLOW
- The active browser login ID is **not** authenticated or mapped to employee by this module; the caller must verify it through control-plane session infrastructure.
- Owner-scoped LiveMonitoringAccess is **not** fabricated; owner access must be resolved through an authorized principal.
- Auth login/logout and workspace-open handlers are **not yet wired** to this module.
- Existing LiveMonitoringService.request_live_screen commits during creation; a crash between that commit and lifecycle insertion can leave an orphan request; needs a shared-transaction refactor before production.
- Screen-specific saved approval / real Companion indicator attestation is **not implemented**.
- Relay lease renewable authorization and native Companion shutdown after revoke **not wired**.
- Migration not registered in tenant Alembic chain; the SQL is a review artifact.

**Do not run migration or install into production until those integration tasks are resolved and tested.**

Installable source is under `files/backend/app/modules/live_monitoring/login_lifecycle.py`.
Compile-only check: `python -m py_compile files/backend/app/modules/live_monitoring/login_lifecycle.py`.
