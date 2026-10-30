"use client";

import { useState } from "react";
import {
  CheckCircle2,
  Eye,
  EyeOff,
  LockKeyhole,
} from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { WorkforceLogo } from "@/components/app-shell/workforce-logo";
import { Button } from "@/components/ui/button";

export default function ResetPasswordPage() {
  const router = useRouter();

  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] =
    useState("");
  const [showPassword, setShowPassword] =
    useState(false);
  const [showConfirmPassword, setShowConfirmPassword] =
    useState(false);
  const [error, setError] =
    useState<string | null>(null);
  const [completed, setCompleted] =
    useState(false);

  function submit(
    event: React.FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    setError(null);

    if (password.length < 8) {
      setError(
        "Password must be at least 8 characters.",
      );
      return;
    }

    if (password !== confirmPassword) {
      setError(
        "Passwords do not match.",
      );
      return;
    }

    setCompleted(true);
  }

  return (
    <div
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
          maxWidth: 450,
          padding: 34,
          border:
            "1px solid var(--color-border)",
          borderRadius: 12,
          background:
            "var(--color-surface)",
        }}
      >
        <WorkforceLogo />

        {!completed ? (
          <>
            <h1
              style={{
                marginTop: 34,
                color: "var(--color-black)",
                fontSize: 27,
                fontWeight: 500,
                letterSpacing: "-0.03em",
              }}
            >
              Create new password
            </h1>

            <p
              style={{
                marginTop: 8,
                color:
                  "var(--color-text-muted)",
                fontSize: 12,
                lineHeight: 1.6,
              }}
            >
              Choose a secure password for your
              Workforce OS account.
            </p>

            <form
              onSubmit={submit}
              style={{
                marginTop: 24,
              }}
            >
              <PasswordField
                label="New Password"
                value={password}
                visible={showPassword}
                onChange={setPassword}
                onToggle={() =>
                  setShowPassword(
                    (current) => !current,
                  )
                }
              />

              <PasswordField
                label="Confirm Password"
                value={confirmPassword}
                visible={showConfirmPassword}
                onChange={setConfirmPassword}
                onToggle={() =>
                  setShowConfirmPassword(
                    (current) => !current,
                  )
                }
              />

              {error ? (
                <div
                  role="alert"
                  style={{
                    marginTop: 14,
                    padding: "10px 12px",
                    borderRadius: 8,
                    background:
                      "var(--color-danger-soft)",
                    color:
                      "var(--color-danger-dark)",
                    fontSize: 11,
                  }}
                >
                  {error}
                </div>
              ) : null}

              <Button
                type="submit"
                style={{
                  width: "100%",
                  marginTop: 18,
                }}
              >
                Reset Password
              </Button>
            </form>
          </>
        ) : (
          <div
            style={{
              paddingTop: 42,
              textAlign: "center",
            }}
          >
            <div
              style={{
                display: "grid",
                width: 56,
                height: 56,
                margin: "0 auto",
                placeItems: "center",
                borderRadius: "50%",
                background:
                  "var(--color-success-soft)",
                color:
                  "var(--color-success-dark)",
              }}
            >
              <CheckCircle2 size={26} />
            </div>

            <h1
              style={{
                marginTop: 20,
                fontSize: 25,
                fontWeight: 500,
              }}
            >
              Password updated
            </h1>

            <p
              style={{
                marginTop: 8,
                color:
                  "var(--color-text-muted)",
                fontSize: 12,
                lineHeight: 1.6,
              }}
            >
              Your password has been changed
              successfully.
            </p>

            <Button
              style={{
                width: "100%",
                marginTop: 24,
              }}
              onClick={() =>
                router.push("/login")
              }
            >
              Continue to Sign In
            </Button>
          </div>
        )}

        {!completed ? (
          <p
            style={{
              marginTop: 20,
              textAlign: "center",
              fontSize: 11,
            }}
          >
            <Link
              href="/login"
              style={{
                color: "#916700",
                fontWeight: 600,
              }}
            >
              Back to sign in
            </Link>
          </p>
        ) : null}
      </section>
    </div>
  );
}

function PasswordField({
  label,
  value,
  visible,
  onChange,
  onToggle,
}: {
  label: string;
  value: string;
  visible: boolean;
  onChange: (value: string) => void;
  onToggle: () => void;
}) {
  return (
    <label
      className="field"
      style={{
        marginBottom: 14,
      }}
    >
      <span className="field-label">
        {label}
      </span>

      <div
        style={{
          position: "relative",
        }}
      >
        <LockKeyhole
          size={15}
          style={{
            position: "absolute",
            left: 12,
            top: "50%",
            color: "#83868a",
            transform: "translateY(-50%)",
          }}
        />

        <input
          className="input"
          type={
            visible
              ? "text"
              : "password"
          }
          value={value}
          autoComplete="new-password"
          placeholder="Enter password"
          onChange={(event) =>
            onChange(event.target.value)
          }
          style={{
            paddingLeft: 38,
            paddingRight: 42,
          }}
        />

        <button
          type="button"
          onClick={onToggle}
          aria-label={
            visible
              ? "Hide password"
              : "Show password"
          }
          style={{
            position: "absolute",
            top: "50%",
            right: 7,
            display: "grid",
            width: 28,
            height: 28,
            placeItems: "center",
            border: 0,
            borderRadius: 6,
            background: "transparent",
            color: "#73777b",
            cursor: "pointer",
            transform: "translateY(-50%)",
          }}
        >
          {visible ? (
            <EyeOff size={15} />
          ) : (
            <Eye size={15} />
          )}
        </button>
      </div>
    </label>
  );
}