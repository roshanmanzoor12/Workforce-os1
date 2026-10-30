import type {
  AuthUser,
  RefreshTokenResponse,
  TokenResponse,
} from "@/types/auth";


const SESSION_STORAGE_KEY =
  "workforce_os_auth_session";


const LOCAL_STORAGE_KEY =
  "workforce_os_auth_session_persistent";


export interface StoredAuthSession {
  accessToken:
    string;

  refreshToken:
    string;

  accessTokenExpiresAt:
    number;

  rememberMe:
    boolean;

  user:
    AuthUser | null;
}


function canUseBrowserStorage():
  boolean {
  return (
    typeof window !==
    "undefined"
  );
}


function getStorage(
  rememberMe:
    boolean,
): Storage | null {
  if (
    !canUseBrowserStorage()
  ) {
    return null;
  }

  return rememberMe
    ? window.localStorage
    : window.sessionStorage;
}


function safelyParseSession(
  value:
    string | null,
): StoredAuthSession | null {
  if (!value) {
    return null;
  }


  try {
    const parsed =
      JSON.parse(
        value,
      ) as Partial<StoredAuthSession>;


    if (
      typeof parsed.accessToken !==
        "string" ||

      typeof parsed.refreshToken !==
        "string" ||

      typeof parsed.accessTokenExpiresAt !==
        "number" ||

      typeof parsed.rememberMe !==
        "boolean"
    ) {
      return null;
    }


    return {
      accessToken:
        parsed.accessToken,

      refreshToken:
        parsed.refreshToken,

      accessTokenExpiresAt:
        parsed.accessTokenExpiresAt,

      rememberMe:
        parsed.rememberMe,

      user:
        parsed.user ??
        null,
    };

  } catch {
    return null;
  }
}


function writeSession(
  session:
    StoredAuthSession,
): void {
  const storage =
    getStorage(
      session.rememberMe,
    );


  if (!storage) {
    return;
  }


  const key =
    session.rememberMe
      ? LOCAL_STORAGE_KEY
      : SESSION_STORAGE_KEY;


  storage.setItem(
    key,
    JSON.stringify(
      session,
    ),
  );
}


/**
 * Save a complete authentication response.
 *
 * Used by normal email/password authentication
 * where the backend returns:
 *
 * - access token
 * - refresh token
 * - expiry
 * - authenticated user
 */
export function saveAuthSession(
  response:
    TokenResponse,

  rememberMe:
    boolean,
): StoredAuthSession {
  clearAuthSession();


  const session:
    StoredAuthSession = {
    accessToken:
      response.access_token,

    refreshToken:
      response.refresh_token,

    accessTokenExpiresAt:
      Date.now() +
      response.expires_in *
        1000,

    rememberMe,

    user:
      response.user,
  };


  writeSession(
    session,
  );


  return session;
}


/**
 * OAuth bootstrap session.
 *
 * OAuth callback tokens can be stored before the
 * frontend has resolved the authoritative user.
 *
 * The user is deliberately null here.
 *
 * The OAuth callback must subsequently call
 * /auth/me and then updateStoredUser().
 */
export function saveOAuthSessionTokens(
  response: {
    access_token:
      string;

    refresh_token:
      string;

    expires_in:
      number;
  },

  rememberMe:
    boolean,
): StoredAuthSession {
  clearAuthSession();


  const session:
    StoredAuthSession = {
    accessToken:
      response.access_token,

    refreshToken:
      response.refresh_token,

    accessTokenExpiresAt:
      Date.now() +
      response.expires_in *
        1000,

    rememberMe,

    user:
      null,
  };


  writeSession(
    session,
  );


  return session;
}


export function getAuthSession():
  StoredAuthSession | null {
  if (
    !canUseBrowserStorage()
  ) {
    return null;
  }


  const sessionValue =
    window.sessionStorage.getItem(
      SESSION_STORAGE_KEY,
    );


  const session =
    safelyParseSession(
      sessionValue,
    );


  if (session) {
    return session;
  }


  const persistentValue =
    window.localStorage.getItem(
      LOCAL_STORAGE_KEY,
    );


  const persistentSession =
    safelyParseSession(
      persistentValue,
    );


  if (
    persistentSession
  ) {
    return persistentSession;
  }


  return null;
}


export function getAccessToken():
  string | null {
  return (
    getAuthSession()
      ?.accessToken ??
    null
  );
}


export function getRefreshToken():
  string | null {
  return (
    getAuthSession()
      ?.refreshToken ??
    null
  );
}


export function getStoredUser():
  AuthUser | null {
  return (
    getAuthSession()
      ?.user ??
    null
  );
}


export function updateStoredUser(
  user:
    AuthUser,
): void {
  const session =
    getAuthSession();


  if (!session) {
    return;
  }


  writeSession({
    ...session,

    user,
  });
}


export function updateAuthTokens(
  response:
    RefreshTokenResponse,
): StoredAuthSession | null {
  const current =
    getAuthSession();


  if (!current) {
    return null;
  }


  const updated:
    StoredAuthSession = {
    ...current,

    accessToken:
      response.access_token,

    refreshToken:
      response.refresh_token,

    accessTokenExpiresAt:
      Date.now() +
      response.expires_in *
        1000,
  };


  writeSession(
    updated,
  );


  return updated;
}


export function isAccessTokenExpired(
  safetyWindowSeconds =
    15,
): boolean {
  const session =
    getAuthSession();


  if (!session) {
    return true;
  }


  const safetyWindow =
    safetyWindowSeconds *
    1000;


  return (
    Date.now() +
      safetyWindow >=
    session.accessTokenExpiresAt
  );
}


export function clearAuthSession():
  void {
  if (
    !canUseBrowserStorage()
  ) {
    return;
  }


  window.sessionStorage.removeItem(
    SESSION_STORAGE_KEY,
  );


  window.localStorage.removeItem(
    LOCAL_STORAGE_KEY,
  );
}


export function hasAuthSession():
  boolean {
  return (
    getAuthSession() !==
    null
  );
}