export type OAuthIntent =
  | "login"
  | "signup";

const OAUTH_INTENT_KEY =
  "workforce.oauth.intent";

const OAUTH_REMEMBER_KEY =
  "workforce.oauth.remember_me";

function isBrowser(): boolean {
  return (
    typeof window !==
    "undefined"
  );
}

export function setOAuthIntent(
  intent: OAuthIntent,
  rememberMe = false,
): void {
  if (
    !isBrowser()
  ) {
    return;
  }

  window.sessionStorage.setItem(
    OAUTH_INTENT_KEY,
    intent,
  );

  window.sessionStorage.setItem(
    OAUTH_REMEMBER_KEY,
    String(
      rememberMe,
    ),
  );
}

export function getOAuthIntent():
  OAuthIntent {
  if (
    !isBrowser()
  ) {
    return "login";
  }

  const value =
    window.sessionStorage.getItem(
      OAUTH_INTENT_KEY,
    );

  if (
    value === "login" ||
    value === "signup"
  ) {
    return value;
  }

  return "login";
}

export function getOAuthRememberMe():
  boolean {
  if (
    !isBrowser()
  ) {
    return false;
  }

  return (
    window.sessionStorage.getItem(
      OAUTH_REMEMBER_KEY,
    ) === "true"
  );
}

export function clearOAuthIntent():
  void {
  if (
    !isBrowser()
  ) {
    return;
  }

  window.sessionStorage.removeItem(
    OAUTH_INTENT_KEY,
  );

  window.sessionStorage.removeItem(
    OAUTH_REMEMBER_KEY,
  );
}