import {
  channelRealtimeService,
} from "@/services/channel-realtime.service";

import type {
  ChannelRealtimeConnectionState,
  ChannelRealtimeEvent,
  ChannelRealtimeSocketAction,
} from "@/types/channel-realtime";


export interface ChannelRealtimeClientOptions {
  workspaceId: string;
  channelId: string;

  onEvent: (
    event: ChannelRealtimeEvent,
  ) => void;

  onStateChange?: (
    state: ChannelRealtimeConnectionState,
  ) => void;

  reconnectDelayMs?: number;
  heartbeatIntervalMs?: number;
}


function resolveWebSocketBase(): string {
  const configured =
    process.env.NEXT_PUBLIC_API_URL?.trim();

  if (configured) {
    const url = new URL(
      configured,
      window.location.origin,
    );

    const protocol =
      url.protocol === "https:"
        ? "wss:"
        : "ws:";

    return (
      `${protocol}//${url.host}` +
      url.pathname.replace(
        /\/$/,
        "",
      )
    );
  }

  const protocol =
    window.location.protocol === "https:"
      ? "wss:"
      : "ws:";

  return (
    `${protocol}//` +
    window.location.host +
    "/api/v1"
  );
}


export class ChannelRealtimeClient {
  private readonly options:
    ChannelRealtimeClientOptions;

  private socket: WebSocket | null = null;

  private stopped = false;

  private reconnectTimer:
    ReturnType<typeof setTimeout>
    | null = null;

  private heartbeatTimer:
    ReturnType<typeof setInterval>
    | null = null;

  private reconnecting = false;


  constructor(
    options: ChannelRealtimeClientOptions,
  ) {
    this.options = options;
  }


  private setState(
    state: ChannelRealtimeConnectionState,
  ): void {
    this.options.onStateChange?.(
      state,
    );
  }


  async connect(): Promise<void> {
    if (
      typeof window === "undefined"
      || this.stopped
    ) {
      return;
    }

    if (
      this.socket
      && (
        this.socket.readyState
        === WebSocket.OPEN
        || this.socket.readyState
        === WebSocket.CONNECTING
      )
    ) {
      return;
    }

    this.setState(
      this.reconnecting
        ? "reconnecting"
        : "connecting",
    );

    try {
      const ticket =
        await channelRealtimeService
          .createTicket(
            this.options.workspaceId,
            this.options.channelId,
          );

      if (this.stopped) {
        return;
      }

      const base =
        resolveWebSocketBase();

      const path =
        (
          `/workspaces/` +
          `${this.options.workspaceId}` +
          `/channels/` +
          `${this.options.channelId}` +
          `/realtime/ws`
        );

      const socketUrl =
        `${base}${path}` +
        `?ticket=${encodeURIComponent(
          ticket.ticket,
        )}`;

      this.socket = new WebSocket(
        socketUrl,
      );

      this.bindSocket(
        this.socket,
      );

    } catch {
      this.setState(
        "error",
      );

      this.scheduleReconnect();
    }
  }


  private bindSocket(
    socket: WebSocket,
  ): void {
    socket.onopen = () => {
      if (
        socket !== this.socket
      ) {
        return;
      }

      this.reconnecting = false;

      this.setState(
        "connected",
      );

      this.startHeartbeat();
    };


    socket.onmessage = (
      message,
    ) => {
      if (
        socket !== this.socket
      ) {
        return;
      }

      try {
        const event =
          JSON.parse(
            String(
              message.data,
            ),
          ) as ChannelRealtimeEvent;

        this.options.onEvent(
          event,
        );

      } catch {
        // Ignore malformed remote frames.
      }
    };


    socket.onerror = () => {
      if (
        socket !== this.socket
      ) {
        return;
      }

      this.setState(
        "error",
      );
    };


    socket.onclose = () => {
      if (
        socket !== this.socket
      ) {
        return;
      }

      this.socket = null;

      this.stopHeartbeat();

      if (this.stopped) {
        this.setState(
          "disconnected",
        );

        return;
      }

      this.reconnecting = true;

      this.setState(
        "reconnecting",
      );

      this.scheduleReconnect();
    };
  }


  private scheduleReconnect(): void {
    if (
      this.stopped
      || this.reconnectTimer
    ) {
      return;
    }

    const delay =
      this.options.reconnectDelayMs
      ?? 1500;

    this.reconnectTimer =
      setTimeout(
        () => {
          this.reconnectTimer = null;

          void this.connect();
        },
        delay,
      );
  }


  private startHeartbeat(): void {
    this.stopHeartbeat();

    const interval =
      this.options.heartbeatIntervalMs
      ?? 15000;

    this.heartbeatTimer =
      setInterval(
        () => {
          this.send({
            action: "heartbeat",
          });
        },
        interval,
      );
  }


  private stopHeartbeat(): void {
    if (
      !this.heartbeatTimer
    ) {
      return;
    }

    clearInterval(
      this.heartbeatTimer,
    );

    this.heartbeatTimer = null;
  }


  send(
    action: ChannelRealtimeSocketAction,
  ): void {
    if (
      !this.socket
      || this.socket.readyState
      !== WebSocket.OPEN
    ) {
      return;
    }

    this.socket.send(
      JSON.stringify(
        action,
      ),
    );
  }


  typingStart(): void {
    this.send({
      action: "typing.start",
    });
  }


  typingStop(): void {
    this.send({
      action: "typing.stop",
    });
  }


  disconnect(): void {
    this.stopped = true;

    if (
      this.reconnectTimer
    ) {
      clearTimeout(
        this.reconnectTimer,
      );

      this.reconnectTimer = null;
    }

    this.stopHeartbeat();

    const socket =
      this.socket;

    this.socket = null;

    if (
      socket
      && (
        socket.readyState
        === WebSocket.OPEN
        || socket.readyState
        === WebSocket.CONNECTING
      )
    ) {
      socket.close(
        1000,
        "client_disconnect",
      );
    }

    this.setState(
      "disconnected",
    );
  }
}