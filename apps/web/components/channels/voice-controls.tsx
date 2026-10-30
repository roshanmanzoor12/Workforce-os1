"use client";

import {
  Headphones,
  LogIn,
  LogOut,
  Mic,
  MicOff,
  MonitorUp,
  MonitorX,
  VolumeX,
} from "lucide-react";


interface VoiceControlsProps {
  joined: boolean;

  muted: boolean;

  deafened: boolean;

  screenSharing: boolean;

  busy: boolean;

  onJoin(): Promise<void>;

  onLeave(): Promise<void>;

  onMuteToggle(): Promise<void>;

  onDeafenToggle(): Promise<void>;

  onScreenShareToggle(): Promise<void>;
}


function controlStyle(
  active = false,
): React.CSSProperties {
  return {
    minWidth: 42,
    height: 42,
    borderRadius: 9,
    border:
      "1px solid var(--border, #e5e7eb)",
    cursor: "pointer",
    display: "grid",
    placeItems: "center",
    background:
      active
        ? "rgba(239,68,68,.12)"
        : "transparent",
  };
}


export function VoiceControls({
  joined,
  muted,
  deafened,
  screenSharing,
  busy,
  onJoin,
  onLeave,
  onMuteToggle,
  onDeafenToggle,
  onScreenShareToggle,
}: VoiceControlsProps) {
  if (!joined) {
    return (
      <button
        type="button"
        disabled={busy}
        onClick={() =>
          void onJoin()
        }
        style={{
          minHeight: 42,
          padding:
            "0 16px",
          display: "flex",
          alignItems:
            "center",
          gap: 8,
          cursor:
            "pointer",
        }}
      >
        <LogIn
          size={17}
        />

        Join Voice
      </button>
    );
  }


  return (
    <div
      style={{
        display: "flex",
        alignItems:
          "center",
        gap: 8,
        flexWrap: "wrap",
      }}
    >
      <button
        type="button"
        title={
          muted
            ? "Unmute"
            : "Mute"
        }
        disabled={busy}
        onClick={() =>
          void onMuteToggle()
        }
        style={
          controlStyle(
            muted,
          )
        }
      >
        {muted ? (
          <MicOff
            size={17}
          />
        ) : (
          <Mic
            size={17}
          />
        )}
      </button>

      <button
        type="button"
        title={
          deafened
            ? "Undeafen"
            : "Deafen"
        }
        disabled={busy}
        onClick={() =>
          void onDeafenToggle()
        }
        style={
          controlStyle(
            deafened,
          )
        }
      >
        {deafened ? (
          <VolumeX
            size={17}
          />
        ) : (
          <Headphones
            size={17}
          />
        )}
      </button>

      <button
        type="button"
        title={
          screenSharing
            ? "Stop screen share"
            : "Share screen"
        }
        disabled={busy}
        onClick={() =>
          void onScreenShareToggle()
        }
        style={
          controlStyle(
            screenSharing,
          )
        }
      >
        {screenSharing ? (
          <MonitorX
            size={17}
          />
        ) : (
          <MonitorUp
            size={17}
          />
        )}
      </button>

      <button
        type="button"
        disabled={busy}
        onClick={() =>
          void onLeave()
        }
        style={{
          ...controlStyle(
            true,
          ),
          width: "auto",
          padding:
            "0 12px",
          display: "flex",
          gap: 7,
        }}
      >
        <LogOut
          size={17}
        />

        Disconnect
      </button>
    </div>
  );
}