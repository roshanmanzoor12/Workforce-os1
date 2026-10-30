import {
  Suspense,
} from "react";

import {
  OAuthCallbackClient,
} from "./oauth-callback-client";

export const dynamic = "force-dynamic";

export const metadata = {
  title: "Completing sign in",
};

function OAuthCallbackLoading() {
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
          width: "min(100%, 440px)",
          padding: 28,
          textAlign: "center",
        }}
      >
        <div
          className="auth-submit-spinner"
          style={{
            margin: "0 auto 16px",
          }}
        />

        <h1
          style={{
            margin: 0,
            fontSize: 22,
            fontWeight: 600,
          }}
        >
          Completing sign in
        </h1>

        <p
          className="text-label"
          style={{
            marginTop: 8,
            lineHeight: 1.6,
          }}
        >
          Please wait while Workforce OS securely
          completes your authentication.
        </p>
      </section>
    </main>
  );
}

export default function OAuthCallbackPage() {
  return (
    <Suspense fallback={<OAuthCallbackLoading />}>
      <OAuthCallbackClient />
    </Suspense>
  );
}