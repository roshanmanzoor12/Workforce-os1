"use client";

import {
  useCallback,
  useEffect,
  useId,
  useRef,
  useState,
} from "react";
import { X } from "lucide-react";

import { api } from "@/lib/api/client";
import { chatFeaturesService } from "@/services/chat-features.service";

type ReactionPerson = {
  user_id: string;
  emoji: string;
  mine: boolean;
  name?: string | null;
  username?: string | null;
  avatar_url?: string | null;
};

type ReactionPeople = {
  message_id: string;
  counts: Record<string, number>;
  items: ReactionPerson[];
};

type Props = {
  conversationId: string;
  messageId: string;
  currentUserId: string;
  initialEmoji: string;
  initialCounts: Record<string, number>;
  onCountsChange: (counts: Record<string, number>) => void;
  onClose: () => void;
};

function errorText(cause: unknown): string {
  return cause instanceof Error
    ? cause.message
    : "Unable to load reactions.";
}

function initials(value: string): string {
  return value
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part.charAt(0))
    .join("")
    .toUpperCase() || "?";
}

export function MessageReactionDialog({
  conversationId,
  messageId,
  currentUserId,
  initialEmoji,
  initialCounts,
  onCountsChange,
  onClose,
}: Props) {
  const titleId = useId();
  const dialogRef = useRef<HTMLDialogElement>(null);
  const aliveRef = useRef(false);
  const requestRef = useRef(0);
  const removingRef = useRef(false);
  const countsCallbackRef = useRef(onCountsChange);

  const [people, setPeople] = useState<ReactionPeople | null>(null);
  const [tab, setTab] = useState(initialEmoji);
  const [loading, setLoading] = useState(true);
  const [removing, setRemoving] = useState<string | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    countsCallbackRef.current = onCountsChange;
  }, [onCountsChange]);

  const loadPeople = useCallback(async (): Promise<void> => {
    const request = ++requestRef.current;

    if (aliveRef.current) {
      setLoading(true);
      setError("");
    }

    try {
      const result = await api.get<ReactionPeople>(
        `/chat/${encodeURIComponent(conversationId)}` +
          `/messages/${encodeURIComponent(messageId)}/reactions`,
      );

      if (
        !aliveRef.current ||
        request !== requestRef.current
      ) {
        return;
      }

      setPeople(result);
      setTab((current) =>
        current === "all" || result.counts[current]
          ? current
          : "all",
      );
      countsCallbackRef.current(result.counts);
    } catch (cause) {
      if (
        aliveRef.current &&
        request === requestRef.current
      ) {
        setError(errorText(cause));
      }
    } finally {
      if (
        aliveRef.current &&
        request === requestRef.current
      ) {
        setLoading(false);
      }
    }
  }, [conversationId, messageId]);

  useEffect(() => {
    aliveRef.current = true;

    const dialog = dialogRef.current;

    if (dialog && !dialog.open) {
      dialog.showModal();
    }

    void loadPeople();

    return () => {
      aliveRef.current = false;
      requestRef.current += 1;

      if (dialog?.open) {
        dialog.close();
      }
    };
  }, [loadPeople]);

  async function removeOwnReaction(
    person: ReactionPerson,
  ): Promise<void> {
    if (
      !person.mine ||
      person.user_id !== currentUserId ||
      removingRef.current
    ) {
      return;
    }

    removingRef.current = true;
    requestRef.current += 1;
    setRemoving(person.emoji);
    setError("");

    try {
      await chatFeaturesService.removeReaction(
        conversationId,
        messageId,
        person.emoji,
      );

      if (!aliveRef.current) {
        return;
      }

      await loadPeople();
    } catch (cause) {
      if (aliveRef.current) {
        setError(errorText(cause));
      }
    } finally {
      removingRef.current = false;

      if (aliveRef.current) {
        setRemoving(null);
      }
    }
  }

  const counts = people?.counts ?? initialCounts;
  const visiblePeople = (people?.items ?? []).filter(
    (person) => tab === "all" || person.emoji === tab,
  );

  return (
    <dialog
      ref={dialogRef}
      className="mrDialog"
      aria-labelledby={titleId}
      onCancel={(event) => {
        event.preventDefault();

        if (!removingRef.current) {
          onClose();
        }
      }}
      onClick={(event) => {
        if (
          event.target === event.currentTarget &&
          !removingRef.current
        ) {
          onClose();
        }
      }}
    >
      <header className="mrHeader">
        <h2 id={titleId}>Reactions</h2>

        <button
          type="button"
          className="mrClose"
          aria-label="Close reactions"
          disabled={removing !== null}
          onClick={onClose}
        >
          <X size={18} />
        </button>
      </header>

      <section aria-busy={loading}>
        <div className="mrTabs" aria-label="Filter reactions">
          <button
            type="button"
            aria-pressed={tab === "all"}
            onClick={() => setTab("all")}
          >
            All{" "}
            {people
              ? people.items.length
              : Object.values(counts).reduce(
                  (total, count) => total + count,
                  0,
                )}
          </button>

          {Object.entries(counts)
            .filter(([, count]) => count > 0)
            .map(([emoji, count]) => (
              <button
                type="button"
                key={emoji}
                aria-pressed={tab === emoji}
                onClick={() => setTab(emoji)}
              >
                {emoji} {count}
              </button>
            ))}
        </div>

        {error && (
          <p className="mrError" role="alert">
            {error}{" "}
            <button
              type="button"
              disabled={removing !== null}
              onClick={() => void loadPeople()}
            >
              Retry
            </button>
          </p>
        )}

        {loading && !people ? (
          <p className="mrNote">Loading reactions…</p>
        ) : (
          <div className="mrPeople" aria-live="polite">
            {visiblePeople.map((person) => {
              const own =
                person.mine &&
                person.user_id === currentUserId;
              const name =
                person.name || person.username || "Member";

              const content = (
                <>
                  <span className="mrAvatar">
                    {person.avatar_url ? (
                      <img
                        src={person.avatar_url}
                        alt=""
                        onError={(event) => {
                          event.currentTarget.hidden = true;
                        }}
                      />
                    ) : null}
                    <span aria-hidden="true">{initials(name)}</span>
                  </span>

                  <span className="mrPersonCopy">
                    <strong>{own ? "You" : name}</strong>
                    <small>
                      {own
                        ? removing === person.emoji
                          ? "Removing…"
                          : "Click to remove"
                        : person.username
                          ? `@${person.username.replace(/^@/, "")}`
                          : "Reacted to this message"}
                    </small>
                  </span>

                  <span className="mrPersonEmoji">
                    {person.emoji}
                  </span>
                </>
              );

              return own ? (
                <button
                  type="button"
                  className="mrPerson"
                  key={`${person.user_id}:${person.emoji}`}
                  disabled={removing !== null}
                  onClick={() => void removeOwnReaction(person)}
                >
                  {content}
                </button>
              ) : (
                <div
                  className="mrPerson"
                  key={`${person.user_id}:${person.emoji}`}
                >
                  {content}
                </div>
              );
            })}

            {people && people.items.length === 0 && (
              <p className="mrNote">No reactions yet.</p>
            )}
          </div>
        )}
      </section>

      <style jsx>{`
        .mrDialog {
          box-sizing: border-box;
          width: 460px;
          max-width: calc(100vw - 32px);
          max-height: calc(100dvh - 40px);
          margin: auto;
          padding: 20px;
          overflow: auto;
          border: 1px solid #e8dfcd;
          border-radius: 18px;
          background: #fffdf7;
          color: #292b2e;
          font: inherit;
          box-shadow: 0 24px 70px rgba(30, 25, 15, 0.22);
        }

        .mrDialog::backdrop {
          background: rgba(30, 28, 23, 0.38);
        }

        .mrHeader {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 16px;
          margin-bottom: 20px;
        }

        .mrHeader h2 {
          margin: 0;
          font-size: 18px;
          font-weight: 600;
        }

        .mrClose {
          display: grid;
          place-items: center;
          width: 32px;
          height: 32px;
          padding: 0;
          border: 1px solid #e9e2d4;
          border-radius: 9px;
          background: transparent;
          color: inherit;
          cursor: pointer;
        }

        .mrTabs {
          display: flex;
          flex-wrap: wrap;
          gap: 6px;
          padding-bottom: 12px;
          border-bottom: 1px solid #e9e2d4;
        }

        .mrTabs button {
          min-height: 34px;
          padding: 5px 12px;
          border: 1px solid #e5dcc8;
          border-radius: 999px;
          background: transparent;
          color: #403a30;
          font: inherit;
          font-size: 13px;
          cursor: pointer;
        }

        .mrTabs button[aria-pressed="true"] {
          background: #fff0bc;
          border-color: #d7b647;
        }

        .mrPeople {
          padding-top: 4px;
        }

        .mrPerson {
          box-sizing: border-box;
          display: flex;
          align-items: center;
          gap: 12px;
          width: 100%;
          padding: 12px 0;
          border: 0;
          border-bottom: 1px solid #eee7d9;
          border-radius: 0;
          background: transparent;
          color: #292b2e;
          font: inherit;
          text-align: left;
        }

        button.mrPerson {
          cursor: pointer;
        }

        button.mrPerson:hover:not(:disabled) {
          background: #faf4e6;
        }

        .mrAvatar {
          position: relative;
          display: grid;
          place-items: center;
          flex: 0 0 40px;
          width: 40px;
          height: 40px;
          overflow: hidden;
          border-radius: 50%;
          background: #ebe5da;
          color: #514b42;
          font-size: 13px;
          font-weight: 600;
        }

        .mrAvatar img {
          position: absolute;
          inset: 0;
          z-index: 1;
          width: 100%;
          height: 100%;
          object-fit: cover;
        }

        .mrPersonCopy {
          flex: 1;
          min-width: 0;
          overflow-wrap: anywhere;
        }

        .mrPersonCopy strong {
          display: block;
          margin-bottom: 3px;
          font-size: 13px;
          font-weight: 600;
        }

        .mrPersonCopy small {
          color: #686258;
          font-size: 11px;
        }

        .mrPersonEmoji {
          flex-shrink: 0;
          font-size: 25px;
        }

        .mrNote,
        .mrError {
          margin: 14px 0 0;
          font-size: 12px;
        }

        .mrNote {
          color: #686258;
        }

        .mrError {
          color: #a33232;
        }

        .mrError button {
          color: inherit;
          cursor: pointer;
        }

        button:disabled {
          opacity: 0.55;
          cursor: default;
        }

        button:focus-visible {
          outline: 2px solid #a77500;
          outline-offset: 2px;
        }

        @media (max-width: 640px) {
          .mrTabs button {
            min-height: 40px;
          }

          .mrPerson {
            min-height: 64px;
          }
        }
      `}</style>
    </dialog>
  );
}