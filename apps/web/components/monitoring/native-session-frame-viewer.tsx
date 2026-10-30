"use client";

import { useEffect, useRef, useState } from "react";
import { api } from "@/lib/api/client";

type FrameResponse = { status: string; sequence: number; jpeg_base64: string | null };
type Props = { workspaceId: string; sessionId: string; paused?: boolean };

/** Authenticated workspace-scoped native-frame viewer. Never displays unverified "LIVE". */
export default function NativeSessionFrameViewer({ workspaceId, sessionId, paused = false }: Props) {
  const [frame, setFrame] = useState<string | null>(null);
  const [state, setState] = useState("Waiting for native desktop frames…");
  const sequence = useRef(0);

  useEffect(() => {
    let stopped = false;
    let busy = false;
    sequence.current = 0;
    setFrame(null);
    setState("Waiting for native desktop frames…");
    if (!workspaceId || !sessionId || paused) return;

    const poll = async () => {
      if (stopped || busy) return;
      busy = true;
      try {
        const result = await api.get<FrameResponse>(
          `/workspaces/${encodeURIComponent(workspaceId)}/live-monitoring/live-sessions/${encodeURIComponent(sessionId)}/native-frame?after=${sequence.current}`,
        );
        if (stopped) return;
        if (result.status !== "active") {
          setFrame(null);
          setState("Native session is no longer active.");
          return;
        }
        if (typeof result.jpeg_base64 === "string" && result.jpeg_base64.length > 0 && result.sequence > sequence.current) {
          sequence.current = result.sequence;
          setFrame(`data:image/jpeg;base64,${result.jpeg_base64}`);
          setState("Receiving native desktop frames");
        }
      } catch (error) {
        if (!stopped) {
          setFrame(null);
          setState(error instanceof Error ? `Native frame unavailable: ${error.message}` : "Native frame unavailable");
        }
      } finally { busy = false; }
    };
    void poll();
    const handle = window.setInterval(() => void poll(), 900);
    return () => { stopped = true; window.clearInterval(handle); };
  }, [workspaceId, sessionId, paused]);

  return (
    <div style={{ width: "100%", height: "100%", minHeight: 390, background: "#090b10", position: "relative", display: "grid", placeItems: "center" }}>
      {frame ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={frame} alt="Employee-authorized native desktop stream" style={{ maxWidth: "100%", maxHeight: "75vh", objectFit: "contain" }} />
      ) : <p role="status" style={{ padding: 20, textAlign: "center", color: "#cbd5e1" }}>{paused ? "Viewer paused" : state}</p>}
      {frame && <span aria-live="polite" style={{ position: "absolute", bottom: 10, left: 12, padding: "4px 9px", borderRadius: 5, background: "#101827cc", color: "white", fontSize: 11 }}>{state}</span>}
    </div>
  );
}
