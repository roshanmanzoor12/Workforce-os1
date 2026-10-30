
"use client";

import {
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";

export function CallRingtone({
  callId,
  mode,
  expiresAt,
}: {
  callId: string;
  mode: "incoming" | "outgoing";
  expiresAt?: string;
}) {
  const context = useRef<AudioContext | null>(null);
  const [blocked, setBlocked] = useState(false);

  const enable = useCallback(() => {
    void context.current?.resume()
      .then(() => {
        setBlocked(
          context.current?.state !== "running",
        );
      })
      .catch(() => setBlocked(true));
  }, []);

  useEffect(() => {
    let audio: AudioContext;

    try {
      audio = new AudioContext();
    } catch {
      return;
    }

    context.current = audio;

    let stopped = false;

    const nodes = new Set<OscillatorNode>();

    const deadline = expiresAt
      ? Date.parse(expiresAt)
      : Date.now() + 40_000;

    const play = () => {
      if (stopped || Date.now() >= deadline) return;

      if (audio.state !== "running") {
        setBlocked(true);
        return;
      }

      setBlocked(false);

      for (const offset of [0, .38]) {
        const frequencies = mode === "incoming"
          ? [660, 880]
          : [440, 480];

        for (const frequency of frequencies) {
          const oscillator = audio.createOscillator();
          const gain = audio.createGain();
          const start = audio.currentTime + offset;

          oscillator.frequency.value = frequency;

          gain.gain.setValueAtTime(0, start);
          gain.gain.linearRampToValueAtTime(
            .035,
            start + .015,
          );
          gain.gain.setValueAtTime(
            .035,
            start + .23,
          );
          gain.gain.linearRampToValueAtTime(
            0,
            start + .28,
          );

          oscillator.connect(gain);
          gain.connect(audio.destination);

          nodes.add(oscillator);

          oscillator.onended = () => {
            nodes.delete(oscillator);
            oscillator.disconnect();
            gain.disconnect();
          };

          oscillator.start(start);
          oscillator.stop(start + .3);
        }
      }
    };

    void audio.resume()
      .then(() => {
        if (!stopped) {
          setBlocked(audio.state !== "running");
          play();
        }
      })
      .catch(() => {
        if (!stopped) setBlocked(true);
      });

    const interval = setInterval(
      play,
      mode === "incoming" ? 2400 : 3000,
    );

    const resume = () => {
      if (audio.state === "suspended") {
        void audio.resume().catch(() => undefined);
      }
    };

    document.addEventListener(
      "pointerdown",
      resume,
    );

    return () => {
      stopped = true;

      clearInterval(interval);

      document.removeEventListener(
        "pointerdown",
        resume,
      );

      for (const node of nodes) {
        try {
          node.stop();
        } catch {
          // Already ended.
        }
      }

      void audio.close().catch(() => undefined);

      if (context.current === audio) {
        context.current = null;
      }
    };
  }, [callId, mode, expiresAt]);

  return blocked ? (
    <button
      type="button"
      onClick={enable}
      style={{
        padding: "6px 10px",
        margin: "7px 0",
        border: "1px solid #d9b84e",
        borderRadius: 7,
        background: "#ffdc64",
        color: "#252627",
        fontSize: 12,
      }}
    >
      Enable call sound
    </button>
  ) : null;
}
