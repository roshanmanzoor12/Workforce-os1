"use client";
import { UserAvatar } from "@/components/account/user-avatar";
import { CallRingtone } from "./call-ringtone";

import { useEffect, useRef, useState } from "react";

import { useWorkspace } from "@/contexts/workspace-context";
import { api } from "@/lib/api/client";
import { groupsService } from "@/services/groups.service";
import type { GroupCall } from "@/services/groups.service";
import { chatFeaturesService } from "@/services/chat-features.service";
import { ConversationCallPanel } from "./conversation-call-panel";

type IncomingCall = GroupCall & {
  conversation_name: string;
  caller_name: string;
  caller_username: string | null;
  caller_avatar_url: string | null;
  invitation_expires_at?: string;
  can_reply?: boolean;
};

function Invitation({
  call,
  busy,
  onAnswer,
  onDecline,
}: {
  call: IncomingCall;
  busy: boolean;
  onAnswer: () => void;
  onDecline: (message?: string) => void;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  const [reply, setReply] = useState("Catch you later.");

  useEffect(() => {
    const dialog = ref.current;
    if (dialog && !dialog.open) dialog.showModal();

    return () => {
      if (dialog?.open) dialog.close();
    };
  }, []);

  return (
    <dialog
      ref={ref}
      className="icDialog"
      aria-labelledby="incoming-call-title"
      onCancel={(event) => {
        event.preventDefault();
        if (!busy) onDecline();
      }}
    >
      <CallRingtone
        callId={call.id}
        mode="incoming"
        expiresAt={call.invitation_expires_at}
      />

      <h2 id="incoming-call-title">
        Incoming {call.kind === "VIDEO" ? "video" : "voice"} call
      </h2>

      <div
        style={{
          display: "flex",
          justifyContent: "center",
          marginBottom: 12,
        }}
      >
        <UserAvatar
          userId={call.started_by_user_id}
          src={call.caller_avatar_url}
          name={call.caller_name}
          size={76}
        />
      </div>

      <strong>{call.caller_name}</strong>

      {call.caller_username && (
        <p>@{call.caller_username}</p>
      )}

      <p>{call.conversation_name}</p>

      <div className="icActions">
        <button type="button" disabled={busy} onClick={onAnswer}>
          Answer
        </button>

        <button
          type="button"
          disabled={busy}
          onClick={() => onDecline()}
        >
          Decline
        </button>
      </div>

      <label>
        Quick reply
        <select
          value={reply}
          disabled={busy || !call.can_reply}
          onChange={(event) => setReply(event.target.value)}
        >
          <option>Catch you later.</option>
          <option>I will call you back.</option>
          <option>I cannot talk right now.</option>
        </select>
      </label>

      <button
        type="button"
        disabled={busy}
        onClick={() => onDecline(call.can_reply ? reply : undefined)}
      >
        Decline and send reply
      </button>

      <style jsx>{`
        .icDialog {
          box-sizing: border-box;
          width: 380px;
          max-width: calc(100vw - 32px);
          max-height: calc(100dvh - 32px);
          margin: auto;
          padding: 24px;
          overflow: auto;
          border: 1px solid #e5ddcd;
          border-radius: 18px;
          background: #fffdf7;
          color: #25282c;
          font: inherit;
          text-align: center;
          box-shadow: 0 20px 70px rgba(0, 0, 0, 0.2);
        }

        .icDialog::backdrop {
          background: rgba(0, 0, 0, 0.4);
        }

        h2 {
          margin: 0 0 20px;
          font-size: 18px;
        }

        img {
          display: block;
          width: 76px;
          height: 76px;
          margin: 0 auto 12px;
          border-radius: 50%;
          object-fit: cover;
        }

        strong {
          display: block;
        }

        p {
          color: #686258;
          font-size: 13px;
        }

        .icActions {
          display: flex;
          justify-content: center;
          gap: 10px;
          margin: 20px 0;
        }

        button,
        select {
          min-height: 38px;
          padding: 8px 12px;
          border: 1px solid #ddd3bf;
          border-radius: 8px;
          background: #fff;
          color: inherit;
          font: inherit;
          font-size: 13px;
        }

        button {
          cursor: pointer;
        }

        .icActions button:first-child {
          border-color: #246b42;
          background: #246b42;
          color: #fff;
        }

        label,
        select {
          display: block;
          width: 100%;
          box-sizing: border-box;
        }

        label {
          margin-bottom: 12px;
          font-size: 12px;
          text-align: left;
        }

        select {
          margin-top: 6px;
        }

        button:disabled {
          opacity: 0.5;
          cursor: default;
        }
      `}</style>
    </dialog>
  );
}

export function IncomingCallHost() {
  const { user } = useWorkspace();

  return user?.is_email_verified ? (
    <IncomingCalls
      key={user.id}
      userId={user.id}
    />
  ) : null;
}

function IncomingCalls({ userId }: { userId: string }) {
  const [incoming, setIncoming] = useState<IncomingCall | null>(null);
  const [accepted, setAccepted] = useState<IncomingCall | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const acceptedRef = useRef<IncomingCall | null>(null);
  const busyRef = useRef(false);
  const aliveRef = useRef(false);

  useEffect(() => {
    aliveRef.current = true;

    let timer: ReturnType<typeof setTimeout> | undefined;
    let disposed = false;

    async function check(): Promise<void> {
      try {
        const response = await api.get<{
          items: IncomingCall[];
        }>("/calls/active");

        if (disposed || busyRef.current) return;

        const callPanelOpen =
          document.querySelector(
            "dialog.wcDialog[open], main.pc-page",
          ) !== null;

        const next =
          acceptedRef.current || callPanelOpen
            ? null
            : response.items.find(
                (call) =>
                  call.started_by_user_id !== userId &&
                  call.participants.some(
                    (participant) =>
                      participant.user_id === userId &&
                      participant.state === "INVITED",
                  ),
              ) ?? null;

        setIncoming((current) =>
          next,
        );
      } catch (cause) {
        if (!disposed) {
          setError(
            cause instanceof Error
              ? cause.message
              : "Incoming call check failed.",
          );
        }
      } finally {
        if (!disposed) {
          timer = setTimeout(() => void check(), 2000);
        }
      }
    }

    void check();

    return () => {
      aliveRef.current = false;
      disposed = true;
      if (timer) clearTimeout(timer);
    };
  }, [userId]);

  async function decline(message?: string): Promise<void> {
    const call = incoming;
    if (!call || busyRef.current) return;

    busyRef.current = true;
    setBusy(true);
    setError("");

    let declined = false;

    try {
      await groupsService.declineCall(call.id);
      declined = true;

      if (aliveRef.current) {
        setIncoming(null);
      }

      if (message && call.conversation_id) {
        await chatFeaturesService.sendMessage(
          call.conversation_id,
          message,
          {
            clientMessageId: crypto.randomUUID(),
          },
        );
      }
    } catch (cause) {
      if (aliveRef.current) {
        const detail = cause instanceof Error
          ? cause.message
          : "Please retry.";

        setError(
          declined
            ? `Call declined, but the reply was not confirmed: ${detail}`
            : detail,
        );
      }
    } finally {
      busyRef.current = false;

      if (aliveRef.current) setBusy(false);
    }
  }

  return (
    <>
      {error && (
        <div
          role="alert"
          style={{
            position: "fixed",
            bottom: 20,
            right: 20,
            zIndex: 10001,
            maxWidth: 360,
            padding: 12,
            borderRadius: 10,
            background: "#fff0ea",
            color: "#8d3027",
          }}
        >
          {error}
          <button
            type="button"
            onClick={() => setError("")}
            style={{ marginLeft: 10 }}
          >
            Dismiss
          </button>
        </div>
      )}

      {incoming && !accepted && (
        <Invitation
          key={incoming.id}
          call={incoming}
          busy={busy}
          onAnswer={() => {
            acceptedRef.current = incoming;
            setAccepted(incoming);
            setIncoming(null);
          }}
          onDecline={(message) => void decline(message)}
        />
      )}

      {accepted?.conversation_id && (
        <ConversationCallPanel
          key={accepted.id}
          conversationId={accepted.conversation_id}
          conversationName={accepted.conversation_name}
          currentUserId={userId}
          initialKind={accepted.kind}
          existingCallId={accepted.id}
          onClose={() => {
            acceptedRef.current = null;
            setAccepted(null);
          }}
        />
      )}
    </>
  );
}