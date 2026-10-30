import { api } from "@/lib/api/client";
import { socialChatService } from "@/services/social-chat.service";
import type {
  ChatMessagePagePublic,
  ChatMessagePublic,
} from "@/types/social-chat";

export type PersonalChatConnectionState =
  | "connecting"
  | "connected"
  | "reconnecting"
  | "disconnected"
  | "error";

export interface PersonalChatRealtimeEvent {
  event?: string;
  event_type?: string;
  conversation_id?: string | null;
  data?: Record<string, unknown>;
  [key: string]: unknown;
}

export interface PersonalChatRealtimeOptions {
  conversationId?: string;

  onMessages: (
    messages: ChatMessagePublic[],
  ) => void;

  onEvent?: (
    event: PersonalChatRealtimeEvent,
  ) => void;

  onStateChange?: (
    state: PersonalChatConnectionState,
  ) => void;

  onError?: (
    error: Error,
  ) => void;
}

function websocketUrl(ticket: string): string {
  const configured =
    (process.env.NEXT_PUBLIC_API_BASE_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "/backend").trim();

  const url = new URL(
    configured || "/api/v1",
    window.location.origin,
  );

  url.protocol =
    url.protocol === "https:" ? "wss:" : "ws:";

  const basePath = url.pathname.replace(/\/+$/, "");

  url.pathname =
    `${basePath || "/api/v1"}/chat/realtime/ws`;

  url.search = "";
  url.hash = "";
  url.searchParams.set("ticket", ticket);

  return url.toString();
}

function toError(cause: unknown): Error {
  return cause instanceof Error
    ? cause
    : new Error("Personal chat realtime request failed.");
}

export class PersonalChatRealtimeClient {
  private socket: WebSocket | null = null;
  private stopped = false;
  private connecting = false;
  private attempt = 0;
  private generation = 0;

  // Separate from the history/load-older cursor.
  private recoveryCursor: string | null = null;
  private recovering = false;
  private recoveryRequested = false;
  private lastFrameAt = 0;

  private reconnectTimer:
    ReturnType<typeof setTimeout> | null = null;

  private recoveryTimer:
    ReturnType<typeof setTimeout> | null = null;

  private heartbeatTimer:
    ReturnType<typeof setInterval> | null = null;

  constructor(
    private readonly options: PersonalChatRealtimeOptions,
  ) {}

  private setState(
    state: PersonalChatConnectionState,
  ): void {
    this.options.onStateChange?.(state);
  }

  private report(cause: unknown): void {
    this.options.onError?.(toError(cause));
  }

  async connect(): Promise<void> {
    if (
      typeof window === "undefined" ||
      this.stopped ||
      this.connecting ||
      this.socket?.readyState === WebSocket.OPEN ||
      this.socket?.readyState === WebSocket.CONNECTING
    ) {
      return;
    }

    this.connecting = true;
    const generation = this.generation;

    this.setState(
      this.attempt > 0 ? "reconnecting" : "connecting",
    );

    try {
      const ticket =
        await socialChatService.createRealtimeTicket();

      if (
        this.stopped ||
        generation !== this.generation
      ) {
        return;
      }

      const socket = new WebSocket(
        websocketUrl(ticket.ticket),
      );

      this.socket = socket;

      socket.onopen = () => {
        if (!this.isCurrent(socket)) return;

        this.attempt = 0;
        this.lastFrameAt = Date.now();
        this.setState("connected");
        this.startHeartbeat(socket);
        this.requestRecovery();
      };

      socket.onmessage = (message) => {
        if (!this.isCurrent(socket)) return;

        this.lastFrameAt = Date.now();

        if (message.data === "pong") return;
        if (typeof message.data !== "string") return;

        let value: unknown;

        try {
          value = JSON.parse(message.data);
        } catch {
          return;
        }

        if (
          !value ||
          typeof value !== "object" ||
          Array.isArray(value)
        ) {
          return;
        }

        const event =
          value as PersonalChatRealtimeEvent;

        if (event.event === "resume.required") {
          this.requestRecovery();
        }

        // Published chat events and command envelopes
        // have different shapes. Preserve the full frame.
        this.options.onEvent?.(event);
      };

      socket.onerror = () => {
        if (!this.isCurrent(socket)) return;
        this.setState("error");
      };

      socket.onclose = (event) => {
        if (!this.isCurrent(socket)) return;

        this.socket = null;
        this.generation += 1;
        this.stopHeartbeat();
        this.clearRecoveryTimer();

        if (this.stopped) return;

        // Backend uses 1008 for invalid tickets or
        // accounts that are no longer eligible.
        if (event.code === 1008) {
          this.stopped = true;
          this.setState("error");
          this.report(
            new Error(
              "Chat realtime access was rejected. Check your session and account eligibility.",
            ),
          );
          return;
        }

        this.setState("reconnecting");
        this.scheduleReconnect();
      };
    } catch (cause) {
      if (
        !this.stopped &&
        generation === this.generation
      ) {
        this.setState("error");
        this.report(cause);
        this.scheduleReconnect();
      }
    } finally {
      this.connecting = false;
    }
  }

  private isCurrent(socket: WebSocket): boolean {
    return !this.stopped && socket === this.socket;
  }

  private scheduleReconnect(): void {
    if (this.stopped || this.reconnectTimer !== null) {
      return;
    }

    const delay = Math.min(
      1000 * 2 ** Math.min(this.attempt, 5),
      30000,
    );

    this.attempt += 1;

    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      void this.connect();
    }, delay + Math.floor(Math.random() * 400));
  }

  private startHeartbeat(socket: WebSocket): void {
    this.stopHeartbeat();

    this.heartbeatTimer = setInterval(() => {
      if (
        !this.isCurrent(socket) ||
        socket.readyState !== WebSocket.OPEN
      ) {
        return;
      }

      // Any received frame proves the socket is alive.
      if (Date.now() - this.lastFrameAt > 60000) {
        socket.close(4000, "heartbeat_timeout");
        return;
      }

      // Explicitly supported by your backend.
      socket.send("ping");
    }, 15000);
  }

  private stopHeartbeat(): void {
    if (this.heartbeatTimer !== null) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  private clearRecoveryTimer(): void {
    if (this.recoveryTimer !== null) {
      clearTimeout(this.recoveryTimer);
      this.recoveryTimer = null;
    }
  }

  requestRecovery(): void {
    if (this.stopped || !this.options.conversationId) return;

    this.recoveryRequested = true;
    this.clearRecoveryTimer();
    void this.recover();
  }

  private async recover(): Promise<void> {
    if (
      this.stopped ||
      this.recovering ||
      this.socket?.readyState !== WebSocket.OPEN
    ) {
      return;
    }

    this.recovering = true;
    this.recoveryRequested = false;

    const generation = this.generation;
    let failed = false;

    try {
      let hasMore = true;

      while (
        hasMore &&
        !this.stopped &&
        generation === this.generation
      ) {
        const previousCursor = this.recoveryCursor;

        const page = await api.post<ChatMessagePagePublic>(
          "/chat/realtime/resume",
          {
            conversation_id: this.options.conversationId,
            cursor: previousCursor,
            limit: 100,
          },
        );

        if (
          this.stopped ||
          generation !== this.generation
        ) {
          return;
        }

        if (
          !Array.isArray(page.items) ||
          typeof page.has_more !== "boolean" ||
          (
            page.next_cursor !== null &&
            typeof page.next_cursor !== "string"
          ) ||
          page.items.some(
            (message) =>
              message.conversation_id !==
              this.options.conversationId,
          )
        ) {
          throw new Error(
            "Invalid chat recovery response.",
          );
        }

        if (
          page.has_more &&
          (
            !page.next_cursor ||
            page.next_cursor === previousCursor
          )
        ) {
          throw new Error(
            "Chat recovery cursor did not advance.",
          );
        }

        // Apply messages before advancing the watermark.
        this.options.onMessages(page.items);

        this.recoveryCursor =
          page.next_cursor ?? previousCursor;

        hasMore = page.has_more;
      }
    } catch (cause) {
      if (
        !this.stopped &&
        generation === this.generation
      ) {
        failed = true;
        this.report(cause);

        this.recoveryTimer = setTimeout(() => {
          this.recoveryTimer = null;
          this.requestRecovery();
        }, 5000);
      }
    } finally {
      this.recovering = false;

      if (
        !failed &&
        !this.stopped &&
        (
          this.recoveryRequested ||
          generation !== this.generation
        )
      ) {
        this.requestRecovery();
      }
    }
  }

  disconnect(): void {
    this.stopped = true;
    this.generation += 1;

    if (this.reconnectTimer !== null) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    this.clearRecoveryTimer();
    this.stopHeartbeat();

    const socket = this.socket;
    this.socket = null;

    if (
      socket &&
      (
        socket.readyState === WebSocket.OPEN ||
        socket.readyState === WebSocket.CONNECTING
      )
    ) {
      socket.close(1000, "client_disconnect");
    }

    this.setState("disconnected");
  }
}