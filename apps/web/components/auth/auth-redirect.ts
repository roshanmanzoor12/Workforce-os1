const DEFAULT_AUTHENTICATED_ROUTE =
  "/home";

const DEFAULT_LOGIN_ROUTE =
  "/login";

function isSafeInternalPath(
  value: string,
): boolean {
  if (!value) {
    return false;
  }

  /*
   * Only allow same-origin application paths.
   *
   * Reject:
   *   https://example.com
   *   //example.com
   *   javascript:...
   */
  if (
    !value.startsWith("/") ||
    value.startsWith("//")
  ) {
    return false;
  }

  if (
    value.includes("\n") ||
    value.includes("\r")
  ) {
    return false;
  }

  return true;
}

export function getSafeRedirectPath(
  value:
    | string
    | null
    | undefined,
  fallback =
    DEFAULT_AUTHENTICATED_ROUTE,
): string {
  if (
    typeof value !==
    "string"
  ) {
    return fallback;
  }

  const normalized =
    value.trim();

  if (
    !isSafeInternalPath(
      normalized,
    )
  ) {
    return fallback;
  }

  return normalized;
}

export function getLoginRedirect(
  value:
    | string
    | null
    | undefined,
): string {
  const next =
    getSafeRedirectPath(
      value,
      DEFAULT_AUTHENTICATED_ROUTE,
    );

  return `${DEFAULT_LOGIN_ROUTE}?next=${encodeURIComponent(
    next,
  )}`;
}

export function getAuthenticatedRedirect(
  value:
    | string
    | null
    | undefined,
): string {
  return getSafeRedirectPath(
    value,
    DEFAULT_AUTHENTICATED_ROUTE,
  );
}