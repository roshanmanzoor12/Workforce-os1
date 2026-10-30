"use client";

import type {
  ChannelRealtimeConnectionState,
} from "@/types/channel-realtime";


interface ChannelRealtimeStatusProps {
  state: ChannelRealtimeConnectionState;
}


export function ChannelRealtimeStatus({
  state,
}: ChannelRealtimeStatusProps) {
  let label =
    "Offline";

  if (
    state === "connected"
  ) {
    label = "Live";
  }

  if (
    state === "connecting"
  ) {
    label = "Connecting";
  }

  if (
    state === "reconnecting"
  ) {
    label = "Reconnecting";
  }

  if (
    state === "error"
  ) {
    label = "Connection issue";
  }


  return (
    <div
      className="
        inline-flex items-center
        gap-1.5 rounded-full
        border px-2 py-1
        text-[11px]
        text-muted-foreground
      "
      title={`Realtime: ${label}`}
    >
      <span
        className="
          inline-block h-1.5
          w-1.5 rounded-full
          bg-current
        "
        aria-hidden="true"
      />

      <span>
        {label}
      </span>
    </div>
  );
}