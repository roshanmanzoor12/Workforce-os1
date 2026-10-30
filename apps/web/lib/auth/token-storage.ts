import type {
  RefreshTokenResponse,
} from "@/types/auth";


import {
  clearAuthSession,
  getAccessToken as getSessionAccessToken,
  getRefreshToken as getSessionRefreshToken,
  getAuthSession,
  hasAuthSession,
  saveOAuthSessionTokens,
  updateAuthTokens,
} from "@/lib/auth/session";


function isBrowser():
  boolean {
  return (
    typeof window !==
    "undefined"
  );
}


/**
 * Store tokens when only token information is
 * available.
 *
 * This is intentionally NOT a TokenResponse because
 * TokenResponse requires an authoritative AuthUser.
 *
 * OAuth callback/bootstrap flows can legitimately
 * have no user object yet.
 */
export function saveTokens(
  accessToken:
    string,

  refreshToken:
    string,

  remember:
    boolean,

  expiresInSeconds =
    3600,
): void {
  if (
    !isBrowser()
  ) {
    return;
  }


  saveOAuthSessionTokens(
    {
      access_token:
        accessToken,

      refresh_token:
        refreshToken,

      expires_in:
        expiresInSeconds,
    },

    remember,
  );
}


/**
 * Update an already existing authenticated session
 * with a refreshed access/refresh token pair.
 */
export function updateTokens(
  accessToken:
    string,

  refreshToken:
    string,

  expiresInSeconds?:
    number,
): void {
  if (
    !isBrowser()
  ) {
    return;
  }


  const current =
    getAuthSession();


  if (!current) {
    return;
  }


  const response:
    RefreshTokenResponse = {
    access_token:
      accessToken,

    refresh_token:
      refreshToken,

    token_type:
      "bearer",

    expires_in:
      expiresInSeconds ??
      Math.max(
        1,

        Math.floor(
          (
            current.accessTokenExpiresAt -
            Date.now()
          ) / 1000,
        ),
      ),
  };


  updateAuthTokens(
    response,
  );
}


export function getAccessToken():
  string | null {
  return getSessionAccessToken();
}


export function getRefreshToken():
  string | null {
  return getSessionRefreshToken();
}


export function clearTokens():
  void {
  clearAuthSession();
}


export function hasSession():
  boolean {
  return hasAuthSession();
}