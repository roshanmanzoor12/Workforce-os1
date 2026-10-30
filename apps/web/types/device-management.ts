export type DeviceStatus =
  | "pending"
  | "active"
  | "offline"
  | "disabled"
  | "revoked";


export interface DevicePublic {
  id:
    string;

  device_uuid:
    string;

  employee_id:
    string | null;

  hostname:
    string;

  os_name:
    string;

  os_version:
    string | null;

  architecture:
    string | null;

  agent_version:
    string | null;

  agent_identifier:
    string | null;

  status:
    DeviceStatus;

  is_active:
    boolean;

  first_seen_at:
    string | null;

  last_seen_at:
    string | null;

  registered_at:
    string | null;

  revoked_at:
    string | null;

  monitoring_profile_id:
    string | null;

  created_at:
    string;

  updated_at:
    string;
}


export interface DeviceListResponse {
  devices:
    DevicePublic[];

  total:
    number;
}


export interface DeviceResponse {
  message:
    string;

  device:
    DevicePublic;
}


export interface DeviceDeleteResponse {
  message:
    string;

  success:
    boolean;
}


export interface DeviceAssignmentRequest {
  employee_id:
    string | null;
}


export type DeviceActivationCodeStatus =
  | "active"
  | "expired"
  | "revoked"
  | "exhausted";


export interface DeviceActivationCodePublic {
  id:
    string;

  workspace_id:
    string;

  created_by_user_id:
    string;

  code_prefix:
    string | null;

  status:
    DeviceActivationCodeStatus;

  is_active:
    boolean;

  expires_at:
    string | null;

  revoked_at:
    string | null;

  last_used_at:
    string | null;

  max_uses:
    number | null;

  used_count:
    number;

  label:
    string | null;

  created_at:
    string;

  updated_at:
    string;
}


export interface DeviceActivationCodeCreateRequest {
  label?:
    string | null;

  expires_at?:
    string | null;

  max_uses?:
    number | null;
}


export interface DeviceActivationCodeCreateResponse {
  message:
    string;

  activation_code:
    string;

  activation:
    DeviceActivationCodePublic;
}


export interface DeviceActivationCodeListResponse {
  activation_codes:
    DeviceActivationCodePublic[];

  total:
    number;
}


export interface DeviceActivationCodeRevokeResponse {
  message:
    string;

  success:
    boolean;
}