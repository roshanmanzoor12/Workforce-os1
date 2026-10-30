
"use client";

import { useEffect, useState } from "react";
import { useWorkspace } from "@/contexts/workspace-context";
import { api } from "@/lib/api/client";

export function CallingNumber() {
  const { user } = useWorkspace();
  const owner = user?.id;

  const [value, setValue] = useState<{
    owner: string;
    number: string;
  } | null>(null);
  const [error, setError] = useState("");
  const [retry, setRetry] = useState(0);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!owner) return;

    let stopped = false;

    setValue(null);
    setError("");
    setCopied(false);

    void api
      .get<{ calling_number: string }>(
        "/calls/numbers/me",
      )
      .then(result => {
        if (
          !/^[0-9]{10}$/.test(
            result.calling_number,
          )
        ) {
          throw new Error(
            "The server returned an invalid calling number.",
          );
        }

        if (!stopped) {
          setValue({
            owner,
            number: result.calling_number,
          });
        }
      })
      .catch(cause => {
        if (!stopped) {
          setError(
            cause instanceof Error
              ? cause.message
              : "Could not load your calling number.",
          );
        }
      });

    return () => {
      stopped = true;
    };
  }, [owner, retry]);

  if (error) {
    return (
      <span role="alert">
        {error}{" "}
        <button
          type="button"
          onClick={() =>
            setRetry(value => value + 1)
          }
        >
          Retry
        </button>
      </span>
    );
  }

  if (!value || value.owner !== owner) {
    return (
      <span role="status">
        Loading…
      </span>
    );
  }

  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 8,
        flexWrap: "wrap",
      }}
    >
      <code
        style={{
          letterSpacing: ".06em",
        }}
      >
        {value.number}
      </code>

      <button
        type="button"
        style={{
          border: 0,
          background: "#fff0b7",
          borderRadius: 5,
          padding: "3px 7px",
          color: "#252627",
          cursor: "pointer",
          fontSize: 11,
        }}
        onClick={() => {
          if (!navigator.clipboard) {
            window.prompt(
              "Copy calling number",
              value.number,
            );
            return;
          }

          void navigator.clipboard
            .writeText(value.number)
            .then(() => setCopied(true))
            .catch(() => {
              window.prompt(
                "Copy calling number",
                value.number,
              );
            });
        }}
      >
        {copied ? "Copied" : "Copy"}
      </button>
    </span>
  );
}
