"use client";

import {
  useEffect,
  useState,
} from "react";

export function SpeakingIndicator({
  stream,
}: {
  stream?: MediaStream | null;
}) {
  const [speaking, setSpeaking] = useState(false);

  useEffect(() => {
    setSpeaking(false);

    if (!stream?.getAudioTracks().length) return;

    let context: AudioContext;

    try {
      context = new AudioContext();
    } catch {
      return;
    }

    const analyser = context.createAnalyser();
    analyser.fftSize = 512;

    const source = context.createMediaStreamSource(stream);
    source.connect(analyser);

    const samples = new Float32Array(
      analyser.fftSize,
    );

    let lastVoice = 0;

    const resume = () => {
      void context.resume().catch(() => undefined);
    };

    document.addEventListener(
      "pointerdown",
      resume,
    );

    resume();

    const timer = window.setInterval(() => {
      analyser.getFloatTimeDomainData(samples);

      let power = 0;

      for (const value of samples) {
        power += value * value;
      }

      const enabled = stream.getAudioTracks().some(
        track =>
          track.enabled
          && !track.muted
          && track.readyState === "live",
      );

      if (
        enabled
        && Math.sqrt(power / samples.length) > 0.025
      ) {
        lastVoice = performance.now();
      }

      setSpeaking(
        enabled
        && lastVoice > 0
        && performance.now() - lastVoice < 180,
      );
    }, 80);

    return () => {
      clearInterval(timer);

      document.removeEventListener(
        "pointerdown",
        resume,
      );

      source.disconnect();
      analyser.disconnect();

      void context.close().catch(() => undefined);
    };
  }, [stream]);

  return (
    <span
      title={speaking ? "Speaking" : "Not speaking"}
      aria-label={speaking ? "Speaking" : "Not speaking"}
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 2,
        padding: "3px 5px",
        marginLeft: 6,
        borderRadius: 8,
        background: speaking ? "#ffda55" : "transparent",
        verticalAlign: "middle",
        height: 19,
      }}
    >
      {[6, 11, 8].map((height, index) => (
        <i
          key={index}
          style={{
            display: "block",
            width: 3,
            height: speaking ? height : 3,
            borderRadius: 2,
            background: speaking ? "#6b4c00" : "#8b8b85",
            transition: "height 100ms",
          }}
        />
      ))}
    </span>
  );
}
