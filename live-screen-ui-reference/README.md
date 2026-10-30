# WorkforceOS Live Screen — reference-style owner UI (page-only)

Replaces `apps/web/app/(workspace)/monitoring/live-screen/page.tsx` with a responsive layout based on the supplied reference screenshot. Retains existing workspace authorization, employee/device API reads, live-session request/stop calls and NativeJpegStream local development relay. Employee selection resolves the assigned enrolled desktop agent automatically; the device remains changeable when an employee has multiple assigned devices.

## Install

Extract this ZIP anywhere, then run `powershell -NoProfile -ExecutionPolicy Bypass -File .\INSTALL.ps1` from the extracted folder or use the full installer path.

## Rollback

Run `powershell -NoProfile -ExecutionPolicy Bypass -File .\ROLLBACK.ps1`.

## Important boundaries

* This is an **owner page UI implementation**. It does not change the Windows companion, suppress its window, introduce employee-side popups, or start capture at workspace login.
* Existing localhost JPEG relay demo credentials are still required for current playback. The viewer is not production-safe without workspace-scoped backend media authorization.
* The **Pause viewer** control unmounts/reconnects the viewer locally; it does not pause employee capture.
* Fullscreen uses the browser fullscreen API. No invented screenshot data, live health metrics or session events are displayed.
* Existing agent capability may still report `live_screen=false` even when the standalone development relay is sending frames. The UI distinguishes the two.
* Active employee-controlled sharing authorization, visible notice and a working Stop Sharing control remain required for remote capture.
* Windows/Next.js compile and pixel-diff against the supplied screenshot must be done in the real repository; those tests were not available here.
