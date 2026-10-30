# WorkforceOS Native Relay Core — engineering tranche (NOT final streaming fix)

This package adds `backend/app/modules/live_monitoring/native_frame_relay.py` containing a consent-gated, workspace-bound, session-token-backed in-memory JPEG buffer.

Verified: 6 Python unittest cases passed. No backend API routes have been added; no agent or ScreenCompanion changes are included. This module is deliberately **not exposed externally** until authenticated ticket issuance and employee consent paths are connected. Installing it will **not** make the owner's black viewer show frames.

## Safe install

From the extracted directory:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\Apply.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\Apply.ps1 -Apply
```

## Remaining critical integrations

- Bind approved live-screen session to authenticated tenant owner, employee and enrolled device; issue short-lived viewer/publisher capabilities only after server-side authorization.
- Secure Agent-to-interactive-Companion request notifications and visible employee Accept/Decline/Stop controls.
- WebSocket endpoints with role-specific validation, rate limits, revocation, audit and disconnect semantics.
- Owner frame decoding/viewer and native Companion publisher session URL acquisition.
- Multi-worker deployment needs Redis pub/sub or another shared media plane; this in-memory core is single-process only.

## Tests

```powershell
python -m unittest discover -s .\tests -v
```
