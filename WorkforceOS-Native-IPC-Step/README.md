# WorkforceOS native Windows notification bridge (source-only)

This patch adds **best-effort Agent inbox → interactive Companion notification delivery** over a local named pipe. It does **not** implement session approval, backend consent decision, capture-to-Agent JPEG forwarding, or end-to-end streaming.

## Implementation

- The Agent continues authenticating to `/device-agent/live-screen/inbox` using its existing enrollment. It sends session IDs and expiry only for newly requested valid sessions.
- The Screen Companion starts a local pipe receiver in its interactive user session and displays an informational Windows dialog, never launching capture from a pipe message.
- No device secret leaves the Agent. This is NOT yet secure authorization IPC: other local processes could forge a notification; the future approval/capture channel must authenticate messages and bind them to the correct logged-in user/session. Do not connect capture to this pipe as-is.
- Current backend `live_screen` capability remains false; this source patch does not change it.

## Install

Run `Apply.ps1` (dry run), `Apply.ps1 -Apply`, then build both projects in Release mode. This only changes source and **does not** update running executables. No Windows runtime test has been performed by this package.

## Rollback

`Apply.ps1 -Rollback` restores files saved under the most recent backup path, and removes newly added source files when safe.
