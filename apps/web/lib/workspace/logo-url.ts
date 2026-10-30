/** Workspace logo stored under FastAPI's /api/v1 is served through Next.js /backend rewrite. */
export function workspaceLogoSrc(value: string | null | undefined): string {
  if (!value) return "";
  if (value.startsWith("/api/v1/workspaces/logos/")) {
    return "/backend/" + value.slice("/api/v1/".length);
  }
  if (value.startsWith("/backend/workspaces/logos/")) return value;
  if (/^https?:\/\//i.test(value)) return value;
  return "";
}
