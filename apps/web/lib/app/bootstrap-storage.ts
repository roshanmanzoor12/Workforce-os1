const LAST_WORKSPACE_KEY =
  "workforce_os_last_workspace_id";

function canUseStorage():
  boolean {
  return (
    typeof window !==
    "undefined"
  );
}

export function getLastWorkspaceId():
  string | null {
  if (
    !canUseStorage()
  ) {
    return null;
  }

  return (
    window.localStorage.getItem(
      LAST_WORKSPACE_KEY,
    )
  );
}

export function saveLastWorkspaceId(
  workspaceId:
    string,
): void {
  if (
    !canUseStorage()
  ) {
    return;
  }

  window.localStorage.setItem(
    LAST_WORKSPACE_KEY,
    workspaceId,
  );
}

export function clearLastWorkspaceId():
  void {
  if (
    !canUseStorage()
  ) {
    return;
  }

  window.localStorage.removeItem(
    LAST_WORKSPACE_KEY,
  );
}