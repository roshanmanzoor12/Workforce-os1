
"use client";

import { useCallback, useEffect, useState } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  Loader2,
  MonitorPlay,
  RefreshCw,
  ShieldCheck,
  Square,
} from "lucide-react";

import { api } from "@/lib/api/client";
import { useWorkspace } from "@/contexts/workspace-context";

type ReadinessDevice = {
  device_id: string;
  employee_id: string;
  device_name: string;
  is_online: boolean;
  monitoring_ready: boolean;
  live_ready: boolean;
  consent_granted: boolean;
  setup_reasons: string[];
};

type ReadinessResponse = {
  devices: ReadinessDevice[];
};

type LiveSession = {
  id: string;
  device_id: string;
  employee_id: string;
  status: string;
  transport: string;
  session_channel: string | null;
  consent_required: boolean;
  visible_indicator_required: boolean;
};

interface Props {
  // Must be a genuine desktop-agent UUID, not a
  // general devices table ID.
  deviceId: string | null;
  employeeId: string | null;
  disabled?: boolean;
  onRequested?: (session: LiveSession) => void;
  onEnded?: () => void;
}

export function LiveScreenRequestButton({
  deviceId,
  employeeId,
  disabled = false,
  onRequested,
  onEnded,
}: Props) {
  const { workspaceId } = useWorkspace();

  const [device, setDevice] =
    useState<ReadinessDevice | null>(null);

  const [session, setSession] =
    useState<LiveSession | null>(null);

  const [checking, setChecking] = useState(false);
  const [busy, setBusy] = useState(false);
  const [checked, setChecked] = useState(false);
  const [error, setError] = useState("");

  const verify = useCallback(async () => {
    setDevice(null);
    setChecked(false);
    setError("");

    if (!workspaceId || !deviceId || !employeeId) {
      setChecked(true);
      return;
    }

    setChecking(true);

    try {
      const result = await api.get<ReadinessResponse>(
        `/workspaces/${workspaceId}/devices/readiness`
      );

      const match = (result.devices || []).find(
        (item) =>
          item.device_id === deviceId &&
          item.employee_id === employeeId
      );

      if (!match) {
        setError(
          "This computer is assigned in the general device " +
          "inventory but has no matching authorized desktop-agent " +
          "readiness record. Complete desktop-agent enrollment."
        );
        return;
      }

      setDevice(match);

      if (!match.is_online) {
        setError("Desktop monitoring agent is offline.");
      } else if (!match.consent_granted) {
        setError(
          "Employee monitoring consent has not been granted."
        );
      } else if (!match.live_ready) {
        setError(
          match.setup_reasons?.join("; ") ||
          "Desktop agent is not ready for live screen."
        );
      }
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Could not verify desktop-agent readiness."
      );
    } finally {
      setChecking(false);
      setChecked(true);
    }
  }, [workspaceId, deviceId, employeeId]);

  useEffect(() => {
    setSession(null);
    void verify();
  }, [verify]);

  const ready =
    checked &&
    device !== null &&
    device.is_online &&
    device.consent_granted &&
    device.live_ready;

  async function request() {
    if (
      !workspaceId ||
      !device ||
      !ready ||
      busy ||
      session
    ) {
      return;
    }

    setBusy(true);
    setError("");

    try {
      // Backend creates a request. This does not start
      // capture or bypass employee session approval.
      const result = await api.post<LiveSession>(
        `/workspaces/${workspaceId}/live-monitoring/live-sessions`,
        {
          device_id: device.device_id,
          reason: "Authorized live-screen request",
        }
      );

      setSession(result);
      onRequested?.(result);
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Live-screen request failed."
      );
    } finally {
      setBusy(false);
    }
  }

  async function endSession() {
    if (!workspaceId || !session || busy) return;

    setBusy(true);
    setError("");

    try {
      await api.post(
        `/workspaces/${workspaceId}/live-monitoring/live-sessions/${session.id}/end`,
        {
          reason: "Stopped by workspace viewer",
        }
      );

      setSession(null);
      onEnded?.();
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Could not end live-screen session."
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="lsr-container">
      {session ? (
        <div className="lsr-session">
          <span className="lsr-session-status">
            <ShieldCheck size={15} />
            Session: {session.status}
          </span>

          <button
            type="button"
            className="lsr-stop"
            disabled={busy}
            onClick={() => void endSession()}
          >
            {busy ? (
              <Loader2 size={15} className="lsr-spin" />
            ) : (
              <Square size={14} />
            )}
            End session
          </button>
        </div>
      ) : (
        <button
          type="button"
          className="lsr-request"
          disabled={
            disabled ||
            checking ||
            busy ||
            !ready
          }
          onClick={() => void request()}
        >
          {checking || busy ? (
            <Loader2 size={15} className="lsr-spin" />
          ) : (
            <MonitorPlay size={16} />
          )}
          {checking
            ? "Checking agent..."
            : busy
              ? "Requesting..."
              : "Request session"}
        </button>
      )}

      {ready && !session && (
        <div className="lsr-ready">
          <CheckCircle2 size={15} />
          Desktop agent verified and live-ready
        </div>
      )}

      {error && (
        <div className="lsr-error" role="alert">
          <AlertTriangle size={16} />
          <span>{error}</span>
          <button
            type="button"
            disabled={checking}
            onClick={() => void verify()}
          >
            <RefreshCw size={14} />
            Retry
          </button>
        </div>
      )}

      {session && (
        <p className="lsr-note">
          Request submitted. Video will not start until
          the employee approves the session and a
          supported media transport connects.
        </p>
      )}

      <style jsx>{`
        .lsr-container {
          display: grid;
          gap: 9px;
          min-width: 0;
        }

        .lsr-request,
        .lsr-stop {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
          min-height: 39px;
          padding: 0 13px;
          border-radius: 7px;
          font-size: 12px;
          font-weight: 700;
          cursor: pointer;
        }

        .lsr-request {
          border: 1px solid #192531;
          background: #192531;
          color: white;
        }

        .lsr-request:disabled,
        .lsr-stop:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .lsr-session {
          display: flex;
          align-items: center;
          gap: 9px;
          flex-wrap: wrap;
        }

        .lsr-session-status,
        .lsr-ready {
          display: flex;
          align-items: center;
          gap: 7px;
          color: #18814a;
          font-size: 11px;
        }

        .lsr-stop {
          border: 1px solid #e3c9c9;
          background: #fff0f0;
          color: #a52d2d;
        }

        .lsr-error {
          display: flex;
          align-items: flex-start;
          flex-wrap: wrap;
          gap: 8px;
          padding: 11px;
          border-radius: 8px;
          border: 1px solid #eed5a1;
          background: #fff7e6;
          color: #906400;
          font-size: 12px;
          line-height: 1.5;
        }

        .lsr-error > span {
          flex: 1;
          min-width: 160px;
        }

        .lsr-error button {
          display: inline-flex;
          gap: 5px;
          align-items: center;
          border: 0;
          background: transparent;
          color: inherit;
          text-decoration: underline;
          cursor: pointer;
        }

        .lsr-note {
          margin: 0;
          color: #6b7890;
          font-size: 11px;
          line-height: 1.5;
        }

        .lsr-spin {
          animation: lsr-spin 1s linear infinite;
        }

        @keyframes lsr-spin {
          to {
            transform: rotate(360deg);
          }
        }
      `}</style>
    </div>
  );
}
