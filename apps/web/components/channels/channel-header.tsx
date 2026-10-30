"use client";

import {
  Hash,
  Megaphone,
  MoreHorizontal,
  RefreshCcw,
  Volume2,
} from "lucide-react";

import type {
  WorkspaceChannel,
} from "@/types/channels";


interface ChannelHeaderProps {
  channel:
    WorkspaceChannel;

  loading?: boolean;

  onRefresh?():
    void;
}


export function ChannelHeader({
  channel,
  loading = false,
  onRefresh,
}: ChannelHeaderProps) {
  const icon =
    channel.channel_type ===
    "voice" ? (
      <Volume2
        size={18}
      />
    ) : channel.channel_type ===
      "announcement" ? (
      <Megaphone
        size={18}
      />
    ) : (
      <Hash
        size={18}
      />
    );


  return (
    <header
      style={{
        minHeight:
          58,

        padding:
          "0 16px",

        display:
          "flex",

        alignItems:
          "center",

        justifyContent:
          "space-between",

        gap: 14,

        borderBottom:
          "1px solid var(--border, #e5e7eb)",
      }}
    >
      <div
        style={{
          minWidth:
            0,

          display:
            "flex",

          alignItems:
            "center",

          gap: 9,
        }}
      >
        {icon}

        <div
          style={{
            minWidth:
              0,
          }}
        >
          <div
            style={{
              fontWeight:
                800,

              overflow:
                "hidden",

              whiteSpace:
                "nowrap",

              textOverflow:
                "ellipsis",
            }}
          >
            {
              channel.name
            }
          </div>

          <div
            style={{
              marginTop:
                1,

              fontSize:
                11,

              opacity:
                0.55,

              textTransform:
                "capitalize",
            }}
          >
            {
              channel.channel_type
            }{" "}
            channel
          </div>
        </div>
      </div>

      <div
        style={{
          display:
            "flex",

          alignItems:
            "center",

          gap: 5,
        }}
      >
        {onRefresh ? (
          <button
            type="button"
            title="Refresh"
            disabled={
              loading
            }
            onClick={
              onRefresh
            }
            style={{
              width: 36,
              height: 36,
              display:
                "grid",
              placeItems:
                "center",
              border:
                0,
              borderRadius:
                8,
              background:
                "transparent",
              cursor:
                "pointer",
              color:
                "inherit",
            }}
          >
            <RefreshCcw
              size={16}
            />
          </button>
        ) : null}

        <button
          type="button"
          title="Channel options"
          disabled
          style={{
            width: 36,
            height: 36,
            display:
              "grid",
            placeItems:
              "center",
            border:
              0,
            borderRadius:
              8,
            background:
              "transparent",
            opacity:
              0.4,
          }}
        >
          <MoreHorizontal
            size={17}
          />
        </button>
      </div>
    </header>
  );
}