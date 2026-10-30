
"use client";

import {
  useEffect,
  useRef,
  useState,
} from "react";

import { UserAvatar } from "@/components/account/user-avatar";
import { api } from "@/lib/api/client";
import { personalSocialService } from "@/services/personal-social.service";

type Person = {
  user_id: string;
  name: string;
  username?: string | null;
  avatar_url?: string | null;
  calling_number?: string;
};

type Context = {
  conversation_type: string;
  members: Person[];
};

type Call = {
  participants: {
    user_id: string;
    state: string;
  }[];
};

export function DirectCallInvite({
  callId,
  userId,
  hideTrigger = false,
}: {
  callId: string;
  userId: string;
  hideTrigger?: boolean;
}) {
  const [open, setOpen] = useState(false);
  const [kind, setKind] = useState("");
  const [friends, setFriends] = useState<Person[]>([]);
  const [states, setStates] = useState<Record<string, string>>({});
  const [query, setQuery] = useState("");
  const [found, setFound] = useState<Person | null>(null);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const owner = useRef(callId);
  const lock = useRef(false);

  owner.current = callId;

  useEffect(() => {
    let stopped = false;

    setKind("");
    setOpen(false);
    setError("");
    setFriends([]);
    setFound(null);
    setStates({});

    void api.get<Context>(
      `/calls/${callId}/context`,
    ).then(result => {
      if (!stopped) {
        setKind(result.conversation_type);
      }
    }).catch(() => undefined);

    const show = (event: Event) => {
      if (
        (event as CustomEvent<string>).detail === callId
      ) {
        setOpen(true);
      }
    };

    window.addEventListener(
      "workforce:open-call-invite",
      show,
    );

    return () => {
      stopped = true;

      window.removeEventListener(
        "workforce:open-call-invite",
        show,
      );
    };
  }, [callId]);

  useEffect(() => {
    if (!open || kind !== "direct") return;

    let stopped = false;

    setLoading(true);
    setError("");

    void Promise.all([
      personalSocialService.friends(),
      api.get<Call>(`/calls/${callId}`),
    ]).then(([response, call]) => {
      if (stopped) return;

      setFriends(
        response.items
          .filter(
            item =>
              String(item.status).toLowerCase() === "accepted"
              && !item.blocked_by_me,
          )
          .map(item => ({
            user_id: item.person.id,
            name: item.person.name,
            username: item.person.username,
            avatar_url: item.person.avatar_url,
          })),
      );

      setStates(
        Object.fromEntries(
          call.participants.map(
            item => [item.user_id, item.state],
          ),
        ),
      );
    }).catch(cause => {
      if (!stopped) {
        setError(
          cause instanceof Error
            ? cause.message
            : "Unable to load friends.",
        );
      }
    }).finally(() => {
      if (!stopped) setLoading(false);
    });

    return () => {
      stopped = true;
    };
  }, [open, kind, callId]);

  useEffect(() => {
    if (!open || kind !== "direct") return;

    let stopped = false;

    const timer = setInterval(() => {
      void api.get<Call>(
        `/calls/${callId}`,
      ).then(call => {
        if (!stopped) {
          setStates(
            Object.fromEntries(
              call.participants.map(
                item => [item.user_id, item.state],
              ),
            ),
          );
        }
      }).catch(() => undefined);
    }, 3000);

    return () => {
      stopped = true;
      clearInterval(timer);
    };
  }, [open, kind, callId]);

  useEffect(() => {
    setFound(null);

    if (
      !open
      || kind !== "direct"
      || !/^\d{10}$/.test(query.trim())
    ) {
      return;
    }

    let stopped = false;

    const timer = setTimeout(() => {
      void api.get<Person>(
        `/calls/numbers/lookup?number=${encodeURIComponent(query.trim())}`,
      ).then(person => {
        if (!stopped) setFound(person);
      }).catch(cause => {
        if (!stopped) {
          setError(
            cause instanceof Error
              ? cause.message
              : "Number not found.",
          );
        }
      });
    }, 250);

    return () => {
      stopped = true;
      clearTimeout(timer);
    };
  }, [open, kind, query]);

  async function invite(person: Person) {
    if (lock.current) return;

    const id = callId;

    lock.current = true;

    setBusy(person.user_id);
    setError("");

    try {
      await api.post(
        `/calls/${id}/participants/invite`,
        {
          user_ids: [person.user_id],
        },
      );

      if (owner.current === id) {
        setStates(current => ({
          ...current,
          [person.user_id]: "INVITED",
        }));
      }
    } catch (cause) {
      if (owner.current === id) {
        setError(
          cause instanceof Error
            ? cause.message
            : "Invitation failed.",
        );
      }
    } finally {
      lock.current = false;

      if (owner.current === id) {
        setBusy("");
      }
    }
  }

  if (kind !== "direct") return null;

  const term = query.trim().toLowerCase();

  const people = found
    ? [found]
    : friends.filter(
        person =>
          `${person.name} ${person.username || ""}`
            .toLowerCase()
            .includes(term),
      );

  return (
    <div className="directInvite">
      {!hideTrigger && (
<button
        type="button"
        className="inviteToggle"
        onClick={() => setOpen(value => !value)}
        aria-expanded={open}
      >
        ＋ Add user
      </button>
      )}

      {open && (
        <section aria-label="Invite a friend to this call">
          <header>
            <strong>Add to this call</strong>

            <button
              type="button"
              onClick={() => setOpen(false)}
              aria-label="Close invitations"
            >
              ×
            </button>
          </header>

          <input
            aria-label="Search friends or calling number"
            placeholder="Search friends or enter 10-digit calling number"
            value={query}
            onChange={event => {
              setQuery(event.target.value);
              setError("");
            }}
          />

          <small>
            Added users join this call. Your direct chat stays private.
            Invitations require an accepted friendship.
          </small>

          {loading && (
            <p role="status">
              Loading friends…
            </p>
          )}

          <div className="inviteList">
            {people
              .filter(person => person.user_id !== userId)
              .map(person => {
                const existing = [
                  "JOINED",
                  "INVITED",
                ].includes(
                  states[person.user_id] || "",
                );

                return (
                  <div
                    className="inviteRow"
                    key={person.user_id}
                  >
                    <UserAvatar
                      userId={person.user_id}
                      src={person.avatar_url}
                      name={person.name}
                      size={34}
                    />

                    <span>
                      <strong>{person.name}</strong>

                      <small>
                        {person.username
                          ? `@${person.username}`
                          : person.calling_number}
                      </small>
                    </span>

                    <button
                      type="button"
                      disabled={Boolean(busy) || existing}
                      onClick={() => void invite(person)}
                    >
                      {states[person.user_id] === "JOINED"
                        ? "Joined"
                        : existing
                          ? "Invited"
                          : busy === person.user_id
                            ? "Inviting…"
                            : "Invite"}
                    </button>
                  </div>
                );
              })}
          </div>

          {!loading && !people.length && (
            <p>
              No matching friends. You can also enter a calling number.
            </p>
          )}

          {error && (
            <p role="alert">{error}</p>
          )}
        </section>
      )}

      <style jsx>{`
        .directInvite {
          margin: 10px 0;
          text-align: left;
          font-size: 12px;
          color: #252627;
        }

        button {
          padding: 7px 10px;
          border: 1px solid #e0c474;
          border-radius: 7px;
          background: #ffdc64;
          color: #252627;
          cursor: pointer;
          font: inherit;
        }

        button:disabled {
          opacity: .6;
          cursor: default;
        }

        section {
          padding: 12px;
          margin-top: 8px;
          background: #fffdf5;
          border: 1px solid #dfd4b9;
          border-radius: 10px;
        }

        header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 8px;
        }

        input {
          box-sizing: border-box;
          width: 100%;
          padding: 9px;
          border: 1px solid #d9d1be;
          border-radius: 7px;
          background: white;
          color: #252627;
          font: inherit;
        }

        small {
          display: block;
          margin-top: 5px;
          font-size: 10px;
          color: #6b6558;
          line-height: 1.5;
        }

        .inviteList {
          max-height: 210px;
          overflow: auto;
        }

        .inviteRow {
          display: flex;
          align-items: center;
          gap: 9px;
          padding: 9px 0;
          border-bottom: 1px solid #eee7d7;
        }

        .inviteRow > span {
          flex: 1;
          min-width: 0;
          overflow-wrap: anywhere;
        }

        p {
          font-size: 11px;
          line-height: 1.5;
        }

        p[role=alert] {
          color: #a83232;
        }
      `}</style>
    </div>
  );
}
