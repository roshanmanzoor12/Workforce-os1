import type {
  OAuthAuthorizationResponse,
} from "@/types/auth";

import {
  setOAuthIntent,
} from "@/lib/auth/oauth-intent";

export type OAuthIntent =
  | "login"
  | "signup";

export class GoogleOAuthError
  extends Error {
  constructor(
    message: string,
  ) {
    super(message);

    this.name =
      "GoogleOAuthError";
  }
}


/**
 * Resolve the actual backend origin.
 *
 * OAuth state is stored by the backend on the backend host.
 * Therefore this request must not silently go through the
 * Next.js `/backend` proxy when the OAuth callback itself is
 * going to `localhost:8001`.
 */
function getBackendApiBase(): string {
  const configured =
    process.env
      .NEXT_PUBLIC_API_BASE_URL
      ?.trim();

  if (
    configured &&
    /^https?:\/\//i.test(
      configured,
    )
  ) {
    return configured.replace(
      /\/+$/,
      "",
    );
  }

  /*
   * Current local WorkforceOS backend.
   *
   * Keep localhost consistent with the Google redirect URI.
   * Do not switch this fallback to 127.0.0.1 because localhost
   * and 127.0.0.1 are different cookie hosts.
   */
  return "http://localhost:8001/api/v1";
}


export async function startGoogleOAuth(
  intent: OAuthIntent,
  rememberMe = false,
): Promise<void> {
  if (
    typeof window ===
    "undefined"
  ) {
    throw new GoogleOAuthError(
      "Google authentication can only be started in the browser.",
    );
  }

  /*
   * Store the UI intent locally so the frontend callback knows
   * whether this flow started from Login or Signup.
   *
   * The backend remains the authority for the actual OAuth state.
   */
  setOAuthIntent(
    intent,
    rememberMe,
  );

  const query =
    new URLSearchParams({
      intent,
      remember_me:
        String(
          rememberMe,
        ),
    });

  const backendBase =
    getBackendApiBase();

  const endpoint =
    `${backendBase}/auth/oauth/google/authorize?${query.toString()}`;

  try {
    /*
     * credentials: include is critical here because the backend
     * sets the short-lived OAuth state cookie in this response.
     *
     * The browser must retain that cookie for the subsequent
     * Google -> backend callback.
     */
    const response =
      await fetch(
        endpoint,
        {
          method: "GET",

          headers: {
            Accept:
              "application/json",
          },

          credentials:
            "include",

          cache:
            "no-store",
        },
      );

    if (
      !response.ok
    ) {
      let message =
        "Google authentication could not be started.";

      try {
        const body =
          (await response.json()) as {
            detail?: unknown;
            message?: unknown;
            error?: {
              message?: unknown;
            };
          };

        if (
          typeof body.detail ===
          "string"
        ) {
          message =
            body.detail;
        } else if (
          typeof body.message ===
          "string"
        ) {
          message =
            body.message;
        } else if (
          typeof body.error?.message ===
          "string"
        ) {
          message =
            body.error.message;
        }
      } catch {
        // Keep the safe default message.
      }

      throw new GoogleOAuthError(
        message,
      );
    }

    const result =
      (await response.json()) as OAuthAuthorizationResponse;

    if (
      !result ||
      typeof result.authorization_url !==
        "string" ||
      !result.authorization_url
    ) {
      throw new GoogleOAuthError(
        "Google authorization URL was not returned by Workforce OS.",
      );
    }

    /*
     * Top-level navigation to Google.
     *
     * The backend state cookie has already been established
     * before this navigation occurs.
     */
    window.location.assign(
      result.authorization_url,
    );
  } catch (
    error
  ) {
    if (
      error instanceof
      GoogleOAuthError
    ) {
      throw error;
    }

    throw new GoogleOAuthError(
      "Unable to connect to Google authentication.",
    );
  }
}