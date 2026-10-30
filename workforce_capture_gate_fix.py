from pathlib import Path
import sys,shutil,datetime
root=Path(sys.argv[1] if len(sys.argv)>1 else r'C:\workforce-os')
rel=Path('apps/web/components/monitoring/monitoring-consent-gate.tsx')
target=root/rel
if not target.is_file(): raise SystemExit(f'FILE NOT FOUND: {target}')
backup=root/'backups'/('screen-capture-gate-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S'))/rel
backup.parent.mkdir(parents=True,exist_ok=True)
shutil.copy2(target,backup)
source=r'''"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { MonitorUp, ShieldCheck, Square } from "lucide-react";
import { api } from "@/lib/api/client";
import { useWorkspace } from "@/contexts/workspace-context";
import { monitoringService } from "@/services/monitoring.service";
import { hasAnyPermission } from "@/lib/workspace/access";

type ConsentState = { required: boolean; granted?: boolean; policy_version?: string };

/**
 * Browser capture manager. This does NOT publish media to remote viewers.
 * A separate authenticated signaling/WebRTC pipeline is required for video.
 * Browser permission requires a user gesture for each new capture session.
 */
export function MonitoringConsentGate() {
  const { workspaceId, user, permissions, navigationView } = useWorkspace();
  const eligible = hasAnyPermission(permissions, ["monitoring.live_screen"], navigationView);
  const [policy, setPolicy] = useState<ConsentState | null>(null);
  const [active, setActive] = useState(false);
  const [dismissed, setDismissed] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const streamRef = useRef<MediaStream | null>(null);
  const ownerRef = useRef<string | null>(null);
  const epochRef = useRef(0);

  const stop = useCallback(() => {
    epochRef.current += 1;
    const stream = streamRef.current;
    streamRef.current = null;
    ownerRef.current = null;
    stream?.getTracks().forEach((track) => track.stop());
    setActive(false);
  }, []);

  // Do not retain capture after logout, user change or workspace change.
  // A new workspace has its own consent and permissions.
  useEffect(() => {
    stop();
    setPolicy(null);
    setDismissed(false);
    setError("");
    if (!workspaceId || !user || !eligible) return;
    let cancelled = false;
    api.get<ConsentState>(`/workspaces/${workspaceId}/monitoring/consent`)
      .then((result) => { if (!cancelled) setPolicy(result); })
      .catch(() => { if (!cancelled) setError("Could not check monitoring policy. Sharing has not started."); });
    return () => { cancelled = true; };
  }, [workspaceId, user?.id, eligible, stop]);

  useEffect(() => () => {
    streamRef.current?.getTracks().forEach(track => track.stop());
    streamRef.current = null;
  }, []);

  const begin = async () => {
    if (!workspaceId || !eligible || busy || streamRef.current) return;
    if (!navigator.mediaDevices?.getDisplayMedia) {
      setError("This browser does not support screen capture.");
      return;
    }
    const epoch = ++epochRef.current;
    const requestedWorkspace = workspaceId;
    setBusy(true);
    setError("");
    let captured: MediaStream | null = null;
    try {
      // Requires user click. Chrome's Share confirmation cannot be automated.
      captured = await navigator.mediaDevices.getDisplayMedia({video: true, audio: false});
      if (epoch !== epochRef.current) { captured.getTracks().forEach(t => t.stop()); return; }
      if (!policy?.granted) await monitoringService.saveScreenConsent(requestedWorkspace, true);
      if (epoch !== epochRef.current) { captured.getTracks().forEach(t => t.stop()); return; }
      streamRef.current = captured;
      ownerRef.current = requestedWorkspace;
      captured.getVideoTracks()[0]?.addEventListener("ended", () => {
        if (streamRef.current === captured) stop();
      }, {once: true});
      setPolicy(current => current ? {...current, granted: true} : current);
      setActive(true);
      setDismissed(false);
    } catch (cause) {
      captured?.getTracks().forEach(t => t.stop());
      setError(cause instanceof Error ? cause.message : "Screen sharing was not started.");
    } finally { setBusy(false); }
  };

  if (!workspaceId || !user || !eligible || !policy || !policy.required) return null;
  if (active) return (
    <div role="status" className="capture-chip">
      <MonitorUp size={17}/><span>Screen capture active (local only — remote video not connected)</span>
      <button type="button" onClick={stop}><Square size={14}/> Stop sharing</button>
      <style jsx>{`.capture-chip{position:fixed;bottom:18px;right:18px;z-index:120;display:flex;flex-wrap:wrap;gap:10px;align-items:center;max-width:min(95vw,680px);background:#142235;color:#fff;padding:12px 14px;border:1px solid #67b7a3;border-radius:12px;box-shadow:0 12px 40px #0005;font-size:12px}.capture-chip button{display:flex;gap:5px;align-items:center;background:#fff;border:0;border-radius:7px;padding:7px 10px;color:#192335;cursor:pointer}`}</style>
    </div>
  );
  if (dismissed) return (
    <div className="capture-chip"><MonitorUp size={16}/> Screen sharing off
      <button type="button" onClick={() => setDismissed(false)}>Start sharing</button>
      <style jsx>{`.capture-chip{position:fixed;bottom:18px;right:18px;z-index:120;display:flex;gap:10px;align-items:center;background:#142235;color:white;padding:12px;border-radius:10px;font-size:13px}.capture-chip button{padding:7px 10px;border:0;border-radius:7px;cursor:pointer}`}</style>
    </div>
  );
  return (
    <div className="capture-backdrop" role="dialog" aria-modal="true" aria-labelledby="capture-heading">
      <div className="capture-card">
        <MonitorUp size={30}/><h2 id="capture-heading">Start workspace screen sharing?</h2>
        <p>Your workspace permits screen sharing. Choose the screen to share using Chrome's Share prompt. You can stop sharing at any time.</p>
        <p className="capture-note"><ShieldCheck size={16}/> Your workspace policy acknowledgment is saved; Chrome still requires a new sharing choice for each fresh capture.</p>
        {error && <p role="alert" className="capture-error">{error}</p>}
        <div className="capture-actions">
          <button type="button" onClick={() => setDismissed(true)}>Not now</button>
          <button type="button" className="primary" disabled={busy} onClick={() => void begin()}>{busy ? "Opening Chrome permission…" : "Start screen sharing"}</button>
        </div>
      </div>
      <style jsx>{`.capture-backdrop{position:fixed;inset:0;z-index:110;display:grid;place-items:center;padding:20px;background:#0e1729a8}.capture-card{width:min(100%,510px);padding:28px;background:#fffdfa;border-radius:17px;color:#152238;box-shadow:0 25px 80px #0005}.capture-card h2{font-size:23px;margin:17px 0 9px}.capture-card p{color:#5f6c7e;line-height:1.6}.capture-note{display:flex;gap:8px;font-size:13px}.capture-actions{display:flex;justify-content:flex-end;gap:10px;margin-top:20px}.capture-actions button{padding:10px 14px;border-radius:9px;background:#fff;border:1px solid #d8dee8;cursor:pointer}.capture-actions .primary{background:#172534;color:#fff}.capture-actions button:disabled{opacity:.6;cursor:not-allowed}.capture-error{color:#b42318!important}`}</style>
    </div>
  );
}
'''
target.write_text(source, encoding='utf-8')
print('PATCHED', target)
print('BACKUP',backup)
print('NOTE: Browser capture only. WebRTC media transport NOT installed.')
