/**
 * WorkforceOS — Device Assignment + Employee Account Link
 * Destination: apps/web/lib/devices/reassign-device-and-link-account.ts
 * Uses the existing authenticated API client through application services.
 * Never grants monitoring consent or live-screen capability.
 */
import { deviceManagementService } from "@/services/device-management.service";
import { employeesService } from "@/services/employees.service";
import { workspaceMembersService } from "@/services/workspace-members.service";

export type ReassignDeviceInput = {
  workspaceId: string;
  deviceId: string;
  employeeId: string;
  /** Selected member user ID, verified by the owner in the UI. */
  memberUserId: string;
};

export async function reassignDeviceAndLinkAccount(input: ReassignDeviceInput) {
  const { workspaceId, deviceId, employeeId, memberUserId } = input;
  if (![workspaceId, deviceId, employeeId, memberUserId].every(Boolean)) {
    throw new Error("Select a device, employee and linked workspace account.");
  }

  // Fetch authoritative records via the app's authenticated client.
  const [devices, employees, members] = await Promise.all([
    deviceManagementService.listDevices(workspaceId, { includeInactive: true }),
    employeesService.list(workspaceId, { includeInactive: true }),
    workspaceMembersService.list(workspaceId),
  ]);
  const device = devices.devices.find((item) => item.id === deviceId);
  const employee = employees.employees.find((item) => item.id === employeeId);
  const member = members.members.find((item) => item.user_id === memberUserId);

  if (!device || !device.is_active || device.status === "revoked" || device.status === "disabled") {
    throw new Error("Device is missing, disabled or revoked.");
  }
  if (!employee || !employee.is_active || employee.employment_status !== "active") {
    throw new Error("Employee must be active.");
  }
  if (!member || member.status.toLowerCase() !== "active" || member.moderation?.is_banned) {
    throw new Error("Linked login must be an active, unbanned workspace member.");
  }
  if (employee.user_id && employee.user_id !== memberUserId) {
    throw new Error("Employee is already linked to a different login. Resolve that link explicitly first.");
  }
  if (employees.employees.some((e) => e.id !== employee.id && e.user_id === memberUserId)) {
    throw new Error("This login is already linked to another employee.");
  }
  // Email is an additional safeguard; the owner must confirm identity in the UI.
  if (employee.work_email && employee.work_email.trim().toLowerCase() !== member.email.trim().toLowerCase()) {
    throw new Error("Employee work email and selected member email differ. Verify identity before linking.");
  }

  // Link first: when linking fails, do NOT reassign device.
  // Backend validates workspace membership, uniqueness and management permissions.
  let accountLinked = false;
  if (!employee.user_id) {
    await employeesService.update(workspaceId, employee.id, { user_id: memberUserId });
    accountLinked = true;
  }

  // Do not generate a pointless reassignment heartbeat when already assigned.
  let deviceReassigned = false;
  if (device.employee_id !== employee.id) {
    try {
      await deviceManagementService.assignDevice(workspaceId, device.id, { employee_id: employee.id });
      deviceReassigned = true;
    } catch (error) {
      // The identity link might now be committed: report partial state truthfully.
      throw new Error(
        accountLinked
          ? `Account linked, but device assignment failed. Refresh to review the partial update. ${error instanceof Error ? error.message : ""}`
          : `Device assignment failed. ${error instanceof Error ? error.message : ""}`,
      );
    }
  }

  return {
    accountLinked,
    deviceReassigned,
    message: deviceReassigned
      ? "Device assigned and verified employee account linked."
      : accountLinked
        ? "Employee account linked; existing device assignment preserved."
        : "Device assignment and employee login link are already correct.",
  };
}
