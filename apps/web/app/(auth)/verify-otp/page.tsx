"use client";

import {
  CheckCircle2,
  MailCheck,
} from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { WorkforceLogo } from "@/components/app-shell/workforce-logo";
import { Button } from "@/components/ui/button";

export default function VerifyEmailPage() {
  const router = useRouter();

  const [verified, setVerified] =
    useState(false);
  const [resent, setResent] =
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
            background: verified
              ? "var(--color-success-soft)"
              : "var(--color-brand-soft)",
            color: verified
              ? "var(--color-success-dark)"
              : "#a87300",
          }}
        >
          {verified ? (
            <CheckCircle2 size={27} />
          ) : (
            <MailCheck size={27} />
          )}
        </div>

        <h1
          style={{
            marginTop: 20,
            fontSize: 27,
            fontWeight: 500,
            letterSpacing: "-0.03em",
          }}
        >
          {verified
            ? "Email verified"
            : "Verify your email"}
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
          {verified
            ? "Your Workforce OS account is ready."
            : "We sent a verification link to your email address. Open the message and confirm your account."}
        </p>

        {!verified ? (
          <>
            <Button
              style={{
                width: "100%",
                marginTop: 24,
              }}
              onClick={() =>
                setVerified(true)
              }
            >
              I&apos;ve Verified My Email
            </Button>

            <Button
              variant="outline"
              style={{
                width: "100%",
                marginTop: 9,
              }}
              onClick={() =>
                setResent(true)
              }
            >
              Resend Email
            </Button>

            {resent ? (
              <div
                style={{
                  marginTop: 12,
                  color:
                    "var(--color-success-dark)",
                  fontSize: 11,
                }}
              >
                Verification email resent.
              </div>
            ) : null}
          </>
        ) : (
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
        )}
      </section>
    </div>
  );
}