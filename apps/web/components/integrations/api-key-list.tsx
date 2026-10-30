"use client";

import {
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";

import {
  KeyRound,
  Plus,
  RefreshCcw,
} from "lucide-react";

import {
  APIKeyCreateDialog,
} from "@/components/integrations/api-key-create-dialog";

import {
  APIKeyRow,
} from "@/components/integrations/api-key-row";

import {
  APIKeySecretDialog,
} from "@/components/integrations/api-key-secret-dialog";

import {
  apiKeysService,
} from "@/services/api-keys.service";

import type {
  APIKeyCreateRequest,
  APIKeyPublic,
} from "@/types/api-keys";

type IssuedKey = Awaited<
  ReturnType<typeof apiKeysService.create>
>;

interface APIKeyListProps {
  workspaceId: string;
  canManage: boolean;
}

export function APIKeyList(props: APIKeyListProps) {
  if (!props.canManage) {
    return (
      <section className="panel">
        <div className="panel-body">
          <h2>API key management unavailable</h2>

          <p>
            Your workspace role does not allow you
            to manage API keys.
          </p>
        </div>
      </section>
    );
  }

  if (!props.workspaceId) {
    return (
      <p>
        Select a workspace to manage API keys.
      </p>
    );
  }

  return (
    <WorkspaceAPIKeys
      key={props.workspaceId}
      workspaceId={props.workspaceId}
    />
  );
}

function WorkspaceAPIKeys({
  workspaceId,
}: {
  workspaceId: string;
}) {
  const [items, setItems] =
    useState<APIKeyPublic[]>([]);

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [saving, setSaving] = useState(false);

  const [busyKeyId, setBusyKeyId] =
    useState<string | null>(null);

  const [error, setError] =
    useState<string | null>(null);

  const [createError, setCreateError] =
    useState<string | null>(null);

  const [createOpen, setCreateOpen] =
    useState(false);

  const [issuedKey, setIssuedKey] =
    useState<IssuedKey | null>(null);

  const alive = useRef(false);
  const sequence = useRef(0);
  const mutationLock = useRef(false);

  const load = useCallback(
    async (initial = false) => {
      const request = ++sequence.current;

      if (initial) {
        setLoading(true);
      } else {
        setRefreshing(true);
      }

      setError(null);

      try {
        const response = await apiKeysService.list(
          workspaceId,
        );

        if (
          alive.current &&
          request === sequence.current
        ) {
          setItems(response);
        }
      } catch (cause) {
        if (
          alive.current &&
          request === sequence.current
        ) {
          setError(
            cause instanceof Error
              ? cause.message
              : "Unable to load API keys. Try refreshing.",
          );
        }
      } finally {
        if (
          alive.current &&
          request === sequence.current
        ) {
          setLoading(false);
          setRefreshing(false);
        }
      }
    },
    [workspaceId],
  );

  useEffect(() => {
    alive.current = true;

    void load(true);

    return () => {
      alive.current = false;
      ++sequence.current;
    };
  }, [load]);

  async function createKey(
    payload: APIKeyCreateRequest,
  ) {
    if (mutationLock.current) return;

    mutationLock.current = true;
    ++sequence.current;

    setRefreshing(false);
    setSaving(true);
    setCreateError(null);

    try {
      const issued = await apiKeysService.create(
        workspaceId,
        payload,
      );

      if (!alive.current) return;

      setItems((current) => [
        issued.key,
        ...current.filter(
          (item) => item.id !== issued.key.id,
        ),
      ]);

      setCreateOpen(false);
      setIssuedKey(issued);

      await load();
    } catch (cause) {
      if (alive.current) {
        setCreateError(
          cause instanceof Error
            ? cause.message
            : "Unable to create API key.",
        );
      }

      throw cause;
    } finally {
      mutationLock.current = false;

      if (alive.current) {
        setSaving(false);
      }
    }
  }

  async function changeKey(
    item: APIKeyPublic,
    action: "rotate" | "revoke",
  ) {
    if (mutationLock.current) return;

    mutationLock.current = true;
    ++sequence.current;

    setRefreshing(false);
    setBusyKeyId(item.id);
    setError(null);

    try {
      if (action === "rotate") {
        const issued = await apiKeysService.rotate(
          workspaceId,
          item.id,
        );

        if (!alive.current) return;

        setIssuedKey(issued);

        setItems((current) => [
          issued.key,
          ...current.filter(
            (key) =>
              key.id !== item.id &&
              key.id !== issued.key.id,
          ),
        ]);
      } else {
        const revoked = await apiKeysService.revoke(
          workspaceId,
          item.id,
        );

        if (!alive.current) return;

        setItems((current) =>
          current.map((key) =>
            key.id === item.id ? revoked : key,
          ),
        );
      }

      await load();
    } catch (cause) {
      if (alive.current) {
        setError(
          cause instanceof Error
            ? cause.message
            : `Unable to ${action} API key.`,
        );
      }
    } finally {
      mutationLock.current = false;

      if (alive.current) {
        setBusyKeyId(null);
      }
    }
  }

  const busy = saving || busyKeyId !== null;

  return (
    <>
      <section className="panel">
        <div
          className="panel-body"
          style={{
            display: "grid",
            gap: 18,
          }}
        >
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              gap: 16,
              flexWrap: "wrap",
            }}
          >
            <div>
              <h2>
                <KeyRound size={17} /> API Keys
              </h2>

              <p className="text-label">
                Manage workspace credentials and
                their access scopes.
              </p>
            </div>

            <div
              style={{
                display: "flex",
                gap: 8,
                flexWrap: "wrap",
              }}
            >
              <button
                type="button"
                disabled={
                  loading || refreshing || busy
                }
                onClick={() => void load()}
              >
                <RefreshCcw size={14} />

                {refreshing
                  ? "Refreshing…"
                  : "Refresh"}
              </button>

              <button
                type="button"
                disabled={
                  loading ||
                  busy ||
                  issuedKey !== null
                }
                onClick={() => {
                  setCreateError(null);
                  setCreateOpen(true);
                }}
              >
                <Plus size={15} />
                Create API Key
              </button>
            </div>
          </div>

          {error ? (
            <p role="alert">{error}</p>
          ) : null}

          {loading ? (
            <p role="status">Loading API keys…</p>
          ) : items.length === 0 ? (
            <p>
              {error
                ? "API keys could not be loaded. Use Refresh to try again."
                : "No API keys yet. Create a scoped key to connect an external service."}
            </p>
          ) : (
            <div
              style={{
                display: "grid",
                gap: 10,
              }}
            >
              {items.map((item) => (
                <APIKeyRow
                  key={item.id}
                  item={item}
                  busy={
                    busy || issuedKey !== null
                  }
                  onRotate={(key) =>
                    changeKey(key, "rotate")
                  }
                  onRevoke={(key) =>
                    changeKey(key, "revoke")
                  }
                />
              ))}
            </div>
          )}
        </div>
      </section>

      <APIKeyCreateDialog
        open={createOpen}
        saving={saving}
        error={createError}
        onClose={() => {
          if (!mutationLock.current) {
            setCreateOpen(false);
          }
        }}
        onSubmit={createKey}
      />

      <APIKeySecretDialog
        open={issuedKey !== null}
        keyData={issuedKey?.key ?? null}
        secret={issuedKey?.secret ?? null}
        onClose={() => setIssuedKey(null)}
      />
    </>
  );
}