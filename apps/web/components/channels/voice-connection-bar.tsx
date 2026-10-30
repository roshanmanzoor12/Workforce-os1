"use client";

import {
  Headphones,
  HeadphoneOff,
  Mic,
  MicOff,
  MonitorUp,
  PhoneOff,
  Volume2,
} from "lucide-react";


interface VoiceConnectionBarProps {
  channelName:
    string;

  muted:
    boolean;

  deafened:
    boolean;

  screenSharing:
    boolean;

  busy:
    boolean;

  onOpen:
    () => void;

  onToggleMute:
    () => void;

  onToggleDeafen:
    () => void;

  onToggleScreenShare:
    () => void;

  onDisconnect:
    () => void;
}


export function VoiceConnectionBar({
  channelName,

  muted,

  deafened,

  screenSharing,

  busy,

  onOpen,

  onToggleMute,

  onToggleDeafen,

  onToggleScreenShare,

  onDisconnect,
}: VoiceConnectionBarProps) {
  return (
    <div
      style={{
        display:
          "grid",

        gap:
          8,

        padding:
          9,

        borderTop:
          "1px solid var(--color-border)",

        background:
          "#f0ece3",
      }}
    >
      <button
        type="button"
        onClick={
          onOpen
        }
        style={{
          display:
            "grid",

          gridTemplateColumns:
            "28px minmax(0, 1fr)",

          gap:
            8,

          alignItems:
            "center",

          width:
            "100%",

          padding:
            0,

          border:
            0,

          background:
            "transparent",

          color:
            "inherit",

          textAlign:
            "left",

          cursor:
            "pointer",
        }}
      >
        <div
          style={{
            display:
              "grid",

            width:
              28,

            height:
              28,

            placeItems:
              "center",

            borderRadius:
              7,

            background:
              "#e4f3df",

            color:
              "#35772e",
          }}
        >
          <Volume2
            size={
              14
            }
          />
        </div>


        <div
          style={{
            minWidth:
              0,
          }}
        >
          <strong
            style={{
              display:
                "block",

              overflow:
                "hidden",

              textOverflow:
                "ellipsis",

              whiteSpace:
                "nowrap",

              color:
                "#34732a",

              fontSize:
                9,
            }}
          >
            Voice Connected
          </strong>


          <div
            style={{
              marginTop:
                1,

              overflow:
                "hidden",

              textOverflow:
                "ellipsis",

              whiteSpace:
                "nowrap",

              color:
                "#6f7274",

              fontSize:
                7,
            }}
          >
            {channelName}
          </div>
        </div>
      </button>


      <div
        style={{
          display:
            "grid",

          gridTemplateColumns:
            "repeat(4, 1fr)",

          gap:
            5,
        }}
      >
        <ControlButton
          title={
            muted
              ? "Unmute"
              : "Mute"
          }
          active={
            muted
          }
          disabled={
            busy
          }
          onClick={
            onToggleMute
          }
        >
          {muted ? (
            <MicOff
              size={
                13
              }
            />
          ) : (
            <Mic
              size={
                13
              }
            />
          )}
        </ControlButton>


        <ControlButton
          title={
            deafened
              ? "Undeafen"
              : "Deafen"
          }
          active={
            deafened
          }
          disabled={
            busy
          }
          onClick={
            onToggleDeafen
          }
        >
          {deafened ? (
            <HeadphoneOff
              size={
                13
              }
            />
          ) : (
            <Headphones
              size={
                13
              }
            />
          )}
        </ControlButton>


        <ControlButton
          title={
            screenSharing
              ? "Stop screen share"
              : "Share screen"
          }
          active={
            screenSharing
          }
          disabled={
            busy
          }
          onClick={
            onToggleScreenShare
          }
        >
          <MonitorUp
            size={
              13
            }
          />
        </ControlButton>


        <ControlButton
          title="Disconnect"
          danger
          disabled={
            busy
          }
          onClick={
            onDisconnect
          }
        >
          <PhoneOff
            size={
              13
            }
          />
        </ControlButton>
      </div>
    </div>
  );
}


function ControlButton({
  children,

  title,

  active =
    false,

  danger =
    false,

  disabled =
    false,

  onClick,
}: {
  children:
    React.ReactNode;

  title:
    string;

  active?:
    boolean;

  danger?:
    boolean;

  disabled?:
    boolean;

  onClick:
    () => void;
}) {
  return (
    <button
      type="button"
      title={
        title
      }
      disabled={
        disabled
      }
      onClick={
        onClick
      }
      style={{
        display:
          "grid",

        height:
          30,

        placeItems:
          "center",

        border:
          active
            ? "1px solid #c4a248"
            : "1px solid #dcd7cd",

        borderRadius:
          6,

        background:
          active
            ? "#fff4cf"
            : "#fffefa",

        color:
          danger
            ? "#b52b2b"
            : active
              ? "#80610b"
              : "#55585a",

        cursor:
          disabled
            ? "not-allowed"
            : "pointer",

        opacity:
          disabled
            ? 0.55
            : 1,
      }}
    >
      {children}
    </button>
  );
}