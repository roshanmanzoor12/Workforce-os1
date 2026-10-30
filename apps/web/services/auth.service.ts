import {
  api,
} from "@/lib/api/client";

import { endLiveScreenLoginOnLogout } from "@/services/live-screen-auto-flow.service";

import {
  clearAuthSession,
  getAuthSession,
  saveAuthSession,
  updateStoredUser,
} from "@/lib/auth/session";

import type {
  CurrentUserResponse,
  EmailVerificationResponse,
  ForgotPasswordRequest,
  ForgotPasswordResponse,
  LoginRequest,
  LogoutAllResponse,
  LogoutResponse,
  OAuthAuthorizationResponse,
  OAuthExchangeRequest,
  OAuthExchangeResponse,
  OAuthIntent,
  ResendVerificationRequest,
  ResetPasswordRequest,
  ResetPasswordResponse,
  SessionsResponse,
  SignupRequest,
  SignupResponse,
  TokenResponse,
  VerifyEmailRequest,
  VerifyResetOtpRequest,
  VerifyResetOtpResponse,
} from "@/types/auth";


function getWebDeviceName():
  string {
  if (
    typeof navigator ===
    "undefined"
  ) {
    return "Workforce OS Web";
  }

  const platform =
    navigator.platform?.trim();

  return platform
    ? `Workforce OS Web - ${platform}`
    : "Workforce OS Web";
}


async function login(
  payload: LoginRequest,
): Promise<TokenResponse> {
  return api.post<TokenResponse>(
    "/auth/login",
    payload,
    {
      auth: false,

      retryOnUnauthorized:
        false,

      headers: {
        "X-Device-Name":
          getWebDeviceName(),
      },
    },
  );
}


async function signup(
  payload: SignupRequest,
): Promise<SignupResponse> {
  return api.post<SignupResponse>(
    "/auth/signup",
    payload,
    {
      auth:
        false,

      retryOnUnauthorized:
        false,
    },
  );
}


async function verifyEmail(
  payload:
    VerifyEmailRequest,
): Promise<EmailVerificationResponse> {
  return api.post<EmailVerificationResponse>(
    "/auth/verify-email",
    payload,
    {
      auth:
        false,

      retryOnUnauthorized:
        false,
    },
  );
}


async function resendVerification(
  payload:
    ResendVerificationRequest,
): Promise<EmailVerificationResponse> {
  return api.post<EmailVerificationResponse>(
    "/auth/resend-verification",
    payload,
    {
      auth:
        false,

      retryOnUnauthorized:
        false,
    },
  );
}


async function forgotPassword(
  payload:
    ForgotPasswordRequest,
): Promise<ForgotPasswordResponse> {
  return api.post<ForgotPasswordResponse>(
    "/auth/forgot-password",
    payload,
    {
      auth:
        false,

      retryOnUnauthorized:
        false,
    },
  );
}


async function verifyResetOtp(
  payload:
    VerifyResetOtpRequest,
): Promise<VerifyResetOtpResponse> {
  return api.post<VerifyResetOtpResponse>(
    "/auth/verify-reset-otp",
    payload,
    {
      auth:
        false,

      retryOnUnauthorized:
        false,
    },
  );
}


async function resetPassword(
  payload:
    ResetPasswordRequest,
): Promise<ResetPasswordResponse> {
  return api.post<ResetPasswordResponse>(
    "/auth/reset-password",
    payload,
    {
      auth:
        false,

      retryOnUnauthorized:
        false,
    },
  );
}


async function getCurrentUser():
  Promise<CurrentUserResponse> {
  const response =
    await api.get<CurrentUserResponse>(
      "/auth/me",
    );

  updateStoredUser(
    response.user,
  );

  return response;
}


async function getVerifiedCurrentUser():
  Promise<CurrentUserResponse> {
  const response =
    await api.get<CurrentUserResponse>(
      "/auth/me/verified",
    );

  updateStoredUser(
    response.user,
  );

  return response;
}


async function getSessions():
  Promise<SessionsResponse> {
  return api.get<SessionsResponse>(
    "/auth/sessions",
  );
}


async function revokeSession(
  sessionId: string,
): Promise<LogoutResponse> {
  return api.delete<LogoutResponse>(
    `/auth/sessions/${sessionId}`,
  );
}


async function logout():
  Promise<LogoutResponse | null> {
  const session =
    getAuthSession();

  if (!session) {
    clearAuthSession();

    return null;
  }

  try {
    // Revoke backend auto-requested sharing BEFORE revoking the browser token.
    // If offline, the server's short lease rejects capture after its TTL.
    const workspaceId = typeof window !== "undefined"
      ? window.localStorage.getItem("workforce_current_workspace_id") : null;
    if (workspaceId) {
      try { await endLiveScreenLoginOnLogout(workspaceId); }
      catch (error) { console.warn("Live-screen logout revocation deferred to lease expiry", error); }
    }
    return await api.post<LogoutResponse>(
      "/auth/logout",
      {
        refresh_token:
          session.refreshToken,
      },
      {
        auth:
          false,

        retryOnUnauthorized:
          false,
      },
    );
  } finally {
    clearAuthSession();
  }
}


async function logoutAll():
  Promise<LogoutAllResponse> {
  try {
    const workspaceId = typeof window !== "undefined"
      ? window.localStorage.getItem("workforce_current_workspace_id") : null;
    if (workspaceId) {
      try { await endLiveScreenLoginOnLogout(workspaceId); }
      catch (error) { console.warn("Live-screen logout-all revocation deferred to lease expiry", error); }
    }
    return await api.post<LogoutAllResponse>(
      "/auth/logout-all",
    );
  } finally {
    clearAuthSession();
  }
}


async function getGoogleAuthorization(
  intent:
    OAuthIntent =
      "login",
  rememberMe =
    false,
): Promise<OAuthAuthorizationResponse> {
  const query =
    new URLSearchParams({
      intent,

      remember_me:
        String(
          rememberMe,
        ),
    });

  return api.get<OAuthAuthorizationResponse>(
    `/auth/oauth/google/authorize?${query.toString()}`,
    {
      auth:
        false,

      retryOnUnauthorized:
        false,
    },
  );
}


async function exchangeOAuthCode(
  payload:
    OAuthExchangeRequest,
): Promise<OAuthExchangeResponse> {
  return api.post<OAuthExchangeResponse>(
    "/auth/oauth/exchange",
    payload,
    {
      auth:
        false,

      retryOnUnauthorized:
        false,

      headers: {
        "X-Device-Name":
          getWebDeviceName(),
      },
    },
  );
}


export const authService = {
  login,
  signup,

  verifyEmail,
  resendVerification,

  forgotPassword,
  verifyResetOtp,
  resetPassword,

  getCurrentUser,
  getVerifiedCurrentUser,

  getSessions,
  revokeSession,

  logout,
  logoutAll,

  getGoogleAuthorization,
  exchangeOAuthCode,
};


export function persistLogin(
  response:
    TokenResponse,
  rememberMe:
    boolean,
): void {
  saveAuthSession(
    response,
    rememberMe,
  );
}