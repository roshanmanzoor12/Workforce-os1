export type DevicePresence =
  | "online"
  | "offline"
  | "unknown";

export type DevicePlatform =
  | "windows"
  | "macos"
  | "linux"
  | "unknown";

export interface DeviceListItemView {
  id: string;

  name: string;
  hostname?: string | null;

  platform: DevicePlatform;

  employeeId?: string | null;
  employeeName?: string | null;

  presence: DevicePresence;

  lastSeenLabel?: string | null;
  agentVersion?: string | null;
}

export interface DevicePageView {
  devices: DeviceListItemView[];

  totalDevices: number;
  onlineDevices: number;
  offlineDevices: number;
  unassignedDevices: number;
}