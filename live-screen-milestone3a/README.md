# WorkforceOS Native Live Screen — Milestone 3A (transport preflight)

This is a non-destructive **readiness/diagnostic** milestone. It checks that Milestones 1, 2B and 2C were installed, inspects original Live Screen code and registered routes, and writes a source-aware report to `C:\workforce-os\artifacts\diagnostics\live-screen-milestone3a`.

## Install
Extract ZIP to `C:\workforce-os\live-screen-milestone3a`, then execute `INSTALL.ps1` with Windows PowerShell 5.1 or PowerShell 7.

## Important
This ZIP **does not implement native remote screen streaming** and does not change the FastAPI backend, Windows service, desktop companion or Next.js UI. It does not authorize, start or transmit screen capture; it requires no elevated privileges. The real next engineering deliverable is a sender/receiver transport bound to employee-controlled active session authorization, same-workspace access checks, persistent visible sharing indicator and Stop Sharing.

## Rollback
No changes made to application files or settings. Delete only the generated diagnostic report if desired.
