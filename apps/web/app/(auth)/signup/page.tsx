"use client";

import {
  ArrowRight,
  AtSign,
  Eye,
  EyeOff,
  LockKeyhole,
  Mail,
  User,
} from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  type FormEvent,
  useState,
} from "react";

import { WorkforceLogo } from "@/components/app-shell/workforce-logo";
import { startGoogleOAuth } from "@/lib/auth/google-oauth";
import { authService } from "@/services/auth.service";


function splitName(
  value: string,
): {
  firstName: string | null;
  lastName: string | null;
} {
  const parts = value
    .trim()
    .split(/\s+/)
    .filter(Boolean);

  if (parts.length === 0) {
    return {
      firstName: null,
      lastName: null,
    };
  }

  if (parts.length === 1) {
    return {
      firstName:
        parts[0] ?? null,
      lastName: null,
    };
  }

  return {
    firstName:
      parts[0] ?? null,
    lastName:
      parts
        .slice(1)
        .join(" ") || null,
  };
}


export default function SignupPage() {
  const router =
    useRouter();

  const [name, setName] =
    useState("");

  const [username, setUsername] =
    useState("");

  const [email, setEmail] =
    useState("");

  const [password, setPassword] =
    useState("");

  const [
    confirmPassword,
    setConfirmPassword,
  ] =
    useState("");

  const [
    showPassword,
    setShowPassword,
  ] =
    useState(false);

  const [
    submitting,
    setSubmitting,
  ] =
    useState(false);

  const [
    googleSubmitting,
    setGoogleSubmitting,
  ] =
    useState(false);

  const [
    error,
    setError,
  ] =
    useState<string | null>(
      null,
    );


  async function submit(
    event:
      FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    setError(
      null,
    );

    const normalizedName =
      name.trim();

    const normalizedUsername =
      username
        .trim()
        .toLowerCase();

    const normalizedEmail =
      email
        .trim()
        .toLowerCase();

    if (
      !normalizedName
    ) {
      setError(
        "Enter your full name.",
      );
      return;
    }

    if (
      normalizedUsername.length <
      3
    ) {
      setError(
        "Username must contain at least 3 characters.",
      );
      return;
    }

    if (
      !/^[a-z0-9._-]+$/.test(
        normalizedUsername,
      )
    ) {
      setError(
        "Username can only contain lowercase letters, numbers, dots, underscores, and hyphens.",
      );
      return;
    }

    if (
      !normalizedEmail
    ) {
      setError(
        "Enter your email address.",
      );
      return;
    }

    if (
      password.length < 8
    ) {
      setError(
        "Password must contain at least 8 characters.",
      );
      return;
    }

    if (
      password !==
      confirmPassword
    ) {
      setError(
        "Passwords do not match.",
      );
      return;
    }

    const {
      firstName,
      lastName,
    } =
      splitName(
        normalizedName,
      );

    setSubmitting(
      true,
    );

    try {
      const response =
        await authService.signup({
          email:
            normalizedEmail,

          username:
            normalizedUsername,

          password,

          confirm_password:
            confirmPassword,

          first_name:
            firstName,

          last_name:
            lastName,
        });

      if (
        typeof window !==
        "undefined"
      ) {
        window.sessionStorage.setItem(
          "workforce_pending_verification_email",
          normalizedEmail,
        );
      }

      if (
        response
          .verification_required
      ) {
        router.push(
          `/verify-email?email=${encodeURIComponent(
            normalizedEmail,
          )}`,
        );

        return;
      }

      router.push(
        "/login?verified=1",
      );
    } catch (
      cause
    ) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Unable to create your account.",
      );
    } finally {
      setSubmitting(
        false,
      );
    }
  }


  async function handleGoogleSignup() {
    if (
      submitting ||
      googleSubmitting
    ) {
      return;
    }

    setError(
      null,
    );

    setGoogleSubmitting(
      true,
    );

    try {
      await startGoogleOAuth(
        "signup",
      );
    } catch (
      cause
    ) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Unable to start Google sign up.",
      );

      setGoogleSubmitting(
        false,
      );
    }
  }


  const formDisabled =
    submitting ||
    googleSubmitting;


  return (
    <main
      style={{
        minHeight:
          "100dvh",
        display:
          "grid",
        placeItems:
          "center",
        padding:
          24,
        background:
          "var(--color-app-background)",
      }}
    >
      <section
        style={{
          width:
            "100%",
          maxWidth:
            480,
          padding:
            34,
          border:
            "1px solid var(--color-border)",
          borderRadius:
            12,
          background:
            "var(--color-surface)",
        }}
      >
        <WorkforceLogo />


        <h1
          style={{
            marginTop:
              34,
            fontSize:
              27,
            fontWeight:
              500,
            letterSpacing:
              "-0.03em",
          }}
        >
          Create your account
        </h1>


        <p
          className="text-muted"
          style={{
            marginTop:
              7,
            fontSize:
              12,
            lineHeight:
              1.6,
          }}
        >
          Create your personal
          Workforce OS account.
          Company workspaces can be
          created or joined after
          authentication.
        </p>


        <button
          type="button"
          disabled={
            formDisabled
          }
          onClick={() => {
            void handleGoogleSignup();
          }}
          style={{
            width:
              "100%",
            height:
              44,
            marginTop:
              26,
            display:
              "flex",
            alignItems:
              "center",
            justifyContent:
              "center",
            gap:
              10,
            border:
              "1px solid var(--color-border)",
            borderRadius:
              8,
            background:
              "var(--color-surface)",
            color:
              "var(--color-text)",
            cursor:
              formDisabled
                ? "not-allowed"
                : "pointer",
            opacity:
              formDisabled
                ? 0.65
                : 1,
            fontSize:
              13,
            fontWeight:
              600,
          }}
        >
          <span
            aria-hidden="true"
            style={{
              width:
                20,
              height:
                20,
              minWidth:
                20,
              display:
                "inline-flex",
              alignItems:
                "center",
              justifyContent:
                "center",
              border:
                "1px solid #ddd7cb",
              borderRadius:
                "50%",
              background:
                "#ffffff",
              color:
                "#4285f4",
              fontSize:
                12,
              fontWeight:
                700,
              lineHeight:
                1,
            }}
          >
            G
          </span>

          {googleSubmitting
            ? "Connecting to Google..."
            : "Sign up with Google"}
        </button>


        <div
          style={{
            display:
              "flex",
            alignItems:
              "center",
            gap:
              12,
            margin:
              "20px 0",
          }}
        >
          <div
            style={{
              height:
                1,
              flex:
                1,
              background:
                "var(--color-border)",
            }}
          />

          <span
            style={{
              color:
                "var(--color-text-muted)",
              fontSize:
                10,
              fontWeight:
                500,
              textTransform:
                "uppercase",
              letterSpacing:
                "0.08em",
            }}
          >
            or continue with email
          </span>

          <div
            style={{
              height:
                1,
              flex:
                1,
              background:
                "var(--color-border)",
            }}
          />
        </div>


        <form
          onSubmit={
            submit
          }
        >
          <AuthField
            label="Full Name"
            icon={
              <User
                size={
                  15
                }
              />
            }
          >
            <input
              className="input"
              autoComplete="name"
              value={
                name
              }
              placeholder="James Fuller"
              disabled={
                formDisabled
              }
              onChange={(
                event,
              ) =>
                setName(
                  event
                    .target
                    .value,
                )
              }
              style={{
                paddingLeft:
                  38,
              }}
            />
          </AuthField>


          <AuthField
            label="Username"
            icon={
              <AtSign
                size={
                  15
                }
              />
            }
          >
            <input
              className="input"
              autoComplete="username"
              value={
                username
              }
              placeholder="jamesfuller"
              disabled={
                formDisabled
              }
              onChange={(
                event,
              ) =>
                setUsername(
                  event
                    .target
                    .value
                    .toLowerCase(),
                )
              }
              style={{
                paddingLeft:
                  38,
              }}
            />
          </AuthField>


          <AuthField
            label="Email Address"
            icon={
              <Mail
                size={
                  15
                }
              />
            }
          >
            <input
              className="input"
              type="email"
              autoComplete="email"
              value={
                email
              }
              placeholder="name@company.com"
              disabled={
                formDisabled
              }
              onChange={(
                event,
              ) =>
                setEmail(
                  event
                    .target
                    .value,
                )
              }
              style={{
                paddingLeft:
                  38,
              }}
            />
          </AuthField>


          <AuthField
            label="Password"
            icon={
              <LockKeyhole
                size={
                  15
                }
              />
            }
          >
            <div
              style={{
                position:
                  "relative",
              }}
            >
              <input
                className="input"
                type={
                  showPassword
                    ? "text"
                    : "password"
                }
                autoComplete="new-password"
                value={
                  password
                }
                placeholder="Create a password"
                disabled={
                  formDisabled
                }
                onChange={(
                  event,
                ) =>
                  setPassword(
                    event
                      .target
                      .value,
                  )
                }
                style={{
                  paddingLeft:
                    38,
                  paddingRight:
                    42,
                }}
              />

              <button
                type="button"
                aria-label={
                  showPassword
                    ? "Hide password"
                    : "Show password"
                }
                disabled={
                  formDisabled
                }
                onClick={() =>
                  setShowPassword(
                    (
                      current,
                    ) =>
                      !current,
                  )
                }
                style={{
                  position:
                    "absolute",
                  top:
                    "50%",
                  right:
                    12,
                  display:
                    "grid",
                  placeItems:
                    "center",
                  border:
                    0,
                  padding:
                    0,
                  background:
                    "transparent",
                  color:
                    "#777b80",
                  cursor:
                    formDisabled
                      ? "not-allowed"
                      : "pointer",
                  transform:
                    "translateY(-50%)",
                }}
              >
                {showPassword ? (
                  <EyeOff
                    size={
                      16
                    }
                  />
                ) : (
                  <Eye
                    size={
                      16
                    }
                  />
                )}
              </button>
            </div>
          </AuthField>


          <AuthField
            label="Confirm Password"
            icon={
              <LockKeyhole
                size={
                  15
                }
              />
            }
          >
            <input
              className="input"
              type={
                showPassword
                  ? "text"
                  : "password"
              }
              autoComplete="new-password"
              value={
                confirmPassword
              }
              placeholder="Confirm password"
              disabled={
                formDisabled
              }
              onChange={(
                event,
              ) =>
                setConfirmPassword(
                  event
                    .target
                    .value,
                )
              }
              style={{
                paddingLeft:
                  38,
              }}
            />
          </AuthField>


          {error ? (
            <div
              className="auth-error"
              role="alert"
              style={{
                marginBottom:
                  12,
              }}
            >
              {error}
            </div>
          ) : null}


          <button
            type="submit"
            className="button button--primary"
            disabled={
              formDisabled
            }
            style={{
              width:
                "100%",
              marginTop:
                8,
            }}
          >
            {submitting
              ? "Creating Account..."
              : "Create Account"}

            {!submitting ? (
              <ArrowRight
                size={
                  15
                }
              />
            ) : null}
          </button>
        </form>


        <p
          style={{
            marginTop:
              20,
            textAlign:
              "center",
            fontSize:
              11,
            color:
              "var(--color-text-muted)",
          }}
        >
          Already have an
          account?{" "}
          <Link
            href="/login"
            style={{
              color:
                "#916700",
              fontWeight:
                600,
            }}
          >
            Sign in
          </Link>
        </p>
      </section>
    </main>
  );
}


function AuthField({
  label,
  icon,
  children,
}: {
  label: string;
  icon:
    React.ReactNode;
  children:
    React.ReactNode;
}) {
  return (
    <label
      className="field"
      style={{
        display:
          "block",
        marginBottom:
          14,
      }}
    >
      <span className="field-label">
        {label}
      </span>

      <div
        style={{
          position:
            "relative",
        }}
      >
        <span
          style={{
            position:
              "absolute",
            top:
              "50%",
            left:
              12,
            zIndex:
              2,
            display:
              "grid",
            placeItems:
              "center",
            color:
              "#808489",
            transform:
              "translateY(-50%)",
            pointerEvents:
              "none",
          }}
        >
          {icon}
        </span>

        {children}
      </div>
    </label>
  );
}