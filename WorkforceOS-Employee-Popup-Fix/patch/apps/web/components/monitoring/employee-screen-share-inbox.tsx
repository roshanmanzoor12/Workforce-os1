"use client";

import BrowserScreenSharePanel from "@/components/monitoring/browser-screen-share-panel";

// Mounted by the authenticated workspace layout, not the owner-only Live Screen route.
// The browser share API returns requests only for the logged-in employee account.
export function EmployeeScreenShareInbox() {
  return <BrowserScreenSharePanel incomingOnly />;
}
