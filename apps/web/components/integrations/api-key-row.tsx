"use client";

import {
  useEffect,
  useRef,
  useState,
} from "react";

import {
  Clipboard,
  RefreshCcw,
  Trash2,
} from "lucide-react";

import { Button } from "@/components/ui/button";

import {
  formatAPIKeyScope,
} from "@/lib/integrations/api-key-display";

import type {
  APIKeyPublic,
} from "@/types/api-keys";

interface APIKeyRowProps {
  item: APIKeyPublic;
  busy?: boolean;
  onRotate: (item: APIKeyPublic) => Promise<void>;
  onRevoke: (item: APIKeyPublic) => Promise<void>;
}

function formatDate(
  value: string | null | undefined,
): string {
  if (!value) return "Never";

  const date = new Date(value);

  return Number.isFinite(date.getTime())
    ? date.toLocaleString()
    : "Unknown";
}

export function APIKeyRow({
  item,
  busy = false,
  onRotate,
  onRevoke,
}: APIKeyRowProps) {
  const [copied, setCopied] = useState(false);

  const [error, setError] =
    useState<string | null>(null);

  const timer =
    useRef<ReturnType<typeof setTimeout> | null>(
      null,
    );

  const alive = useRef(false);
  const actionLock = useRef(false);
  const [working, setWorking] = useState(false);

  useEffect(() => {
    alive.current = true;

    return () => {
      alive.current = false;

      if (timer.current) {
        clearTimeout(timer.current);
      }
    };
  }, []);

  const expired = Boolean(
    item.expires_at &&
    new Date(item.expires_at).getTime() <= Date.now(),
  );

  const status = item.revoked_at
    ? "Revoked"
    : expired
      ? "Expired"
      : "Active";

  const disabled = busy || working;

  async function copyId() {
    setError(null);

    try {
      await navigator.clipboard.writeText(item.id);

      if (!alive.current) return;

      setCopied(true);

      if (timer.current) {
        clearTimeout(timer.current);
      }

      timer.current = setTimeout(
        () => setCopied(false),
        1500,
      );
    } catch {
      if (alive.current) {
        setError(
          "Copy failed. Select and copy the key ID manually.",
        );
      }
    }
  }

  async function act(
    action: "rotate" | "revoke",
  ) {
    if (
      disabled ||
      item.revoked_at ||
      actionLock.current
    ) {
      return;
    }

    const prompt = action === "rotate"
      ? `Rotate "${item.name}"? Its existing secret will stop working.`
      : `Revoke "${item.name}"? This key will stop working.`;

    if (!window.confirm(prompt)) return;

    actionLock.current = true;
    setWorking(true);
    setError(null);

    try {
      await (
        action === "rotate"
          ? onRotate(item)
          : onRevoke(item)
      );
    } catch (cause) {
      if (alive.current) {
        setError(
          cause instanceof Error
            ? cause.message
            : `Unable to ${action} API key.`,
        );
      }
    } finally {
      actionLock.current = false;

      if (alive.current) {
        setWorking(false);
      }
    }
  }

  return (
    <article
      aria-busy={disabled}
      style={{
        padding: 16,
        border: "1px solid var(--color-border, #ddd)",
        borderRadius: 10,
        display: "grid",
        gap: 12,
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          gap: 12,
          flexWrap: "wrap",
        }}
      >
        <div style={{ minWidth: 0 }}>
          <strong
            style={{
              overflowWrap: "anywhere",
            }}
          >
            {item.name}
          </strong>

          <div>
            <code>{item.key_prefix}</code>
          </div>
        </div>

        <span>{status}</span>
      </div>

      <dl
        style={{
          display: "grid",
          gridTemplateColumns:
            "repeat(auto-fit,minmax(160px,1fr))",
          gap: 12,
          margin: 0,
        }}
      >
        <div>
          <dt>Created</dt>
          <dd style={{ margin: 0 }}>
            {formatDate(item.created_at)}
          </dd>
        </div>

        <div>
          <dt>Last used</dt>
          <dd style={{ margin: 0 }}>
            {formatDate(item.last_used_at)}
          </dd>
        </div>

        <div>
          <dt>Expires</dt>
          <dd style={{ margin: 0 }}>
            {formatDate(item.expires_at)}
          </dd>
        </div>
      </dl>

      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          gap: 8,
        }}
      >
        {item.scopes.map((scope) => (
          <span
            key={scope}
            title={scope}
          >
            {formatAPIKeyScope(scope)}
          </span>
        ))}
      </div>

      <code
        style={{
          overflowWrap: "anywhere",
        }}
      >
        {item.id}
      </code>

      {error ? (
        <p role="alert">{error}</p>
      ) : null}

      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          gap: 8,
        }}
      >
        <Button
          type="button"
          variant="outline"
          disabled={disabled}
          onClick={() => void copyId()}
        >
          <Clipboard size={14} />

          {copied ? "Copied" : "Copy ID"}
        </Button>

        {!item.revoked_at ? (
          <>
            <Button
              type="button"
              variant="outline"
              disabled={disabled}
              onClick={() => void act("rotate")}
            >
              <RefreshCcw size={14} />
              Rotate
            </Button>

            <Button
              type="button"
              variant="outline"
              disabled={disabled}
              onClick={() => void act("revoke")}
            >
              <Trash2 size={14} />
              Revoke
            </Button>
          </>
        ) : null}
      </div>
    </article>
  );
}