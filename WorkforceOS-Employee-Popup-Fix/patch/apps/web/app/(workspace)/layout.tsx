import type { ReactNode } from "react";

import { WorkspaceShell } from "@/components/app-shell/workspace-shell";
import { WorkspaceProvider } from "@/contexts/workspace-context";
import { ChatLiveSync } from "@/components/chat/chat-live-sync";
import { IncomingCallHost } from "@/components/chat/incoming-call-host";
import { EmployeeScreenShareInbox } from "@/components/monitoring/employee-screen-share-inbox";
import { MonitoringConsentGate } from "@/components/monitoring/monitoring-consent-gate";

interface WorkspaceLayoutProps {
  children: ReactNode;
}

export default function WorkspaceLayout({
  children,
}: WorkspaceLayoutProps) {
  return (
    <WorkspaceProvider>
      <WorkspaceShell>
        {children}
      </WorkspaceShell>

      <ChatLiveSync />
      <IncomingCallHost />
      <MonitoringConsentGate />
      <EmployeeScreenShareInbox />
    </WorkspaceProvider>
  );
}
