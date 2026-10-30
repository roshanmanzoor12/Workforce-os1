export type EmployeePresence =
  | "online"
  | "offline"
  | "unknown";

export type EmployeeAccountStatus =
  | "active"
  | "inactive"
  | "unknown";

export interface EmployeeListItemView {
  id: string;

  displayName: string;
  email?: string | null;
  avatarUrl?: string | null;

  department?: string | null;
  role?: string | null;

  accountStatus: EmployeeAccountStatus;
  presence: EmployeePresence;

  deviceName?: string | null;
  lastActiveLabel?: string | null;
}

export interface EmployeeDetailView
  extends EmployeeListItemView {
  jobTitle?: string | null;
  phone?: string | null;
  joinedLabel?: string | null;

  devicePlatform?: string | null;
  deviceLastSeenLabel?: string | null;
}

export interface EmployeePageView {
  employees: EmployeeListItemView[];

  totalEmployees: number;
  activeEmployees: number;
  onlineEmployees: number;
  offlineEmployees: number;
}