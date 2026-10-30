"use client";

import { useState } from "react";

import {
  ArrowLeft,
  Mail,
} from "lucide-react";
import Link from "next/link";

import { Button } from "@/components/ui/button";
import { WorkforceLogo } from "@/components/app-shell/workforce-logo";

export default function ForgotPasswordPage() {
  const [email, setEmail] =
    useState("");
  const [sent, setSent] =
    useState(false);

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
          maxWidth: 440,
          padding: 34,
          border:
            "1px solid var(--color-border)",
          borderRadius: 12,
          background:
            "var(--color-surface)",
        }}
      >
        <WorkforceLogo />

        <h1
          style={{
            marginTop: 34,
            fontSize: 27,
            fontWeight: 500,
            letterSpacing: "-0.03em",
          }}
        >
          Reset your password
        </h1>

        <p
          className="text-muted"
          style={{
            marginTop: 8,
            fontSize: 12,
            lineHeight: 1.6,
          }}
        >
          Enter the email address
          associated with your account.
        </p>

        {!sent ? (
          <form
            onSubmit={(event) => {
              event.preventDefault();

              if (email.trim()) {
                setSent(true);
              }
            }}
            style={{
              marginTop: 24,
            }}
          >
            <label className="field">
              <span className="field-label">
                Email address
              </span>

              <div className="input-group">
                <Mail
                  size={15}
                  className="input-group__icon"
                />

                <input
                  className="input"
                  type="email"
                  value={email}
                  placeholder="name@company.com"
                  onChange={(event) =>
                    setEmail(
                      event.target.value,
                    )
                  }
                />
              </div>
            </label>

            <Button
              type="submit"
              style={{
                width: "100%",
                marginTop: 18,
              }}
            >
              Send Reset Link
            </Button>
          </form>
        ) : (
          <div
            style={{
              marginTop: 24,
              padding: 16,
              borderRadius: 8,
              background:
                "var(--color-success-soft)",
              color:
                "var(--color-success-dark)",
              fontSize: 12,
              lineHeight: 1.6,
            }}
          >
            Password reset instructions
            have been prepared for{" "}
            <strong>{email}</strong>.
          </div>
        )}

        <Link
          href="/login"
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 6,
            marginTop: 22,
            color:
              "var(--color-text-muted)",
            fontSize: 11,
          }}
        >
          <ArrowLeft size={14} />
          Back to sign in
        </Link>
      </section>
    </div>
  );
}