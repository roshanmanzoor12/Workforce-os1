"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";

import type {
  APIKeyCreateRequest,
} from "@/types/api-keys";

export function ApiKeyCreateForm({
  saving,
  onSubmit,
  onCancel,
}: {
  saving: boolean;
  onSubmit: (
    payload: APIKeyCreateRequest,
  ) => Promise<void>;
  onCancel: () => void;
}) {
  const [name, setName] =
    useState("");

  const [scopes, setScopes] =
    useState("");

  const [expiresAt, setExpiresAt] =
    useState("");

  const submit = async () => {
    const normalizedScopes =
      scopes
        .split(",")
        .map((scope) =>
          scope.trim(),
        )
        .filter(Boolean);

    if (
      !name.trim() ||
      normalizedScopes.length === 0
    ) {
      return;
    }

    await onSubmit({
      name: name.trim(),
      scopes: normalizedScopes,
      expires_at: expiresAt
        ? new Date(
            `${expiresAt}T23:59:59`,
          ).toISOString()
        : null,
    });
  };

  return (
    <div
      style={{
        display: "grid",
        gap: 14,
      }}
    >
      <label style={labelStyle}>
        API Key Name

        <input
          value={name}
          onChange={(event) =>
            setName(
              event.target.value,
            )
          }
          maxLength={120}
          placeholder="Production Integration"
          style={inputStyle}
        />
      </label>

      <label style={labelStyle}>
        Scopes

        <input
          value={scopes}
          onChange={(event) =>
            setScopes(
              event.target.value,
            )
          }
          placeholder="employees:read, reports:read"
          style={inputStyle}
        />

        <span className="text-label">
          Enter one or more backend-supported scopes separated by commas.
        </span>
      </label>

      <label style={labelStyle}>
        Expiration Date

        <input
          type="date"
          value={expiresAt}
          onChange={(event) =>
            setExpiresAt(
              event.target.value,
            )
          }
          style={inputStyle}
        />

        <span className="text-label">
          Leave empty for no expiration.
        </span>
      </label>

      <div
        style={{
          display: "flex",
          justifyContent: "flex-end",
          gap: 8,
        }}
      >
        <Button
          variant="outline"
          disabled={saving}
          onClick={onCancel}
        >
          Cancel
        </Button>

        <Button
          disabled={
            saving ||
            !name.trim() ||
            !scopes.trim()
          }
          onClick={() =>
            void submit()
          }
        >
          {saving
            ? "Creating…"
            : "Create API Key"}
        </Button>
      </div>
    </div>
  );
}

const inputStyle = {
  width: "100%",
  minHeight: 36,
  padding: "0 10px",
  border:
    "1px solid var(--color-border)",
  borderRadius: 7,
  background: "#fffefa",
  color: "#303235",
  fontSize: 11,
  outline: "none",
} as const;

const labelStyle = {
  display: "grid",
  gap: 6,
  color: "var(--color-text-muted)",
  fontSize: 10,
} as const;