"use client";

import {
  useEffect,
  useRef,
  useState,
} from "react";

import type {
  FormEvent,
} from "react";

import Link from "next/link";

import {
  ArrowUpRight,
  CalendarDays,
  Check,
  ChevronDown,
  ChevronRight,
  ClipboardList,
  Copy,
  Database,
  ExternalLink,
  FileText,
  ListTodo,
  LockKeyhole,
  MessageCircle,
  MessageSquare,
  MoreHorizontal,
  NotebookPen,
  Paperclip,
  Plus,
  Search,
  Send,
  Settings,
  ShieldCheck,
  SlidersHorizontal,
  Sparkles,
  SquareCheck,
  Target,
  ThumbsDown,
  ThumbsUp,
  Trash2,
  UserRound,
  X,
} from "lucide-react";

import type {
  LucideIcon,
} from "lucide-react";


type Tab =
  | "Overview"
  | "Chat"
  | "History"
  | "Memory"
  | "Settings";

type SourceKey =
  | "notes"
  | "goals"
  | "calendar"
  | "tasks"
  | "conversations";

type ResponseStyle =
  | "Concise"
  | "Balanced"
  | "Detailed";

type Feedback =
  | "up"
  | "down";

type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  text: string;
  time: string;
  plan?: boolean;
  draft?: boolean;
};

type Chat = {
  id: string;
  title: string;
  subtitle: string;
  date: string;
  sample: boolean;
  messages: ChatMessage[];
};

type AttachedDocument = {
  id: string;
  name: string;
};

type MemoryItem = {
  id: string;
  text: string;
};

type SourceDefinition = {
  key: SourceKey;
  label: string;
  icon: LucideIcon;
};

type QuickAction = {
  title: string;
  description: string;
  prompt: string;
  icon: LucideIcon;
};

type IconButtonProps = {
  label: string;
  onClick: () => void;
  children: React.ReactNode;
  expanded?: boolean;
};


const TABS: Tab[] = [
  "Overview",
  "Chat",
  "History",
  "Memory",
  "Settings",
];

const SOURCE_DEFINITIONS: SourceDefinition[] = [
  {
    key: "notes",
    label: "Notes",
    icon: NotebookPen,
  },
  {
    key: "goals",
    label: "Goals",
    icon: Target,
  },
  {
    key: "calendar",
    label: "Calendar",
    icon: CalendarDays,
  },
  {
    key: "tasks",
    label: "Tasks",
    icon: SquareCheck,
  },
];

const QUICK_ACTIONS: QuickAction[] = [
  {
    title: "Summarize notes",
    description: "Get key points from your notes",
    prompt: "Summarize my learning notes into clear key points.",
    icon: NotebookPen,
  },
  {
    title: "Plan my goals",
    description: "Break goals into actionable steps",
    prompt: "Help me break down my next goal into actionable steps.",
    icon: Target,
  },
  {
    title: "Review a document",
    description: "Get a summary and key insights",
    prompt: "Review my attached document and summarize the key insights.",
    icon: FileText,
  },
  {
    title: "Organize tasks",
    description: "Turn ideas into a clear task list",
    prompt: "Help me organize my ideas into a clear task list.",
    icon: ListTodo,
  },
];

const WEEK_PLAN = [
  {
    day: "Monday",
    title: "Complete Python practice",
    description:
      "Build on your learning notes and complete one practice project.",
  },
  {
    day: "Wednesday",
    title: "Review portfolio ideas",
    description:
      "Go through your notes, choose top 3 ideas and outline next steps.",
  },
  {
    day: "Friday",
    title: "Prepare your launch checklist",
    description:
      "Pull together your notes and create a final checklist.",
  },
];

const PLAN_TEXT = [
  "Here is a focused plan for your week.",
  "",
  "Based on your notes and goals, here are the three key priorities for this week that will move you forward while keeping a realistic balance.",
  "",
  ...WEEK_PLAN.map(
    (item) =>
      `${item.day}: ${item.title}\n${item.description}`,
  ),
  "",
  "Suggested next step",
  "Start with one task today, then review your progress on Friday.",
].join("\n");

const INITIAL_CHATS: Chat[] = [
  {
    id: "sample-week",
    title: "Plan my week",
    subtitle: "Help me plan this week using my ...",
    date: "10:24",
    sample: true,
    messages: [
      {
        id: "sample-week-user",
        role: "user",
        text: "Help me plan this week using my notes and goals.",
        time: "10:24",
      },
      {
        id: "sample-week-assistant",
        role: "assistant",
        text: PLAN_TEXT,
        time: "10:24",
        plan: true,
      },
    ],
  },
  {
    id: "sample-notes",
    title: "Summarize learning notes",
    subtitle: "Key takeaways from my notes",
    date: "Yesterday",
    sample: true,
    messages: [
      {
        id: "sample-notes-user",
        role: "user",
        text: "Summarize my learning notes.",
        time: "09:15",
      },
    ],
  },
  {
    id: "sample-goal",
    title: "Break down my next goal",
    subtitle: "Turn my goal into smaller steps",
    date: "10 Nov",
    sample: true,
    messages: [
      {
        id: "sample-goal-user",
        role: "user",
        text: "Help me turn my next goal into smaller steps.",
        time: "14:30",
      },
    ],
  },
  {
    id: "sample-document",
    title: "Review a document",
    subtitle: "Summarize this document for me",
    date: "8 Nov",
    sample: true,
    messages: [
      {
        id: "sample-document-user",
        role: "user",
        text: "Summarize this document for me.",
        time: "11:20",
      },
    ],
  },
];


function makeId() {
  return crypto.randomUUID();
}

function currentTime() {
  return new Intl.DateTimeFormat(undefined, {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).format(new Date());
}

function IconButton({
  label,
  onClick,
  children,
  expanded,
}: IconButtonProps) {
  return (
    <button
      type="button"
      className="pai-icon-button"
      aria-label={label}
      aria-expanded={expanded}
      title={label}
      onClick={onClick}
    >
      {children}
    </button>
  );
}

function Toggle({
  label,
  checked,
  onChange,
}: {
  label: string;
  checked: boolean;
  onChange: () => void;
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-label={label}
      aria-checked={checked}
      className={`pai-toggle ${checked ? "is-on" : ""}`}
      onClick={onChange}
    >
      <span />
    </button>
  );
}


export default function PersonalAIPage() {
  const [tab, setTab] = useState<Tab>("Chat");

  const [chats, setChats] =
    useState<Chat[]>(INITIAL_CHATS);

  const [activeChatId, setActiveChatId] =
    useState("sample-week");

  const [search, setSearch] = useState("");

  const [draft, setDraft] = useState("");

  const [notice, setNotice] = useState("");

  const [sources, setSources] = useState<
    Record<SourceKey, boolean>
  >({
    notes: true,
    goals: true,
    calendar: false,
    tasks: false,
    conversations: false,
  });

  const [documents, setDocuments] =
    useState<AttachedDocument[]>([]);

  const [memoryEnabled, setMemoryEnabled] =
    useState(true);

  const [memories, setMemories] =
    useState<MemoryItem[]>([
      {
        id: "sample-memory",
        text: "Prefer short, practical plans",
      },
    ]);

  const [newMemory, setNewMemory] =
    useState("");

  const [responseStyle, setResponseStyle] =
    useState<ResponseStyle>("Concise");

  const [openMenu, setOpenMenu] =
    useState<string | null>(null);

  const [feedback, setFeedback] = useState<
    Record<string, Feedback>
  >({});

  const fileInputRef =
    useRef<HTMLInputElement>(null);

  const composerRef =
    useRef<HTMLTextAreaElement>(null);

  const messagesEndRef =
    useRef<HTMLDivElement>(null);

  const activeChat =
    chats.find(
      (chat) => chat.id === activeChatId,
    ) ?? null;

  const visibleChats = chats.filter(
    (chat) =>
      `${chat.title} ${chat.subtitle}`
        .toLowerCase()
        .includes(search.toLowerCase().trim()),
  );

  const sourceCount =
    Object.values(sources).filter(Boolean).length +
    documents.length;

  const draftCount = chats.reduce(
    (total, chat) =>
      total +
      chat.messages.filter(
        (message) => message.draft,
      ).length,
    0,
  );


  useEffect(() => {
    if (!openMenu) {
      return;
    }

    function closeMenu(event: MouseEvent) {
      const target = event.target;

      if (
        target instanceof Element &&
        target.closest(".pai-menu-anchor")
      ) {
        return;
      }

      setOpenMenu(null);
    }

    function handleKey(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setOpenMenu(null);
      }
    }

    document.addEventListener("click", closeMenu);
    document.addEventListener("keydown", handleKey);

    return () => {
      document.removeEventListener(
        "click",
        closeMenu,
      );

      document.removeEventListener(
        "keydown",
        handleKey,
      );
    };
  }, [openMenu]);


  useEffect(() => {
    if (
      activeChat?.messages.some(
        (message) => message.draft,
      )
    ) {
      messagesEndRef.current?.scrollIntoView({
        block: "nearest",
      });
    }
  }, [
    activeChatId,
    activeChat?.messages.length,
  ]);


  function changeTab(nextTab: Tab) {
    setTab(nextTab);
    setOpenMenu(null);
    setNotice("");
  }

  function toggleSource(key: SourceKey) {
    setSources((current) => ({
      ...current,
      [key]: !current[key],
    }));
  }

  function startChat() {
    const id = makeId();

    const chat: Chat = {
      id,
      title: "New chat",
      subtitle: "Draft a new conversation",
      date: currentTime(),
      sample: false,
      messages: [],
    };

    setChats((current) => [
      chat,
      ...current,
    ]);

    setActiveChatId(id);
    setDraft("");
    setTab("Chat");
    setNotice("");
    setOpenMenu(null);
  }

  function openChat(id: string) {
    setActiveChatId(id);
    setTab("Chat");
    setDraft("");
    setNotice("");
    setOpenMenu(null);
  }

  function deleteChat(id: string) {
    const remaining = chats.filter(
      (chat) => chat.id !== id,
    );

    setChats(remaining);

    if (activeChatId === id) {
      setActiveChatId(
        remaining[0]?.id ?? "",
      );

      setDraft("");
    }

    setOpenMenu(null);
  }

  function useQuickAction(action: QuickAction) {
    setTab("Chat");
    setDraft(action.prompt);
    setNotice("");

    requestAnimationFrame(() => {
      composerRef.current?.focus();
    });
  }

  function saveDraft(event: FormEvent) {
    event.preventDefault();

    const text = draft.trim();

    if (!text) {
      return;
    }

    const time = currentTime();

    const message: ChatMessage = {
      id: makeId(),
      role: "user",
      text,
      time,
      draft: true,
    };

    if (activeChat) {
      setChats((current) =>
        current.map((chat) => {
          if (chat.id !== activeChat.id) {
            return chat;
          }

          return {
            ...chat,
            title:
              chat.title === "New chat"
                ? text.slice(0, 36)
                : chat.title,
            subtitle: text,
            date: time,
            messages: [
              ...chat.messages,
              message,
            ],
          };
        }),
      );
    } else {
      const id = makeId();

      setChats((current) => [
        {
          id,
          title: text.slice(0, 36),
          subtitle: text,
          date: time,
          sample: false,
          messages: [message],
        },
        ...current,
      ]);

      setActiveChatId(id);
    }

    setDraft("");

    setNotice(
      "Draft saved in this page only. It has not been sent to an AI service.",
    );
  }

  async function copyMessage(text: string) {
    try {
      await navigator.clipboard.writeText(text);

      setNotice("Response copied.");
    } catch {
      setNotice(
        "Copy was unavailable. Select the response text and copy it manually.",
      );
    }
  }

  function setMessageFeedback(
    messageId: string,
    value: Feedback,
  ) {
    setFeedback((current) => {
      const next = {
        ...current,
      };

      if (next[messageId] === value) {
        delete next[messageId];
      } else {
        next[messageId] = value;
      }

      return next;
    });
  }

  function addMemory(event: FormEvent) {
    event.preventDefault();

    const text = newMemory.trim();

    if (!text) {
      return;
    }

    setMemories((current) => [
      ...current,
      {
        id: makeId(),
        text,
      },
    ]);

    setNewMemory("");
  }

  function backendRequired(action: string) {
    setNotice(
      `${action} needs the Personal AI backend connection. Nothing has been submitted.`,
    );

    setOpenMenu(null);
  }


  function renderSources() {
    return (
      <>
        <div className="pai-source-list">
          {SOURCE_DEFINITIONS.map(
            ({
              key,
              label,
              icon: Icon,
            }) => (
              <div
                className="pai-source-row"
                key={key}
              >
                <Icon size={20} />

                <span>{label}</span>

                <Toggle
                  label={`Include ${label.toLowerCase()} in the context selection`}
                  checked={sources[key]}
                  onChange={() =>
                    toggleSource(key)
                  }
                />
              </div>
            ),
          )}

          <div className="pai-source-row">
            <FileText size={20} />

            <span>Documents</span>

            <button
              type="button"
              className="pai-button pai-button-small"
              onClick={() =>
                fileInputRef.current?.click()
              }
            >
              <Plus size={12} />
              Add document
            </button>
          </div>
        </div>

        {documents.length > 0 ? (
          <div className="pai-documents">
            {documents.map((document) => (
              <div
                className="pai-document"
                key={document.id}
              >
                <FileText size={14} />

                <span title={document.name}>
                  {document.name}
                </span>

                <IconButton
                  label={`Remove ${document.name}`}
                  onClick={() =>
                    setDocuments((current) =>
                      current.filter(
                        (item) =>
                          item.id !== document.id,
                      ),
                    )
                  }
                >
                  <X size={13} />
                </IconButton>
              </div>
            ))}

            <p className="pai-helper">
              Selected locally. Files have not been
              uploaded or analyzed.
            </p>
          </div>
        ) : null}

        <div className="pai-source-detail">
          <LockKeyhole size={20} />

          <div>
            <strong>Conversations</strong>

            <p>
              Allow access to selected conversations
            </p>
          </div>

          <Toggle
            label="Include conversations in the context selection"
            checked={sources.conversations}
            onChange={() =>
              toggleSource("conversations")
            }
          />
        </div>

        <div className="pai-source-detail pai-workspace-source">
          <Database size={20} />

          <div>
            <strong>Workspace data</strong>

            <p>
              Not connected to your workspace data
            </p>
          </div>

          <span
            className="pai-toggle is-unavailable"
            role="img"
            aria-label="Workspace data is not connected"
            title="Workspace data is not connected"
          >
            <span />
          </span>

          <button
            type="button"
            className="pai-button pai-workspace-button"
            onClick={() =>
              backendRequired(
                "Opening Workspace AI",
              )
            }
          >
            <ExternalLink size={14} />
            Open Workspace AI
          </button>
        </div>
      </>
    );
  }


  function renderResponse(
    message: ChatMessage,
  ) {
    return (
      <div
        className="pai-assistant-row"
        key={message.id}
      >
        <span className="pai-ai-avatar">
          <Sparkles size={22} />
        </span>

        <div className="pai-assistant-content">
          <article className="pai-response">
            {message.plan ? (
              <>
                <h3>
                  Here is a focused plan for your week.
                </h3>

                <p className="pai-response-intro">
                  Based on your notes and goals, here
                  are the three key priorities for
                  this week that will move you forward
                  while keeping a realistic balance.
                </p>

                <div className="pai-week-plan">
                  {WEEK_PLAN.map((item) => (
                    <div
                      className="pai-plan-row"
                      key={item.day}
                    >
                      <div className="pai-plan-day">
                        {item.day}
                      </div>

                      <div className="pai-plan-description">
                        <strong>
                          {item.title}
                        </strong>

                        <p>
                          {item.description}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="pai-next-step">
                  <h4>
                    Suggested next step
                  </h4>

                  <p>
                    Start with one task today, then
                    review your progress on Friday.
                  </p>
                </div>

                <div className="pai-used-sources">
                  <span>Sources used</span>

                  <div className="pai-source-chips">
                    <span className="pai-chip">
                      <FileText size={14} />
                      Weekly planning · Note
                    </span>

                    <span className="pai-chip">
                      <Target size={14} />
                      Learn Python · Goal
                    </span>
                  </div>
                </div>
              </>
            ) : (
              <p className="pai-message-text">
                {message.text}
              </p>
            )}

            <div className="pai-response-actions">
              <button
                type="button"
                onClick={() =>
                  copyMessage(message.text)
                }
              >
                <Copy size={14} />
                Copy
              </button>

              <button
                type="button"
                onClick={() =>
                  backendRequired(
                    "Regenerating a response",
                  )
                }
              >
                <svg
                  width="15"
                  height="15"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.7"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  aria-hidden="true"
                >
                  <path d="M20 7v5h-5" />
                  <path d="M4 17v-5h5" />
                  <path d="M6.1 7a7 7 0 0 1 11.6-1L20 9" />
                  <path d="M4 15l2.3 3a7 7 0 0 0 11.6-1" />
                </svg>
                Regenerate
              </button>

              <button
                type="button"
                aria-label="Helpful response"
                aria-pressed={
                  feedback[message.id] === "up"
                }
                className={
                  feedback[message.id] === "up"
                    ? "is-selected"
                    : ""
                }
                onClick={() =>
                  setMessageFeedback(
                    message.id,
                    "up",
                  )
                }
              >
                <ThumbsUp size={15} />
              </button>

              <button
                type="button"
                aria-label="Unhelpful response"
                aria-pressed={
                  feedback[message.id] === "down"
                }
                className={
                  feedback[message.id] === "down"
                    ? "is-selected"
                    : ""
                }
                onClick={() =>
                  setMessageFeedback(
                    message.id,
                    "down",
                  )
                }
              >
                <ThumbsDown size={15} />
              </button>
            </div>
          </article>

          <div className="pai-follow-up-actions">
            <button
              type="button"
              className="pai-button pai-button-yellow"
              onClick={() =>
                backendRequired(
                  "Creating tasks",
                )
              }
            >
              <SquareCheck size={17} />
              Create tasks
            </button>

            <button
              type="button"
              className="pai-button"
              onClick={() =>
                backendRequired(
                  "Saving a response to Notes",
                )
              }
            >
              <ClipboardList size={17} />
              Save to notes
            </button>
          </div>
        </div>
      </div>
    );
  }


  return (
    <div className="pai">
      <header className="pai-page-header">
        <div>
          <h1>Personal AI</h1>

          <p>
            Think clearly, plan your next step and
            work with your personal information.
          </p>
        </div>

        <button
          type="button"
          className="pai-button pai-button-dark pai-new-chat"
          onClick={startChat}
        >
          <Plus size={17} />
          New chat
        </button>
      </header>

      <nav
        className="pai-tabs"
        aria-label="Personal AI sections"
      >
        {TABS.map((item) => (
          <button
            type="button"
            key={item}
            className={
              tab === item ? "is-active" : ""
            }
            aria-current={
              tab === item ? "page" : undefined
            }
            onClick={() =>
              changeTab(item)
            }
          >
            {item}
          </button>
        ))}
      </nav>

      <input
        ref={fileInputRef}
        type="file"
        multiple
        className="pai-visually-hidden"
        tabIndex={-1}
        aria-label="Choose documents"
        accept=".pdf,.txt,.md,.doc,.docx,.csv"
        onChange={(event) => {
          const files = Array.from(
            event.currentTarget.files ?? [],
          );

          if (files.length === 0) {
            return;
          }

          setDocuments((current) => [
            ...current,
            ...files.map((file) => ({
              id: makeId(),
              name: file.name,
            })),
          ]);

          setNotice(
            "Document names added to the local preview. Upload and analysis need the backend connection.",
          );

          event.currentTarget.value = "";
        }}
      />

      {notice ? (
        <div
          className="pai-notice"
          role="status"
        >
          <span>{notice}</span>

          <IconButton
            label="Dismiss notification"
            onClick={() =>
              setNotice("")
            }
          >
            <X size={15} />
          </IconButton>
        </div>
      ) : null}

      {tab === "Chat" ? (
        <div className="pai-chat-layout">
          <aside className="pai-left-column">
            <section className="pai-panel pai-recent">
              <h2>Recent chats</h2>

              <div className="pai-search">
                <Search size={17} />

                <input
                  type="search"
                  aria-label="Search chats"
                  placeholder="Search chats..."
                  value={search}
                  onChange={(event) =>
                    setSearch(
                      event.target.value,
                    )
                  }
                />
              </div>

              <div className="pai-chat-list">
                {visibleChats.length > 0 ? (
                  visibleChats.map(
                    (chat, index) => (
                      <div
                        key={chat.id}
                        className={`pai-chat-item ${
                          activeChatId === chat.id
                            ? "is-active"
                            : ""
                        }`}
                      >
                        <button
                          type="button"
                          className="pai-chat-select"
                          aria-pressed={
                            activeChatId === chat.id
                          }
                          onClick={() =>
                            openChat(chat.id)
                          }
                        >
                          {index === 3 ? (
                            <MessageCircle
                              size={21}
                            />
                          ) : (
                            <MessageSquare
                              size={21}
                            />
                          )}

                          <span className="pai-chat-copy">
                            <strong>
                              {chat.title}
                            </strong>

                            <span>
                              {chat.subtitle}
                            </span>
                          </span>

                          <time>
                            {chat.date}
                          </time>
                        </button>

                        <div className="pai-menu-anchor">
                          <IconButton
                            label={`Options for ${chat.title}`}
                            expanded={
                              openMenu === chat.id
                            }
                            onClick={() =>
                              setOpenMenu(
                                openMenu === chat.id
                                  ? null
                                  : chat.id,
                              )
                            }
                          >
                            <MoreHorizontal
                              size={17}
                            />
                          </IconButton>

                          {openMenu === chat.id ? (
                            <div className="pai-dropdown">
                              <button
                                type="button"
                                onClick={() =>
                                  deleteChat(
                                    chat.id,
                                  )
                                }
                              >
                                <Trash2 size={14} />
                                Remove from preview
                              </button>
                            </div>
                          ) : null}
                        </div>
                      </div>
                    ),
                  )
                ) : (
                  <p className="pai-empty-small">
                    No matching chats.
                  </p>
                )}
              </div>
            </section>

            <section className="pai-panel pai-quick">
              <h2>Quick actions</h2>

              <div className="pai-quick-list">
                {QUICK_ACTIONS.map(
                  (action) => {
                    const Icon = action.icon;

                    return (
                      <button
                        type="button"
                        className="pai-quick-action"
                        key={action.title}
                        onClick={() =>
                          useQuickAction(action)
                        }
                      >
                        <span className="pai-quick-icon">
                          <Icon size={21} />
                        </span>

                        <span className="pai-quick-copy">
                          <strong>
                            {action.title}
                          </strong>

                          <span>
                            {action.description}
                          </span>
                        </span>

                        <ChevronRight size={16} />
                      </button>
                    );
                  },
                )}
              </div>
            </section>
          </aside>

          <section
            className="pai-panel pai-conversation"
            aria-label="Current conversation"
          >
            <header className="pai-conversation-header">
              <h2>
                {activeChat?.title ?? "New chat"}
              </h2>

              <span className="pai-context-badge">
                <UserRound size={14} />
                Personal context
              </span>

              <div className="pai-menu-anchor">
                <IconButton
                  label="Conversation options"
                  expanded={
                    openMenu === "conversation"
                  }
                  onClick={() =>
                    setOpenMenu(
                      openMenu === "conversation"
                        ? null
                        : "conversation",
                    )
                  }
                >
                  <MoreHorizontal size={17} />
                </IconButton>

                {openMenu === "conversation" ? (
                  <div className="pai-dropdown">
                    <button
                      type="button"
                      onClick={() =>
                        changeTab("History")
                      }
                    >
                      <MessageSquare size={14} />
                      View history
                    </button>

                    {activeChat ? (
                      <button
                        type="button"
                        onClick={() =>
                          deleteChat(
                            activeChat.id,
                          )
                        }
                      >
                        <Trash2 size={14} />
                        Remove from preview
                      </button>
                    ) : null}
                  </div>
                ) : null}
              </div>
            </header>

            <div className="pai-message-scroll">
              {activeChat?.messages.length ? (
                activeChat.messages.map(
                  (message) =>
                    message.role === "user" ? (
                      <div
                        className="pai-user-row"
                        key={message.id}
                      >
                        <div className="pai-user-message">
                          <p>
                            {message.text}
                          </p>

                          <div className="pai-message-meta">
                            {message.draft ? (
                              <span>
                                Draft · not sent
                              </span>
                            ) : null}

                            <time>
                              {message.time}
                            </time>
                          </div>
                        </div>
                      </div>
                    ) : (
                      renderResponse(message)
                    ),
                )
              ) : (
                <div className="pai-conversation-empty">
                  <span className="pai-empty-spark">
                    <Sparkles size={29} />
                  </span>

                  <h3>
                    What would you like to work on?
                  </h3>

                  <p>
                    Start with your notes, a goal,
                    or a document.
                  </p>

                  <p className="pai-helper">
                    You can prepare a local draft
                    while the AI connection is added.
                  </p>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            <div className="pai-composer-area">
              <form
                className="pai-composer"
                onSubmit={saveDraft}
              >
                <IconButton
                  label="Select a document"
                  onClick={() =>
                    fileInputRef.current?.click()
                  }
                >
                  <Paperclip size={21} />
                </IconButton>

                <textarea
                  ref={composerRef}
                  rows={1}
                  aria-label="Draft a message for Personal AI"
                  placeholder="Ask Personal AI..."
                  value={draft}
                  onChange={(event) =>
                    setDraft(
                      event.target.value,
                    )
                  }
                />

                <div className="pai-menu-anchor pai-composer-sources">
                  <button
                    type="button"
                    className="pai-button"
                    aria-expanded={
                      openMenu === "sources"
                    }
                    onClick={() =>
                      setOpenMenu(
                        openMenu === "sources"
                          ? null
                          : "sources",
                      )
                    }
                  >
                    {sourceCount}{" "}
                    {sourceCount === 1
                      ? "source"
                      : "sources"}

                    <ChevronDown size={14} />
                  </button>

                  {openMenu === "sources" ? (
                    <div className="pai-dropdown pai-dropdown-up">
                      {SOURCE_DEFINITIONS.map(
                        ({
                          key,
                          label,
                          icon: Icon,
                        }) => (
                          <button
                            type="button"
                            key={key}
                            aria-pressed={
                              sources[key]
                            }
                            onClick={() =>
                              toggleSource(key)
                            }
                          >
                            <Icon size={15} />
                            {label}

                            {sources[key] ? (
                              <Check size={14} />
                            ) : null}
                          </button>
                        ),
                      )}
                    </div>
                  ) : null}
                </div>

                <button
                  type="submit"
                  className="pai-send-button"
                  disabled={!draft.trim()}
                  aria-label="Save message as a local draft"
                  title="Save draft locally; AI sending is not connected"
                >
                  <Send size={20} />
                </button>
              </form>

              <p className="pai-composer-help">
                {activeChat?.sample
                  ? "Sample conversation. "
                  : ""}
                Local preview · messages are saved
                as drafts, not sent.
              </p>
            </div>
          </section>

          <aside className="pai-right-column">
            <section className="pai-panel pai-context-panel">
              <header className="pai-panel-heading">
                <div>
                  <h2>Context sources</h2>

                  <p>
                    Choose what this chat can use
                  </p>
                </div>

                <IconButton
                  label="Context source settings"
                  onClick={() =>
                    changeTab("Settings")
                  }
                >
                  <MoreHorizontal size={17} />
                </IconButton>
              </header>

              {renderSources()}
            </section>

            <section className="pai-panel pai-memory-panel">
              <header className="pai-panel-heading">
                <h2>Memory</h2>

                <IconButton
                  label="Memory options"
                  onClick={() =>
                    changeTab("Memory")
                  }
                >
                  <MoreHorizontal size={17} />
                </IconButton>
              </header>

              <div className="pai-memory-summary">
                <span className="pai-memory-icon">
                  <Sparkles size={18} />
                </span>

                <div className="pai-memory-copy">
                  <p>
                    {memories[0]?.text ??
                      "No saved preferences"}
                  </p>

                  <div className="pai-memory-controls">
                    <button
                      type="button"
                      className="pai-button pai-button-small"
                      onClick={() =>
                        changeTab("Memory")
                      }
                    >
                      Manage memory
                    </button>

                    <span className="pai-memory-switch-label">
                      Memory{" "}
                      {memoryEnabled
                        ? "enabled"
                        : "disabled"}
                    </span>

                    <Toggle
                      label="Enable memory in the local preview"
                      checked={memoryEnabled}
                      onChange={() =>
                        setMemoryEnabled(
                          (current) => !current,
                        )
                      }
                    />
                  </div>
                </div>
              </div>
            </section>

            <section className="pai-panel pai-settings-panel">
              <header className="pai-panel-heading">
                <h2>AI settings</h2>

                <IconButton
                  label="Open AI settings"
                  onClick={() =>
                    changeTab("Settings")
                  }
                >
                  <MoreHorizontal size={17} />
                </IconButton>
              </header>

              <div className="pai-setting-row">
                <SlidersHorizontal size={18} />

                <label htmlFor="pai-response-style">
                  Response style
                </label>

                <select
                  id="pai-response-style"
                  value={responseStyle}
                  onChange={(event) =>
                    setResponseStyle(
                      event.target
                        .value as ResponseStyle,
                    )
                  }
                >
                  <option>Concise</option>
                  <option>Balanced</option>
                  <option>Detailed</option>
                </select>
              </div>

              <button
                type="button"
                className="pai-data-controls"
                onClick={() =>
                  changeTab("Settings")
                }
              >
                <Settings size={19} />
                Data controls
                <ChevronRight size={16} />
              </button>
            </section>
          </aside>
        </div>
      ) : null}

      {tab === "Overview" ? (
        <section className="pai-panel pai-tab-page">
          <div className="pai-tab-heading">
            <div>
              <h2>
                Think clearly. Take your next step.
              </h2>

              <p>
                Use Personal AI to work with your
                notes, goals, and documents.
              </p>
            </div>

            <span className="pai-preview-label">
              Local preview
            </span>
          </div>

          <div className="pai-overview-grid">
            {QUICK_ACTIONS.map((action) => {
              const Icon = action.icon;

              return (
                <button
                  type="button"
                  className="pai-overview-action"
                  key={action.title}
                  onClick={() =>
                    useQuickAction(action)
                  }
                >
                  <span className="pai-quick-icon">
                    <Icon size={23} />
                  </span>

                  <strong>
                    {action.title}
                  </strong>

                  <p>
                    {action.description}
                  </p>

                  <ArrowUpRight size={18} />
                </button>
              );
            })}
          </div>

          <div className="pai-overview-bottom">
            <div>
              <h3>
                Continue a conversation
              </h3>

              <p>
                {chats.length} local conversations ·{" "}
                {draftCount} draft messages
              </p>
            </div>

            <button
              type="button"
              className="pai-button"
              onClick={() =>
                changeTab("History")
              }
            >
              View history
              <ChevronRight size={15} />
            </button>
          </div>

          <p className="pai-helper">
            The initial conversation and preference
            are screenshot examples. Your account
            data has not been loaded.
          </p>
        </section>
      ) : null}

      {tab === "History" ? (
        <section className="pai-panel pai-tab-page">
          <div className="pai-tab-heading">
            <div>
              <h2>Conversation history</h2>

              <p>
                Sample conversations and drafts
                from this page session.
              </p>
            </div>

            <button
              type="button"
              className="pai-button pai-button-dark"
              onClick={startChat}
            >
              <Plus size={16} />
              New chat
            </button>
          </div>

          <div className="pai-search pai-history-search">
            <Search size={17} />

            <input
              type="search"
              aria-label="Search conversation history"
              placeholder="Search conversations..."
              value={search}
              onChange={(event) =>
                setSearch(
                  event.target.value,
                )
              }
            />
          </div>

          <div className="pai-history-list">
            {visibleChats.length ? (
              visibleChats.map((chat) => (
                <div
                  className="pai-history-row"
                  key={chat.id}
                >
                  <MessageSquare size={21} />

                  <button
                    type="button"
                    className="pai-history-open"
                    onClick={() =>
                      openChat(chat.id)
                    }
                  >
                    <strong>
                      {chat.title}
                    </strong>

                    <span>
                      {chat.subtitle}
                    </span>
                  </button>

                  <span className="pai-preview-label">
                    {chat.sample
                      ? "Sample"
                      : "Local draft"}
                  </span>

                  <time>
                    {chat.date}
                  </time>

                  <IconButton
                    label={`Remove ${chat.title} from preview`}
                    onClick={() =>
                      deleteChat(chat.id)
                    }
                  >
                    <Trash2 size={16} />
                  </IconButton>
                </div>
              ))
            ) : (
              <div className="pai-empty-state">
                <MessageSquare size={28} />

                <h3>
                  No conversations found
                </h3>

                <p>
                  Try another search or start a new
                  local draft.
                </p>
              </div>
            )}
          </div>
        </section>
      ) : null}

      {tab === "Memory" ? (
        <section className="pai-panel pai-tab-page">
          <div className="pai-tab-heading">
            <div>
              <h2>Memory</h2>

              <p>
                Manage preferences in this local
                preview.
              </p>
            </div>

            <div className="pai-inline-control">
              <span>
                Memory{" "}
                {memoryEnabled
                  ? "enabled"
                  : "disabled"}
              </span>

              <Toggle
                label="Enable memory in the local preview"
                checked={memoryEnabled}
                onChange={() =>
                  setMemoryEnabled(
                    (current) => !current,
                  )
                }
              />
            </div>
          </div>

          <form
            className="pai-memory-form"
            onSubmit={addMemory}
          >
            <label htmlFor="pai-new-memory">
              Add a preference
            </label>

            <div>
              <input
                id="pai-new-memory"
                type="text"
                maxLength={300}
                placeholder="For example: Keep my plans short and practical"
                value={newMemory}
                onChange={(event) =>
                  setNewMemory(
                    event.target.value,
                  )
                }
              />

              <button
                type="submit"
                className="pai-button pai-button-yellow"
                disabled={!newMemory.trim()}
              >
                <Plus size={16} />
                Add preference
              </button>
            </div>
          </form>

          <div className="pai-memory-list">
            {memories.length ? (
              memories.map((memory) => (
                <div
                  className="pai-memory-list-item"
                  key={memory.id}
                >
                  <span className="pai-memory-icon">
                    <Sparkles size={19} />
                  </span>

                  <p>
                    {memory.text}
                  </p>

                  <IconButton
                    label={`Remove preference: ${memory.text}`}
                    onClick={() =>
                      setMemories((current) =>
                        current.filter(
                          (item) =>
                            item.id !== memory.id,
                        ),
                      )
                    }
                  >
                    <Trash2 size={16} />
                  </IconButton>
                </div>
              ))
            ) : (
              <p className="pai-empty-small">
                No preferences added.
              </p>
            )}
          </div>

          <p className="pai-helper">
            Preferences stay in this page session
            and are not saved to your account.
          </p>
        </section>
      ) : null}

      {tab === "Settings" ? (
        <section className="pai-panel pai-tab-page">
          <div className="pai-tab-heading">
            <div>
              <h2>AI settings</h2>

              <p>
                Configure the local preview and
                review connection status.
              </p>
            </div>

            <SlidersHorizontal size={24} />
          </div>

          <div className="pai-settings-grid">
            <div className="pai-settings-section">
              <h3>Response preferences</h3>

              <div className="pai-preference-row">
                <div>
                  <strong>
                    Response style
                  </strong>

                  <p>
                    Choose the preferred level of
                    detail for future responses.
                  </p>
                </div>

                <select
                  aria-label="Preferred response style"
                  value={responseStyle}
                  onChange={(event) =>
                    setResponseStyle(
                      event.target
                        .value as ResponseStyle,
                    )
                  }
                >
                  <option>Concise</option>
                  <option>Balanced</option>
                  <option>Detailed</option>
                </select>
              </div>

              <div className="pai-preference-row">
                <div>
                  <strong>
                    Memory
                  </strong>

                  <p>
                    Include saved preferences in
                    the local context selection.
                  </p>
                </div>

                <Toggle
                  label="Enable memory in the local preview"
                  checked={memoryEnabled}
                  onChange={() =>
                    setMemoryEnabled(
                      (current) => !current,
                    )
                  }
                />
              </div>

              <div className="pai-connection-note">
                <ShieldCheck size={22} />

                <div>
                  <strong>
                    Backend connection pending
                  </strong>

                  <p>
                    These controls do not change
                    account permissions. Personal
                    notes, goals, conversations,
                    and workspace data have not
                    been accessed.
                  </p>
                </div>
              </div>
            </div>

            <div className="pai-settings-section">
              <h3>Context sources</h3>

              {renderSources()}
            </div>
          </div>
        </section>
      ) : null}

      <style jsx global>{`
        .pai {
          --pai-ink: #11151d;
          --pai-muted: #5e6574;
          --pai-line: #e5e1d7;
          --pai-soft-line: #eeece6;
          --pai-yellow: #ffdc67;
          --pai-yellow-soft: #fff0be;
          --pai-panel: #fcfaf5;
          width: 100%;
          min-width: 0;
          max-width: 1500px;
          margin: 0 auto;
          color: var(--pai-ink);
          font-family: inherit;
          font-size: 13px;
          line-height: 1.4;
          color-scheme: light;
          accent-color: #edbb28;
        }

        .pai,
        .pai * {
          box-sizing: border-box;
        }

        .pai ::selection {
          color: #171717;
          background: #ffe390;
        }

        .pai button,
        .pai input,
        .pai textarea,
        .pai select {
          font: inherit;
        }

        .pai button {
          color: inherit;
          cursor: pointer;
        }

        .pai button:disabled {
          cursor: not-allowed;
          opacity: 0.52;
        }

        .pai button,
        .pai a,
        .pai input,
        .pai textarea,
        .pai select {
          -webkit-tap-highlight-color: transparent;
        }

        .pai button:focus-visible,
        .pai a:focus-visible,
        .pai input:focus-visible,
        .pai textarea:focus-visible,
        .pai select:focus-visible {
          outline: 2px solid #9b7413;
          outline-offset: 3px;
        }

        .pai h1,
        .pai h2,
        .pai h3,
        .pai h4,
        .pai p {
          margin: 0;
        }

        .pai svg {
          flex-shrink: 0;
          stroke-width: 1.65;
        }

        .pai button,
        .pai a {
          transition:
            background-color 140ms ease,
            border-color 140ms ease,
            color 140ms ease;
        }

        .pai-page-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 20px;
          margin-bottom: 17px;
        }

        .pai-page-header h1 {
          font-size: 36px;
          font-weight: 500;
          line-height: 1.1;
          letter-spacing: -1px;
        }

        .pai-page-header p {
          margin-top: 2px;
          color: var(--pai-muted);
          font-size: 15px;
          line-height: 1.45;
        }

        .pai-button {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          gap: 9px;
          min-height: 35px;
          padding: 7px 14px;
          border: 1px solid #dcdad4;
          border-radius: 11px;
          background: transparent;
          color: var(--pai-ink);
          font-size: 12px;
          font-weight: 400;
          line-height: 1.3;
          text-decoration: none;
          white-space: nowrap;
        }

        .pai-button:hover:not(:disabled) {
          background: #f3efe6;
          border-color: #cfc9ba;
        }

        .pai-button-dark {
          border-color: #24262a;
          background: linear-gradient(
            155deg,
            #2c2e33,
            #25272b
          );
          color: #ffffff !important;
        }

        .pai-button-dark:hover:not(:disabled) {
          border-color: #393c43;
          background: #393c43;
        }

        .pai-new-chat {
          min-width: 138px;
          min-height: 41px;
          padding: 10px 20px;
          border-radius: 10px;
          font-size: 13px;
        }

        .pai-button-yellow {
          border-color: #ffda58;
          background: linear-gradient(
            110deg,
            #ffe17b,
            #ffdc62
          );
        }

        .pai-button-yellow:hover:not(:disabled) {
          border-color: #ecc344;
          background: #ffd44c;
        }

        .pai-button-small {
          min-height: 27px;
          gap: 6px;
          padding: 5px 11px;
          font-size: 11px;
        }

        .pai-icon-button {
          display: inline-flex;
          flex-shrink: 0;
          align-items: center;
          justify-content: center;
          width: 29px;
          height: 29px;
          padding: 0;
          border: 1px solid #e6e3dc;
          border-radius: 50%;
          background: transparent;
        }

        .pai-icon-button:hover {
          background: #f2eee4;
        }

        .pai-tabs {
          display: grid;
          grid-template-columns: repeat(5, minmax(0, 1fr));
          align-items: center;
          min-height: 45px;
          margin-bottom: 10px;
          padding: 4px;
          border: 1px solid var(--pai-line);
          border-radius: 12px;
          background: rgba(255, 255, 255, 0.36);
        }

        .pai-tabs > button {
          position: relative;
          min-width: 0;
          min-height: 35px;
          padding: 7px 10px;
          border: 0;
          border-radius: 10px;
          background: transparent;
          font-size: 13px;
        }

        .pai-tabs > button + button::before {
          position: absolute;
          top: 2px;
          bottom: 2px;
          left: 0;
          width: 1px;
          background: var(--pai-line);
          content: "";
        }

        .pai-tabs > button.is-active {
          background: var(--pai-yellow-soft);
        }

        .pai-tabs > button:hover:not(.is-active) {
          background: rgba(244, 237, 216, 0.65);
        }

        .pai-tabs > button.is-active::before,
        .pai-tabs > button.is-active + button::before {
          display: none;
        }

        .pai-chat-layout {
          display: grid;
          grid-template-columns:
            minmax(245px, 1.13fr)
            minmax(410px, 1.86fr)
            minmax(258px, 1fr);
          align-items: start;
          gap: 8px;
        }

        .pai-left-column,
        .pai-right-column {
          display: flex;
          min-width: 0;
          flex-direction: column;
          gap: 8px;
        }

        .pai-panel {
          min-width: 0;
          border: 1px solid var(--pai-line);
          border-radius: 13px;
          background: linear-gradient(
            125deg,
            rgba(255, 255, 255, 0.79),
            rgba(252, 250, 245, 0.9)
          );
          box-shadow: 0 3px 7px rgba(76, 62, 26, 0.035);
        }

        .pai-panel h2 {
          font-size: 16px;
          font-weight: 600;
          line-height: 1.35;
          letter-spacing: -0.2px;
        }

        .pai-recent {
          min-height: 339px;
          padding: 15px 9px 12px;
        }

        .pai-recent > h2 {
          margin: 0 11px 11px;
        }

        .pai-search {
          display: flex;
          align-items: center;
          gap: 9px;
          height: 35px;
          margin: 0 9px 7px;
          padding: 0 10px;
          border: 1px solid #deddd7;
          border-radius: 11px;
          color: #7a8290;
          background: rgba(255, 255, 255, 0.25);
        }

        .pai-search input {
          width: 100%;
          min-width: 0;
          height: 100%;
          padding: 0;
          border: 0;
          outline: none;
          background: transparent;
          color: var(--pai-ink);
          font-size: 11px;
        }

        .pai-search input::placeholder {
          color: #6c7483;
          opacity: 1;
        }

        .pai-search:focus-within {
          border-color: #bba261;
        }

        .pai-chat-item {
          position: relative;
          display: flex;
          align-items: center;
          min-height: 60px;
          padding-right: 5px;
          border-radius: 9px;
        }

        .pai-chat-item + .pai-chat-item::before {
          position: absolute;
          right: 11px;
          bottom: 0;
          left: 11px;
          height: 1px;
          background: #f0ede6;
          content: "";
        }

        .pai-chat-item.is-active {
          min-height: 55px;
          background: #fff0c2;
        }

        .pai-chat-item.is-active::before {
          display: none;
        }

        .pai-chat-select {
          display: flex;
          flex: 1;
          align-items: center;
          gap: 14px;
          min-width: 0;
          min-height: 55px;
          padding: 9px 5px 9px 12px;
          border: 0;
          border-radius: 9px;
          background: transparent;
          text-align: left;
        }

        .pai-chat-copy {
          display: flex;
          flex: 1;
          min-width: 0;
          flex-direction: column;
          gap: 3px;
        }

        .pai-chat-copy strong {
          overflow: hidden;
          font-size: 13px;
          font-weight: 500;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .pai-chat-copy > span {
          overflow: hidden;
          color: var(--pai-muted);
          font-size: 11px;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .pai-chat-select time {
          align-self: flex-start;
          margin-top: 2px;
          color: #626c7c;
          font-size: 10px;
          white-space: nowrap;
        }

        .pai-chat-item .pai-icon-button {
          width: 22px;
          height: 28px;
          border: 0;
        }

        .pai-quick {
          padding: 14px 16px 17px;
        }

        .pai-quick > h2 {
          margin: 0 4px 11px;
        }

        .pai-quick-list {
          display: flex;
          flex-direction: column;
          gap: 6px;
        }

        .pai-quick-action {
          display: flex;
          align-items: center;
          gap: 15px;
          width: 100%;
          min-height: 55px;
          padding: 8px 11px 8px 9px;
          border: 1px solid #e8e5dd;
          border-radius: 12px;
          background: rgba(255, 255, 255, 0.3);
          text-align: left;
        }

        .pai-quick-action:hover {
          border-color: #d8c897;
          background: #fff9e8;
        }

        .pai-quick-icon {
          display: inline-flex;
          flex-shrink: 0;
          align-items: center;
          justify-content: center;
          width: 37px;
          height: 37px;
          border-radius: 9px;
          background: linear-gradient(
            135deg,
            #fff5d1,
            #ffebb0
          );
        }

        .pai-quick-copy {
          display: flex;
          flex: 1;
          min-width: 0;
          flex-direction: column;
          gap: 3px;
        }

        .pai-quick-copy strong {
          font-size: 13px;
          font-weight: 500;
        }

        .pai-quick-copy > span {
          color: var(--pai-muted);
          font-size: 11px;
          line-height: 1.35;
        }

        .pai-quick-action > svg {
          color: #606a79;
        }

        .pai-conversation {
          display: flex;
          min-height: 665px;
          height: calc(100dvh - 238px);
          max-height: 900px;
          flex-direction: column;
          overflow: hidden;
        }

        .pai-conversation-header {
          display: flex;
          flex-shrink: 0;
          align-items: center;
          gap: 12px;
          min-height: 63px;
          padding: 15px 20px;
          border-bottom: 1px solid var(--pai-soft-line);
        }

        .pai-conversation-header h2 {
          overflow: hidden;
          font-size: 19px;
          font-weight: 500;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .pai-context-badge {
          display: inline-flex;
          flex-shrink: 0;
          align-items: center;
          gap: 7px;
          min-height: 28px;
          padding: 5px 10px;
          border: 1px solid #dcdbd6;
          border-radius: 18px;
          color: #485060;
          font-size: 11px;
          white-space: nowrap;
        }

        .pai-conversation-header > .pai-menu-anchor {
          margin-left: auto;
        }

        .pai-message-scroll {
          flex: 1;
          min-height: 0;
          padding: 6px 12px 12px;
          overflow-x: hidden;
          overflow-y: auto;
          scrollbar-color: #d4cbb4 transparent;
          scrollbar-width: thin;
          overscroll-behavior: contain;
        }

        .pai-user-row {
          display: flex;
          justify-content: flex-end;
          margin-bottom: 15px;
          padding-left: 45px;
        }

        .pai-user-message {
          position: relative;
          max-width: 100%;
          padding: 12px 15px 7px;
          border-radius: 12px 12px 3px 12px;
          background: linear-gradient(
            115deg,
            #fff2cb,
            #fff0c2
          );
        }

        .pai-user-message p {
          font-size: 13px;
          line-height: 1.5;
          overflow-wrap: anywhere;
          white-space: pre-wrap;
        }

        .pai-message-meta {
          display: flex;
          justify-content: flex-end;
          gap: 10px;
          margin-top: 8px;
          color: #686d75;
          font-size: 10px;
          font-variant-numeric: tabular-nums;
        }

        .pai-assistant-row {
          display: flex;
          align-items: flex-start;
          gap: 10px;
          margin-bottom: 4px;
        }

        .pai-ai-avatar {
          display: inline-flex;
          flex-shrink: 0;
          align-items: center;
          justify-content: center;
          width: 34px;
          height: 34px;
          margin-top: 2px;
          border-radius: 50%;
          background: #fff3cf;
        }

        .pai-assistant-content {
          flex: 1;
          min-width: 0;
        }

        .pai-response {
          min-width: 0;
          padding: 13px 14px 7px;
          border: 1px solid #e8e8e8;
          border-radius: 12px;
          background: rgba(255, 255, 255, 0.91);
        }

        .pai-response > h3 {
          font-size: 15px;
          font-weight: 500;
          line-height: 1.5;
        }

        .pai-response-intro {
          margin-top: 7px !important;
          color: #444c5c;
          font-size: 12px;
          line-height: 1.45;
        }

        .pai-week-plan {
          display: flex;
          flex-direction: column;
          gap: 4px;
          margin-top: 10px;
        }

        .pai-plan-row {
          display: grid;
          grid-template-columns: 85px minmax(0, 1fr);
          gap: 5px;
          min-height: 47px;
        }

        .pai-plan-day {
          display: flex;
          align-items: center;
          padding: 9px 12px;
          border-radius: 7px;
          background: linear-gradient(
            135deg,
            #f6f6f7,
            #f8f8f8
          );
          font-size: 12px;
        }

        .pai-plan-description {
          padding: 6px 8px;
          border: 1px solid #f1f1f1;
          border-radius: 7px;
          background: #fdfdfd;
        }

        .pai-plan-description strong {
          display: block;
          font-size: 12px;
          font-weight: 500;
          line-height: 1.35;
        }

        .pai-plan-description p {
          margin-top: 2px;
          color: #5d6473;
          font-size: 11px;
          line-height: 1.4;
        }

        .pai-next-step {
          margin-top: 14px;
          padding-top: 5px;
          border-top: 1px solid #e7e7e7;
        }

        .pai-next-step h4 {
          font-size: 14px;
          font-weight: 500;
        }

        .pai-next-step p {
          margin-top: 4px;
          color: #444c5c;
          font-size: 12px;
          line-height: 1.5;
        }

        .pai-used-sources {
          margin-top: 9px;
        }

        .pai-used-sources > span {
          color: #535c6b;
          font-size: 11px;
        }

        .pai-source-chips {
          display: flex;
          flex-wrap: wrap;
          gap: 9px;
          margin-top: 4px;
        }

        .pai-chip {
          display: inline-flex;
          align-items: center;
          gap: 7px;
          min-height: 28px;
          padding: 5px 9px;
          border: 1px solid #e9e9eb;
          border-radius: 13px;
          background: #f6f6f7;
          color: #424a59;
          font-size: 10px;
          white-space: nowrap;
        }

        .pai-response-actions {
          display: flex;
          align-items: center;
          justify-content: flex-end;
          flex-wrap: wrap;
          gap: 10px;
          margin-top: 9px;
        }

        .pai-response-actions button {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          gap: 7px;
          min-height: 21px;
          padding: 2px;
          border: 0;
          border-radius: 4px;
          background: transparent;
          color: #444d5e;
          font-size: 10px;
        }

        .pai-response-actions button:hover,
        .pai-response-actions button.is-selected {
          color: #7d5a00;
          background: #fff1c0;
        }

        .pai-follow-up-actions {
          display: flex;
          flex-wrap: wrap;
          gap: 10px;
          margin-top: 8px;
        }

        .pai-follow-up-actions .pai-button {
          min-height: 34px;
          padding: 7px 15px;
          font-size: 11px;
        }

        .pai-message-text {
          overflow-wrap: anywhere;
          white-space: pre-wrap;
        }

        .pai-composer-area {
          flex-shrink: 0;
          padding: 0 11px 7px;
        }

        .pai-composer {
          display: flex;
          align-items: center;
          gap: 8px;
          min-height: 52px;
          padding: 5px;
          border: 1px solid #dadbe0;
          border-radius: 14px;
          background: rgba(255, 255, 255, 0.96);
        }

        .pai-composer > .pai-icon-button {
          width: 36px;
          height: 36px;
          border: 0;
        }

        .pai-composer textarea {
          flex: 1;
          width: 100%;
          min-width: 0;
          min-height: 22px;
          max-height: 110px;
          padding: 3px 0;
          border: 0;
          background: transparent;
          color: var(--pai-ink);
          font-size: 13px;
          line-height: 1.45;
          resize: vertical;
          caret-color: #98700e;
        }

        .pai-composer textarea::placeholder {
          color: #8b91a0;
          opacity: 1;
        }

        .pai-composer-sources > .pai-button {
          min-height: 36px;
          gap: 11px;
          padding: 7px 12px;
          border-radius: 14px;
        }

        .pai-send-button {
          display: inline-flex;
          flex-shrink: 0;
          align-items: center;
          justify-content: center;
          width: 43px;
          height: 41px;
          padding: 0;
          border: 1px solid #202227;
          border-radius: 12px;
          background: linear-gradient(
            140deg,
            #34363c,
            #24262a
          );
          color: #ffffff !important;
        }

        .pai-send-button:hover:not(:disabled) {
          background: #41444a;
        }

        .pai-composer-help {
          margin: 6px 3px 0 !important;
          color: #626b79;
          font-size: 10px;
          line-height: 1.35;
        }

        .pai-context-panel {
          padding: 12px 15px;
        }

        .pai-panel-heading {
          display: flex;
          align-items: flex-start;
          justify-content: space-between;
          gap: 10px;
        }

        .pai-panel-heading h2 {
          padding-top: 3px;
        }

        .pai-panel-heading p {
          margin-top: 1px;
          color: var(--pai-muted);
          font-size: 12px;
        }

        .pai-source-list {
          margin-top: 5px;
        }

        .pai-source-row {
          display: flex;
          align-items: center;
          gap: 17px;
          min-height: 33px;
          padding: 3px 5px 3px 9px;
        }

        .pai-source-row > span:not(.pai-toggle) {
          flex: 1;
          min-width: 0;
          font-size: 12px;
        }

        .pai-source-row > .pai-button {
          padding-right: 10px;
          padding-left: 10px;
        }

        .pai-toggle {
          display: inline-flex;
          position: relative;
          flex-shrink: 0;
          align-items: center;
          width: 36px;
          height: 20px;
          padding: 2px;
          border: 0;
          border-radius: 12px;
          background: #d3d5d9;
          vertical-align: middle;
        }

        .pai-toggle > span {
          display: block;
          width: 16px;
          height: 16px;
          border-radius: 50%;
          background: #ffffff;
          box-shadow: 0 1px 2px rgba(0, 0, 0, 0.06);
          transform: translateX(0);
          transition: transform 140ms ease;
        }

        .pai-toggle.is-on {
          background: #ffc923;
        }

        .pai-toggle.is-on > span {
          transform: translateX(16px);
        }

        .pai-toggle.is-unavailable {
          opacity: 0.9;
          cursor: not-allowed;
        }

        .pai-source-detail {
          display: grid;
          grid-template-columns: 20px minmax(0, 1fr) 36px;
          align-items: start;
          column-gap: 17px;
          margin-top: 9px;
          padding: 12px 3px 2px 9px;
          border-top: 1px solid #e9e5dc;
        }

        .pai-source-detail > svg {
          margin-top: 2px;
        }

        .pai-source-detail strong {
          display: block;
          font-size: 12px;
          font-weight: 400;
        }

        .pai-source-detail p {
          margin-top: 1px;
          color: var(--pai-muted);
          font-size: 12px;
          line-height: 1.3;
        }

        .pai-source-detail > .pai-toggle {
          margin-top: 2px;
        }

        .pai-workspace-source {
          margin-top: 10px;
        }

        .pai-workspace-button {
          grid-column: 2 / -1;
          width: 100%;
          min-height: 30px;
          margin-top: 10px;
          padding: 6px 8px;
          font-size: 11px;
        }

        .pai-memory-panel {
          padding: 10px 15px 12px;
        }

        .pai-memory-panel .pai-panel-heading .pai-icon-button,
        .pai-settings-panel .pai-panel-heading .pai-icon-button {
          width: 24px;
          height: 24px;
        }

        .pai-memory-summary {
          display: flex;
          align-items: flex-start;
          gap: 12px;
          margin-top: 12px;
        }

        .pai-memory-icon {
          display: inline-flex;
          flex-shrink: 0;
          align-items: center;
          justify-content: center;
          width: 30px;
          height: 30px;
          border-radius: 10px;
          background: #fff0bd;
        }

        .pai-memory-copy {
          flex: 1;
          min-width: 0;
        }

        .pai-memory-copy > p {
          font-size: 12px;
          line-height: 1.35;
          overflow-wrap: anywhere;
        }

        .pai-memory-controls {
          display: flex;
          align-items: center;
          flex-wrap: wrap;
          gap: 7px;
          margin-top: 8px;
        }

        .pai-memory-controls .pai-button {
          padding: 5px 10px;
          font-size: 10px;
        }

        .pai-memory-switch-label {
          margin-left: auto;
          font-size: 9px;
          white-space: nowrap;
        }

        .pai-memory-controls .pai-toggle {
          width: 30px;
          height: 17px;
        }

        .pai-memory-controls .pai-toggle > span {
          width: 13px;
          height: 13px;
        }

        .pai-memory-controls .pai-toggle.is-on > span {
          transform: translateX(13px);
        }

        .pai-settings-panel {
          padding: 9px 15px 11px;
        }

        .pai-setting-row {
          display: flex;
          align-items: center;
          gap: 15px;
          margin-top: 8px;
          padding-left: 5px;
        }

        .pai-setting-row > label {
          flex: 1;
          font-size: 12px;
        }

        .pai select {
          min-width: 105px;
          min-height: 29px;
          padding: 4px 9px;
          border: 1px solid #e0dcd3;
          border-radius: 10px;
          background: #fcfaf6;
          color: var(--pai-ink);
          font-size: 11px;
        }

        .pai-data-controls {
          display: flex;
          align-items: center;
          gap: 15px;
          width: 100%;
          min-height: 34px;
          margin-top: 5px;
          padding: 5px;
          border: 0;
          border-radius: 8px;
          background: transparent;
          font-size: 12px;
          text-align: left;
        }

        .pai-data-controls:hover {
          background: #f3efe6;
        }

        .pai-data-controls > svg:last-child {
          margin-left: auto;
          color: #68717e;
        }

        .pai-menu-anchor {
          position: relative;
          flex-shrink: 0;
        }

        .pai-dropdown {
          position: absolute;
          top: calc(100% + 5px);
          right: 0;
          z-index: 30;
          width: max-content;
          min-width: 170px;
          max-width: 250px;
          padding: 5px;
          border: 1px solid #e1ddd3;
          border-radius: 10px;
          background: #fffdf8;
          box-shadow: 0 8px 25px rgba(37, 32, 21, 0.12);
        }

        .pai-dropdown-up {
          top: auto;
          bottom: calc(100% + 9px);
        }

        .pai-dropdown > button {
          display: flex;
          align-items: center;
          gap: 9px;
          width: 100%;
          min-height: 34px;
          padding: 7px 9px;
          border: 0;
          border-radius: 6px;
          background: transparent;
          font-size: 12px;
          text-align: left;
        }

        .pai-dropdown > button:hover {
          background: #fff0c3;
        }

        .pai-dropdown > button > svg:last-child:not(:first-child) {
          margin-left: auto;
        }

        .pai-notice {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 14px;
          margin-bottom: 10px;
          padding: 9px 12px;
          border: 1px solid #eadcae;
          border-radius: 10px;
          background: #fff6dc;
          color: #665322;
          font-size: 12px;
        }

        .pai-notice .pai-icon-button {
          width: 24px;
          height: 24px;
          border: 0;
        }

        .pai-documents {
          display: flex;
          flex-direction: column;
          gap: 5px;
          padding: 7px 4px 2px;
        }

        .pai-document {
          display: flex;
          align-items: center;
          gap: 7px;
          padding: 4px 6px;
          border: 1px solid #e7e2d5;
          border-radius: 8px;
          background: #fffaf0;
          font-size: 11px;
        }

        .pai-document > span {
          overflow: hidden;
          flex: 1;
          min-width: 0;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .pai-document .pai-icon-button {
          width: 21px;
          height: 21px;
          border: 0;
        }

        .pai-helper {
          margin-top: 12px !important;
          color: var(--pai-muted);
          font-size: 11px;
          line-height: 1.5;
        }

        .pai-documents .pai-helper {
          margin-top: 2px !important;
          font-size: 10px;
        }

        .pai-empty-small {
          padding: 22px 12px;
          color: var(--pai-muted);
          font-size: 12px;
          text-align: center;
        }

        .pai-conversation-empty {
          display: flex;
          min-height: 350px;
          align-items: center;
          justify-content: center;
          flex-direction: column;
          gap: 12px;
          padding: 25px;
          text-align: center;
        }

        .pai-empty-spark {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          width: 60px;
          height: 60px;
          border-radius: 18px;
          background: #fff0bd;
        }

        .pai-conversation-empty h3 {
          font-size: 18px;
          font-weight: 500;
        }

        .pai-conversation-empty > p {
          color: var(--pai-muted);
          font-size: 12px;
        }

        .pai-tab-page {
          min-height: 460px;
          padding: 24px;
        }

        .pai-tab-heading {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 20px;
          margin-bottom: 24px;
        }

        .pai-tab-heading h2 {
          font-size: 22px;
          font-weight: 500;
        }

        .pai-tab-heading p {
          margin-top: 5px;
          color: var(--pai-muted);
          font-size: 13px;
        }

        .pai-preview-label {
          display: inline-flex;
          align-items: center;
          min-height: 25px;
          padding: 4px 9px;
          border: 1px solid #e8dfc4;
          border-radius: 8px;
          background: #fff5d8;
          color: #685c3c;
          font-size: 10px;
          white-space: nowrap;
        }

        .pai-overview-grid {
          display: grid;
          grid-template-columns: repeat(4, minmax(0, 1fr));
          gap: 12px;
        }

        .pai-overview-action {
          position: relative;
          display: flex;
          align-items: flex-start;
          flex-direction: column;
          gap: 12px;
          min-height: 175px;
          padding: 18px;
          border: 1px solid #e7e2d7;
          border-radius: 12px;
          background: #fffdf8;
          text-align: left;
        }

        .pai-overview-action:hover {
          background: #fff6de;
          border-color: #d9c388;
        }

        .pai-overview-action > strong {
          font-size: 14px;
          font-weight: 500;
        }

        .pai-overview-action > p {
          color: var(--pai-muted);
          font-size: 12px;
        }

        .pai-overview-action > svg {
          position: absolute;
          top: 18px;
          right: 15px;
          color: #717785;
        }

        .pai-overview-bottom {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 20px;
          margin-top: 28px;
          padding-top: 22px;
          border-top: 1px solid var(--pai-line);
        }

        .pai-overview-bottom h3 {
          font-size: 15px;
          font-weight: 500;
        }

        .pai-overview-bottom p {
          margin-top: 5px;
          color: var(--pai-muted);
          font-size: 12px;
        }

        .pai-history-search {
          max-width: 430px;
          margin: 0 0 20px;
        }

        .pai-history-row {
          display: flex;
          align-items: center;
          gap: 16px;
          min-height: 76px;
          padding: 12px 4px;
          border-bottom: 1px solid var(--pai-soft-line);
        }

        .pai-history-open {
          display: flex;
          flex: 1;
          min-width: 0;
          flex-direction: column;
          gap: 4px;
          padding: 4px 0;
          border: 0;
          background: transparent;
          text-align: left;
        }

        .pai-history-open strong {
          font-size: 13px;
          font-weight: 500;
        }

        .pai-history-open > span {
          overflow: hidden;
          color: var(--pai-muted);
          font-size: 12px;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .pai-history-row > time {
          color: var(--pai-muted);
          font-size: 11px;
          white-space: nowrap;
        }

        .pai-empty-state {
          display: flex;
          min-height: 220px;
          align-items: center;
          justify-content: center;
          flex-direction: column;
          gap: 12px;
          text-align: center;
        }

        .pai-empty-state h3 {
          font-size: 16px;
          font-weight: 500;
        }

        .pai-empty-state p {
          color: var(--pai-muted);
          font-size: 12px;
        }

        .pai-inline-control {
          display: inline-flex;
          align-items: center;
          gap: 10px;
          font-size: 12px;
        }

        .pai-memory-form {
          padding: 18px;
          border: 1px solid var(--pai-line);
          border-radius: 12px;
          background: #fffdf7;
        }

        .pai-memory-form > label {
          display: block;
          margin-bottom: 10px;
          font-size: 13px;
          font-weight: 500;
        }

        .pai-memory-form > div {
          display: flex;
          gap: 10px;
        }

        .pai-memory-form input {
          flex: 1;
          width: 100%;
          min-width: 0;
          min-height: 39px;
          padding: 9px 12px;
          border: 1px solid #ded9cb;
          border-radius: 9px;
          background: #ffffff;
          color: var(--pai-ink);
          font-size: 12px;
        }

        .pai-memory-list {
          margin-top: 20px;
        }

        .pai-memory-list-item {
          display: flex;
          align-items: center;
          gap: 13px;
          min-height: 64px;
          padding: 12px 2px;
          border-bottom: 1px solid var(--pai-soft-line);
        }

        .pai-memory-list-item > p {
          flex: 1;
          min-width: 0;
          overflow-wrap: anywhere;
        }

        .pai-settings-grid {
          display: grid;
          grid-template-columns: minmax(0, 1.2fr) minmax(0, 1fr);
          gap: 30px;
        }

        .pai-settings-section > h3 {
          margin-bottom: 12px;
          font-size: 15px;
          font-weight: 500;
        }

        .pai-preference-row {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 18px;
          min-height: 88px;
          padding: 15px 0;
          border-bottom: 1px solid var(--pai-line);
        }

        .pai-preference-row strong {
          font-size: 13px;
          font-weight: 500;
        }

        .pai-preference-row p {
          max-width: 330px;
          margin-top: 4px;
          color: var(--pai-muted);
          font-size: 12px;
          line-height: 1.5;
        }

        .pai-connection-note {
          display: flex;
          align-items: flex-start;
          gap: 12px;
          margin-top: 22px;
          padding: 16px;
          border: 1px solid #e4d8b8;
          border-radius: 11px;
          background: #fff7e3;
        }

        .pai-connection-note strong {
          font-size: 13px;
          font-weight: 500;
        }

        .pai-connection-note p {
          margin-top: 6px;
          color: #685d43;
          font-size: 12px;
          line-height: 1.6;
        }

        .pai-visually-hidden {
          position: absolute;
          width: 1px;
          height: 1px;
          overflow: hidden;
          clip: rect(0, 0, 0, 0);
          white-space: nowrap;
          clip-path: inset(50%);
        }

        @media (min-width: 1450px) {
          .pai-chat-layout {
            gap: 10px;
          }

          .pai-conversation-header {
            min-height: 65px;
          }

          .pai-response-intro,
          .pai-next-step p {
            font-size: 13px;
          }

          .pai-plan-description strong {
            font-size: 13px;
          }

          .pai-plan-description p {
            font-size: 12px;
          }

          .pai-plan-row {
            min-height: 49px;
          }
        }

        @media (max-width: 1180px) {
          .pai-chat-layout {
            grid-template-columns:
              minmax(220px, 0.8fr)
              minmax(0, 1.6fr);
            gap: 10px;
          }

          .pai-right-column {
            display: grid;
            grid-column: 1 / -1;
            grid-template-columns:
              minmax(0, 1.25fr)
              minmax(0, 1fr);
            align-items: start;
            gap: 10px;
          }

          .pai-context-panel {
            grid-row: span 2;
          }

          .pai-conversation {
            height: 690px;
            min-height: 630px;
          }

          .pai-context-badge {
            gap: 5px;
            padding: 5px 8px;
            font-size: 10px;
          }

          .pai-conversation-header {
            gap: 8px;
            padding-right: 12px;
            padding-left: 14px;
          }

          .pai-conversation-header h2 {
            font-size: 17px;
          }

          .pai-overview-grid {
            grid-template-columns: repeat(2, minmax(0, 1fr));
          }
        }

        @media (max-width: 760px) {
          .pai-page-header {
            align-items: flex-start;
            gap: 12px;
          }

          .pai-page-header h1 {
            font-size: 29px;
            letter-spacing: -0.6px;
          }

          .pai-page-header p {
            max-width: 420px;
            margin-top: 5px;
            font-size: 12px;
          }

          .pai-new-chat {
            min-width: 105px;
            min-height: 36px;
            padding: 8px 12px;
            font-size: 12px;
          }

          .pai-chat-layout {
            grid-template-columns: minmax(0, 1fr);
          }

          .pai-left-column {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            align-items: start;
            gap: 10px;
          }

          .pai-recent {
            min-height: 320px;
          }

          .pai-quick {
            min-height: 320px;
            padding-right: 10px;
            padding-left: 10px;
          }

          .pai-quick-action {
            gap: 9px;
            min-height: 58px;
            padding: 8px;
          }

          .pai-quick-copy strong {
            font-size: 12px;
          }

          .pai-quick-copy > span {
            font-size: 10px;
          }

          .pai-chat-select {
            gap: 8px;
            padding-left: 8px;
          }

          .pai-chat-select time {
            display: none;
          }

          .pai-conversation {
            height: 700px;
            min-height: 610px;
          }

          .pai-right-column {
            grid-column: auto;
          }

          .pai-tab-page {
            padding: 18px;
          }

          .pai-tab-heading {
            align-items: flex-start;
          }

          .pai-tab-heading h2 {
            font-size: 20px;
          }

          .pai-settings-grid {
            grid-template-columns: minmax(0, 1fr);
          }

          .pai-history-row {
            gap: 10px;
          }

          .pai-history-row > .pai-preview-label {
            display: none;
          }
        }

        @media (max-width: 480px) {
          .pai-page-header {
            flex-wrap: wrap;
          }

          .pai-page-header > div {
            flex: 1;
            min-width: 190px;
          }

          .pai-tabs {
            min-height: 43px;
            padding: 3px;
          }

          .pai-tabs > button {
            min-height: 35px;
            padding: 6px 3px;
            font-size: 11px;
          }

          .pai-left-column,
          .pai-right-column {
            display: flex;
            flex-direction: column;
          }

          .pai-left-column > *,
          .pai-right-column > * {
            width: 100%;
          }

          .pai-recent {
            min-height: 0;
          }

          .pai-chat-list {
            max-height: 190px;
            overflow-y: auto;
            scrollbar-color: #d4cbb4 transparent;
            scrollbar-width: thin;
          }

          .pai-chat-select time {
            display: block;
          }

          .pai-quick {
            min-height: 0;
          }

          .pai-quick-list {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
          }

          .pai-quick-action {
            align-items: flex-start;
            gap: 8px;
            min-height: 81px;
          }

          .pai-quick-icon {
            width: 29px;
            height: 31px;
          }

          .pai-quick-icon svg {
            width: 18px;
            height: 18px;
          }

          .pai-quick-action > svg {
            display: none;
          }

          .pai-conversation {
            height: 690px;
            min-height: 0;
          }

          .pai-conversation-header {
            flex-wrap: wrap;
            gap: 7px;
            min-height: 61px;
            padding: 12px;
          }

          .pai-conversation-header h2 {
            max-width: calc(100% - 45px);
            font-size: 17px;
          }

          .pai-context-badge {
            order: 3;
            width: max-content;
            min-height: 24px;
            padding: 3px 8px;
          }

          .pai-message-scroll {
            padding-right: 9px;
            padding-left: 9px;
          }

          .pai-user-row {
            padding-left: 25px;
          }

          .pai-user-message {
            padding: 10px 12px 7px;
          }

          .pai-user-message p {
            font-size: 12px;
          }

          .pai-assistant-row {
            gap: 6px;
          }

          .pai-ai-avatar {
            width: 27px;
            height: 27px;
          }

          .pai-ai-avatar svg {
            width: 18px;
            height: 18px;
          }

          .pai-response {
            padding: 11px 9px 7px;
          }

          .pai-response > h3 {
            font-size: 14px;
          }

          .pai-response-intro {
            font-size: 11px;
          }

          .pai-plan-row {
            grid-template-columns: 65px minmax(0, 1fr);
          }

          .pai-plan-day {
            padding: 8px 6px;
            font-size: 10px;
          }

          .pai-plan-description {
            padding: 6px;
          }

          .pai-plan-description strong {
            font-size: 11px;
          }

          .pai-plan-description p {
            font-size: 10px;
          }

          .pai-source-chips {
            gap: 5px;
          }

          .pai-chip {
            max-width: 100%;
            padding: 5px 7px;
            font-size: 9px;
            white-space: normal;
          }

          .pai-follow-up-actions {
            gap: 6px;
          }

          .pai-follow-up-actions .pai-button {
            gap: 6px;
            padding: 7px 9px;
            font-size: 10px;
          }

          .pai-composer {
            gap: 3px;
          }

          .pai-composer > .pai-icon-button {
            width: 27px;
          }

          .pai-composer textarea {
            font-size: 12px;
          }

          .pai-composer-sources > .pai-button {
            gap: 5px;
            min-height: 33px;
            padding: 6px 7px;
            font-size: 10px;
          }

          .pai-send-button {
            width: 36px;
            height: 37px;
          }

          .pai-overview-grid {
            grid-template-columns: minmax(0, 1fr);
          }

          .pai-overview-action {
            min-height: 145px;
          }

          .pai-tab-heading,
          .pai-overview-bottom {
            flex-wrap: wrap;
          }

          .pai-memory-form > div {
            flex-direction: column;
          }

          .pai-memory-form .pai-button {
            align-self: flex-start;
          }

          .pai-history-row > time {
            font-size: 10px;
          }

          .pai-history-open strong {
            font-size: 12px;
          }

          .pai-history-open > span {
            font-size: 11px;
          }

          .pai-preference-row {
            gap: 12px;
          }
        }

        @media (prefers-reduced-motion: reduce) {
          .pai *,
          .pai *::before,
          .pai *::after {
            transition: none !important;
            scroll-behavior: auto !important;
          }
        }
      `}</style>
    </div>
  );
}