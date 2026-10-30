"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";

import {
  ArrowRight,
  Bell,
  Building2,
  CalendarDays,
  CheckCheck,
  FileText,
  MessageSquare,
  Phone,
  Plus,
  RefreshCcw,
  ShieldCheck,
  Target,
  Users,
} from "lucide-react";

import { useWorkspace } from "@/contexts/workspace-context";
import { UserAvatar } from "@/components/account/user-avatar";
import { api } from "@/lib/api/client";

import {
  personalDashboardService,
  type PersonalDashboardResponse,
} from "@/services/personal-dashboard.service";

import {
  personalSocialService,
  type PersonalFriend,
} from "@/services/personal-social.service";

import type {
  AuthSessionItem,
  SessionsResponse,
} from "@/types/auth";

type Note = {
  id: string;
  title: string;
  content: string;
  plain_text?: string;
  content_format?: string;
  is_pinned: boolean;
  is_archived: boolean;
  updated_at: string;
};

type Goal = {
  id: string;
  title: string;
  status: string;
  progress_percent: number;
};

type Meeting = {
  meeting_id: string;
  title: string;
  meeting_status: string;
  participant_status: string;
  scheduled_start_at: string | null;
  scheduled_end_at: string | null;
};

type WorkspaceData = {
  id: string;
  goals: Goal[] | null;
  meetings: Meeting[] | null;
};

function errorMessage(cause: unknown): string {
  return cause instanceof Error
    ? cause.message
    : "Please try again.";
}

function formatDate(value: string): string {
  return Number.isNaN(Date.parse(value))
    ? "Date unavailable"
    : new Date(value).toLocaleString();
}

function formatTime(value: string): string {
  return new Date(value).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });
}

function Card({
  title,
  action,
  children,
}: {
  title: string;
  action?: ReactNode;
  children: ReactNode;
}) {
  return (
    <section className="ph-card">
      <header>
        <h2>{title}</h2>
        {action}
      </header>

      {children}
    </section>
  );
}

function SessionChart({
  sessions,
}: {
  sessions: AuthSessionItem[];
}) {
  const now = new Date();

  const days = Array.from({ length: 7 }, (_, index) => {
    const day = new Date(
      now.getFullYear(),
      now.getMonth(),
      now.getDate() - 6 + index,
    );

    const end = new Date(
      day.getFullYear(),
      day.getMonth(),
      day.getDate() + 1,
    );

    const count = sessions.filter((item) => {
      const timestamp = Date.parse(
        item.last_used_at || item.created_at,
      );

      return timestamp >= day.getTime()
        && timestamp < end.getTime();
    }).length;

    return {
      day,
      count,
    };
  });

  const maximum = Math.max(
    1,
    ...days.map((item) => item.count),
  );

  const points = days
    .map(
      (item, index) =>
        `${28 + index * 46},${94 - item.count / maximum * 70}`,
    )
    .join(" ");

  return (
    <figure className="ph-chart">
      <svg
        viewBox="0 0 332 125"
        role="img"
        aria-label="Active sessions grouped by last use over the last seven days"
      >
        {[0, 1, 2].map((index) => (
          <line
            key={index}
            x1="20"
            x2="320"
            y1={24 + index * 35}
            y2={24 + index * 35}
            stroke="#e8e4da"
            strokeDasharray="4 4"
          />
        ))}

        <polygon
          points={`28,94 ${points} 304,94`}
          fill="#fff3c6"
        />

        <polyline
          points={points}
          fill="none"
          stroke="#e9ae00"
          strokeWidth="2"
        />

        {days.map((item, index) => (
          <g key={index}>
            <circle
              cx={28 + index * 46}
              cy={94 - item.count / maximum * 70}
              r="3"
              fill="#ffcd3c"
              stroke="#ba8600"
            >
              <title>
                {item.count} active sessions
              </title>
            </circle>

            <text
              x={28 + index * 46}
              y="118"
              textAnchor="middle"
              fill="#64666b"
              fontSize="10"
            >
              {item.day.toLocaleDateString(undefined, {
                weekday: "short",
              })}
            </text>
          </g>
        ))}
      </svg>

      <figcaption>
        Active sessions by last use, in your local time.
      </figcaption>
    </figure>
  );
}

export default function PersonalHomePage() {
  const router = useRouter();

  const {
    user,
    workspaces,
    subscription,
    workspaceAccess,
    loading,
    error,
    switchWorkspace,
    refreshBootstrap,
  } = useWorkspace();

  const userId = user?.id;

  const [data, setData] =
    useState<PersonalDashboardResponse | null>(null);

  const [sessions, setSessions] =
    useState<AuthSessionItem[] | null>(null);

  const [friends, setFriends] =
    useState<PersonalFriend[] | null>(null);

  const [notes, setNotes] =
    useState<Note[] | null>(null);

  const [busy, setBusy] = useState(false);
  const [actionBusy, setActionBusy] = useState(false);
  const [failures, setFailures] = useState<string[]>([]);
  const [actionError, setActionError] = useState("");

  const [scope, setScope] = useState("");

  const [scoped, setScoped] =
    useState<WorkspaceData | null>(null);

  const [scopeBusy, setScopeBusy] = useState(false);
  const [scopeError, setScopeError] = useState("");

  const sequence = useRef(0);
  const scopeSequence = useRef(0);
  const actionOwner = useRef(userId);
  const actionLock = useRef(false);

  actionOwner.current = userId;

  const activeWorkspaces = workspaces.filter(
    (item) => item.membership.status === "active",
  );

  const load = useCallback(async () => {
    if (!userId) return;

    const run = ++sequence.current;

    setBusy(true);

    const results = await Promise.allSettled([
      personalDashboardService.get(),

      api.get<SessionsResponse>(
        "/auth/sessions",
      ),

      api.get<{ items: Note[] }>(
        "/notes/me",
      ),

      personalSocialService.friends(),
    ] as const);

    if (run !== sequence.current) return;

    const failed: string[] = [];

    const [
      dashboard,
      devices,
      savedNotes,
      connections,
    ] = results;

    if (dashboard.status === "fulfilled") {
      setData(dashboard.value);
    } else {
      failed.push(
        "Dashboard could not be refreshed.",
      );
    }

    if (devices.status === "fulfilled") {
      setSessions(
        devices.value.sessions.filter(
          (item) =>
            !item.revoked_at
            && Date.parse(item.expires_at) > Date.now(),
        ),
      );
    } else {
      failed.push(
        "Sessions could not be refreshed.",
      );
    }

    if (savedNotes.status === "fulfilled") {
      setNotes(
        savedNotes.value.items.filter(
          (item) => !item.is_archived,
        ),
      );
    } else {
      failed.push(
        "Notes could not be refreshed.",
      );
    }

    if (connections.status === "fulfilled") {
      setFriends(connections.value.items);
    } else {
      failed.push(
        "Friend details could not be refreshed.",
      );
    }

    setFailures(failed);
    setBusy(false);
  }, [userId]);

  useEffect(() => {
    setData(null);
    setSessions(null);
    setNotes(null);
    setFriends(null);
    setFailures([]);
    setScope("");
    setScoped(null);
    setActionError("");

    void load();

    return () => {
      sequence.current += 1;
      scopeSequence.current += 1;
    };
  }, [load]);

  useEffect(() => {
    const run = ++scopeSequence.current;

    setScoped(null);
    setScopeError("");
    setScopeBusy(Boolean(scope));

    if (!scope || !userId) return;

    void Promise.allSettled([
      api.get<{ items: Goal[] }>(
        `/workspaces/${scope}/goals/me`,
      ),

      api.get<{ invitations: Meeting[] }>(
        `/workspaces/${scope}/meetings/me/invitations`,
      ),
    ] as const).then(([goals, meetings]) => {
      if (run !== scopeSequence.current) return;

      setScoped({
        id: scope,

        goals:
          goals.status === "fulfilled"
            ? goals.value.items.filter(
                (item) =>
                  item.status === "active"
                  || item.status === "completed",
              )
            : null,

        meetings:
          meetings.status === "fulfilled"
            ? meetings.value.invitations
                .filter(
                  (item) =>
                    ["scheduled", "active"].includes(
                      item.meeting_status,
                    )
                    && item.participant_status !== "declined"
                    && (
                      !item.scheduled_end_at
                      || Date.parse(item.scheduled_end_at)
                        >= Date.now()
                    ),
                )
                .sort(
                  (a, b) =>
                    Date.parse(a.scheduled_start_at ?? "")
                    - Date.parse(b.scheduled_start_at ?? ""),
                )
            : null,
      });

      setScopeError(
        [
          goals.status === "rejected"
            ? "Goals unavailable in this workspace."
            : "",

          meetings.status === "rejected"
            ? "Meetings unavailable in this workspace."
            : "",
        ]
          .filter(Boolean)
          .join(" "),
      );

      setScopeBusy(false);
    });

    return () => {
      scopeSequence.current += 1;
    };
  }, [scope, userId]);

  async function act(
    task: () => Promise<void>,
  ): Promise<void> {
    if (actionLock.current) return;

    const owner = userId;

    actionLock.current = true;

    setActionBusy(true);
    setActionError("");

    try {
      await task();
    } catch (cause) {
      if (actionOwner.current === owner) {
        setActionError(errorMessage(cause));
      }
    } finally {
      actionLock.current = false;
      setActionBusy(false);
    }
  }

  function newNote(): void {
    const owner = userId;

    void act(async () => {
      const note = await api.post<Note>(
        "/notes/me",
        {
          title: "Untitled note",
          content: "",
        },
      );

      if (actionOwner.current !== owner) return;

      setNotes(
        (current) => [
          note,
          ...(current ?? []),
        ],
      );

      router.push(
        `/notes?note=${encodeURIComponent(note.id)}`,
      );
    });
  }

  function pin(note: Note): void {
    const owner = userId;

    void act(async () => {
      const updated = await api.patch<Note>(
        `/notes/me/${note.id}`,
        {
          is_pinned: !note.is_pinned,
        },
      );

      if (actionOwner.current === owner) {
        setNotes(
          (current) =>
            current?.map(
              (item) =>
                item.id === updated.id
                  ? updated
                  : item,
            ) ?? null,
        );
      }
    });
  }

  function openWorkspace(
    id: string,
    href?: string,
  ): void {
    const owner = userId;

    void act(async () => {
      await switchWorkspace(id);

      if (
        href
        && actionOwner.current === owner
      ) {
        router.push(href);
      }
    });
  }

  if (loading && !user) {
    return (
      <main
        className="personalHome"
        role="status"
      >
        Loading your account…
      </main>
    );
  }

  if (!user) {
    return (
      <main>
        <h1>Personal dashboard</h1>

        <p role="alert">
          {error || "Your session is unavailable."}
        </p>

        <button
          onClick={() => void refreshBootstrap()}
        >
          Retry account
        </button>

        {" "}

        <Link href="/login">
          Sign in
        </Link>
      </main>
    );
  }

  const name = user.first_name || user.username;

  const hour = new Date().getHours();

  const greeting =
    hour < 12
      ? "Good morning"
      : hour < 18
        ? "Good afternoon"
        : "Good evening";

  const number = (
    value: number | null | undefined,
  ): string =>
    value == null
      ? "—"
      : value.toLocaleString();

  const goals =
    scoped?.id === scope
      ? scoped.goals
      : null;

  const meetings =
    scoped?.id === scope
      ? scoped.meetings
      : null;

  const progress = goals?.length
    ? Math.round(
        goals.reduce(
          (sum, item) =>
            sum
            + Math.min(
              100,
              Math.max(0, item.progress_percent),
            ),
          0,
        ) / goals.length,
      )
    : null;

  const noteItems = [...(notes ?? [])].sort(
    (a, b) =>
      Number(b.is_pinned)
      - Number(a.is_pinned)
      || Date.parse(b.updated_at)
      - Date.parse(a.updated_at),
  );

  const online =
    data?.friends.filter(
      (item) => item.online,
    ) ?? [];

  const person = (id: string) =>
    friends?.find(
      (item) => item.person.id === id,
    )?.person;

  const unavailable = (
    key: string,
    empty: string,
  ) => (
    <p className="ph-empty">
      {data?.errors[key]
        || (
          busy && !data
            ? "Loading…"
            : !data
              ? "Data unavailable. Refresh to retry."
              : empty
        )}
    </p>
  );

  const workspaceHint = scopeBusy
    ? "Loading workspace details…"
    : !scope
      ? "Choose a workspace above to view your goals and meeting invitations."
      : "No items to display.";

  return (
    <main className="personalHome">
      <section className="ph-hero">
        <div className="ph-welcome">
          <div>
            <h1>
              {greeting}, {name}
            </h1>

            <p>
              Your conversations, connections and daily plans
              in one place.
            </p>

            <small>
              <CalendarDays size={14} />

              {new Date().toLocaleDateString(
                undefined,
                {
                  weekday: "long",
                  day: "numeric",
                  month: "long",
                  year: "numeric",
                },
              )}
            </small>
          </div>

          <button
            className="ph-button"
            onClick={newNote}
            disabled={actionBusy}
          >
            <Plus size={16} />
            New note
          </button>
        </div>

        <div className="ph-metrics">
          {[
            {
              title: "Friends online",
              value: data?.online_total,
              icon: <Users size={20} />,
            },
            {
              title: "Conversations",
              value: data?.conversations_total,
              icon: <MessageSquare size={20} />,
            },
            {
              title: "Upcoming meetings",
              value: meetings?.length,
              icon: <CalendarDays size={20} />,
            },
            {
              title: "Active goals",
              value: goals?.filter(
                (item) => item.status === "active",
              ).length,
              icon: <Target size={20} />,
            },
          ].map((item) => (
            <div
              className="ph-metric"
              key={item.title}
            >
              <span className="ph-icon">
                {item.icon}
              </span>

              <div>
                <span>{item.title}</span>
                <strong>{number(item.value)}</strong>
              </div>
            </div>
          ))}
        </div>

        <div className="ph-gauge">
          <svg
            viewBox="0 0 200 160"
            aria-hidden="true"
          >
            <path
              d="M 35 135 A 75 75 0 1 1 165 135"
              pathLength="100"
              fill="none"
              stroke="#fff"
              strokeWidth="11"
              strokeLinecap="round"
            />

            <path
              d="M 35 135 A 75 75 0 1 1 165 135"
              pathLength="100"
              fill="none"
              stroke="#ffca36"
              strokeWidth="11"
              strokeLinecap="round"
              strokeDasharray={`${progress ?? 0} 100`}
            />
          </svg>

          <div>
            <strong>
              {progress === null
                ? "—"
                : `${progress}%`}
            </strong>

            <span>My goals progress</span>

            <small>
              {scope
                ? "Selected workspace"
                : "Choose a workspace"}
            </small>
          </div>
        </div>
      </section>

      <div className="ph-toolbar">
        <label>
          Goals & meetings

          <select
            value={scope}
            onChange={(event) =>
              setScope(event.target.value)
            }
          >
            <option value="">
              Choose workspace
            </option>

            {activeWorkspaces
              .filter(
                (item) =>
                  item.workspace.is_active
                  && item.workspace.status === "ready",
              )
              .map((item) => (
                <option
                  key={item.workspace.id}
                  value={item.workspace.id}
                >
                  {item.workspace.name}
                </option>
              ))}
          </select>
        </label>

        <button
          className="ph-link"
          disabled={busy}
          onClick={() => void load()}
        >
          <RefreshCcw size={13} />

          {busy
            ? "Refreshing…"
            : "Refresh dashboard"}
        </button>
      </div>

      {[
        error,
        ...failures,
        scopeError,
        actionError,
      ].filter(Boolean).length > 0 && (
        <div
          className="ph-notice"
          role="alert"
        >
          {[
            error,
            ...failures,
            scopeError,
            actionError,
          ]
            .filter(Boolean)
            .map((item, index) => (
              <p key={index}>{item}</p>
            ))}

          {error && (
            <button
              onClick={() => void refreshBootstrap()}
            >
              Retry account details
            </button>
          )}
        </div>
      )}

      <div className="ph-grid">
        <Card
          title="Recent conversations"
          action={
            <Link href="/chat">
              View all
              <ArrowRight size={12} />
            </Link>
          }
        >
          {!data?.conversations.length
          || data.errors.conversations ? (
            unavailable(
              "conversations",
              "No conversations yet.",
            )
          ) : (
            <ul className="ph-list">
              {data.conversations
                .slice(0, 3)
                .map((item) => (
                  <li key={item.id}>
                    <Link
                      className="ph-row"
                      href={`/chat?conversation=${encodeURIComponent(item.id)}`}
                    >
                      <span className="ph-avatar">
                        {item.kind === "group"
                          ? <Users size={21} />
                          : item.name
                              .slice(0, 2)
                              .toUpperCase()}
                      </span>

                      <span className="ph-grow">
                        <strong>{item.name}</strong>

                        <small>
                          {item.kind === "group"
                            ? "Group conversation"
                            : "Direct conversation"}
                        </small>
                      </span>

                      <time
                        dateTime={item.updated_at}
                      >
                        {formatTime(item.updated_at)}
                      </time>
                    </Link>
                  </li>
                ))}
            </ul>
          )}

          <div className="ph-friends">
            <small>
              Friends online ({number(data?.online_total)})
            </small>

            <div>
              <span className="ph-avatarStrip">
                {online.slice(0, 5).map((item) => (
                  <span
                    title={item.name}
                    key={item.user_id}
                  >
                    <UserAvatar
                      userId={item.user_id}
                      src={person(item.user_id)?.avatar_url}
                      name={item.name}
                      size={30}
                    />
                  </span>
                ))}

                {!online.length && (
                  <small>No friends online</small>
                )}
              </span>

              <Link
                className="ph-button"
                href="/friends"
              >
                <Plus size={13} />
                Add friend
              </Link>
            </div>
          </div>
        </Card>

        <Card
          title="My activity"
          action={
            <Link href="/settings/security">
              Devices
              <ArrowRight size={12} />
            </Link>
          }
        >
          {sessions ? (
            <SessionChart sessions={sessions} />
          ) : (
            <p className="ph-empty">
              {busy
                ? "Loading sessions…"
                : "Sessions unavailable. Refresh to retry."}
            </p>
          )}

          <div className="ph-stats">
            {[
              {
                label: "Conversations",
                value: data?.conversations_total,
                icon: <MessageSquare size={16} />,
              },
              {
                label: "Calls",
                value: data?.calls_total,
                icon: <Phone size={16} />,
              },
              {
                label: "Notes",
                value: notes?.length,
                icon: <FileText size={16} />,
              },
            ].map((item) => (
              <div key={item.label}>
                {item.icon}
                <small>{item.label}</small>
                <strong>{number(item.value)}</strong>
              </div>
            ))}
          </div>
        </Card>

        <Card
          title="Upcoming meetings"
          action={
            scope && (
              <button
                className="ph-link"
                disabled={actionBusy}
                onClick={() =>
                  openWorkspace(scope, "/meetings")
                }
              >
                View all
                <ArrowRight size={12} />
              </button>
            )
          }
        >
          {meetings?.length ? (
            meetings.slice(0, 2).map((item) => (
              <div
                className="ph-meeting"
                key={item.meeting_id}
              >
                <div className="ph-date">
                  <small>
                    {item.scheduled_start_at
                      ? new Date(
                          item.scheduled_start_at,
                        ).toLocaleDateString(
                          undefined,
                          { month: "short" },
                        )
                      : "DATE"}
                  </small>

                  <strong>
                    {item.scheduled_start_at
                      ? new Date(
                          item.scheduled_start_at,
                        ).getDate()
                      : "—"}
                  </strong>
                </div>

                <div className="ph-grow">
                  <strong>{item.title}</strong>

                  <small>
                    {item.scheduled_start_at
                      ? formatDate(item.scheduled_start_at)
                      : "Time not set"}
                  </small>

                  <small>
                    {item.participant_status}
                  </small>
                </div>

                <button
                  className="ph-button"
                  disabled={actionBusy}
                  onClick={() =>
                    openWorkspace(
                      scope,
                      `/meetings?meeting=${encodeURIComponent(item.meeting_id)}`,
                    )
                  }
                >
                  Open
                </button>
              </div>
            ))
          ) : (
            <p className="ph-empty">
              {meetings
                ? "No upcoming meeting invitations."
                : workspaceHint}
            </p>
          )}
        </Card>

        <Card
          title="Recent calls"
          action={
            <Link href="/calls">
              View all
              <ArrowRight size={12} />
            </Link>
          }
        >
          {!data?.calls.length
          || data.errors.calls ? (
            unavailable("calls", "No calls yet.")
          ) : (
            <ul className="ph-list">
              {data.calls.slice(0, 3).map((item) => (
                <li key={item.id}>
                  <Link
                    className="ph-row"
                    href="/calls"
                  >
                    <span className="ph-avatar">
                      <Phone size={18} />
                    </span>

                    <span className="ph-grow">
                      <strong>
                        {data.conversations.find(
                          (conversation) =>
                            conversation.id
                            === item.conversation_id,
                        )?.name
                          || (
                            item.kind === "VIDEO"
                              ? "Video call"
                              : "Voice call"
                          )}
                      </strong>

                      <small>
                        {item.status
                          .toLowerCase()
                          .replaceAll("_", " ")}
                      </small>
                    </span>

                    <time dateTime={item.created_at}>
                      {formatDate(item.created_at)}
                    </time>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </Card>

        <Card
          title="My goals"
          action={
            scope && (
              <button
                className="ph-link"
                disabled={actionBusy}
                onClick={() =>
                  openWorkspace(scope, "/goals")
                }
              >
                View all
                <ArrowRight size={12} />
              </button>
            )
          }
        >
          {goals?.length ? (
            goals.slice(0, 3).map((item) => (
              <button
                className="ph-goal"
                key={item.id}
                disabled={actionBusy}
                onClick={() =>
                  openWorkspace(scope, "/goals")
                }
              >
                <span className="ph-avatar">
                  <Target size={20} />
                </span>

                <span className="ph-grow">
                  <span>
                    <strong>{item.title}</strong>

                    <small>
                      {Math.round(item.progress_percent)}%
                    </small>
                  </span>

                  <progress
                    max="100"
                    value={item.progress_percent}
                    aria-label={`${item.title} progress`}
                  />
                </span>
              </button>
            ))
          ) : (
            <p className="ph-empty">
              {goals
                ? "No goals in this workspace yet."
                : workspaceHint}
            </p>
          )}
        </Card>

        <Card
          title="My notes"
          action={
            <Link href="/notes">
              View all
              <ArrowRight size={12} />
            </Link>
          }
        >
          {notes === null ? (
            <p className="ph-empty">
              {busy
                ? "Loading notes…"
                : "Notes unavailable. Refresh to retry."}
            </p>
          ) : !notes.length ? (
            <button
              className="ph-button"
              onClick={newNote}
              disabled={actionBusy}
            >
              <Plus size={14} />
              Create your first note
            </button>
          ) : (
            noteItems.slice(0, 2).map((item) => (
              <div
                className="ph-note"
                key={item.id}
              >
                <FileText size={17} />

                <Link
                  className="ph-grow"
                  href={`/notes?note=${encodeURIComponent(item.id)}`}
                >
                  <strong>
                    {item.title || "Untitled note"}
                    {item.is_pinned ? " · Pinned" : ""}
                  </strong>

                  <p>
                    {item.plain_text
                      || (
                        item.content_format === "rich"
                          ? "Open note to read"
                          : item.content
                      )
                      || "Empty note"}
                  </p>

                  <time dateTime={item.updated_at}>
                    {formatDate(item.updated_at)}
                  </time>
                </Link>

                <button
                  className="ph-link"
                  disabled={actionBusy}
                  onClick={() => pin(item)}
                >
                  {item.is_pinned ? "Unpin" : "Pin"}
                </button>
              </div>
            ))
          )}
        </Card>

        <Card
          title="Workspace shortcuts"
          action={
            <Link href="/billing">
              View plans
              <ArrowRight size={12} />
            </Link>
          }
        >
          {activeWorkspaces.length ? (
            activeWorkspaces.slice(0, 3).map((item) => (
              <button
                className="ph-workspace"
                key={item.workspace.id}
                disabled={
                  actionBusy
                  || !item.workspace.is_active
                  || item.workspace.status !== "ready"
                }
                onClick={() =>
                  openWorkspace(item.workspace.id)
                }
              >
                <Building2 size={17} />

                <span className="ph-grow">
                  <strong>
                    {item.workspace.name}
                  </strong>

                  <small>
                    {item.membership.role_key}
                    {" · "}
                    {item.workspace.status}
                  </small>
                </span>

                <ArrowRight size={14} />
              </button>
            ))
          ) : (
            <p className="ph-empty">
              No active workspace memberships.
            </p>
          )}

          <Link
            className="ph-button"
            href={
              workspaceAccess?.allowed
                ? "/workspaces/new"
                : "/billing"
            }
          >
            <Plus size={14} />

            {workspaceAccess?.allowed
              ? "Create workspace"
              : "Workspace options"}
          </Link>
        </Card>

        <Card title="Personal shortcuts">
          <Link
            className="ph-shortcut"
            href="/notes"
          >
            <FileText size={19} />

            <span>
              <strong>Organize my notes</strong>
              <small>Open notes and checklists</small>
            </span>

            <ArrowRight size={14} />
          </Link>

          <Link
            className="ph-shortcut"
            href="/friends"
          >
            <Users size={19} />

            <span>
              <strong>Grow my connections</strong>
              <small>
                Find friends and review requests
              </small>
            </span>

            <ArrowRight size={14} />
          </Link>

          <Link
            className="ph-shortcut"
            href="/settings/security"
          >
            <ShieldCheck size={19} />

            <span>
              <strong>Review account security</strong>
              <small>Manage active devices</small>
            </span>

            <ArrowRight size={14} />
          </Link>
        </Card>

        <Card
          title="Notifications"
          action={<Bell size={15} />}
        >
          <Link
            className="ph-shortcut"
            href="/friends"
          >
            <Users size={18} />

            <span>
              <strong>Friend requests</strong>

              <small>
                {number(data?.incoming_requests)}
                {" incoming requests"}
              </small>
            </span>

            <ArrowRight size={14} />
          </Link>

          <Link
            className="ph-shortcut"
            href="/settings"
          >
            <ShieldCheck size={18} />

            <span>
              <strong>Email verification</strong>

              <small>
                {user.is_email_verified
                  ? "Your email is verified"
                  : "Verify your email in settings"}
              </small>
            </span>
          </Link>

          {meetings?.[0] && (
            <button
              className="ph-shortcut"
              disabled={actionBusy}
              onClick={() =>
                openWorkspace(scope, "/meetings")
              }
            >
              <CalendarDays size={18} />

              <span>
                <strong>
                  {meetings[0].title}
                </strong>

                <small>
                  {meetings[0].scheduled_start_at
                    ? formatDate(
                        meetings[0].scheduled_start_at,
                      )
                    : "Upcoming meeting"}
                </small>
              </span>
            </button>
          )}
        </Card>
      </div>

      <footer className="ph-footer">
        <div>
          <ShieldCheck size={20} />

          <span>
            <small>Account status</small>

            <strong>
              {user.is_locked
                ? "Locked"
                : user.is_active
                  ? "Active"
                  : "Inactive"}

              {" · "}

              {subscription?.plan_code || "Plan unavailable"}
            </strong>
          </span>

          <Link href="/billing">
            Manage
          </Link>
        </div>

        <div>
          <CheckCheck size={20} />

          <span>
            <small>
              {user.is_email_verified
                ? "Email verified"
                : "Email unverified"}
            </small>

            <strong>{user.email}</strong>
          </span>
        </div>

        <div>
          <Users size={20} />

          <span>
            <small>Total friends</small>
            <strong>{number(data?.friends_total)}</strong>
          </span>
        </div>

        <div>
          <ShieldCheck size={20} />

          <span>
            <small>Active sessions</small>
            <strong>{number(sessions?.length)}</strong>
          </span>

          <Link href="/settings/security">
            Review
          </Link>
        </div>
      </footer>

      <details className="ph-account">
        <summary>
          Account and session details
        </summary>

        <p>
          Joined {formatDate(user.created_at)}.
          {" "}

          {workspaceAccess?.reason
            || (
              workspaceAccess?.allowed
                ? "You can create a workspace."
                : "View plans for workspace options."
            )}
        </p>

        {sessions?.map((item) => (
          <p key={item.id}>
            {item.device_name || "Signed-in session"}
            {" · Last used "}
            {formatDate(
              item.last_used_at || item.created_at,
            )}
          </p>
        ))}

        <Link href="/settings">
          Manage profile
        </Link>
      </details>

      {data && (
        <p className="ph-updated">
          Updated {formatDate(data.generated_at)}
        </p>
      )}

      <style jsx global>{`
        .personalHome {
          max-width: 1500px;
          margin: 0 auto;
          color: #171c24;
          font-size: 13px;
        }

        .personalHome * {
          box-sizing: border-box;
        }

        .personalHome h1,
        .personalHome h2,
        .personalHome p {
          margin: 0;
        }

        .personalHome h1 {
          font-size: clamp(23px, 2.3vw, 32px);
          font-weight: 650;
          letter-spacing: -.035em;
        }

        .personalHome h2 {
          font-size: 15px;
          letter-spacing: -.015em;
        }

        .personalHome a {
          color: inherit;
          text-decoration: none;
        }

        .personalHome button,
        .personalHome select {
          font: inherit;
          color: inherit;
        }

        .personalHome button {
          cursor: pointer;
        }

        .personalHome button:disabled {
          opacity: .55;
          cursor: default;
        }

        .personalHome button:focus-visible,
        .personalHome a:focus-visible,
        .personalHome select:focus-visible {
          outline: 2px solid #8f6a00;
          outline-offset: 3px;
        }

        .personalHome small,
        .personalHome time {
          font-size: 11px;
          color: #697280;
        }

        .personalHome strong {
          font-size: 12px;
          font-weight: 600;
          overflow-wrap: anywhere;
        }

        .personalHome .ph-hero {
          display: grid;
          grid-template-columns: minmax(0, 1fr) 230px;
          gap: 18px 26px;
          padding: 22px;
          border: 1px solid #ece7dc;
          border-radius: 10px;
          background:
            radial-gradient(
              ellipse at 97% 72%,
              #fff1c9,
              transparent 48%
            ),
            #fcfbf6;
        }

        .personalHome .ph-welcome {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          gap: 15px;
        }

        .personalHome .ph-welcome p {
          margin: 5px 0 10px;
          color: #697280;
          font-size: 14px;
        }

        .personalHome .ph-welcome small {
          display: flex;
          align-items: center;
          gap: 7px;
        }

        .personalHome .ph-button {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          gap: 7px;
          padding: 9px 12px;
          border: 1px solid #e9dfc7;
          border-radius: 7px;
          background: #fffaea;
          white-space: nowrap;
          font-size: 11px;
        }

        .personalHome .ph-button:hover {
          background: #fff0bd;
        }

        .personalHome .ph-metrics {
          grid-column: 1;
          display: grid;
          grid-template-columns: repeat(4, minmax(0, 1fr));
          gap: 10px;
        }

        .personalHome .ph-metric {
          display: flex;
          align-items: center;
          gap: 10px;
          min-width: 0;
          border: 1px solid #eee9df;
          border-radius: 8px;
          padding: 13px 11px;
          background: #ffffffd9;
        }

        .personalHome .ph-metric span:not(.ph-icon) {
          font-size: 11px;
          color: #596272;
        }

        .personalHome .ph-metric strong {
          display: block;
          font-size: 23px;
          font-weight: 550;
          margin-top: 5px;
        }

        .personalHome .ph-icon {
          flex-shrink: 0;
          display: grid;
          place-items: center;
          height: 39px;
          width: 39px;
          border-radius: 50%;
          background: #fff9e8;
          color: #b87b00;
        }

        .personalHome .ph-gauge {
          grid-column: 2;
          grid-row: 1 / 3;
          position: relative;
          align-self: center;
        }

        .personalHome .ph-gauge svg {
          width: 100%;
          display: block;
        }

        .personalHome .ph-gauge div {
          position: absolute;
          top: 47%;
          left: 0;
          width: 100%;
          text-align: center;
        }

        .personalHome .ph-gauge strong {
          font-size: 28px;
          font-weight: 550;
        }

        .personalHome .ph-gauge span,
        .personalHome .ph-gauge small {
          display: block;
          margin-top: 4px;
          font-size: 11px;
        }

        .personalHome .ph-toolbar {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 12px;
          margin: 12px 0;
        }

        .personalHome .ph-toolbar label {
          display: flex;
          gap: 8px;
          align-items: center;
          font-size: 11px;
          color: #626976;
        }

        .personalHome select {
          padding: 6px 8px;
          border: 1px solid #e7e1d5;
          border-radius: 6px;
          background: #fffdf8;
          max-width: 220px;
        }

        .personalHome .ph-link {
          display: inline-flex;
          align-items: center;
          gap: 5px;
          border: 0;
          padding: 3px 0;
          background: transparent;
          font-size: 11px;
        }

        .personalHome .ph-notice {
          padding: 12px;
          border: 1px solid #e8c887;
          border-radius: 7px;
          background: #fff8e8;
          margin-bottom: 12px;
        }

        .personalHome .ph-notice p + p {
          margin-top: 5px;
        }

        .personalHome .ph-grid {
          display: grid;
          grid-template-columns: 1.15fr 1fr 1fr;
          gap: 12px;
        }

        .personalHome .ph-card {
          min-width: 0;
          padding: 15px;
          border: 1px solid #eae6dc;
          border-radius: 9px;
          background: #fffefa;
        }

        .personalHome .ph-card > header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 8px;
          margin-bottom: 12px;
        }

        .personalHome .ph-card > header a {
          display: inline-flex;
          align-items: center;
          gap: 5px;
          font-size: 10px;
        }

        .personalHome .ph-list {
          padding: 0;
          margin: 0;
          list-style: none;
        }

        .personalHome .ph-list li + li {
          border-top: 1px solid #f1eee7;
        }

        .personalHome .ph-row {
          display: flex;
          align-items: center;
          gap: 10px;
          padding: 9px 0;
        }

        .personalHome .ph-avatar {
          display: grid;
          place-items: center;
          flex-shrink: 0;
          width: 36px;
          height: 36px;
          border-radius: 50%;
          background: #f0efeb;
          font-size: 12px;
        }

        .personalHome .ph-grow {
          flex: 1;
          min-width: 0;
        }

        .personalHome .ph-grow strong,
        .personalHome .ph-grow small {
          display: block;
        }

        .personalHome .ph-grow small {
          margin-top: 4px;
          line-height: 1.4;
        }

        .personalHome .ph-row time {
          max-width: 95px;
          text-align: right;
          font-size: 10px;
        }

        .personalHome .ph-friends {
          margin-top: 8px;
          padding-top: 9px;
          border-top: 1px solid #f0ede6;
        }

        .personalHome .ph-friends > div {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 8px;
          margin-top: 8px;
        }

        .personalHome .ph-avatarStrip {
          display: flex;
          align-items: center;
          gap: 4px;
        }

        .personalHome .ph-chart {
          margin: 0;
        }

        .personalHome .ph-chart svg {
          width: 100%;
          display: block;
        }

        .personalHome .ph-chart figcaption {
          color: #737985;
          font-size: 9px;
          margin: 3px 0 10px;
        }

        .personalHome .ph-stats {
          display: grid;
          grid-template-columns: repeat(3, minmax(0, 1fr));
          gap: 8px;
        }

        .personalHome .ph-stats > div {
          padding: 10px;
          border: 1px solid #eee8dc;
          border-radius: 7px;
        }

        .personalHome .ph-stats svg {
          color: #bd8500;
        }

        .personalHome .ph-stats small {
          display: block;
          font-size: 9px;
          margin: 5px 0;
        }

        .personalHome .ph-stats strong {
          font-size: 21px;
          font-weight: 550;
        }

        .personalHome .ph-empty {
          padding: 15px 0;
          color: #78808c;
          font-size: 12px;
          line-height: 1.7;
        }

        .personalHome .ph-meeting {
          display: flex;
          gap: 10px;
          align-items: center;
          padding: 12px 0;
        }

        .personalHome .ph-meeting + .ph-meeting {
          border-top: 1px solid #eeeae2;
        }

        .personalHome .ph-date {
          flex-shrink: 0;
          padding: 10px 8px;
          min-width: 44px;
          text-align: center;
          border: 1px solid #f1e8cb;
          border-radius: 7px;
          background: #fff9e8;
        }

        .personalHome .ph-date strong {
          display: block;
          font-size: 21px;
          margin-top: 5px;
        }

        .personalHome .ph-goal {
          display: flex;
          width: 100%;
          gap: 10px;
          align-items: center;
          padding: 10px 0;
          background: transparent;
          border: 0;
          text-align: left;
        }

        .personalHome .ph-goal .ph-grow > span {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 8px;
        }

        .personalHome progress {
          appearance: none;
          display: block;
          width: 100%;
          height: 7px;
          margin-top: 7px;
          border: 0;
          border-radius: 10px;
          overflow: hidden;
          background: #efeeea;
        }

        .personalHome progress::-webkit-progress-bar {
          background: #efeeea;
        }

        .personalHome progress::-webkit-progress-value {
          background: #ffcd3f;
          border-radius: 10px;
        }

        .personalHome progress::-moz-progress-bar {
          background: #ffcd3f;
          border-radius: 10px;
        }

        .personalHome .ph-note {
          display: flex;
          align-items: flex-start;
          gap: 9px;
          border: 1px solid #eee7db;
          border-radius: 7px;
          padding: 10px;
          margin-top: 7px;
        }

        .personalHome .ph-note > svg {
          color: #c98f00;
          flex-shrink: 0;
        }

        .personalHome .ph-note p {
          font-size: 11px;
          color: #697280;
          line-height: 1.4;
          margin: 4px 0;
          display: -webkit-box;
          -webkit-line-clamp: 2;
          -webkit-box-orient: vertical;
          overflow: hidden;
          overflow-wrap: anywhere;
        }

        .personalHome .ph-note time {
          font-size: 10px;
        }

        .personalHome .ph-workspace,
        .personalHome .ph-shortcut {
          display: flex;
          width: 100%;
          align-items: center;
          gap: 9px;
          padding: 9px 0;
          background: transparent;
          border: 0;
          text-align: left;
        }

        .personalHome .ph-workspace + .ph-button {
          margin-top: 8px;
        }

        .personalHome .ph-shortcut > span {
          flex: 1;
          min-width: 0;
        }

        .personalHome .ph-shortcut strong,
        .personalHome .ph-shortcut small {
          display: block;
        }

        .personalHome .ph-shortcut small {
          margin-top: 4px;
        }

        .personalHome .ph-shortcut > svg:first-child {
          color: #a47b0d;
          flex-shrink: 0;
        }

        .personalHome .ph-footer {
          display: grid;
          grid-template-columns: repeat(4, minmax(0, 1fr));
          border: 1px solid #eae6dc;
          border-radius: 9px;
          margin-top: 12px;
          background: #fffefa;
        }

        .personalHome .ph-footer > div {
          display: flex;
          align-items: center;
          gap: 9px;
          padding: 12px;
          min-width: 0;
        }

        .personalHome .ph-footer > div + div {
          border-left: 1px solid #eae6dc;
        }

        .personalHome .ph-footer span {
          min-width: 0;
          flex: 1;
        }

        .personalHome .ph-footer small,
        .personalHome .ph-footer strong {
          display: block;
          font-size: 10px;
          overflow-wrap: anywhere;
        }

        .personalHome .ph-footer strong {
          margin-top: 4px;
        }

        .personalHome .ph-footer a {
          font-size: 10px;
        }

        .personalHome .ph-account {
          margin-top: 14px;
          font-size: 11px;
          color: #697280;
        }

        .personalHome .ph-account summary {
          cursor: pointer;
        }

        .personalHome .ph-account p {
          margin: 7px 0;
        }

        .personalHome .ph-updated {
          margin-top: 10px;
          font-size: 10px;
          color: #78808c;
        }

        @media (max-width: 1200px) {
          .personalHome .ph-hero {
            grid-template-columns: minmax(0, 1fr) 175px;
            padding: 18px;
            gap: 16px;
          }

          .personalHome .ph-icon {
            width: 30px;
            height: 30px;
          }

          .personalHome .ph-metric {
            padding: 10px 8px;
            gap: 7px;
          }

          .personalHome .ph-grid {
            grid-template-columns: repeat(2, minmax(0, 1fr));
          }
        }

        @media (max-width: 760px) {
          .personalHome .ph-hero {
            grid-template-columns: 1fr;
          }

          .personalHome .ph-gauge {
            display: none;
          }

          .personalHome .ph-metrics {
            grid-template-columns: repeat(2, minmax(0, 1fr));
          }

          .personalHome .ph-grid {
            grid-template-columns: 1fr;
          }

          .personalHome .ph-footer {
            grid-template-columns: repeat(2, minmax(0, 1fr));
          }

          .personalHome .ph-footer > div + div {
            border-left: 0;
          }

          .personalHome .ph-toolbar {
            flex-wrap: wrap;
          }

          .personalHome h1 {
            font-size: 23px;
          }

          .personalHome .ph-welcome {
            flex-wrap: wrap;
          }
        }
      `}</style>
    </main>
  );
}