"use client";

import {
  useState,
} from "react";

import {
  Check,
  Clipboard,
  KeyRound,
  X,
} from "lucide-react";

import type {
  APIKeyPublic,
} from "@/types/api-keys";

interface APIKeySecretDialogProps {
  open: boolean;

  keyData:
    | APIKeyPublic
    | null;

  secret:
    | string
    | null;

  title?: string;

  onClose: () => void;
}

export function APIKeySecretDialog({
  open,
  keyData,
  secret,
  title = "API Key Secret",
  onClose,
}: APIKeySecretDialogProps) {
  const [
    copied,
    setCopied,
  ] = useState(false);

  /*
   * Keep the narrowing outside the nested callback.
   *
   * TypeScript does not safely preserve the
   * `secret !== null` narrowing inside an async
   * nested function because that function executes
   * later.
   */
  if (
    !open ||
    !keyData ||
    !secret
  ) {
    return null;
  }

  const secretValue =
    secret;

  async function copySecret() {
    try {
      await navigator.clipboard.writeText(
        secretValue,
      );

      setCopied(true);

      window.setTimeout(
        () => {
          setCopied(false);
        },
        1800,
      );
    } catch {
      setCopied(false);
    }
  }

  function close() {
    setCopied(false);
    onClose();
  }

  return (
    <div
      role="presentation"
      onMouseDown={(event) => {
        if (
          event.target ===
          event.currentTarget
        ) {
          close();
        }
      }}
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 110,
        display: "grid",
        placeItems: "center",
        padding: 20,
        background:
          "rgba(15, 23, 42, 0.48)",
      }}
    >
      <section
        role="dialog"
        aria-modal="true"
        aria-labelledby="api-secret-title"
        style={{
          width: "100%",
          maxWidth: 610,
          border:
            "1px solid var(--color-border)",
          borderRadius: 14,
          background:
            "var(--color-surface)",
          boxShadow:
            "0 24px 70px rgba(0,0,0,.2)",
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent:
              "space-between",
            padding:
              "18px 20px",
            borderBottom:
              "1px solid var(--color-border)",
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 10,
            }}
          >
            <div
              style={{
                width: 36,
                height: 36,
                display: "grid",
                placeItems: "center",
                borderRadius: 9,
                background:
                  "var(--color-muted)",
              }}
            >
              <KeyRound
                size={18}
              />
            </div>

            <div>
              <h2
                id="api-secret-title"
                style={{
                  margin: 0,
                  fontSize: 17,
                }}
              >
                {title}
              </h2>

              <p
                className="text-label"
                style={{
                  margin:
                    "4px 0 0",
                }}
              >
                Save this secret now. It will not be shown again.
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={close}
            aria-label="Close"
            style={{
              width: 34,
              height: 34,
              display: "grid",
              placeItems: "center",
              border: 0,
              borderRadius: 8,
              background:
                "transparent",
              cursor: "pointer",
            }}
          >
            <X size={18} />
          </button>
        </div>

        <div
          style={{
            display: "grid",
            gap: 18,
            padding: 20,
          }}
        >
          <div
            style={{
              padding: 12,
              border:
                "1px solid #e8c76c",
              borderRadius: 9,
              background:
                "#fffaf0",
              color:
                "#6f4e00",
              fontSize: 12,
              lineHeight: 1.55,
            }}
          >
            <strong>
              Important:
            </strong>{" "}
            This secret is displayed only at creation or rotation time. WorkforceOS does not expose the secret through the normal API-key listing endpoint.
          </div>

          <div
            style={{
              display: "grid",
              gap: 7,
            }}
          >
            <span className="text-label">
              Key name
            </span>

            <strong>
              {keyData.name}
            </strong>
          </div>

          <div
            style={{
              display: "grid",
              gap: 7,
            }}
          >
            <span className="text-label">
              Secret
            </span>

            <div
              style={{
                display: "flex",
                alignItems: "stretch",
                gap: 8,
              }}
            >
              <code
                style={{
                  flex: 1,
                  minWidth: 0,
                  overflowX: "auto",
                  display: "block",
                  padding: 12,
                  border:
                    "1px solid var(--color-border)",
                  borderRadius: 8,
                  background:
                    "var(--color-muted)",
                  fontSize: 12,
                  lineHeight: 1.5,
                  wordBreak:
                    "break-all",
                }}
              >
                {secretValue}
              </code>

              <button
                type="button"
                onClick={copySecret}
                style={{
                  minWidth: 48,
                  display: "grid",
                  placeItems: "center",
                  border:
                    "1px solid var(--color-border)",
                  borderRadius: 8,
                  background:
                    "var(--color-surface)",
                  cursor: "pointer",
                }}
                aria-label="Copy API secret"
                title="Copy secret"
              >
                {copied ? (
                  <Check
                    size={17}
                  />
                ) : (
                  <Clipboard
                    size={17}
                  />
                )}
              </button>
            </div>

            <span className="text-label">
              Never put this secret into source code, screenshots, client-side configuration, or public repositories.
            </span>
          </div>

          <div
            style={{
              display: "flex",
              justifyContent:
                "space-between",
              gap: 12,
              alignItems:
                "center",
              paddingTop: 4,
            }}
          >
            <span className="text-label">
              Prefix:{" "}
              {keyData.key_prefix}
            </span>

            <button
              type="button"
              onClick={close}
              style={{
                minHeight: 40,
                padding:
                  "0 16px",
                border: 0,
                borderRadius: 8,
                background:
                  "var(--color-foreground)",
                color:
                  "var(--color-surface)",
                fontWeight: 650,
                cursor: "pointer",
              }}
            >
              Done
            </button>
          </div>
        </div>
      </section>
    </div>
  );
}