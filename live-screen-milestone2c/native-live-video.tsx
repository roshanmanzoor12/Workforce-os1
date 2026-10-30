"use client";

import { useEffect, useRef } from "react";

export type NativeLiveVideoProps = {
  stream: MediaStream | null;
  employeeName?: string;
  onTrackEnded?: () => void;
};

/** Direct media renderer: accepts only an authorized MediaStream, never an iframe URL. */
export default function NativeLiveVideo({
  stream,
  employeeName = "employee",
  onTrackEnded,
}: NativeLiveVideoProps) {
  const video = useRef<HTMLVideoElement>(null);
  const endedCallback = useRef(onTrackEnded);
  useEffect(() => { endedCallback.current = onTrackEnded; }, [onTrackEnded]);

  useEffect(() => {
    const el = video.current;
    if (!el) return;
    el.srcObject = stream;
    if (!stream) return;
    const tracks = stream.getVideoTracks();
    const onEnded = () => endedCallback.current?.();
    for (const track of tracks) track.addEventListener("ended", onEnded);
    void el.play().catch(() => {
      // Browser autoplay policy can require the viewer to press Play.
      // Native controls remain visible for this purpose.
    });
    return () => {
      for (const track of tracks) track.removeEventListener("ended", onEnded);
      el.pause();
      el.srcObject = null;
      // Do NOT stop shared tracks here: sender/session manager owns their lifecycle.
    };
  }, [stream]);

  return (
    <section aria-label={`Live desktop view: ${employeeName}`} style={{ width: "100%", height: "100%", minHeight: 360, display: "grid", placeItems: "center", background: "#111318", position: "relative" }}>
      <video ref={video} autoPlay playsInline controls muted={false} style={{ width: "100%", maxHeight: "75vh", display: stream ? "block" : "none", objectFit: "contain" }} />
      {!stream && (
        <div role="status" style={{ color: "#f5f5f5", textAlign: "center", padding: 28 }}>
          <strong style={{ display: "block", marginBottom: 12 }}>No authorized video stream connected</strong>
          <span style={{ fontSize: 13, opacity: 0.8 }}>A native sender and authenticated session transport are required.</span>
        </div>
      )}
    </section>
  );
}
