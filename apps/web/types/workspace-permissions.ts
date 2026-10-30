export interface WorkspacePermissionDefinition {
  key:
    string;

  display_name:
    string;

  description:
    string | null;

  group:
    string;

  dangerous:
    boolean;
}


export interface WorkspacePermissionsResponse {
  permissions:
    WorkspacePermissionDefinition[];
}


/*
 * Raw backend permission catalog.
 *
 * Current backend may return:
 *
 * {
 *   permissions: [
 *     "employees.create",
 *     "members.invite"
 *   ]
 * }
 *
 * Keep this raw contract separate from the
 * UI-normalized WorkspacePermissionsResponse.
 */
export interface RawWorkspacePermissionsResponse {
  permissions:
    unknown[];
}