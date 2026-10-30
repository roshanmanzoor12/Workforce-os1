import {
  forwardChannelAttachmentRealtimeEvent,
} from "@/lib/realtime/channel-attachment-events";

import type {
  ChannelRealtimeEvent,
} from "@/types/channel-realtime";


export function observeChannelRealtimeEvent(
  event:
    ChannelRealtimeEvent<
      Record<string, unknown>
    >,
): void {
  forwardChannelAttachmentRealtimeEvent(
    event,
  );
}