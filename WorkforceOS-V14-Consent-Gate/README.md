# WorkforceOS V14 — consent-gate correction

This is a **narrow source patch**, NOT the requested end-to-end auto-login solution. It makes the V8/V9 tree fail-closed on generic monitoring disclosure and requests a session-specific Accept/Decline decision through the existing Companion dialog. It does not introduce saved screen-specific grants, does not wire owner auto-request, and does not implement logout leases. V9 backend stop-sharing code is preserved.

Run `Install-v14.ps1` in dry-run mode first; use `-Apply` only after reviewing modifications. Builds/restarts are separate. The package deliberately does not silently update a running Windows service or tenant database.
