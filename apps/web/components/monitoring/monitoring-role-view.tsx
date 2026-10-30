"use client";

import { useWorkspace } from "@/contexts/workspace-context";

import OwnerView from "./owner/owner-overview";
import AdminView from "./admin/admin-overview";
import ManagerView from "./manager/manager-overview";
import HRView from "./hr/hr-overview";
import MemberView from "./member/member-overview";

interface Props {
  page?: string;
}

export default function MonitoringRoleView({
  page = "overview",
}: Props) {
  const { membership } = useWorkspace();

  if (!membership) {
    return <div>Workspace access required.</div>;
  }

  if (page !== "overview") {
    return (
      <div>
        This Monitoring page requires its role-specific
        component to be connected.
      </div>
    );
  }

  switch (membership.role_key) {
    case "owner":
      return <OwnerView />;

    case "admin":
      return <AdminView />;

    case "manager":
    case "senior_manager":
      return <ManagerView />;

    case "hr":
      return <HRView />;

    case "member":
    case "employee":
      return <MemberView />;

    case "client":
      return <div>Monitoring is not available to clients.</div>;

    default:
      return <div>Access denied.</div>;
  }
}