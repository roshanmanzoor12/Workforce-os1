"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";

import { WorkforceLogo } from "@/components/app-shell/workforce-logo";
import {
  clearAuthSession,
  saveOAuthSessionTokens,
  updateStoredUser,
} from "@/lib/auth/session";
import {
  clearOAuthIntent,
  getOAuthRememberMe,
} from "@/lib/auth/oauth-intent";
import { authService } from "@/services/auth.service";
import type { OAuthExchangeResponse } from "@/types/auth";

type CallbackStatus = "processing" | "success" | "error";

export function OAuthCallbackClient() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [callback] = useState(() => ({
    code: searchParams.get("code")?.trim() ?? "",
    error: searchParams.get("error"),
  }));

  const exchangeRef = useRef<
    Promise<OAuthExchangeResponse> | null
  >(null);

  const [status, setStatus] =
    useState<CallbackStatus>("processing");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    window.history.replaceState(
      window.history.state,
      document.title,
      window.location.pathname,
    );

    function fail(message: string) {
      if (!active) return;

      clearAuthSession();
      clearOAuthIntent();
      setError(message);
      setStatus("error");
    }

    if (callback.error) {
      fail(
        callback.error === "access_denied"
          ? "Google sign in was cancelled."
          : "Google authentication failed. Please start again from Sign In.",
      );

      return () => {
        active = false;
      };
    }

    if (callback.code.length < 20) {
      fail(
        "The authentication handoff code is missing or invalid. Please start again from Sign In.",
      );

      return () => {
        active = false;
      };
    }

    // Effect replay shares the same single-use exchange request.
    if (!exchangeRef.current) {
      exchangeRef.current = authService.exchangeOAuthCode({
        code: callback.code,
      });
    }

    async function completeAuthentication() {
      try {
        const response = await exchangeRef.current!;

        if (!active) return;

        const rememberMe =
          typeof response.remember_me === "boolean"
            ? response.remember_me
            : getOAuthRememberMe();

        saveOAuthSessionTokens(
          {
            access_token: response.access_token,
            refresh_token: response.refresh_token,
            expires_in: response.expires_in,
          },
          rememberMe,
        );

        updateStoredUser(response.user);

        // Verify that the stored session can authenticate an API call.
        await authService.getCurrentUser();

        if (!active) return;

        clearOAuthIntent();
        setStatus("success");
        router.replace("/home");
      } catch (cause) {
        fail(
          cause instanceof Error
            ? cause.message
            : "WorkforceOS could not establish your session. Please sign in again.",
        );
      }
    }

    void completeAuthentication();

    return () => {
      active = false;
    };
  }, [callback, router]);

  return (
    <main
      style={{
        minHeight: "100dvh",
        display: "grid",
        placeItems: "center",
        padding: 24,
        background: "#f7f4ec",
      }}
    >
      <section
        className="panel"
        style={{
          width: "min(100%, 500px)",
          padding: 32,
          textAlign: "center",
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "center",
            marginBottom: 22,
          }}
        >
          <WorkforceLogo />
        </div>

        {status === "error" ? (
          <>
            <div className="auth-error" role="alert">
              {error}
            </div>

            <button
              type="button"
              className="button button--primary"
              style={{ marginTop: 18 }}
              onClick={() => router.replace("/login")}
            >
              Return to Sign In
            </button>
          </>
        ) : (
          <div role="status" aria-live="polite">
            {status === "processing" && (
              <div
                className="auth-submit-spinner"
                style={{ margin: "0 auto 16px" }}
              />
            )}

            <h1 style={{ margin: 0, fontSize: 22 }}>
              {status === "success"
                ? "Authentication successful"
                : "Signing you in"}
            </h1>

            <p
              className="text-label"
              style={{ marginTop: 8, lineHeight: 1.65 }}
            >
              {status === "success"
                ? "Opening your personal home..."
                : "Completing Google authentication and verifying your account session."}
            </p>
          </div>
        )}
      </section>
    </main>
  );
}