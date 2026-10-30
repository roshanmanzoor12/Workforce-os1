"use client";
import { useEffect, useState } from "react";

/** Development relay viewer, no iframe and no browser screen-sharing permission. */
export default function NativeJpegStream({ endpoint, token, deviceId }: { endpoint: string; token: string; deviceId: string }) {
  const [frame, setFrame] = useState("");
  const [status, setStatus] = useState("Disconnected");
  useEffect(() => {
    if (!endpoint || !token || !deviceId) return;
    let active = true;
    let lastUrl = "";
    const base = endpoint.replace(/\/$/, "").replace(/^http/, "ws");
    const ws = new WebSocket(`${base}/ws/view/${encodeURIComponent(deviceId)}?token=${encodeURIComponent(token)}`);
    ws.binaryType = "blob";
    ws.onopen = () => active && setStatus("Connected — awaiting authorized sender");
    ws.onmessage = (event) => {
      if (!active) return;
      if (event.data === "stopped") { setStatus("Sharing stopped"); setFrame(""); if (lastUrl) URL.revokeObjectURL(lastUrl); lastUrl = ""; return; }
      if (!(event.data instanceof Blob)) return;
      const url = URL.createObjectURL(event.data);
      setFrame(url);
      if (lastUrl) URL.revokeObjectURL(lastUrl);
      lastUrl = url;
      setStatus("LIVE — employee sharing active");
    };
    ws.onerror = () => active && setStatus("Connection error");
    ws.onclose = () => active && setStatus("Disconnected");
    return () => { active = false; ws.close(); if (lastUrl) URL.revokeObjectURL(lastUrl); };
  }, [endpoint, token, deviceId]);
  return <section style={{width:"100%", background:"#111", textAlign:"center", color:"white", padding:12}} aria-label="Native employee live screen">
    <div role="status">{status}</div>
    {frame ? <img src={frame} alt="Authorized employee desktop live frames" style={{width:"100%",height:"auto",maxHeight:"75vh",objectFit:"contain"}}/> : <p>No live screen frame received</p>}
  </section>;
}
