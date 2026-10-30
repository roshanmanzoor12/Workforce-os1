# WorkforceOS v5 — Native frame sequence continuity (targeted fix)

**This is NOT the complete live-screen/auto-request fix.** It patches one grounded frame-freeze cause in `native_frame_relay.py`: issuance of a fresh media lease previously reset `sequence` to zero, while the owner's viewer continued sending `after=<previous sequence>`. New frames could therefore be suppressed after ticket renewal. It preserves the preceding sequence when replacing a lease.

## Installation

Run in Windows PowerShell from `C:\workforce-os` after extracting ZIP into root:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\WorkforceOS-Relay-Continuity-v5\Install-v5.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\WorkforceOS-Relay-Continuity-v5\Install-v5.ps1 -Apply
python .\WorkforceOS-Relay-Continuity-v5\Test-relay-v5.py .\backend\app\modules\live_monitoring\native_frame_relay.py
```

Restart your actual backend process (not just the Windows agent). This patch does not modify the C# Companion, screen permission checks, active-session 15-minute expiry, or desktop identity mapping.

## Presence remains a separate problem

The control `devices` record and the `desktop_agent_devices` record are distinct. The bridge only syncs an exact `installation_id == device_uuid` match (or may create an additional record), when the employee mapping and monitoring consent match. Your screenshots show two registered endpoints for one employee, one online and one offline. **Do not delete, reassign, or force-online those records without inspecting their IDs.** Compare authenticated device UUID and registered Companion installation ID, employee IDs, then check backend bridge outcome logs and actual last_seen_at.

## Important remaining issues

- Active session expiry (v2: 900 seconds) still requires authorized rolling renewal for full login-to-logout sharing. Extending approval TTL to 86400 does not implement that.
- Browser polling and Companion upload can freeze for network, authentication, process-restart, or relay single-worker reasons. This patch fixes only a sequence-reset case.
- The relay is in-memory and explicitly single-worker; multi-worker deployments need shared coordination.
- Request auto-creation is not implemented by this ZIP. Employee approval, visible-indicator evidence, authenticated work-session binding, and trusted workspace-owner resolver must not be bypassed.
- Source-only Python patch; backend restart required.
