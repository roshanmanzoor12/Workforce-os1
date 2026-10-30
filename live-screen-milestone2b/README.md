# WorkforceOS Live Screen Milestone 2B — legacy iframe cleanup

This package removes the misleading nested `/browser-screen-share` iframe from the **original** owner page and replaces it with an accurate non-streaming state. It backs up the page first, aborts safely if the expected marker is absent, and does not change Windows services, backends, authentication, or monitoring consent.

**NOT a streaming implementation.** Milestone 1 captures frames only to a local preview. Milestone 2A launches that companion at Windows sign-in, but does not capture automatically. Secure native media transmission to the owner remains to be implemented and tested on Windows.

Run INSTALL.ps1 from this ZIP; rollback with ROLLBACK.ps1. Refresh the original `/monitoring/live-screen` page.
