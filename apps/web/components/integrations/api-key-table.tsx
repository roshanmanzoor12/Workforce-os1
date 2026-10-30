"use client";

import {
  Copy,
  KeyRound,
  RefreshCcw,
  ShieldOff,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { ApiKeyStatus } from "@/components/integrations/api-key-status";

import type { APIKeyPublic } from "@/types/api-keys";

function formatDate(
  value: string | null,
): string {
  if (!value) {
    return "Never";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString();
}

function copyText(
  value: string,
) {
  void navigator.clipboard?.writeText(
    value,
  );
}

export function ApiKeyTable({
  apiKeys,
  busyKeyId,
  onRevoke,
  onRotate,
  onReveal,
}: {
  apiKeys: APIKeyPublic[];
  busyKeyId: string | null;
  onRevoke: (
    apiKey: APIKeyPublic,
  ) => void;
  onRotate: (
    apiKey: APIKeyPublic,
  ) => void;
  onReveal: (
    apiKey: APIKeyPublic,
  ) => void;
}) {
  if (apiKeys.length === 0) {
    return (
      <div className="empty-state">
        <KeyRound size={25} />

        <strong>
          No API keys
        </strong>

        <span>
          Create an API key when an external system needs authorized WorkforceOS access.
        </span>
      </div>
    );
  }

  return (
    <div className="table-container">
      <table className="data-table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Key</th>
            <th>Scopes</th>
            <th>Last Used</th>
            <th>Expires</th>
            <th>Status</th>
            <th />
          </tr>
        </thead>

        <tbody>
          {apiKeys.map((apiKey) => {
            const revoked =
              Boolean(
                apiKey.revoked_at,
              );

            return (
              <tr
                key={apiKey.id}
              >
                <td>
                  <strong>
                    {apiKey.name}
                  </strong>
                </td>

                <td>
                  <code>
                    {apiKey.key_prefix}
                    {"••••••••"}
                  </code>
                </td>

                <td>
                  <div
                    style={{
                      display: "flex",
                      flexWrap:
                        "wrap",
                      gap: 4,
                    }}
                  >
                    {apiKey.scopes.map(
                      (scope) => (
                        <span
                          key={
                            scope
                          }
                          className="text-label"
                          style={{
                            padding:
                              "3px 6px",
                            border:
                              "1px solid var(--color-border)",
                            borderRadius:
                              5,
                          }}
                        >
                          {scope}
                        </span>
                      ),
                    )}
                  </div>
                </td>

                <td>
                  {formatDate(
                    apiKey.last_used_at,
                  )}
                </td>

                <td>
                  {formatDate(
                    apiKey.expires_at,
                  )}
                </td>

                <td>
                  <ApiKeyStatus
                    apiKey={apiKey}
                  />
                </td>

                <td>
                  <div
                    style={{
                      display:
                        "flex",
                      gap: 5,
                      justifyContent:
                        "flex-end",
                    }}
                  >
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() =>
                        copyText(
                          apiKey.key_prefix,
                        )
                      }
                      title="Copy key prefix"
                    >
                      <Copy
                        size={13}
                      />
                    </Button>

                    {!revoked ? (
                      <>
                        <Button
                          variant="outline"
                          size="sm"
                          disabled={
                            busyKeyId ===
                            apiKey.id
                          }
                          onClick={() =>
                            onReveal(
                              apiKey,
                            )
                          }
                        >
                          View
                        </Button>

                        <Button
                          variant="outline"
                          size="sm"
                          disabled={
                            busyKeyId ===
                            apiKey.id
                          }
                          onClick={() =>
                            onRotate(
                              apiKey,
                            )
                          }
                        >
                          <RefreshCcw
                            size={13}
                          />
                          Rotate
                        </Button>

                        <Button
                          variant="ghost"
                          size="sm"
                          disabled={
                            busyKeyId ===
                            apiKey.id
                          }
                          onClick={() =>
                            onRevoke(
                              apiKey,
                            )
                          }
                        >
                          <ShieldOff
                            size={13}
                          />
                        </Button>
                      </>
                    ) : null}
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}