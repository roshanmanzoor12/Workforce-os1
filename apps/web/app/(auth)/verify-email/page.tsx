"use client";

import {
  ArrowRight,
  CheckCircle2,
  MailCheck,
  RefreshCcw,
} from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  type FormEvent,
  useEffect,
  useState,
} from "react";

import { WorkforceLogo } from "@/components/app-shell/workforce-logo";
import { Button } from "@/components/ui/button";
import { authService } from "@/services/auth.service";

export default function VerifyEmailPage() {
  const router = useRouter();

  const [email, setEmail] =
    useState("");

  const [otp, setOtp] =
    useState("");

  const [
    submitting,
    setSubmitting,
  ] = useState(false);

  const [
    resending,
    setResending,
  ] = useState(false);

  const [
    verified,
    setVerified,
  ] = useState(false);

  const [
    message,
    setMessage,
  ] = useState<string | null>(
    null,
  );

  const [error, setError] =
    useState<string | null>(null);

  useEffect(() => {
    const params =
      new URLSearchParams(
        window.location.search,
      );

    const emailFromUrl =
      params.get("email");

    const storedEmail =
      window.sessionStorage.getItem(
        "workforce_pending_verification_email",
      );

    setEmail(
      emailFromUrl ??
        storedEmail ??
        "",
    );
  }, []);

  async function handleVerify(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    setError(null);
    setMessage(null);

    const normalizedEmail =
      email.trim().toLowerCase();

    const normalizedOtp =
      otp.trim();

    if (!normalizedEmail) {
      setError(
        "Enter the email address used during signup.",
      );
      return;
    }

    if (!normalizedOtp) {
      setError(
        "Enter the verification code sent to your email.",
      );
      return;
    }

    setSubmitting(true);

    try {
      const response =
        await authService.verifyEmail({
          email:
            normalizedEmail,

          otp:
            normalizedOtp,
        });

      if (!response.verified) {
        setError(
          response.message ||
            "Email verification was not completed.",
        );

        return;
      }

      setVerified(true);

      setMessage(
        response.message ||
          "Your email has been verified.",
      );

      window.sessionStorage.removeItem(
        "workforce_pending_verification_email",
      );
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Unable to verify your email.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  async function handleResend() {
    setError(null);
    setMessage(null);

    const normalizedEmail =
      email.trim().toLowerCase();

    if (!normalizedEmail) {
      setError(
        "Enter your email address first.",
      );
      return;
    }

    setResending(true);

    try {
      const response =
        await authService.resendVerification(
          {
            email:
              normalizedEmail,
          },
        );

      setMessage(
        response.message ||
          "A new verification code has been sent.",
      );
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Unable to resend the verification code.",
      );
    } finally {
      setResending(false);
    }
  }

  if (verified) {
    return (
      <main
        style={{
          minHeight: "100dvh",
          display: "grid",
          placeItems: "center",
          padding: 24,
          background:
            "var(--color-app-background)",
        }}
      >
        <section
          style={{
            width: "100%",
            maxWidth: 460,
            padding: 36,
            border:
              "1px solid var(--color-border)",
            borderRadius: 12,
            background:
              "var(--color-surface)",
            textAlign:
              "center",
          }}
        >
          <div
            style={{
              display: "flex",
              justifyContent:
                "center",
            }}
          >
            <WorkforceLogo />
          </div>

          <div
            style={{
              display: "grid",
              width: 58,
              height: 58,
              margin:
                "34px auto 0",
              placeItems:
                "center",
              borderRadius:
                "50%",
              background:
                "var(--color-success-soft)",
              color:
                "var(--color-success-dark)",
            }}
          >
            <CheckCircle2
              size={27}
            />
          </div>

          <h1
            style={{
              marginTop: 20,
              fontSize: 27,
              fontWeight: 500,
              letterSpacing:
                "-0.03em",
            }}
          >
            Email verified
          </h1>

          <p
            style={{
              marginTop: 9,
              color:
                "var(--color-text-muted)",
              fontSize: 12,
              lineHeight: 1.7,
            }}
          >
            {message ??
              "Your Workforce OS account is ready."}
          </p>

          <Button
            style={{
              width: "100%",
              marginTop: 24,
            }}
            onClick={() =>
              router.replace(
                "/login?verified=1",
              )
            }
          >
            Continue to Sign In

            <ArrowRight
              size={15}
            />
          </Button>
        </section>
      </main>
    );
  }

  return (
    <main
      style={{
        minHeight: "100dvh",
        display: "grid",
        placeItems: "center",
        padding: 24,
        background:
          "var(--color-app-background)",
      }}
    >
      <section
        style={{
          width: "100%",
          maxWidth: 460,
          padding: 36,
          border:
            "1px solid var(--color-border)",
          borderRadius: 12,
          background:
            "var(--color-surface)",
          textAlign: "center",
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "center",
          }}
        >
          <WorkforceLogo />
        </div>

        <div
          style={{
            display: "grid",
            width: 58,
            height: 58,
            margin: "34px auto 0",
            placeItems: "center",
            borderRadius: "50%",
            background:
              "var(--color-brand-soft)",
            color: "#a87300",
          }}
        >
          <MailCheck size={27} />
        </div>

        <h1
          style={{
            marginTop: 20,
            fontSize: 27,
            fontWeight: 500,
            letterSpacing:
              "-0.03em",
          }}
        >
          Verify your email
        </h1>

        <p
          style={{
            marginTop: 9,
            color:
              "var(--color-text-muted)",
            fontSize: 12,
            lineHeight: 1.7,
          }}
        >
          Enter the verification
          code sent to your email
          address.
        </p>

        <form
          onSubmit={
            handleVerify
          }
          style={{
            marginTop: 24,
            textAlign: "left",
          }}
        >
          <label className="field">
            <span className="field-label">
              Email Address
            </span>

            <input
              className="input"
              type="email"
              autoComplete="email"
              value={email}
              disabled={
                submitting ||
                resending
              }
              onChange={(event) =>
                setEmail(
                  event.target.value,
                )
              }
            />
          </label>

          <label
            className="field"
            style={{
              marginTop: 14,
            }}
          >
            <span className="field-label">
              Verification Code
            </span>

            <input
              className="input"
              type="text"
              inputMode="numeric"
              autoComplete="one-time-code"
              value={otp}
              placeholder="Enter code"
              disabled={
                submitting ||
                resending
              }
              onChange={(event) =>
                setOtp(
                  event.target.value.replace(
                    /\s/g,
                    "",
                  ),
                )
              }
              style={{
                fontSize: 18,
                fontWeight: 600,
                letterSpacing:
                  "0.14em",
                textAlign:
                  "center",
              }}
            />
          </label>

          {error ? (
            <div
              className="auth-error"
              role="alert"
              style={{
                marginTop: 14,
              }}
            >
              {error}
            </div>
          ) : null}

          {message ? (
            <div
              style={{
                marginTop: 14,
                padding: 10,
                border:
                  "1px solid var(--color-border)",
                borderRadius: 8,
                background:
                  "var(--color-success-soft)",
                color:
                  "var(--color-success-dark)",
                fontSize: 11,
              }}
            >
              {message}
            </div>
          ) : null}

          <Button
            type="submit"
            style={{
              width: "100%",
              marginTop: 18,
            }}
            disabled={
              submitting ||
              resending
            }
          >
            {submitting
              ? "Verifying..."
              : "Verify Email"}
          </Button>

          <Button
            type="button"
            variant="outline"
            style={{
              width: "100%",
              marginTop: 9,
            }}
            disabled={
              submitting ||
              resending
            }
            onClick={() =>
              void handleResend()
            }
          >
            <RefreshCcw
              size={14}
            />

            {resending
              ? "Sending..."
              : "Resend Code"}
          </Button>
        </form>

        <p
          style={{
            marginTop: 20,
            fontSize: 11,
            color:
              "var(--color-text-muted)",
          }}
        >
          Already verified?{" "}
          <Link
            href="/login"
            style={{
              color: "#916700",
              fontWeight: 600,
            }}
          >
            Sign in
          </Link>
        </p>
      </section>
    </main>
  );
}