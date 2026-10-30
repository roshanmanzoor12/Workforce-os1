export function buildWorkspaceInvitationLink(
  token:
    string,
): string {
  const path =
    `/invite/${encodeURIComponent(
      token,
    )}`;


  if (
    typeof window ===
    "undefined"
  ) {
    return path;
  }


  return `${window.location.origin}${path}`;
}