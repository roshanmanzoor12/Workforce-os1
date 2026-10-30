"use client";

import { useEffect, useRef, useState } from "react";
import { Pause, Play, Send, Trash2 } from "lucide-react";

interface VoiceRecordingIndicatorProps {
  stream: MediaStream | null;
  disabled?: boolean;
  onCancel: () => void;
  onPause: (paused: boolean) => void;
  onSend: () => void;
}

export function VoiceRecordingIndicator({
  stream,
  disabled = false,
  onCancel,
  onPause,
  onSend,
}: VoiceRecordingIndicatorProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const startedAt = useRef(0);
  const pausedAt = useRef<number | null>(null);
  const pausedMs = useRef(0);

  const [seconds, setSeconds] = useState(0);
  const [paused, setPaused] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    startedAt.current = Date.now();
    pausedAt.current = null;
    pausedMs.current = 0;

    const timer = window.setInterval(() => {
      const end = pausedAt.current ?? Date.now();

      setSeconds(
        Math.max(
          0,
          Math.floor(
            (
              end -
              startedAt.current -
              pausedMs.current
            ) / 1000,
          ),
        ),
      );
    }, 200);

    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    if (
      !stream ||
      paused ||
      window.matchMedia(
        "(prefers-reduced-motion: reduce)",
      ).matches
    ) {
      return;
    }

    let frame = 0;
    let context: AudioContext | null = null;
    let source: MediaStreamAudioSourceNode | null = null;

    try {
      context = new AudioContext();

      void context.resume().catch(() => undefined);

      source = context.createMediaStreamSource(stream);

      const analyser = context.createAnalyser();
      analyser.fftSize = 256;

      source.connect(analyser);

      const samples = new Uint8Array(analyser.fftSize);

      const paint = () => {
        const canvas = canvasRef.current;
        const drawing = canvas?.getContext("2d");

        if (canvas && drawing) {
          analyser.getByteTimeDomainData(samples);

          drawing.clearRect(
            0,
            0,
            canvas.width,
            canvas.height,
          );

          drawing.strokeStyle = "#655b40";
          drawing.lineWidth = 3;
          drawing.beginPath();

          samples.forEach((sample, index) => {
            const x =
              index * canvas.width /
              (samples.length - 1);

            const y =
              sample / 255 * canvas.height;

            if (index === 0) {
              drawing.moveTo(x, y);
            } else {
              drawing.lineTo(x, y);
            }
          });

          drawing.stroke();
        }

        frame = requestAnimationFrame(paint);
      };

      paint();
    } catch {
      // Recording remains available without waveform analysis.
    }

    return () => {
      cancelAnimationFrame(frame);
      source?.disconnect();

      void context?.close().catch(() => undefined);
    };
  }, [stream, paused]);

  function togglePause(): void {
    try {
      const next = !paused;

      onPause(next);

      const now = Date.now();

      if (next) {
        pausedAt.current = now;
      } else if (pausedAt.current !== null) {
        pausedMs.current += now - pausedAt.current;
        pausedAt.current = null;
      }

      setPaused(next);
      setError("");
    } catch {
      setError(
        "Recording could not pause or resume. Cancel and try again.",
      );
    }
  }

  return (
    <div className="voiceRecorder">
      <button
        type="button"
        disabled={disabled}
        onClick={onCancel}
        aria-label="Cancel recording"
        title="Cancel recording"
      >
        <Trash2 size={18} />
      </button>

      <span
        className={`recordDot ${paused ? "paused" : ""}`}
        aria-hidden="true"
      />

      <time>
        {Math.floor(seconds / 60)}:
        {String(seconds % 60).padStart(2, "0")}
      </time>

      <span className="recordStatus" role="status">
        {disabled
          ? "Sending…"
          : paused
            ? "Paused"
            : "Recording"}
      </span>

      <canvas
        ref={canvasRef}
        width="400"
        height="56"
        aria-hidden="true"
      />

      <button
        type="button"
        className="pauseControl"
        disabled={disabled}
        onClick={togglePause}
        aria-label={
          paused ? "Resume recording" : "Pause recording"
        }
        title={
          paused ? "Resume recording" : "Pause recording"
        }
      >
        {paused ? (
          <Play size={19} fill="currentColor" />
        ) : (
          <Pause size={19} fill="currentColor" />
        )}
      </button>

      <button
        type="button"
        className="sendControl"
        disabled={disabled}
        onClick={onSend}
        aria-label="Send voice message"
        title="Send voice message"
      >
        <Send size={19} />
      </button>

      {error && (
        <span className="recordError" role="alert">
          {error}
        </span>
      )}

      <style jsx>{`
        .voiceRecorder {
          display: flex;
          align-items: center;
          flex-wrap: wrap;
          gap: 9px;
          min-height: 46px;
          margin: 6px 0;
          padding: 5px 9px;
          border-radius: 12px;
          background: #fff3c5;
          color: #252627;
          font-size: 12px;
        }

        button {
          display: grid;
          place-items: center;
          flex: 0 0 32px;
          width: 32px;
          height: 34px;
          padding: 0;
          border: 0;
          border-radius: 6px;
          background: transparent;
          color: inherit;
          cursor: pointer;
        }

        button:focus-visible {
          outline: none;
          background: #ffe69a;
          outline-offset: 2px;
        }

        button:disabled {
          opacity: 0.5;
          cursor: wait;
        }

        .recordDot {
          width: 7px;
          height: 7px;
          border-radius: 50%;
          background: #b88700;
        }

        .recordDot.paused {
          background: #655b40;
        }

        time {
          font-variant-numeric: tabular-nums;
        }

        .recordStatus {
          font-size: 10px;
          color: #655b40;
        }

        canvas {
          flex: 1;
          min-width: 30px;
          width: 80px;
          height: 28px;
        }

        .pauseControl {
          color: #252627;
        }

        .sendControl {
          width: 36px;
          height: 36px;
          flex-basis: 36px;
          border-radius: 50%;
          background: #f4c400;
          color: #252627;
        }

        .recordError {
          flex-basis: 100%;
          color: #ffb9b9;
          font-size: 11px;
        }

        @media (max-width: 480px) {
          .recordStatus {
            position: absolute;
            width: 1px;
            height: 1px;
            overflow: hidden;
            clip-path: inset(50%);
          }
        }

        @media (prefers-reduced-motion: reduce) {
          canvas {
            visibility: hidden;
          }
        }
      `}</style>
    </div>
  );
}