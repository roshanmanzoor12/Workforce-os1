# Native viewer integration (partial)
This package adds frame polling from the *separately installed* Native Gateway source and renders frames in the main black Live Screen viewer when an existing native session is active.

It does NOT provide a Windows Companion publisher, employee native Accept/Decline, agent-to-companion IPC, or unattended capture. It is NOT a complete end-to-end fix. Do not install the backend gateway on a production server without verifying authorization and tests, and never manually set live_screen true.

Windows command: `powershell -NoProfile -ExecutionPolicy Bypass -File .\Apply.ps1` dry-run; add `-Apply` to install; `-Rollback` restores backed up files. Run `npx tsc --noEmit --incremental false` in apps/web, then restart Next.js. Avoid simultaneous next dev/build.

Includes previous native backend gateway source only for review, not auto-install.
