export interface WorkspaceRolePublic {
  id:
    string | null;

  role_key:
    string;

  display_name:
    string;

  description:
    string | null;

  permissions:
    string[];

  is_builtin:
    boolean;

  is_immutable:
    boolean;

  is_active:
    boolean;
}


export interface WorkspaceRolesResponse {
  roles:
    WorkspaceRolePublic[];
}


export interface CreateWorkspaceRoleRequest {
  role_key:
    string;

  display_name:
    string;

  description?:
    string | null;

  permissions?:
    string[];
}


export interface CreateWorkspaceRoleResponse {
  message:
    string;

  role:
    WorkspaceRolePublic;
}


export interface UpdateWorkspaceRoleRequest {
  display_name?:
    string | null;

  description?:
    string | null;

  permissions?:
    string[] | null;

  is_active?:
    boolean | null;
}


export interface UpdateWorkspaceRoleResponse {
  message:
    string;

  role:
    WorkspaceRolePublic;
}


export interface DeleteWorkspaceRoleResponse {
  message:
    string;

  success:
    boolean;
}