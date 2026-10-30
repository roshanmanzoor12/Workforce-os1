# WorkforceOS native media HTTP gateway (partial backend integration)

This bundle adds authenticated owner JPEG snapshot and device JPEG upload endpoints backed by the existing native relay core. It enforces active database session and device/owner bindings on every request.

**NOT A COMPLETE LIVE SCREEN FIX:** It does not implement the Companion request UI, Windows Agent IPC, a deployed frame publisher, or owner viewer client. No capture occurs as a result of applying it. Do not enable `desktop_agent.live_screen` based on this alone.

Routes: `GET /api/v1/workspaces/{workspace_id}/live-monitoring/live-sessions/{session_id}/native-frame?after=N`, `POST /api/v1/device-agent/live-screen/{session_id}/native-frame` authenticated via existing device headers, body image/jpeg.

Single backend worker only. In-memory frames; not for HA/production. Security tests require environment-level verification and rate-limiting.

Files are based on Oct 26 uploaded source snapshot; installer overwrites router files. Inspect diff and backup before applying.
