"use client";

import { useEffect, useState } from "react";

type Props = {
  endpoint: string;
  token: string;
  deviceId: string;
};

/**
 * Localhost-only development viewer.
 * Production must use workspace-scoped ephemeral credentials.
 */
export default function NativeJpegStream({
  endpoint,
  token,
  deviceId,
}: Props) {
  const [viewToken, setViewToken] = useState("");
  const [draft, setDraft] = useState("");
  const [frame, setFrame] = useState("");
  const [status, setStatus] = useState(
    "Waiting for local viewer configuration"
  );

  useEffect(() => {
    const saved =
      window.sessionStorage.getItem("wfos_screen_view_token") ||
      token ||
      "";

    setViewToken(saved);
  }, [token]);

  useEffect(() => {
    if (!endpoint || !viewToken || !deviceId) {
      setFrame("");

      setStatus(
        !endpoint
          ? "Relay URL not configured: run Configure-Viewer.ps1 and restart frontend"
          : !deviceId
            ? "Select an employee and enrolled desktop device"
            : "Enter your local viewer token below"
      );

      return;
    }

    let active = true;
    let lastUrl = "";

    const base = endpoint
      .replace(/\/$/, "")
      .replace(/^http/, "ws");

    let ws: WebSocket;

    try {
      ws = new WebSocket(
        `${base}/ws/view/${encodeURIComponent(
          deviceId
        )}?token=${encodeURIComponent(viewToken)}`
      );
    } catch {
      setStatus("Invalid relay URL");
      return;
    }

    ws.binaryType = "blob";

    ws.onopen = () => {
      if (active) {
        setStatus("Connected — waiting for employee sharing");
      }
    };

    ws.onmessage = (event) => {
      if (!active) {
        return;
      }

      if (event.data === "stopped") {
        setStatus("Sharing stopped");
        setFrame("");

        if (lastUrl) {
          URL.revokeObjectURL(lastUrl);
        }

        lastUrl = "";
        return;
      }

      if (!(event.data instanceof Blob)) {
        return;
      }

      const next = URL.createObjectURL(event.data);

      setFrame(next);

      if (lastUrl) {
        URL.revokeObjectURL(lastUrl);
      }

      lastUrl = next;

      setStatus("LIVE — employee sharing active");
    };

    ws.onerror = () => {
      if (active) {
        setStatus(
          "Relay connection failed — check relay, token and frontend configuration"
        );
      }
    };

    ws.onclose = () => {
      if (active) {
        setStatus(
          "Disconnected — verify local relay and viewer token"
        );
      }
    };

    return () => {
      active = false;

      ws.close();

      if (lastUrl) {
        URL.revokeObjectURL(lastUrl);
      }
    };
  }, [endpoint, viewToken, deviceId]);

  return (
    <section
      aria-label="Native employee live screen"
      style={{
        width: "100%",
        background: "#111",
        color: "white",
        padding: 12,
        textAlign: "center",
      }}
    >
      {/* Hidden intentionally. Live stream remains active. */}
      <div
        role="status"
        aria-hidden="true"
        style={{
          display: "none",
          marginBottom: 8,
        }}
      >
        {status}
      </div>

      {!viewToken && (
        <form
          onSubmit={(event) => {
            event.preventDefault();

            const value = draft.trim();

            if (!/^[a-fA-F0-9]{64}$/.test(value)) {
              setStatus(
                "Viewer token must be 64 hexadecimal characters"
              );
              return;
            }

            window.sessionStorage.setItem(
              "wfos_screen_view_token",
              value
            );

            setDraft("");
            setViewToken(value);
          }}
          style={{
            display: "flex",
            flexWrap: "wrap",
            gap: 8,
            alignItems: "center",
            justifyContent: "center",
            padding: 14,
          }}
        >
          <label htmlFor="wfos-view-token">
            Local development viewer token
          </label>

          <input
            id="wfos-view-token"
            type="password"
            autoComplete="off"
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            placeholder="Paste token from clipboard"
            style={{
              padding: 8,
              minWidth: 260,
              color: "#111",
            }}
          />

          <button
            type="submit"
            style={{
              color: "#111",
              background: "white",
              padding: 8,
              borderRadius: 4,
            }}
          >
            Connect viewer
          </button>
        </form>
      )}

      {viewToken && (
        <button
          type="button"
          onClick={() => {
            window.sessionStorage.removeItem(
              "wfos_screen_view_token"
            );

            setViewToken("");
            setFrame("");
          }}
          style={{
            padding: 5,
            background: "white",
            color: "#111",
            borderRadius: 4,
          }}
        >
          Clear local viewer token
        </button>
      )}

      {frame ? (
        <img
          src={frame}
          alt="Authorized employee desktop live frames"
          style={{
            width: "100%",
            height: "auto",
            maxHeight: "75vh",
            objectFit: "contain",
            display: "block",
            marginTop: 8,
          }}
        />
      ) : (
        <p>No live screen frame received</p>
      )}

      <small>
        Local development relay only. Production requires
        short-lived, workspace-scoped viewer authorization.
      </small>
    </section>
  );
}