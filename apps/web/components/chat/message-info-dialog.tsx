
"use client";

import {
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";
import { X } from "lucide-react";
import { UserAvatar } from "@/components/account/user-avatar";
import { socialChatService } from "@/services/social-chat.service";
import { CHAT_LIVE_EVENT } from "@/lib/chat-live-events";
import type {
  ChatMessagePublic,
  MessageReceiptPublic,
} from "@/types/social-chat";

type Person = {
  id: string;
  name: string;
  username: string;
  avatar_url: string | null;
};

export function MessageInfoDialog({
  message,
  userId,
  members,
  onClose,
}: {
  message: ChatMessagePublic;
  userId: string;
  members: Person[];
  onClose: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const generation = useRef(0);
  const [receipts, setReceipts] = useState<
    MessageReceiptPublic[]
  >([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    const version = ++generation.current;

    setLoading(true);
    setError("");

    try {
      const items =
        await socialChatService.listReadReceipts(
          message.conversation_id,
          message.id,
        );

      if (version === generation.current) {
        setReceipts(
          items.filter(
            item => item.user_id !== userId,
          ),
        );
      }
    } catch (cause) {
      if (version === generation.current) {
        setError(
          cause instanceof Error
            ? cause.message
            : "Could not load readers.",
        );
      }
    } finally {
      if (version === generation.current) {
        setLoading(false);
      }
    }
  }, [
    message.conversation_id,
    message.id,
    userId,
  ]);

  useEffect(() => {
    if (message.sender_user_id !== userId) return;

    dialog.current?.showModal();
    void load();

    function changed(event: Event) {
      const detail = (event as CustomEvent).detail;
      const frame = detail.event;

      if (
        detail.owner === userId &&
        (
          frame.conversation_id ??
          frame.data?.conversation_id
        ) === message.conversation_id &&
        String(
          frame.event_type ?? frame.event,
        ).includes("read")
      ) {
        void load();
      }
    }

    window.addEventListener(
      CHAT_LIVE_EVENT,
      changed,
    );

    return () => {
      generation.current += 1;
      window.removeEventListener(
        CHAT_LIVE_EVENT,
        changed,
      );
    };
  }, [
    message.conversation_id,
    message.sender_user_id,
    userId,
    load,
  ]);

  if (message.sender_user_id !== userId) {
    return null;
  }

  return (
    <dialog
      ref={dialog}
      className="messageInfoDialog"
      aria-labelledby="message-info-title"
      onCancel={event => {
        event.preventDefault();
        onClose();
      }}
    >
      <header>
        <h2 id="message-info-title">
          Message info
        </h2>
        <button
          type="button"
          aria-label="Close message info"
          onClick={onClose}
        >
          <X size={18} />
        </button>
      </header>

      <p className="preview">
        {message.content || "Attachment"}
      </p>

      <header>
        <h3>Read by</h3>
        <button
          type="button"
          disabled={loading}
          onClick={() => void load()}
        >
          Refresh
        </button>
      </header>

      {loading && (
        <p role="status">Loading readers…</p>
      )}
      {error && <p role="alert">{error}</p>}
      {!loading &&
        !error &&
        receipts.length === 0 && (
          <p>No read receipts yet.</p>
        )}

      <ul>
        {receipts.map(receipt => {
          const person = members.find(
            item => item.id === receipt.user_id,
          );

          return (
            <li key={receipt.user_id}>
              <UserAvatar
                userId={receipt.user_id}
                src={person?.avatar_url}
                name={
                  person?.name ||
                  person?.username ||
                  "Member"
                }
              />
              <div>
                <strong>
                  {person?.name ||
                    person?.username ||
                    "Member"}
                </strong>
                {person?.username && (
                  <small>@{person.username}</small>
                )}
                <time dateTime={receipt.read_at}>
                  {new Date(
                    receipt.read_at,
                  ).toLocaleString()}
                </time>
              </div>
            </li>
          );
        })}
      </ul>

      <style jsx>{`
        dialog {
          width: 380px;
          max-width: calc(100vw - 32px);
          max-height: 80dvh;
          overflow: auto;
          padding: 20px;
          border: 1px solid #e7dfca;
          border-radius: 14px;
          background: #fffdf7;
          color: #252627;
          outline: none;
        }
        dialog::backdrop {
          background: rgba(0, 0, 0, 0.35);
        }
        header,
        li {
          display: flex;
          align-items: center;
          gap: 12px;
        }
        header {
          justify-content: space-between;
        }
        h2 { font-size: 17px; }
        h3 { font-size: 14px; }
        p,
        li { font-size: 12px; }
        .preview {
          padding: 12px;
          border-radius: 8px;
          background: #fff3c5;
          overflow-wrap: anywhere;
        }
        ul {
          padding: 0;
          list-style: none;
        }
        li { padding: 10px 0; }
        small,
        time {
          display: block;
          margin-top: 3px;
          color: #655b40;
          font-size: 11px;
        }
        button {
          padding: 6px;
          border: 0;
          border-radius: 6px;
          background: transparent;
          color: inherit;
          cursor: pointer;
        }
        button:hover,
        button:focus-visible {
          background: #ffe69a;
          outline: none;
        }
      `}</style>
    </dialog>
  );
}
