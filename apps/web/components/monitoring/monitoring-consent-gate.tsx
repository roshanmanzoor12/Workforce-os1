
"use client";
import { SavedScreenSharingSetting } from "@/components/monitoring/saved-screen-sharing-setting";


import { useCallback, useEffect, useState } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  Loader2,
  MonitorUp,
  Settings2,
  ShieldCheck,
  X,
} from "lucide-react";

import { api } from "@/lib/api/client";
import { useWorkspace } from "@/contexts/workspace-context";
import { monitoringService } from "@/services/monitoring.service";

type ConsentState = {
  required: boolean;
  granted: boolean;
  policy_version: string;
};

export function MonitoringConsentGate() {
  const {
    workspaceId,
    user,
    permissions,
    navigationView,
    loading: workspaceLoading,
  } = useWorkspace();

  const eligible =
    navigationView !== "client" &&
    (
      permissions.includes("monitoring.self.read") ||
      permissions.includes("monitoring.team.read") ||
      permissions.includes("monitoring.all.read")
    );

  const [consent, setConsent] =
    useState<ConsentState | null>(null);

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const [dialogOpen, setDialogOpen] = useState(false);
  const [dismissed, setDismissed] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);

  const loadConsent = useCallback(async () => {
    if (!workspaceId || !user || !eligible) {
      setConsent(null);
      setLoading(false);
      return;
    }

    setLoading(true);
    setError("");

    try {
      const result = await api.get<ConsentState>(
        `/workspaces/${workspaceId}/monitoring/consent`
      );

      setConsent(result);
      setDialogOpen(!result.granted && !dismissed);
    } catch (cause) {
      setConsent(null);
      setDialogOpen(false);
      setError(
        cause instanceof Error
          ? cause.message
          : "Unable to load monitoring permission."
      );
    } finally {
      setLoading(false);
    }
  }, [workspaceId, user?.id, eligible, dismissed]);

  useEffect(() => {
    setDismissed(false);
    setSettingsOpen(false);
    setConsent(null);
  }, [workspaceId, user?.id]);

  useEffect(() => {
    if (!workspaceLoading) {
      void loadConsent();
    }
  }, [workspaceLoading, loadConsent]);

  async function save(granted: boolean) {
    if (!workspaceId || saving) return;

    setSaving(true);
    setError("");

    try {
      await monitoringService.saveScreenConsent(
        workspaceId,
        granted
      );

      setConsent((current) => ({
        required: !granted,
        granted,
        policy_version: current?.policy_version || "v1",
      }));

      setDialogOpen(false);
      setSettingsOpen(false);
      setDismissed(false);
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Unable to save your monitoring preference."
      );
    } finally {
      setSaving(false);
    }
  }

  if (
    workspaceLoading ||
    loading ||
    !workspaceId ||
    !user ||
    !eligible
  ) {
    return null;
  }

  return (
    <>
      {consent && (
        <button
          type="button"
          className="mc-settings-trigger"
          aria-label="Monitoring permission settings"
          title="Monitoring permission settings"
          onClick={() => {
            setSettingsOpen(true);
            setDialogOpen(false);
            setError("");
          }}
        >
          <ShieldCheck size={17} />
          <span>
            Monitoring: {consent.granted ? "Allowed" : "Off"}
          </span>
          <Settings2 size={15} />
        </button>
      )}

      {(dialogOpen || settingsOpen) && (
        <div className="mc-overlay">
          <section
            className="mc-card"
            role="dialog"
            aria-modal="true"
            aria-labelledby="mc-title"
          >
            <header className="mc-header">
              <div className="mc-icon">
                <MonitorUp size={25} />
              </div>

              <button
                type="button"
                className="mc-close"
                aria-label="Close"
                onClick={() => {
                  setDialogOpen(false);
                  setSettingsOpen(false);
                  setDismissed(true);
                }}
              >
                <X size={19} />
              </button>
            </header>

            <h2 id="mc-title">
              {settingsOpen
                ? "Employee monitoring settings"
                : "Monitoring & Screen Sharing Permission"}
            </h2>

            <p className="mc-intro">
              Choose whether WorkforceOS may use your
              approved device for workplace monitoring.
              This preference is remembered for your
              workspace account until you change it.
            </p>

            <div className="mc-setting">
              <div className="mc-setting-icon">
                <ShieldCheck size={19} />
              </div>

              <div className="mc-setting-content">
                <strong>Monitoring disclosure</strong>
                <small>
                  Your decision is saved to the workspace
                  consent record.
                </small>
              </div>

              <span
                className={
                  consent?.granted
                    ? "mc-state mc-state-on"
                    : "mc-state mc-state-off"
                }
              >
                {consent?.granted ? "Accepted" : "Not accepted"}
              </span>
            </div>

            <div className="mc-setting">
              <div className="mc-setting-icon">
                <MonitorUp size={19} />
              </div>

              <div className="mc-setting-content">
                <strong>Allow live-screen requests</strong>
                <small>
                  Remember this preference for future
                  sessions. You will still be shown when
                  an actual screen-sharing session starts.
                </small>
              </div>

              <button
                type="button"
                className={
                  consent?.granted
                    ? "mc-toggle mc-toggle-on"
                    : "mc-toggle"
                }
                role="switch"
                aria-checked={Boolean(consent?.granted)}
                aria-label="Allow live-screen requests"
                disabled={saving}
                onClick={() =>
                  void save(!Boolean(consent?.granted))
                }
              >
                <span />
              </button>
            </div>
                    {/* V17_SAVED_APPROVAL_IN_MODAL */}
                    <SavedScreenSharingSetting />

            <div className="mc-notice">
              <ShieldCheck size={18} />
              <p>
                Enabling this setting does not silently
                capture your screen. A real live-screen
                session must be authorized, visibly
                indicated, and stoppable by you.
              </p>
            </div>

            {error && (
              <div className="mc-error" role="alert">
                <AlertTriangle size={17} />
                {error}
              </div>
            )}

            <footer className="mc-actions">
              <button
                type="button"
                className="mc-secondary"
                disabled={saving}
                onClick={() => {
                  setDialogOpen(false);
                  setSettingsOpen(false);
                  setDismissed(true);
                }}
              >
                {settingsOpen ? "Close" : "Not now"}
              </button>

              {!consent?.granted && (
                <button
                  type="button"
                  className="mc-primary"
                  disabled={saving}
                  onClick={() => void save(true)}
                >
                  {saving ? (
                    <Loader2 size={17} className="mc-spin" />
                  ) : (
                    <CheckCircle2 size={17} />
                  )}
                  Allow & remember
                </button>
              )}

              {consent?.granted && (
                <button
                  type="button"
                  className="mc-primary"
                  disabled={saving}
                  onClick={() => {
                    setDialogOpen(false);
                    setSettingsOpen(false);
                  }}
                >
                  <CheckCircle2 size={17} />
                  Done
                </button>
              )}
            </footer>
          </section>
        </div>
      )}

      <style jsx global>{`
        .mc-settings-trigger {
          position: fixed;
          right: 22px;
          bottom: 22px;
          z-index: 80;
          display: inline-flex;
          align-items: center;
          gap: 9px;
          border: 1px solid #dcdedc;
          background: #fffdf8;
          color: #1b293c;
          padding: 10px 13px;
          border-radius: 999px;
          box-shadow: 0 8px 26px #14223818;
          font-size: 12px;
          font-weight: 650;
          cursor: pointer;
        }

        .mc-overlay {
          position: fixed;
          inset: 0;
          z-index: 500;
          display: grid;
          place-items: center;
          padding: 20px;
          background: #1119289c;
        }

        .mc-card {
          box-sizing: border-box;
          width: min(540px, 100%);
          max-height: 90vh;
          overflow-y: auto;
          border: 1px solid #ece5da;
          border-radius: 17px;
          background: #fffdf9;
          padding: 26px;
          color: #17253c;
          box-shadow: 0 28px 75px #0004;
        }

        .mc-card * {
          box-sizing: border-box;
        }

        .mc-header {
          display: flex;
          align-items: flex-start;
          justify-content: space-between;
        }

        .mc-icon {
          width: 52px;
          height: 52px;
          display: grid;
          place-items: center;
          border-radius: 14px;
          background: #fff0c7;
          color: #a36e00;
        }

        .mc-close {
          border: 1px solid #e5e2dc;
          border-radius: 8px;
          background: white;
          padding: 7px;
          cursor: pointer;
        }

        .mc-card h2 {
          font-size: 23px;
          line-height: 1.25;
          letter-spacing: -.5px;
          margin: 19px 0 8px;
        }

        .mc-intro {
          font-size: 13px;
          line-height: 1.65;
          color: #6e7b8e;
          margin: 0 0 22px;
        }

        .mc-setting {
          display: flex;
          align-items: center;
          gap: 13px;
          padding: 17px 0;
          border-top: 1px solid #eeeae3;
        }

        .mc-setting-icon {
          color: #9b710b;
          flex-shrink: 0;
        }

        .mc-setting-content {
          display: flex;
          flex: 1;
          flex-direction: column;
          gap: 6px;
          min-width: 0;
        }

        .mc-setting-content strong {
          font-size: 13px;
        }

        .mc-setting-content small {
          color: #758198;
          font-size: 11px;
          line-height: 1.55;
        }

        .mc-state {
          font-size: 11px;
          white-space: nowrap;
          border-radius: 30px;
          padding: 7px 10px;
        }

        .mc-state-on {
          background: #e3f7e9;
          color: #218450;
        }

        .mc-state-off {
          background: #f2f1ee;
          color: #788392;
        }

        .mc-toggle {
          width: 44px;
          height: 26px;
          flex-shrink: 0;
          border: 0;
          border-radius: 30px;
          background: #c4cbd4;
          padding: 3px;
          cursor: pointer;
          transition: background .2s;
        }

        .mc-toggle span {
          display: block;
          width: 20px;
          height: 20px;
          background: white;
          border-radius: 50%;
          box-shadow: 0 1px 3px #0002;
          transition: transform .2s;
        }

        .mc-toggle-on {
          background: #21a366;
        }

        .mc-toggle-on span {
          transform: translateX(18px);
        }

        .mc-notice {
          display: flex;
          align-items: flex-start;
          gap: 10px;
          margin-top: 12px;
          padding: 14px;
          background: #eff6ff;
          border: 1px solid #d7e7fa;
          border-radius: 9px;
          color: #456482;
          font-size: 12px;
        }

        .mc-notice svg {
          flex-shrink: 0;
        }

        .mc-notice p {
          line-height: 1.6;
          margin: 0;
        }

        .mc-error {
          display: flex;
          align-items: flex-start;
          gap: 8px;
          padding: 12px;
          margin-top: 14px;
          color: #b12f32;
          background: #fff0f0;
          border-radius: 8px;
          font-size: 12px;
        }

        .mc-actions {
          display: flex;
          justify-content: flex-end;
          gap: 10px;
          margin-top: 23px;
        }

        .mc-actions button {
          border-radius: 8px;
          min-height: 41px;
          padding: 0 15px;
          display: inline-flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
          font-size: 12px;
          font-weight: 700;
          cursor: pointer;
        }

        .mc-secondary {
          border: 1px solid #e2e4e7;
          background: white;
          color: #263246;
        }

        .mc-primary {
          border: 1px solid #1d2834;
          background: #1d2834;
          color: white;
        }

        .mc-spin {
          animation: mc-spin 1s linear infinite;
        }

        @keyframes mc-spin {
          to { transform: rotate(360deg); }
        }

        @media (max-width: 500px) {
          .mc-card {
            padding: 20px;
          }

          .mc-settings-trigger {
            right: 12px;
            bottom: 12px;
          }
        }
      `}</style>
    </>
  );
}
