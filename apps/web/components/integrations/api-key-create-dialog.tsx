"use client";

import {
  useEffect,
  useRef,
  useState,
  type FormEvent,
} from "react";

import { X } from "lucide-react";

import { Button } from "@/components/ui/button";

import {
  useModalFocus,
} from "@/lib/ui/use-modal-focus";

import {
  parseAPIKeyScopes,
} from "@/lib/integrations/api-key-display";

import type {
  APIKeyCreateRequest,
} from "@/types/api-keys";

interface APIKeyCreateDialogProps {
  open: boolean;
  saving?: boolean;
  error?: string | null;
  onClose: () => void;
  onSubmit: (
    payload: APIKeyCreateRequest,
  ) => Promise<void>;
}

export function APIKeyCreateDialog({
  open,
  saving = false,
  error = null,
  onClose,
  onSubmit,
}: APIKeyCreateDialogProps) {
  const [name, setName] = useState("");
  const [scopeText, setScopeText] = useState("");
  const [expiresAt, setExpiresAt] = useState("");

  const [localError, setLocalError] =
    useState<string | null>(null);

  const [submitting, setSubmitting] =
    useState(false);

  const submitLock = useRef(false);
  const alive = useRef(false);

  const busy = saving || submitting;

  const dialogRef = useModalFocus(
    open,
    onClose,
    busy,
  );

  useEffect(() => {
    alive.current = true;

    return () => {
      alive.current = false;
    };
  }, []);

  useEffect(() => {
    if (!open) return;

    setName("");
    setScopeText("");
    setExpiresAt("");
    setLocalError(null);
  }, [open]);

  if (!open) return null;

  async function submit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    if (busy || submitLock.current) return;

    const trimmedName = name.trim();
    const scopes = parseAPIKeyScopes(scopeText);

    if (
      !trimmedName ||
      trimmedName.length > 120
    ) {
      setLocalError(
        "Enter a key name between 1 and 120 characters.",
      );
      return;
    }

    if (scopes.length === 0) {
      setLocalError(
        "Enter at least one supported API scope.",
      );
      return;
    }

    let expiry: string | null = null;

    if (expiresAt) {
      const parsed = new Date(expiresAt);

      if (
        !Number.isFinite(parsed.getTime()) ||
        parsed.getTime() <= Date.now()
      ) {
        setLocalError(
          "Expiry must be a valid future date and time.",
        );
        return;
      }

      expiry = parsed.toISOString();
    }

    submitLock.current = true;
    setSubmitting(true);
    setLocalError(null);

    try {
      await onSubmit({
        name: trimmedName,
        scopes,
        expires_at: expiry,
      });
    } catch (cause) {
      if (alive.current) {
        setLocalError(
          cause instanceof Error
            ? cause.message
            : "Unable to create API key. Try again.",
        );
      }
    } finally {
      submitLock.current = false;

      if (alive.current) {
        setSubmitting(false);
      }
    }
  }

  return (
    <div
      ref={dialogRef}
      tabIndex={-1}
      role="dialog"
      aria-modal="true"
      aria-labelledby="api-key-create-title"
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 100,
        padding: 20,
        display: "grid",
        placeItems: "center",
        background: "rgba(15,23,42,.42)",
      }}
      onMouseDown={(event) => {
        if (
          event.target === event.currentTarget &&
          !busy &&
          !submitLock.current
        ) {
          onClose();
        }
      }}
    >
      <section
        className="panel"
        style={{
          width: "min(620px,100%)",
          maxHeight: "90dvh",
          overflowY: "auto",
          background:
            "var(--color-surface, #fff)",
        }}
      >
        <div
          className="panel-header"
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <h2 id="api-key-create-title">
            Create API Key
          </h2>

          <Button
            type="button"
            variant="ghost"
            size="sm"
            disabled={busy}
            onClick={onClose}
            aria-label="Close"
          >
            <X size={16} />
          </Button>
        </div>

        <form
          className="panel-body"
          onSubmit={(event) =>
            void submit(event)
          }
          style={{
            display: "grid",
            gap: 16,
          }}
        >
          {(localError || error) ? (
            <p role="alert">
              {localError || error}
            </p>
          ) : null}

          <label style={labelStyle}>
            Key name

            <input
              required
              maxLength={120}
              value={name}
              onChange={(event) =>
                setName(event.target.value)
              }
              disabled={busy}
              style={inputStyle}
            />
          </label>

          <label style={labelStyle}>
            Access scopes

            <textarea
              required
              rows={3}
              value={scopeText}
              onChange={(event) =>
                setScopeText(event.target.value)
              }
              disabled={busy}
              style={inputStyle}
              aria-describedby="api-key-scope-help"
            />
          </label>

          <p
            id="api-key-scope-help"
            className="text-label"
          >
            Enter supported scope names separated
            by commas or new lines. The server
            validates access scopes.
          </p>

          <label style={labelStyle}>
            Expiry (optional, your local time)

            <input
              type="datetime-local"
              value={expiresAt}
              onChange={(event) =>
                setExpiresAt(event.target.value)
              }
              disabled={busy}
              style={inputStyle}
            />
          </label>

          <div
            style={{
              display: "flex",
              justifyContent: "flex-end",
              gap: 8,
            }}
          >
            <Button
              type="button"
              variant="outline"
              disabled={busy}
              onClick={onClose}
            >
              Cancel
            </Button>

            <Button
              type="submit"
              disabled={busy}
            >
              {busy
                ? "Creating…"
                : "Create API Key"}
            </Button>
          </div>
        </form>
      </section>
    </div>
  );
}

const labelStyle = {
  display: "grid",
  gap: 7,
} as const;

const inputStyle = {
  width: "100%",
  minHeight: 40,
  padding: 10,
  fontSize: 16,
  border:
    "1px solid var(--color-border, #ddd)",
  borderRadius: 7,
  background:
    "var(--color-surface, #fff)",
  color: "inherit",
} as const;