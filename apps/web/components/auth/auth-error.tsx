"use client";

import Link from "next/link";

interface AuthErrorProps {
  title?: string;
  message: string;
  retryHref?: string;
  retryLabel?: string;
  secondaryHref?: string;
  secondaryLabel?: string;
}

export function AuthError({
  title = "Authentication error",
  message,
  retryHref = "/login",
  retryLabel = "Return to Sign In",
  secondaryHref = "/signup",
  secondaryLabel = "Create Account",
}: AuthErrorProps) {
  return (
    <section
      className="panel"
      style={{
        width: "min(100%, 500px)",
        padding: 32,
      }}
    >
      <div
        className="auth-error"
        role="alert"
      >
        {message}
      </div>

      <h1
        style={{
          marginTop: 18,
          fontSize: 22,
          fontWeight: 600,
        }}
      >
        {title}
      </h1>

      <div
        style={{
          display: "flex",
          gap: 8,
          flexWrap: "wrap",
          marginTop: 18,
        }}
      >
        <Link
          href={retryHref}
          className="button button--primary"
        >
          {retryLabel}
        </Link>

        {secondaryHref &&
        secondaryLabel ? (
          <Link
            href={secondaryHref}
            className="button button--outline"
          >
            {secondaryLabel}
          </Link>
        ) : null}
      </div>
    </section>
  );
}