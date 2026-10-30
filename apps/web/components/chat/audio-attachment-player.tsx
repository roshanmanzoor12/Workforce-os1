"use client";

import { useEffect, useRef, useState } from "react";
import { Loader2, Pause, Play } from "lucide-react";
import { attachmentsService } from "@/services/attachments.service";

export function isGeneratedVoiceCaption(
  content: string,
  filenames: string[],
): boolean {
  const text = content.trim();

  return filenames.length > 0 && (
    /^(?:🎙️?\s*)?Voice message$/iu.test(text) ||
    text === filenames.join(", ")
  );
}

function clock(seconds: number): string {
  const value = Number.isFinite(seconds)
    ? Math.max(0, Math.floor(seconds))
    : 0;

  return `${Math.floor(value / 60)}:${String(value % 60).padStart(2, "0")}`;
}

export function AudioAttachmentPlayer({
  attachmentId,
  filename = "Voice message",
}: {
  attachmentId: string;
  filename?: string;
}) {
  const audioRef = useRef<HTMLAudioElement>(null);
  const hostRef = useRef<HTMLDivElement>(null);
  const pendingUrl = useRef<Promise<string> | null>(null);
  const [started, setStarted] = useState(false);
  const [rate, setRate] = useState(1);
  const generation = useRef(0);
  const busyRef = useRef(false);
  const controller = useRef<AbortController | null>(null);
  const context = useRef<AudioContext | null>(null);

  const [playing, setPlaying] = useState(false);
  const [loading, setLoading] = useState(false);
  const [position, setPosition] = useState(0);
  const [duration, setDuration] = useState(0);
  const [peaks, setPeaks] = useState<number[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    generation.current += 1;
    busyRef.current = false;

    pendingUrl.current = null;
    setStarted(false);
    setRate(1);
    setPlaying(false);
    setLoading(false);
    setPosition(0);
    setDuration(0);
    setPeaks([]);
    setError("");

    const audio = audioRef.current;

    const pauseOther = (event: Event) => {
      if (event.target !== audio) {
        audio?.pause();
      }
    };

    document.addEventListener("play", pauseOther, true);

    return () => {
      generation.current += 1;
      controller.current?.abort();

      void context.current?.close().catch(() => undefined);
      context.current = null;

      audio?.pause();
      audio?.removeAttribute("src");
      audio?.load();

      document.removeEventListener("play", pauseOther, true);
    };
  }, [attachmentId]);

  async function decodeWaveform(
    url: string,
    run: number,
  ): Promise<void> {
    controller.current?.abort();

    const request = new AbortController();
    controller.current = request;

    let decoder: AudioContext | null = null;

    try {
      const response = await fetch(url, {
        signal: request.signal,
        credentials: "omit",
      });

      if (!response.ok) return;

      const data = await response.arrayBuffer();

      if (
        run !== generation.current ||
        data.byteLength > 32 * 1024 * 1024
      ) {
        return;
      }

      decoder = new AudioContext();
      context.current = decoder;

      const buffer = await decoder.decodeAudioData(data);

      if (run !== generation.current) return;

      const samples = buffer.getChannelData(0);

      const bars = Array.from({ length: 44 }, (_, index) => {
        const start = Math.floor(index * samples.length / 44);
        const end = Math.floor((index + 1) * samples.length / 44);
        const stride = Math.max(
          1,
          Math.floor((end - start) / 300),
        );

        let sum = 0;
        let count = 0;

        for (let i = start; i < end; i += stride) {
          sum += samples[i]! * samples[i]!;
          count += 1;
        }

        return Math.sqrt(sum / Math.max(1, count));
      });

      const maximum = Math.max(0.001, ...bars);

      setPeaks(
        bars.map(value => Math.max(0.08, value / maximum)),
      );

      setDuration(buffer.duration);
    } catch {
      // Playback can still work when storage CORS blocks waveform decoding.
    } finally {
      if (decoder) {
        await decoder.close().catch(() => undefined);
      }

      if (context.current === decoder) {
        context.current = null;
      }
    }
  }


  // voice-player-compact-v2
  async function prepareAudio(): Promise<string> {
    const audio = audioRef.current;

    if (!audio) {
      throw new Error("Audio player unavailable.");
    }

    if (audio.getAttribute("src") && !audio.error) {
      return audio.src;
    }

    if (pendingUrl.current) {
      return pendingUrl.current;
    }

    const run = generation.current;

    const request = (async () => {
      const result = await attachmentsService.createDownload(
        attachmentId,
      );

      const url = new URL(
        result.download_url,
        window.location.origin,
      );

      if (!["https:", "http:"].includes(url.protocol)) {
        throw new Error("Invalid audio URL.");
      }

      if (run !== generation.current) {
        throw new Error("Audio changed.");
      }

      audio.src = url.href;
      audio.playbackRate = rate;
      audio.load();

      void decodeWaveform(url.href, run);

      return url.href;
    })();

    pendingUrl.current = request;

    try {
      return await request;
    } finally {
      if (pendingUrl.current === request) {
        pendingUrl.current = null;
      }
    }
  }

  useEffect(() => {
    let disposed = false;

    const load = () => {
      if (!disposed) {
        void prepareAudio().catch(() => undefined);
      }
    };

    if (
      !hostRef.current ||
      !("IntersectionObserver" in window)
    ) {
      load();

      return () => {
        disposed = true;
      };
    }

    const observer = new IntersectionObserver(
      entries => {
        if (entries.some(entry => entry.isIntersecting)) {
          observer.disconnect();
          load();
        }
      },
      {
        rootMargin: "120px",
      },
    );

    observer.observe(hostRef.current);

    return () => {
      disposed = true;
      observer.disconnect();
    };
  }, [attachmentId]);

  async function toggle(): Promise<void> {
    const audio = audioRef.current;

    if (!audio || busyRef.current) return;

    if (!audio.paused) {
      audio.pause();
      return;
    }

    busyRef.current = true;
    setLoading(true);
    setError("");

    const run = generation.current;

    try {
      await prepareAudio();
      if (run !== generation.current) return;

      if (audio.ended) {
        audio.currentTime = 0;
      }

      await audio.play();
    } catch (cause) {
      if (run === generation.current) {
        setError(
          cause instanceof DOMException &&
          cause.name === "NotAllowedError"
            ? "Press Play again to allow audio."
            : "Audio could not play. Press Play to retry.",
        );
      }
    } finally {
      if (run === generation.current) {
        busyRef.current = false;
        setLoading(false);
      }
    }
  }

  const progress = duration > 0
    ? Math.min(1, position / duration)
    : 0;

  return (
    <div
      ref={hostRef}
      className="voicePlayer"
      role="group"
      aria-label={
        filename.startsWith("voice-")
          ? "Voice message"
          : filename
      }
    >
      <audio
        ref={audioRef}
        preload="metadata"
        aria-label="Voice message"
        onPlay={() => {
          setStarted(true);
          setPlaying(true);
        }}
        onPause={() => setPlaying(false)}
        onEnded={() => {
          setPlaying(false);
          setStarted(false);
          setPosition(0);
        }}
        onTimeUpdate={event => {
          setPosition(event.currentTarget.currentTime);
        }}
        onLoadedMetadata={event => {
          if (Number.isFinite(event.currentTarget.duration)) {
            setDuration(event.currentTarget.duration);
          }
        }}
        onError={() => {
          setPlaying(false);
          setError(
            "Audio unavailable. Press Play to renew the link.",
          );
        }}
      />

      <button
        type="button"
        className="voicePlay"
        disabled={loading}
        aria-label={
          playing
            ? "Pause voice message"
            : "Play voice message"
        }
        onClick={() => void toggle()}
      >
        {loading ? (
          <Loader2 size={19} />
        ) : playing ? (
          <Pause size={19} fill="currentColor" />
        ) : (
          <Play size={19} fill="currentColor" />
        )}
      </button>

      <div className="voiceTrack">
        <div className="voiceWave">
          <svg
            viewBox="0 0 176 32"
            preserveAspectRatio="none"
            aria-hidden="true"
          >
            {peaks.length ? (
              peaks.map((height, index) => (
                <rect
                  key={index}
                  x={index * 4}
                  y={16 - height * 14}
                  width="2.5"
                  height={height * 28}
                  rx="1.25"
                  fill={
                    index / 44 <= progress
                      ? "#252627"
                      : "#b5a879"
                  }
                />
              ))
            ) : (
              <>
                <path
                  d="M0 16H176"
                  stroke="#b5a879"
                  strokeWidth="2"
                />
                <path
                  d={`M0 16H${176 * progress}`}
                  stroke="#252627"
                  strokeWidth="3"
                />
              </>
            )}
          </svg>

          <input
            type="range"
            min="0"
            max={duration || 1}
            step="0.01"
            value={Math.min(position, duration || 1)}
            disabled={!duration}
            aria-label="Seek voice message"
            aria-valuetext={`${clock(position)} of ${clock(duration)}`}
            onChange={event => {
              const next = Number(event.target.value);

              if (audioRef.current) {
                audioRef.current.currentTime = next;
              }

              setPosition(next);
            }}
          />
        </div>

        <div className="voiceTimes">
          <span>{clock(started ? position : duration)}</span>
        </div>
      </div>

      <button
        type="button"
        className="voiceSpeed"
        aria-label={`Playback speed ${rate} times`}
        onClick={() => {
          const rates = [1, 1.25, 1.5, 2];

          const next = rates[
            (rates.indexOf(rate) + 1) % rates.length
          ]!;

          setRate(next);

          if (audioRef.current) {
            audioRef.current.playbackRate = next;
          }
        }}
      >
        {rate}×
      </button>

      {error && (
        <span className="voiceError" role="alert">
          {error}
        </span>
      )}

      <style jsx>{`
        .voicePlayer {
          display: grid;
          grid-template-columns: 32px minmax(0, 1fr);
          align-items: center;
          gap: 8px;
          width: 250px;
          max-width: 100%;
          padding: 5px 0;
          color: #252627;
        }

        .voicePlayer audio {
          display: none;
        }

        .voicePlay {
          display: grid;
          place-items: center;
          width: 32px;
          height: 36px;
          padding: 0;
          border: 0;
          border-radius: 6px;
          background: transparent;
          color: inherit;
          cursor: pointer;
        }

        .voicePlay:hover {
          background: #ffe69a;
        }

        .voicePlay:focus-visible {
          outline: none;
          background: #ffe69a;
          outline-offset: 2px;
        }

        .voicePlay:disabled {
          opacity: 0.6;
          cursor: wait;
        }

        .voiceTrack {
          min-width: 0;
        }

        .voiceWave {
          position: relative;
          height: 32px;
        }

        .voiceWave svg {
          display: block;
          width: 100%;
          height: 32px;
        }

        .voiceWave input {
          position: absolute;
          inset: 0;
          width: 100%;
          height: 100%;
          margin: 0;
          opacity: 0;
          cursor: pointer;
        }

        .voiceWave:focus-within {
          outline: none;
          background: #ffe69a;
          outline-offset: 2px;
          border-radius: 3px;
        }

        .voiceTimes {
          display: flex;
          justify-content: space-between;
          color: #655b40;
          font-size: 10px;
          line-height: 16px;
          font-variant-numeric: tabular-nums;
        }

        .voiceError {
          grid-column: 1 / -1;
          color: #a33232;
          font-size: 11px;
        }
        .voicePlayer {
          grid-template-columns: 26px minmax(0, 1fr) 40px;
          gap: 7px;
          width: 250px;
          padding: 2px 0;
          border: 0;
        }

        .voicePlay {
          width: 26px;
          height: 28px;
        }

        .voiceWave,
        .voiceWave svg {
          height: 22px;
        }

        .voiceTimes {
          line-height: 12px;
          font-size: 9px;
        }

        .voiceSpeed {
          align-self: center;
          padding: 4px 3px;
          min-width: 37px;
          border: 0;
          border-radius: 12px;
          background: #292722;
          color: #fff;
          font-size: 10px;
          cursor: pointer;
        }

        .voiceSpeed:focus-visible {
          outline: 2px solid #bd8c00;
          outline-offset: 2px;
        }
      `}</style>
    </div>
  );
}