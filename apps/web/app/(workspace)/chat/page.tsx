"use client";

import { UserAvatar } from "@/components/account/user-avatar";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import {
  Archive,
  Bell,
  Check,
  CheckCheck,
  ChevronRight,
  Copy,
  Download,
  Edit3,
  FileText,
  Image as ImageIcon,
  MessageCircle,
  Mic,
  MoreHorizontal,
  Phone,
  Pin,
  Plus,
  Reply,
  Search,
  Send,
  Smile,
  Star,
  Trash2,
  UsersRound,
  Video,
  VolumeX,
  X,
} from "lucide-react";
import {
  Suspense,
  useCallback,
  useEffect,
  useId,
  useLayoutEffect,
  useMemo,
  useRef,
  useState,
  type FormEvent,
  type ReactNode,
} from "react";

import { ConversationCallPanel } from "@/components/chat/conversation-call-panel";
import { ChatAttachmentPicker } from "@/components/chat/chat-attachment-picker";
import { MessageAttachments } from "@/components/chat/message-attachments";
import { useWorkspace } from "@/contexts/workspace-context";
import { api } from "@/lib/api/client";
import {
  PersonalChatRealtimeClient,
  type PersonalChatConnectionState,
} from "@/lib/realtime/personal-chat-realtime-client";
import { attachmentsService } from "@/services/attachments.service";
import { chatFeaturesService } from "@/services/chat-features.service";
import {
  personalSocialService as social,
  conversationName,
  type PersonalConversation,
  type PersonalFriend,
} from "@/services/personal-social.service";
import { socialChatService as chat } from "@/services/social-chat.service";
import type { CallKind } from "@/types/conversation-call";
import type {
  ConversationFeatureSummary,
  FeatureMessage,
} from "@/types/chat-features";
import type {
  ChatMessagePublic,
  MessageReceiptPublic,
  PresenceStatus,
} from "@/types/social-chat";
import { MessageReactionDialog } from "@/components/chat/message-reaction-dialog";
import { GroupAvatar,GroupsContent, } from "@/components/chat/groups-workspace";
import { FullEmojiPicker } from "@/components/chat/full-emoji-picker";
import { isSingleEmojiMessage } from "@/lib/chat-emoji";
import { useChatInbox } from "@/components/chat/chat-live-sync";
import { useVisibleChatRead } from "@/hooks/use-visible-chat-read";
import { MessageInfoDialog } from "@/components/chat/message-info-dialog";
import { CHAT_LIVE_EVENT, getChatInbox } from "@/lib/chat-live-events";
import { jumpToMessage } from "@/lib/jump-to-message";
import { VoiceRecordingIndicator } from "@/components/chat/voice-recording-indicator";
import type { VoiceRecordingSession } from "@/services/voice-messages.service";
type InboxFilter = "all" | "unread" | "groups" | "archived";
type DetailView = "overview" | "search" | "pinned" | "media";
type PermissionAction = CallKind | "record";

interface PreferencePatch {
  pinned?: boolean;
  muted?: boolean;
  archived?: boolean;
}

interface BoundAttachment {
  attachment_id: string;
  message_id: string;
  filename: string;
  content_type: string;
  size_bytes: number;
  kind: string;
}

type ChatDownloadFile = {
  attachment_id: string;
  filename: string;
};

interface MessageAttachmentsResponse {
  message_id: string;
  attachments: BoundAttachment[];
}

interface AttachmentDownloadResponse {
  attachment_id: string;
  download_url: string;
  expires_in_seconds: number;
}

interface ThreadSnapshot {
  conversationId: string;
  latest: ChatMessagePublic | null;
  summary: ConversationFeatureSummary | null;
}

const EMOJIS = [
  "😀", "😂", "😍", "❤️", "👍",
  "👏", "🎉", "🙏", "🔥", "😮",
];

const FILTERS: { key: InboxFilter; label: string }[] = [
  { key: "all", label: "All" },
  { key: "unread", label: "Unread" },
  { key: "groups", label: "Groups" },
  { key: "archived", label: "Archived" },
];

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "Request failed.";
}

function mediaError(error: unknown): string {
  if (!(error instanceof DOMException)) {
    return errorMessage(error);
  }

  switch (error.name) {
    case "NotAllowedError":
    case "SecurityError":
      return (
        "Microphone or camera access was blocked. Check this site's " +
        "browser permissions and the page's Permissions-Policy header."
      );
    case "NotFoundError":
      return (
        "The requested microphone or camera was not found. " +
        "Connect the device and check your operating-system settings."
      );
    case "NotReadableError":
      return (
        "The device could not be opened. Close other apps using " +
        "the microphone or camera, then try again."
      );
    case "OverconstrainedError":
      return "The device does not support the requested media settings.";
    case "AbortError":
      return "The media request was interrupted. Please try again.";
    default:
      return error.message || "Media access failed.";
  }
}

async function requestMediaAccess(
  action: PermissionAction,
): Promise<MediaStream> {
  if (!window.isSecureContext) {
    throw new Error(
      "Microphone and camera access require HTTPS or a trusted localhost page.",
    );
  }

  if (!navigator.mediaDevices?.getUserMedia) {
    throw new Error(
      "Microphone and camera access are unavailable in this browser context.",
    );
  }

  const policyDocument = document as Document & {
    permissionsPolicy?: {
      allowsFeature: (feature: string) => boolean;
    };
    featurePolicy?: {
      allowsFeature: (feature: string) => boolean;
    };
  };

  const policy =
    policyDocument.permissionsPolicy ??
    policyDocument.featurePolicy;

  if (policy && !policy.allowsFeature("microphone")) {
    throw new Error(
      "This page's Permissions-Policy blocks the microphone. " +
      "Allow microphone=(self) in the frontend response headers, " +
      "then restart the frontend and reload this page.",
    );
  }

  if (
    action === "VIDEO" &&
    policy &&
    !policy.allowsFeature("camera")
  ) {
    throw new Error(
      "This page's Permissions-Policy blocks the camera. " +
      "Allow camera=(self) in the frontend response headers.",
    );
  }

  return navigator.mediaDevices.getUserMedia({
    audio: true,
    video: action === "VIDEO",
  });
}

function mergeMessages(
  current: ChatMessagePublic[],
  incoming: ChatMessagePublic[],
): ChatMessagePublic[] {
  if (!incoming.length) return current;

  const map = new Map(
    current.map((message) => [message.id, message]),
  );
  let changed = false;

  for (const message of incoming) {
    const previous = map.get(message.id);

    // An older snapshot must not resurrect a deleted message.
    if (previous?.deleted_at && !message.deleted_at) {
      continue;
    }

    // Preserve a newer edit while an older request completes.
    if (
      previous?.edited_at &&
      !message.deleted_at &&
      (
        !message.edited_at ||
        Date.parse(previous.edited_at) >
          Date.parse(message.edited_at)
      )
    ) {
      continue;
    }

    if (
      previous &&
      previous.content === message.content &&
      previous.edited_at === message.edited_at &&
      previous.deleted_at === message.deleted_at &&
      previous.created_at === message.created_at &&
      previous.sender_user_id === message.sender_user_id &&
      previous.message_type === message.message_type
    ) {
      continue;
    }

    map.set(message.id, message);
    changed = true;
  }

  if (!changed) return current;

  return [...map.values()].sort((a, b) => {
    const difference =
      Date.parse(a.created_at) - Date.parse(b.created_at);

    return difference || a.id.localeCompare(b.id);
  });
}

function timeLabel(value?: string | null): string {
  if (!value) return "";

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";

  const today = new Date();
  const yesterday = new Date();
  yesterday.setDate(today.getDate() - 1);

  if (date.toDateString() === today.toDateString()) {
    return date.toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  if (date.toDateString() === yesterday.toDateString()) {
    return "Yesterday";
  }

  return date.toLocaleDateString([], {
    month: "short",
    day: "numeric",
  });
}

function dayLabel(value: string): string {
  const date = new Date(value);
  const today = new Date();
  const yesterday = new Date();
  yesterday.setDate(today.getDate() - 1);

  if (date.toDateString() === today.toDateString()) {
    return "Today";
  }

  if (date.toDateString() === yesterday.toDateString()) {
    return "Yesterday";
  }

  return date.toLocaleDateString([], {
    day: "numeric",
    month: "long",
    year: "numeric",
  });
}

function downloadText(message: ChatMessagePublic): void {
  const blob = new Blob([message.content], {
    type: "text/plain;charset=utf-8",
  });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");

  anchor.href = url;
  anchor.download = `message-${message.id}.txt`;
  anchor.click();
  URL.revokeObjectURL(url);
}
function InboxGroupAvatar({
  conversationId,
  name,
}: {
  conversationId: string;
  name: string;
}) {
  const [details, setDetails] = useState<
    Parameters<typeof GroupAvatar>[0]["details"]
  >(undefined);

  useEffect(() => {
    let active = true;
    let request = 0;

    setDetails(undefined);

    async function loadAvatar(): Promise<void> {
      const currentRequest = ++request;

      try {
        const result = await api.get<
          NonNullable<Parameters<typeof GroupAvatar>[0]["details"]>
        >(
          `/chat/group-controls/${encodeURIComponent(conversationId)}`,
        );

        if (active && currentRequest === request) {
          setDetails(result);
        }
      } catch {
        // Preserve the last loaded avatar if a refresh fails.
      }
    }

    function handleAvatarUpdate(event: Event): void {
      const update = event as CustomEvent<{
        conversationId?: string;
      }>;

      if (update.detail?.conversationId === conversationId) {
        void loadAvatar();
      }
    }

    function handleFocus(): void {
      void loadAvatar();
    }

    void loadAvatar();

    window.addEventListener(
      "workforce:group-avatar-updated",
      handleAvatarUpdate,
    );

    window.addEventListener("focus", handleFocus);

    return () => {
      active = false;
      request += 1;

      window.removeEventListener(
        "workforce:group-avatar-updated",
        handleAvatarUpdate,
      );

      window.removeEventListener("focus", handleFocus);
    };
  }, [conversationId]);

  return (
    <span className="pmInboxGroupAvatar">
      <GroupAvatar
        name={name}
        details={details}
      />
    </span>
  );
}

function Avatar({
  conversation,
  userId,
  size = "md",
  online = false,
}: {
  conversation: PersonalConversation;
  userId: string;
  size?: "sm" | "md" | "lg";
  online?: boolean;
}) {
  if (conversation.conversation_type === "group") {
    return (
      <span className={`pmAvatar pmAvatar--${size}`}>
        <InboxGroupAvatar
          key={`${userId}:${conversation.id}`}
          conversationId={conversation.id}
          name={conversationName(conversation, userId)}
        />
      </span>
    );
  }

  const other =
    conversation.conversation_type === "direct"
      ? conversation.members.find(
          (member) => member.id !== userId,
        )
      : null;

  const withAvatar = conversation as PersonalConversation & {
    avatar_url?: string | null;
  };

  const image = other?.avatar_url;
  const name = conversationName(conversation, userId);
  const initials = name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part.charAt(0).toUpperCase())
    .join("");

  return (
    <span className={`pmAvatar pmAvatar--${size}`}>
      <span className="pmAvatarImage">
        <UserAvatar userId={other?.id} src={image} name={name} fallback={initials || "U"} />
      </span>

      {online && conversation.conversation_type === "direct" && (
        <span className="pmPresenceDot" />
      )}
    </span>
  );
}

function Modal({
  title,
  children,
  onClose,
  canClose = true,
}: {
  title: string;
  children: ReactNode;
  onClose: () => void;
  canClose?: boolean;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  const titleId = useId();

  useEffect(() => {
    const dialog = ref.current;
    if (!dialog) return;

    if (!dialog.open) dialog.showModal();

    return () => {
      if (dialog.open) dialog.close();
    };
  }, []);

  return (
    <dialog
      ref={ref}
      className="pmModal"
      aria-labelledby={titleId}
      onCancel={(event) => {
        event.preventDefault();
        if (canClose) onClose();
      }}
      onClick={(event) => {
        if (event.target === event.currentTarget && canClose) {
          onClose();
        }
      }}
    >
      <div className="pmModalContent">
        <header className="pmModalHeader">
          <h2 id={titleId}>{title}</h2>
          <button
            type="button"
            className="pmIconButton"
            aria-label="Close dialog"
            disabled={!canClose}
            onClick={onClose}
          >
            <X size={20} />
          </button>
        </header>
        {children}
      </div>
    </dialog>
  );
}

function PermissionDialog({
  action,
  onClose,
  onAllowed,
}: {
  action: PermissionAction;
  onClose: () => void;
  onAllowed: (action: PermissionAction) => Promise<void>;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const busyRef = useRef(false);
  const aliveRef = useRef(false);

  useEffect(() => {
    aliveRef.current = true;
    return () => {
      aliveRef.current = false;
    };
  }, []);

  async function allow() {
    if (busyRef.current) return;

    busyRef.current = true;
    setBusy(true);
    setError("");

    let stream: MediaStream | null = null;

    try {
      stream = await requestMediaAccess(action);

      // The existing call/recording component owns its live stream.
      stream.getTracks().forEach((track) => track.stop());
      stream = null;

      if (!aliveRef.current) return;

      await onAllowed(action);
    } catch (cause) {
      if (aliveRef.current) {
        setError(mediaError(cause));
      }
    } finally {
      stream?.getTracks().forEach((track) => track.stop());
      busyRef.current = false;

      if (aliveRef.current) setBusy(false);
    }
  }

  return (
    <Modal
      title={
        action === "VIDEO"
          ? "Allow microphone and camera"
          : "Allow microphone"
      }
      onClose={onClose}
      canClose={!busy}
    >
      <div className="pmPermissionIcon">
        {action === "VIDEO" ? (
          <Video size={29} />
        ) : (
          <Mic size={29} />
        )}
      </div>

      <p className="pmModalDescription">
        {action === "record"
          ? "Allow microphone access to record a voice message."
          : "Allow device access before continuing to your call."}
      </p>

      <p className="pmMutedText">
        Your browser controls the permission prompt. If access is
        blocked, use the site controls beside the address bar.
      </p>

      {error && (
        <p className="pmInlineError" role="alert">
          {error}
        </p>
      )}

      <div className="pmModalFooter">
        <button
          type="button"
          className="pmSecondaryButton"
          disabled={busy}
          onClick={onClose}
        >
          Cancel
        </button>
        <button
          type="button"
          className="pmPrimaryButton"
          disabled={busy}
          onClick={() => void allow()}
        >
          {busy ? "Checking access…" : "Allow and continue"}
        </button>
      </div>
    </Modal>
  );
}

function NewMessageDialog({
  friends,
  onClose,
  onCreated,
}: {
  friends: PersonalFriend[];
  onClose: () => void;
  onCreated: (conversationId: string) => Promise<void>;
}) {
  const [mode, setMode] = useState<"direct" | "group">("direct");
  const [search, setSearch] = useState("");
  const [name, setName] = useState("");
  const [memberIds, setMemberIds] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const busyRef = useRef(false);

  const available = friends.filter(
    (friend) =>
      friend.status === "accepted" &&
      (
        friend.person.name.toLowerCase().includes(search.toLowerCase()) ||
        friend.person.username.toLowerCase().includes(search.toLowerCase())
      ),
  );

  async function create(userId?: string) {
    if (busyRef.current) return;

    busyRef.current = true;
    setBusy(true);
    setError("");

    try {
      const conversation =
        mode === "group"
          ? await chat.createGroup({
              name: name.trim(),
              member_user_ids: memberIds,
            })
          : await chat.createOrGetDirect(userId!);

      await onCreated(conversation.id);
    } catch (cause) {
      setError(errorMessage(cause));
    } finally {
      busyRef.current = false;
      setBusy(false);
    }
  }

  return (
    <Modal title="New message" onClose={onClose} canClose={!busy}>
      <div className="pmTabs">
        <button
          type="button"
          className={mode === "direct" ? "isActive" : ""}
          onClick={() => setMode("direct")}
        >
          Direct message
        </button>
        <button
          type="button"
          className={mode === "group" ? "isActive" : ""}
          onClick={() => setMode("group")}
        >
          New group
        </button>
      </div>

      {mode === "group" && (
        <label className="pmField">
          Group name
          <input
            value={name}
            maxLength={120}
            onChange={(event) => setName(event.target.value)}
            placeholder="Enter group name"
          />
        </label>
      )}

      <label className="pmSearch">
        <Search size={18} />
        <input
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          placeholder="Search accepted friends"
          aria-label="Search accepted friends"
        />
      </label>

      <div className="pmFriendList">
        {available.map((friend) =>
          mode === "group" ? (
            <label className="pmFriendChoice" key={friend.id}>
              <input
                type="checkbox"
                checked={memberIds.includes(friend.person.id)}
                disabled={busy}
                onChange={(event) =>
                  setMemberIds((current) =>
                    event.target.checked
                      ? [...current, friend.person.id]
                      : current.filter(
                          (id) => id !== friend.person.id,
                        ),
                  )
                }
              />
              <span>
                <strong>{friend.person.name}</strong>
                <small>@{friend.person.username}</small>
              </span>
            </label>
          ) : (
            <button
              key={friend.id}
              type="button"
              className="pmFriendChoice"
              disabled={busy}
              onClick={() => void create(friend.person.id)}
            >
              <span>
                <strong>{friend.person.name}</strong>
                <small>@{friend.person.username}</small>
              </span>
              <ChevronRight size={18} />
            </button>
          ),
        )}

        {!available.length && (
          <p className="pmMutedText">
            No matching accepted friends.{" "}
            <Link href="/friends">Open Friends</Link>.
          </p>
        )}
      </div>

      {error && (
        <p className="pmInlineError" role="alert">{error}</p>
      )}

      {mode === "group" && (
        <div className="pmModalFooter">
          <button
            type="button"
            className="pmPrimaryButton"
            disabled={busy || !name.trim() || !memberIds.length}
            onClick={() => void create()}
          >
            {busy ? "Creating…" : "Create group"}
          </button>
        </div>
      )}
    </Modal>
  );
}

function closeActionMenu(event: {
  target: EventTarget | null;
  currentTarget: HTMLElement;
}) {
  if (!(event.target instanceof Element)) return;

  const button = event.target.closest("button");

  if (!button || button.disabled) return;

  const menu = event.currentTarget.closest("details");

  if (menu instanceof HTMLDetailsElement) {
    menu.open = false;
  }
}


export default function ChatPage() {
  return (
    <>
      <style jsx global>{MESSAGES_CSS}</style>
      <Suspense fallback={<p role="status">Loading messages…</p>}>
        <ChatAccount />
      </Suspense>
    </>
  );
}

function ChatAccount() {
  const { user, loading } = useWorkspace();

  if (loading && !user) {
    return <p role="status">Loading your account…</p>;
  }

  if (!user) {
    return (
      <p>
        Please <Link href="/login">sign in</Link> to use Messages.
      </p>
    );
  }

  if (!user.is_email_verified) {
    return <p role="alert">Verify your email to use Messages.</p>;
  }

  return <MessagesScreen key={user.id} userId={user.id} />;
}

function MessagesScreen({ userId }: { userId: string }) {
  const params = useSearchParams();
  const requested = params.get("conversation");
  const liveInbox = useChatInbox(userId);

  useEffect(() => {
    if (liveInbox) setSummaries(liveInbox);
  }, [liveInbox]);

  const [conversations, setConversations] =
    useState<PersonalConversation[]>([]);
  const [friends, setFriends] = useState<PersonalFriend[]>([]);
  const [summaries, setSummaries] =
    useState<ConversationFeatureSummary[]>([]);
  const [previews, setPreviews] =
    useState<Record<string, ChatMessagePublic>>({});
  const [selectedId, setSelectedId] =
    useState<string | null>(requested);
  const [filter, setFilter] = useState<InboxFilter>("all");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [detailsOpen, setDetailsOpen] = useState(true);
  const [newMessageOpen, setNewMessageOpen] = useState(false);
  const [inboxMenuOpen, setInboxMenuOpen] = useState(false);

  const aliveRef = useRef(false);
  const requestRef = useRef<Promise<void> | null>(null);
  const initializedRef = useRef(false);
  
  useEffect(() => {
    function handleOutsideClick(event: PointerEvent) {
      if (!(event.target instanceof Node)) return;

      const target = event.target;

      document
        .querySelectorAll<HTMLDetailsElement>(
          ".personalMessages details[open]",
        )
        .forEach((menu) => {
          if (!menu.contains(target)) {
            menu.open = false;
          }
        });
    }

    function handleEscape(event: KeyboardEvent) {
      if (event.key !== "Escape") return;

      document
        .querySelectorAll<HTMLDetailsElement>(
          ".personalMessages details[open]",
        )
        .forEach((menu) => {
          menu.open = false;
        });
    }

    document.addEventListener(
      "pointerdown",
      handleOutsideClick,
    );

    document.addEventListener(
      "keydown",
      handleEscape,
    );

    return () => {
      document.removeEventListener(
        "pointerdown",
        handleOutsideClick,
      );

      document.removeEventListener(
        "keydown",
        handleEscape,
      );
    };
  }, []);

  useEffect(() => {
    aliveRef.current = true;
    return () => {
      aliveRef.current = false;
    };
  }, []);

  const load = useCallback((): Promise<void> => {
    if (requestRef.current) return requestRef.current;

    const promise = (async () => {
      try {
        const results = await Promise.allSettled([
          social.conversations(),
          social.friends(),
          chatFeaturesService.listConversationFeatures(),
        ]);

        if (!aliveRef.current) return;

        const failures: string[] = [];

        if (results[0].status === "fulfilled") {
          const items = results[0].value;
          setConversations(items);

          setSelectedId((previous) =>
            items.some((item) => item.id === previous)
              ? previous
              : items.some((item) => item.id === requested)
                ? requested
                : items[0]?.id ?? null,
          );

          // Hydrate previews once, without timed polling.
          if (!initializedRef.current) {
            initializedRef.current = true;

            const previewResults = await Promise.allSettled(
              items.map(async (item) => {
                const page = await chat.listMessagePage(
                  item.id,
                  null,
                  1,
                );
                return [item.id, page.items[0]] as const;
              }),
            );

            if (aliveRef.current) {
              setPreviews((current) => {
                const next = { ...current };

                for (const result of previewResults) {
                  if (
                    result.status === "fulfilled" &&
                    result.value[1] &&
                    !next[result.value[0]]
                  ) {
                    next[result.value[0]] = result.value[1];
                  }
                }

                return next;
              });
            }
          }
        } else {
          failures.push(errorMessage(results[0].reason));
        }

        if (results[1].status === "fulfilled") {
          setFriends(results[1].value.items);
        } else {
          failures.push(errorMessage(results[1].reason));
        }

        if (results[2].status === "fulfilled") {
          setSummaries(getChatInbox(userId) ?? results[2].value);
        } else {
          failures.push(errorMessage(results[2].reason));
        }

        if (aliveRef.current) {
          setError([...new Set(failures)].join(" "));
        }
      } catch (cause) {
        if (aliveRef.current) setError(errorMessage(cause));
      } finally {
        requestRef.current = null;
        if (aliveRef.current) setLoading(false);
      }
    })();

    requestRef.current = promise;
    return promise;
  }, [requested, userId]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    if (
      requested &&
      conversations.some((item) => item.id === requested)
    ) {
      setSelectedId(requested);
    }
  }, [requested, conversations]);

  useEffect(() => {
    let stopped = false;
    const sequences = new Map<string, number>();

    function changed(event: Event) {
      const detail = (event as CustomEvent).detail;
      if (detail.owner !== userId) return;

      const frame = detail.event;
      const type = String(frame.event_type ?? frame.event ?? "");

      if (!/created|updated|deleted|member/.test(type)) return;

      const id = frame.conversation_id ?? frame.data?.conversation_id;
      if (typeof id !== "string") return;

      const request = (sequences.get(id) ?? 0) + 1;
      sequences.set(id, request);

      void chat.listMessagePage(id, null, 1).then(page => {
        if (stopped || request !== sequences.get(id)) return;

        const latest = page.items[0];

        if (latest) {
          setPreviews(current => ({ ...current, [id]: latest }));
          setConversations(current =>
            current.map(item =>
              item.id === id
                ? { ...item, updated_at: latest.created_at }
                : item,
            ),
          );
        }
      }).catch(() => {});

      void load();
    }

    window.addEventListener(CHAT_LIVE_EVENT, changed);

    return () => {
      stopped = true;
      window.removeEventListener(CHAT_LIVE_EVENT, changed);
    };
  }, [userId, load]);

  const onSnapshot = useCallback((snapshot: ThreadSnapshot) => {
    if (snapshot.latest) {
      setPreviews((current) => ({
        ...current,
        [snapshot.conversationId]: snapshot.latest!,
      }));
    }

    if (snapshot.summary) {
      setSummaries((current) => {
        const remaining = current.filter(
          (item) =>
            item.conversation_id !== snapshot.conversationId,
        );

        return [...remaining, snapshot.summary!];
      });
    }
  }, []);

  const closeDetails = useCallback(() => {
    setDetailsOpen(false);
  }, []);

  const openDetails = useCallback(() => {
    setDetailsOpen(true);
  }, []);

  const summaryById = useMemo(
    () =>
      new Map(
        summaries.map((summary) => [
          summary.conversation_id,
          summary,
        ]),
      ),
    [summaries],
  );

  const selected =
    conversations.find((item) => item.id === selectedId) ?? null;

  const visible = conversations
    .filter((conversation) => {
      const summary = summaryById.get(conversation.id);

      if (
        !conversationName(conversation, userId)
          .toLowerCase()
          .includes(search.trim().toLowerCase())
      ) {
        return false;
      }

      if (filter === "archived") return Boolean(summary?.archived);
      if (summary?.archived) return false;
      if (filter === "unread") return (summary?.unread_count ?? 0) > 0;
      if (filter === "groups") {
        return conversation.conversation_type === "group";
      }

      return true;
    })
    .sort((a, b) => {
      const pinDifference =
        Number(summaryById.get(b.id)?.pinned ?? false) -
        Number(summaryById.get(a.id)?.pinned ?? false);

      if (pinDifference) return pinDifference;

      return (
        Date.parse(previews[b.id]?.created_at ?? b.updated_at) -
        Date.parse(previews[a.id]?.created_at ?? a.updated_at)
      );
    });

  async function onCreated(conversationId: string) {
    await load();
    setSelectedId(conversationId);
    setFilter("all");
    setNewMessageOpen(false);
  }

  return (
    <main className="personalMessages">
      <header className="pmPageHeader">
        <div>
          <h1>Messages</h1>
          <p>Stay connected with your team and contacts</p>
        </div>

        <button
          type="button"
          className="pmPrimaryButton"
          onClick={() => setNewMessageOpen(true)}
        >
          <Plus size={22} />
          New message
        </button>
      </header>

      {error && (
        <div className="pmPageError" role="alert">
          <span>{error}</span>
          <button type="button" onClick={() => void load()}>
            Retry
          </button>
        </div>
      )}

      <div
        className={`pmShell ${
          detailsOpen && selected ? "" : "pmShell--noDetails"
        }`}
      >
        <aside className="pmInbox">
          <header className="pmInboxHeader">
            <h2>Inbox</h2>
            <div className="pmMenuAnchor">
              <button
                type="button"
                className="pmIconButton pmBorderButton"
                aria-label="Inbox options"
                aria-expanded={inboxMenuOpen}
                onClick={() => setInboxMenuOpen((current) => !current)}
              >
                <MoreHorizontal size={20} />
              </button>

              {inboxMenuOpen && (
                <div className="pmMenu">
                  <button
                    type="button"
                    onClick={() => {
                      setInboxMenuOpen(false);
                      setNewMessageOpen(true);
                    }}
                  >
                    <Plus size={16} /> New message
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setInboxMenuOpen(false);
                      void load();
                    }}
                  >
                    <MessageCircle size={16} /> Refresh inbox
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setInboxMenuOpen(false);
                      setFilter("archived");
                    }}
                  >
                    <Archive size={16} /> Archived conversations
                  </button>
                </div>
              )}
            </div>
          </header>

          <label className="pmSearch">
            <Search size={18} />
            <input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search conversations"
              aria-label="Search conversations"
            />
          </label>

          <div className="pmFilters" aria-label="Inbox filters">
            {FILTERS.map((item) => (
              <button
                key={item.key}
                type="button"
                aria-pressed={filter === item.key}
                className={filter === item.key ? "isActive" : ""}
                onClick={() => setFilter(item.key)}
              >
                {item.label}
              </button>
            ))}
          </div>

          <nav className="pmConversationList" aria-label="Conversations">
            {loading && !conversations.length ? (
              <p className="pmListNotice" role="status">
                Loading conversations…
              </p>
            ) : !visible.length ? (
              <p className="pmListNotice">
                No conversations in this view.
              </p>
            ) : (
              visible.map((conversation) => {
                const summary = summaryById.get(conversation.id);
                const preview = previews[conversation.id];
                const peer = conversation.members.find(
                  (member) => member.id !== userId,
                );
                const friend = friends.find(
                  (item) => item.person.id === peer?.id,
                );

                return (
                  <button
                    type="button"
                    key={conversation.id}
                    className={`pmConversation ${
                      selectedId === conversation.id ? "isActive" : ""
                    }`}
                    onClick={() => setSelectedId(conversation.id)}
                  >
                    <Avatar
                      conversation={conversation}
                      userId={userId}
                      online={friend?.presence === "online"}
                    />
                    <span className="pmConversationText">
                      <strong>
                        {conversationName(conversation, userId)}
                      </strong>
                      <small>
                        {preview
                          ? preview.deleted_at
                            ? "Message deleted"
                            : preview.content
                          : conversation.conversation_type === "group"
                            ? `${conversation.members.length} members`
                            : "Direct conversation"}
                      </small>
                    </span>
                    <span className="pmConversationMeta">
                      <time>{timeLabel(preview?.created_at)}</time>
                      <span className="pmConversationIndicators">
                        {summary?.muted && <VolumeX size={16} />}
                        {summary?.pinned && <Pin size={15} />}
                        {(summary?.unread_count ?? 0) > 0 && (
                          <span className="pmUnread">
                            {summary!.unread_count}
                          </span>
                        )}
                      </span>
                    </span>
                  </button>
                );
              })
            )}
          </nav>
        </aside>

        {selected ? (
          selected.conversation_type === "group" ? (
            <div className="pmGroupHost">
              <GroupsContent
                key={`${userId}:${selected.id}`}
                conversationId={selected.id}
                embedded
              />
            </div>
          ) : (
            <ConversationThread
              key={`${userId}:${selected.id}`}
              conversation={selected}
              userId={userId}
              detailsOpen={detailsOpen}
              onCloseDetails={closeDetails}
              onOpenDetails={openDetails}
              onSnapshot={onSnapshot}
            />
          )
        ) : (
          <section className="pmThread pmEmpty">
            <MessageCircle size={38} />
            <h2>Select a conversation</h2>
            <p>Choose a friend or group, or start a new message.</p>
          </section>
        )}
      </div>

      {newMessageOpen && (
        <NewMessageDialog
          friends={friends}
          onClose={() => setNewMessageOpen(false)}
          onCreated={onCreated}
        />
      )}
    </main>
  );
}

function ConversationThread({
  conversation,
  userId,
  detailsOpen,
  onCloseDetails,
  onOpenDetails,
  onSnapshot,
}: {
  conversation: PersonalConversation;
  userId: string;
  detailsOpen: boolean;
  onCloseDetails: () => void;
  onOpenDetails: () => void;
  onSnapshot: (snapshot: ThreadSnapshot) => void;
}) {
  const conversationId = conversation.id;
  const name = conversationName(conversation, userId);
  const peerId =
    conversation.conversation_type === "direct"
      ? conversation.members.find((member) => member.id !== userId)?.id
      : undefined;

  const [messages, setMessages] = useState<ChatMessagePublic[]>([]);
  const [features, setFeatures] =
    useState<Record<string, FeatureMessage>>({});
  const [preference, setPreference] =
    useState<ConversationFeatureSummary | null>(null);
  const [receipts, setReceipts] =
    useState<Record<string, MessageReceiptPublic[]>>({});
  const [infoTarget, setInfoTarget] =
    useState<ChatMessagePublic | null>(null);
  const [draft, setDraft] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const [replyTo, setReplyTo] = useState<ChatMessagePublic | null>(null);
  const [reactionDetails, setReactionDetails] = useState<{message: ChatMessagePublic;emoji: string;} | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editingText, setEditingText] = useState("");
  const [emojiOpen, setEmojiOpen] = useState(false);
  const [recording, setRecording] = useState(false);
  const [callKind, setCallKind] = useState<CallKind | null>(null);
  const [pendingPermission, setPendingPermission] =
    useState<PermissionAction | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [connection, setConnection] =
    useState<PersonalChatConnectionState>("connecting");
  const [presence, setPresence] = useState<PresenceStatus | null>(null);
  const [detailView, setDetailView] = useState<DetailView>("overview");
  const [messageSearch, setMessageSearch] = useState("");
  const [threadSearchOpen, setThreadSearchOpen] = useState(false);
  const [moreOpen, setMoreOpen] = useState(false);
  const [typingIds, setTypingIds] = useState<string[]>([]);
  const [historyCursor, setHistoryCursor] = useState<string | null>(null);
  const [hasOlder, setHasOlder] = useState(false);
  const [loadingOlder, setLoadingOlder] = useState(false);
  const [initialLoading, setInitialLoading] = useState(true);

  const [sharedFiles, setSharedFiles] = useState<
    BoundAttachment[]
  >([]);

  const [messageFiles, setMessageFiles] = useState<
    Record<string, ChatDownloadFile[]>
  >({});

  const [mediaLoading, setMediaLoading] = useState(false);

  const viewportRef = useRef<HTMLDivElement>(null);
  const composerRef = useRef<HTMLTextAreaElement>(null);
  const aliveRef = useRef(false);
  const lifecycleRef = useRef(0);
  const busyRef = useRef(false);
  const olderBusyRef = useRef(false);
  const initializedHistoryRef = useRef(false);
  const scrollAtBottomRef = useRef(true);
  const preserveScrollRef = useRef<{
    height: number;
    top: number;
  } | null>(null);
  const lastReadMessageRef = useRef<string | null>(null);
  const clientMessageIdRef = useRef(crypto.randomUUID());
  const typingLastSentRef = useRef(0);
  const typingStopTimerRef =
    useRef<ReturnType<typeof setTimeout> | null>(null);
  const typingExpiryRef =
    useRef<ReturnType<typeof setTimeout> | null>(null);
  const preferenceRef = useRef<ConversationFeatureSummary | null>(null);

  const mediaPermissionRef = useRef({
    microphone: false,
    camera: false,
  });

  const mediaCheckInFlightRef = useRef(false);

  const recorderRef =
    useRef<VoiceRecordingSession | null>(null);

  function cancelVoiceRecording(): void {
    const recorder = recorderRef.current;

    recorderRef.current = null;

    try {
      recorder?.cancel();
    } finally {
      setRecording(false);
    }
  }

  const participantKey = conversation.members
    .filter((member) => member.id !== userId)
    .map((member) => member.id)
    .sort()
    .join(",");

  const invitedUserIds = useMemo(
    () => participantKey ? participantKey.split(",") : [],
    [participantKey],
  );

  const closeCall = useCallback(() => setCallKind(null), []);

  useEffect(() => {
    aliveRef.current = true;
    lifecycleRef.current += 1;

    return () => {
      aliveRef.current = false;
      lifecycleRef.current += 1;

      if (typingStopTimerRef.current) {
        clearTimeout(typingStopTimerRef.current);
      }

      if (typingExpiryRef.current) {
        clearTimeout(typingExpiryRef.current);
      }

      void chat.stopTyping(conversationId).catch(() => undefined);

      try {
        recorderRef.current?.cancel();
      } catch {
        // Cleanup must not interrupt navigation.
      }

      recorderRef.current = null;
    };
  }, [conversationId]);

  const refresh = useCallback(async () => {
    const lifecycle = lifecycleRef.current;

    const [page, featureItems, summaries] = await Promise.all([
      chat.listMessagePage(conversationId, null, 50),
      chatFeaturesService.listMessages(conversationId),
      chatFeaturesService.listConversationFeatures(),
    ]);

    if (
      !aliveRef.current ||
      lifecycle !== lifecycleRef.current
    ) {
      return;
    }

    setMessages((current) => mergeMessages(current, page.items));
    setFeatures(
      Object.fromEntries(featureItems.map((item) => [item.id, item])),
    );

    const summary =
      summaries.find(
        (item) => item.conversation_id === conversationId,
      ) ?? null;

    preferenceRef.current = summary;
    setPreference(summary);

    if (!initializedHistoryRef.current) {
      initializedHistoryRef.current = true;
      setHistoryCursor(page.next_cursor);
      setHasOlder(page.has_more);
    }

    const latest = [...page.items].sort(
      (a, b) => Date.parse(b.created_at) - Date.parse(a.created_at),
    )[0] ?? null;

    onSnapshot({ conversationId, latest, summary });
    setInitialLoading(false);

    const own = page.items.filter(
      (item) =>
        item.sender_user_id === userId &&
        !item.deleted_at,
    );

    const receiptResults = await Promise.allSettled(
      own.map(async (message) => [
        message.id,
        await chat.listReadReceipts(conversationId, message.id),
      ] as const),
    );

    if (
      !aliveRef.current ||
      lifecycle !== lifecycleRef.current
    ) {
      return;
    }

    setReceipts((current) => {
      const next = { ...current };

      for (const result of receiptResults) {
        if (result.status === "fulfilled") {
          next[result.value[0]] = result.value[1].filter(receipt => receipt.user_id !== userId);
        }
      }

      return next;
    });
  }, [conversationId, userId, onSnapshot]);

  const refreshPresence = useCallback(async () => {
    if (!peerId) return;

    try {
      const result = await chat.getPresence(peerId);
      if (aliveRef.current) setPresence(result.status);
    } catch {
      // Unknown presence is not displayed as online.
    }
  }, [peerId]);

  useEffect(() => {
    void refreshPresence();
  }, [refreshPresence]);

  useEffect(() => {
    let stopped = false;
    let running = false;
    let requested = false;

    async function refreshSafely() {
      if (stopped) return;

      requested = true;
      if (running) return;

      running = true;

      try {
        do {
          requested = false;
          await refresh();
        } while (requested && !stopped);
      } catch (cause) {
        if (!stopped) {
          setError(errorMessage(cause));
          setInitialLoading(false);
        }
      } finally {
        running = false;
      }
    }

    async function refreshTyping() {
      try {
        const result = await chat.listTypingUsers(conversationId);
        if (stopped) return;

        setTypingIds(
          (result.user_ids ?? []).filter((id) => id !== userId),
        );

        if (typingExpiryRef.current) {
          clearTimeout(typingExpiryRef.current);
        }

        // Expire the indicator without polling.
        typingExpiryRef.current = setTimeout(() => {
          if (!stopped) setTypingIds([]);
        }, 6000);
      } catch {
        // Typing is optional and must not block messages.
      }
    }

    const client = new PersonalChatRealtimeClient({
      conversationId,

      onMessages: (incoming) => {
        if (stopped || !incoming.length) return;
        setMessages((current) => mergeMessages(current, incoming));
      },

      onStateChange: (state) => {
        if (stopped) return;
        setConnection(state);

        if (state === "connected") {
          void refreshSafely();
          void refreshTyping();
          void refreshPresence();
        }
      },

      onEvent: (event) => {
        if (stopped) return;

        if (
          event.event === "pong" ||
          event.event === "command.accepted" ||
          event.event === "command.rejected"
        ) {
          return;
        }

        const eventConversationId =
          event.conversation_id ?? event.data?.conversation_id;

        if (eventConversationId === conversationId) {
          const eventType = String(
            event.event_type ?? event.event ?? "",
          ).toLowerCase();

          if (eventType.includes("typing")) {
            void refreshTyping();
          } else {
            void refreshSafely();
          }
        }

        const eventType = String(
          event.event_type ?? event.event ?? "",
        ).toLowerCase();

        if (eventType.includes("presence")) {
          void refreshPresence();
        }
      },

      onError: (cause) => {
        if (!stopped) setError(cause.message);
      },
    });

    function resumeVisible() {
      if (stopped || document.hidden) return;

      void client.connect();
      client.requestRecovery();
      void refreshSafely();
      void refreshPresence();
    }

    void refreshSafely();
    void client.connect();

    document.addEventListener("visibilitychange", resumeVisible);
    window.addEventListener("online", resumeVisible);
    window.addEventListener("focus", resumeVisible);

    return () => {
      stopped = true;
      document.removeEventListener("visibilitychange", resumeVisible);
      window.removeEventListener("online", resumeVisible);
      window.removeEventListener("focus", resumeVisible);
      client.disconnect();
    };
  }, [
    conversationId,
    userId,
    refresh,
    refreshPresence,
  ]);

  useVisibleChatRead(
    conversationId,
    userId,
    messages,
    viewportRef,
  );

  useLayoutEffect(() => {
    const viewport = viewportRef.current;
    if (!viewport) return;

    const anchor = preserveScrollRef.current;

    if (anchor) {
      viewport.scrollTop =
        anchor.top + viewport.scrollHeight - anchor.height;
      preserveScrollRef.current = null;
      return;
    }

    if (scrollAtBottomRef.current) {
      viewport.scrollTop = viewport.scrollHeight;
    }
  }, [messages]);

  const loadedMessageKey = messages.map((item) => item.id).join(",");

  useEffect(() => {
    if (detailView !== "media" || !detailsOpen) return;

    let stopped = false;
    setMediaLoading(true);

    const ids = loadedMessageKey.split(",").filter(Boolean);

    void Promise.allSettled(
      ids.map((id) =>
        api.get<MessageAttachmentsResponse>(
          `/chat/${conversationId}/messages/${id}/attachments`,
        ),
      ),
    ).then((results) => {
      if (stopped) return;

      const filesById = new Map<string, BoundAttachment>();
      let failures = 0;

      for (const result of results) {
        if (result.status === "fulfilled") {
          for (const attachment of result.value.attachments) {
            filesById.set(attachment.attachment_id, attachment);
          }
        } else {
          failures += 1;
        }
      }

      setSharedFiles([...filesById.values()]);
      setMediaLoading(false);

      if (failures) {
        setError("Some shared files could not be loaded. Reopen Shared media to retry.");
      }
    });

    return () => {
      stopped = true;
    };
  }, [
    conversationId,
    detailView,
    detailsOpen,
    loadedMessageKey,
  ]);

  async function run(action: () => Promise<void>) {
    if (busyRef.current) return;

    busyRef.current = true;
    setBusy(true);
    setError("");

    try {
      await action();
    } catch (cause) {
      if (aliveRef.current) setError(errorMessage(cause));
    } finally {
      busyRef.current = false;
      if (aliveRef.current) setBusy(false);
    }
  }

  function stopTyping() {
    if (typingStopTimerRef.current) {
      clearTimeout(typingStopTimerRef.current);
      typingStopTimerRef.current = null;
    }

    void chat.stopTyping(conversationId).catch(() => undefined);
  }

  function changeDraft(value: string) {
    setDraft(value);

    if (!value.trim()) {
      stopTyping();
      return;
    }

    if (Date.now() - typingLastSentRef.current > 3000) {
      typingLastSentRef.current = Date.now();
      void chat.startTyping(conversationId).catch(() => undefined);
    }

    if (typingStopTimerRef.current) {
      clearTimeout(typingStopTimerRef.current);
    }

    typingStopTimerRef.current = setTimeout(stopTyping, 2000);
  }

  async function sendMessage(event?: FormEvent) {
    event?.preventDefault();

    const content = draft.trim();

    if (
      busyRef.current ||
      !conversation.can_message ||
      (!content && !files.length)
    ) {
      return;
    }

    const savedFiles = [...files];
    const savedReply = replyTo;
    const messageId = clientMessageIdRef.current;

    await run(async () => {
      const attachmentIds: string[] = [];

      for (const file of savedFiles) {
        const uploaded =
          await attachmentsService.uploadConversationFile(
            conversationId,
            file,
          );

        attachmentIds.push(uploaded.attachment_id);
      }

      const message = await chatFeaturesService.sendMessage(
        conversationId,
        content || savedFiles.map((file) => file.name).join(", "),
        {
          clientMessageId: messageId,
          replyToMessageId: savedReply?.id ?? null,
        },
      );

      if (attachmentIds.length) {
        await attachmentsService.bindConversationAttachments(
          conversationId,
          message.id,
          attachmentIds,
        );
      }

      clientMessageIdRef.current = crypto.randomUUID();

      if (!aliveRef.current) return;

      scrollAtBottomRef.current = true;
      setMessages((current) => mergeMessages(current, [message]));
      setDraft("");
      setFiles([]);
      setReplyTo(null);
      stopTyping();

      onSnapshot({
        conversationId,
        latest: message,
        summary: preferenceRef.current,
      });

      await refresh();
    });
  }


  async function startMediaAction(
    action: PermissionAction,
  ): Promise<void> {
    if (
      busyRef.current ||
      mediaCheckInFlightRef.current ||
      !conversation.can_message ||
      callKind !== null ||
      pendingPermission !== null
    ) {
      return;
    }

    mediaCheckInFlightRef.current = true;

    const generation = lifecycleRef.current;

    async function readPermission(
      name: "microphone" | "camera",
    ): Promise<PermissionState | null> {
      if (!navigator.permissions?.query) {
        return null;
      }

      try {
        const result = await navigator.permissions.query({
          name: name as PermissionName,
        });

        return result.state;
      } catch {
        return null;
      }
    }

    try {
      const needsCamera = action === "VIDEO";

      const [microphoneState, cameraState] =
        await Promise.all([
          readPermission("microphone"),
          needsCamera
            ? readPermission("camera")
            : Promise.resolve(null),
        ]);

      if (
        !aliveRef.current ||
        generation !== lifecycleRef.current
      ) {
        return;
      }

      const microphoneAllowed =
        microphoneState === "granted" ||
        (
          microphoneState === null &&
          mediaPermissionRef.current.microphone
        );

      const cameraAllowed =
        !needsCamera ||
        cameraState === "granted" ||
        (
          cameraState === null &&
          mediaPermissionRef.current.camera
        );

      if (!microphoneAllowed || !cameraAllowed) {
        setPendingPermission(action);
        return;
      }

      await onPermissionAllowed(action);
    } catch (cause) {
      if (
        aliveRef.current &&
        generation === lifecycleRef.current
      ) {
        mediaPermissionRef.current = {
          microphone: false,
          camera: false,
        };

        setError(mediaError(cause));
        setPendingPermission(action);
      }
    } finally {
      mediaCheckInFlightRef.current = false;
    }
  }

  async function onPermissionAllowed(
    action: PermissionAction,
  ): Promise<void> {
    if (!aliveRef.current) return;

    mediaPermissionRef.current.microphone = true;

    if (action === "VIDEO") {
      mediaPermissionRef.current.camera = true;
    }

    if (action !== "record") {
      setPendingPermission(null);
      setCallKind(action);
      return;
    }

    const module = await import(
      "@/services/voice-messages.service"
    );

    const recorder = await module.startVoiceRecording(
      conversationId,
    );

    if (!aliveRef.current) {
      recorder.cancel();
      return;
    }

    recorderRef.current = recorder;
    setRecording(true);
    setPendingPermission(null);
  }

  async function toggleVoiceRecording() {
    if (!recording) {
      await startMediaAction("record");
      return;
    }

    await run(async () => {
      const recorder = recorderRef.current;

      if (!recorder) {
        setRecording(false);
        return;
      }

      try {
        const message = await recorder.stop();

        if (!aliveRef.current) return;

        if (message) {
          scrollAtBottomRef.current = true;

          setMessages(current =>
            mergeMessages(current, [message]),
          );
        }

        await refresh();
      } finally {
        recorder.cancel();

        if (recorderRef.current === recorder) {
          recorderRef.current = null;
        }

        if (aliveRef.current) {
          setRecording(false);
        }
      }
    });
  }

  async function updatePreference(patch: PreferencePatch) {
    await run(async () => {
      const updated =
        await chatFeaturesService.setConversationPreference(
          conversationId,
          patch,
        );

      if (!aliveRef.current) return;

      preferenceRef.current = updated;
      setPreference(updated);
      setMoreOpen(false);

      onSnapshot({
        conversationId,
        latest: messages[messages.length - 1] ?? null,
        summary: updated,
      });
    });
  }

  async function toggleMessagePin(message: ChatMessagePublic) {
    await run(async () => {
      if (features[message.id]?.pinned) {
        await chatFeaturesService.unpinMessage(
          conversationId,
          message.id,
        );
      } else {
        await chatFeaturesService.pinMessage(
          conversationId,
          message.id,
        );
      }

      await refresh();
    });
  }

  function beginReply(message: ChatMessagePublic): void {
    setReplyTo(message);
    setEmojiOpen(false);

    requestAnimationFrame(() => {
      const composer = composerRef.current;

      if (!composer || composer.disabled) {
        return;
      }

      composer.focus({ preventScroll: true });

      const position = composer.value.length;
      composer.setSelectionRange(position, position);
    });
  }

  async function react(message: ChatMessagePublic, emoji: string) {
    await run(async () => {
      await chatFeaturesService.addReaction(
        conversationId,
        message.id,
        emoji,
      );
      await refresh();
    });
  }

  async function removeMessageReaction(
    message: ChatMessagePublic,
    emoji: string,
  ): Promise<void> {
    await run(async () => {
      await chatFeaturesService.removeReaction(
        conversationId,
        message.id,
        emoji,
      );

      if (!aliveRef.current) {
        return;
      }

      setReactionDetails(null);
      await refresh();
    });
  }
  
  async function deleteChatMessage(messageId: string) {
    await run(async () => {
      const deleted = await chat.deleteMessage(
        conversationId,
        messageId,
      );

      if (!aliveRef.current) return;

      setMessages((current) => mergeMessages(current, [deleted]));
      await refresh();
    });
  }

  async function loadOlder() {
    if (
      olderBusyRef.current ||
      !hasOlder ||
      !historyCursor
    ) {
      return;
    }

    olderBusyRef.current = true;
    setLoadingOlder(true);

    try {
      const page = await chat.listMessagePage(
        conversationId,
        historyCursor,
        50,
      );

      if (!aliveRef.current) return;

      const viewport = viewportRef.current;

      if (viewport) {
        preserveScrollRef.current = {
          height: viewport.scrollHeight,
          top: viewport.scrollTop,
        };
      }

      setMessages((current) => mergeMessages(current, page.items));
      setHistoryCursor(page.next_cursor);
      setHasOlder(page.has_more);
    } catch (cause) {
      if (aliveRef.current) setError(errorMessage(cause));
    } finally {
      olderBusyRef.current = false;
      if (aliveRef.current) setLoadingOlder(false);
    }
  }

  async function loadMessageFiles(
    messageId: string,
  ): Promise<void> {
    const generation = lifecycleRef.current;

    try {
      const result = await api.get<{
        attachments: ChatDownloadFile[];
      }>(
        `/chat/${conversationId}/messages/${messageId}/attachments`,
      );

      if (
        !aliveRef.current ||
        generation !== lifecycleRef.current
      ) {
        return;
      }

      setMessageFiles((current) => ({
        ...current,
        [messageId]: result.attachments,
      }));
    } catch (cause) {
      if (
        aliveRef.current &&
        generation === lifecycleRef.current
      ) {
        setError(errorMessage(cause));
      }
    }
  }

  async function downloadAttachment(attachmentId: string) {
    await run(async () => {
      const result = await api.post<AttachmentDownloadResponse>(
        `/attachments/${attachmentId}/download`,
        {},
      );

      const url = new URL(result.download_url, location.origin);

      if (!["http:", "https:"].includes(url.protocol)) {
        throw new Error("Invalid attachment download URL.");
      }

      window.open(url.toString(), "_blank", "noopener,noreferrer");
    });
  }

  const query = messageSearch.trim().toLowerCase();
  const searchedMessages = query
    ? messages.filter(
        (message) =>
          !message.deleted_at &&
          message.content.toLowerCase().includes(query),
      )
    : messages;

  const pinnedMessages = messages.filter(
    (message) =>
      !message.deleted_at && features[message.id]?.pinned,
  );

  const typingNames = typingIds
    .map((id) =>
      conversation.members.find((member) => member.id === id)?.name,
    )
    .filter(Boolean)
    .join(", ");

  const statusLabel =
    conversation.conversation_type === "group"
      ? `${conversation.members.length} members`
      : presence === "online"
        ? "Online"
        : presence === "idle"
          ? "Away"
          : presence === "dnd"
            ? "Do not disturb"
            : presence === "offline"
              ? "Offline"
              : "Direct conversation";



  function showDetail(view: DetailView) {
    setDetailView(view);
    onOpenDetails();

    if (view === "search") {
      setThreadSearchOpen(true);
    }
  }

  return (
    <>
      <section className="pmThread">
        <header className="pmThreadHeader">
          <div className="pmThreadIdentity">
            <Avatar
              conversation={conversation}
              userId={userId}
              online={presence === "online"}
            />
            <div>
              <h2>{name}</h2>
              <p>{statusLabel}</p>
            </div>
          </div>

          <div className="pmThreadActions">
            <button
              type="button"
              className="pmIconButton"
              aria-label="Search messages"
              onClick={() =>
                setThreadSearchOpen((current) => !current)
              }
            >
              <Search size={23} />
            </button>
            <button
              type="button"
              className="pmIconButton"
              aria-label="Start voice call"
              disabled={!conversation.can_message}
              onClick={() => void startMediaAction("VOICE")}
            >
              <Phone size={23} />
            </button>
            <button
              type="button"
              className="pmIconButton"
              aria-label="Start video call"
              disabled={!conversation.can_message}
              onClick={() => void setPendingPermission("VIDEO")}
            >
              <Video size={24} />
            </button>
            <button
              type="button"
              className="pmIconButton pmBorderButton"
              aria-label="Open conversation details"
              onClick={onOpenDetails}
            >
              <MoreHorizontal size={22} />
            </button>
          </div>
        </header>

        {threadSearchOpen && (
          <div className="pmThreadSearch">
            <label className="pmSearch">
              <Search size={18} />
              <input
                autoFocus
                value={messageSearch}
                placeholder="Search loaded messages"
                aria-label="Search loaded messages"
                onChange={(event) =>
                  setMessageSearch(event.target.value)
                }
              />
            </label>
            <button
              type="button"
              className="pmIconButton"
              aria-label="Close message search"
              onClick={() => {
                setThreadSearchOpen(false);
                setMessageSearch("");
              }}
            >
              <X size={19} />
            </button>
          </div>
        )}

        {(
          connection === "error" ||
          connection === "disconnected"
        ) && (
          <div className="pmConnectionStatus" role="status">
            {connection === "error"
              ? "Chat realtime connection failed."
              : "Chat realtime is disconnected."}
          </div>
        )}

        {error && (
          <div className="pmThreadError" role="alert">
            <span>{error}</span>
            <button
              type="button"
              className="pmIconButton"
              aria-label="Dismiss error"
              onClick={() => setError("")}
            >
              <X size={17} />
            </button>
          </div>
        )}

        <div
          ref={viewportRef}
          className="pmMessagesViewport"
          onScroll={() => {
            const viewport = viewportRef.current;
            if (!viewport) return;

            scrollAtBottomRef.current =
              viewport.scrollHeight -
                viewport.scrollTop -
                viewport.clientHeight < 70;
          }}
        >
          {hasOlder && (
            <button
              type="button"
              className="pmLoadOlder"
              disabled={loadingOlder}
              onClick={() => void loadOlder()}
            >
              {loadingOlder ? "Loading…" : "Load older messages"}
            </button>
          )}

          {initialLoading && !messages.length ? (
            <p className="pmListNotice" role="status">
              Loading messages…
            </p>
          ) : !searchedMessages.length ? (
            <div className="pmEmpty">
              <MessageCircle size={34} />
              <h2>
                {query ? "No matching messages" : "Start the conversation"}
              </h2>
              <p>
                {query
                  ? "Search checks loaded messages. Load older messages to search further."
                  : "Send a message, file, emoji, or voice note."}
              </p>
            </div>
          ) : (
            searchedMessages.map((message, index) => {
              const own = message.sender_user_id === userId;
              const feature = features[message.id];
              const previous = searchedMessages[index - 1];
              const showDay =
                !previous ||
                new Date(previous.created_at).toDateString() !==
                  new Date(message.created_at).toDateString();
              const sender =
                conversation.members.find(
                  (member) => member.id === message.sender_user_id,
                )?.name ?? "Member";

              return (
                <div key={message.id}>
                  {showDay && (
                    <div className="pmDayDivider">
                      <span>{dayLabel(message.created_at)}</span>
                    </div>
                  )}

                  <article
                    id={`pm-message-${message.id}`}
                    tabIndex={-1}
                    className={`pmMessage ${own ? "isOwn" : ""}`}
                  >
                    <div
                      className={[
                        "pmBubble",
                        isSingleEmojiMessage(message.content) &&
                        String(message.message_type).toLowerCase() === "text" &&
                        !message.deleted_at &&
                        !feature?.reply_to_message_id &&
                        editingId !== message.id &&
                        !(messageFiles[message.id]?.length)
                          ? "pmBubble--singleEmoji"
                          : "",
                      ].join(" ")}
                    >
                      {conversation.conversation_type === "group" && (
                        <strong className="pmSender">
                          {own ? "You" : sender}
                        </strong>
                      )}

                      {!message.deleted_at && (
                        <details
                          className="pmMessageMenu"
                          onToggle={(event) => {
                            if (event.currentTarget.open) {
                              void loadMessageFiles(message.id);
                            }
                          }}
                        >
                          <summary aria-label="Message options">
                            <MoreHorizontal size={17} />
                          </summary>

                          <div
                            className="pmMenu"
                            onClick={closeActionMenu}
                          >
                            <button
                              type="button"
                              onClick={() => beginReply(message)}
                            >
                              <Reply size={15} /> Reply
                            </button>
                            {(messageFiles[message.id] ?? []).map(
                              (file, fileIndex, attachments) => (
                                <button
                                  key={file.attachment_id}
                                  type="button"
                                  disabled={busy}
                                  onClick={() => {
                                    void downloadAttachment(
                                      file.attachment_id,
                                    );
                                  }}
                                >
                                  <Download size={15} />
                                  {attachments.length === 1
                                    ? "Download"
                                    : `Download file ${fileIndex + 1}`}
                                </button>
                              ),
                            )}
                            <button
                              type="button"
                              onClick={() =>
                                void run(async () => {
                                  if (!navigator.clipboard) {
                                    throw new Error(
                                      "Clipboard access is unavailable.",
                                    );
                                  }
                                  await navigator.clipboard.writeText(
                                    message.content,
                                  );
                                })
                              }
                            >
                              <Copy size={15} /> Copy
                            </button>
                            <button
                              type="button"
                              onClick={() => void toggleMessagePin(message)}
                            >
                              <Pin size={15} />
                              {feature?.pinned ? "Unpin" : "Pin"}
                            </button>
                            <button
                              type="button"
                              disabled
                              title="Message starring requires a backend endpoint."
                            >
                              <Star size={15} /> Star unavailable
                            </button>
                            {own && (
                              <>
                                <button
                                  type="button"
                                  onClick={() => setInfoTarget(message)}
                                >
                                  <MessageCircle size={15} /> Message info
                                </button>
                                <button
                                  type="button"
                                  onClick={() => {
                                    setEditingId(message.id);
                                    setEditingText(message.content);
                                  }}
                                >
                                  <Edit3 size={15} /> Edit
                                </button>
                                <button
                                  type="button"
                                  onClick={() =>
                                    void deleteChatMessage(message.id)
                                  }
                                >
                                  <Trash2 size={15} /> Delete
                                </button>
                              </>
                            )}
                          </div>
                        </details>
                      )}

                      {feature?.reply_to_message_id && (
                        <button
                          type="button"
                          className="pmReplyQuote"
                          onClick={() => {
                            const found = jumpToMessage(
                              `pm-message-${feature.reply_to_message_id}`,
                            );

                            if (!found) {
                              setError(
                                "Load older messages to view the original message.",
                              );
                            }
                          }}
                        >
                          {messages.find(
                            (item) =>
                              item.id === feature.reply_to_message_id,
                          )?.content ?? "Reply to an earlier message"}
                        </button>
                      )}

                      {message.deleted_at ? (
                        <p className="pmDeleted">Message deleted</p>
                      ) : editingId === message.id ? (
                        <form
                          className="pmEditForm"
                          onSubmit={(event) => {
                            event.preventDefault();
                            const content = editingText.trim();
                            if (!content) return;

                            void run(async () => {
                              const updated = await chat.editMessage(
                                conversationId,
                                message.id,
                                content,
                              );

                              if (!aliveRef.current) return;

                              setMessages((current) =>
                                mergeMessages(current, [updated]),
                              );
                              setEditingId(null);
                              setEditingText("");
                              await refresh();
                            });
                          }}
                        >
                          <textarea
                            value={editingText}
                            onChange={(event) =>
                              setEditingText(event.target.value)
                            }
                          />
                          <button
                            type="submit"
                            className="pmPrimaryButton"
                            disabled={busy}
                          >
                            Save
                          </button>
                          <button
                            type="button"
                            className="pmSecondaryButton"
                            onClick={() => setEditingId(null)}
                          >
                            Cancel
                          </button>
                        </form>
                      ) : (
                        <>
                          <MessageAttachments
                            conversationId={conversationId}
                            messageId={message.id}
                            content={message.content}
                          />
                        </>
                      )}

                      <footer className="pmMessageFooter">
                        {feature?.pinned && (
                          <Pin size={12} aria-label="Pinned message" />
                        )}
                        {message.edited_at && <span>Edited</span>}
                        <time>
                          {new Date(message.created_at).toLocaleTimeString(
                            [],
                            { hour: "2-digit", minute: "2-digit" },
                          )}
                        </time>
                        {own && !message.deleted_at && (
                          (feature?.read_at ||
                            receipts[message.id]?.length) ? (
                            <CheckCheck
                              size={17}
                              className="pmRead"
                              aria-label="Read"
                            />
                          ) : (
                            <Check
                              size={17}
                              aria-label="Sent"
                            />
                          )
                        )}
                      </footer>
                    </div>

                    {!message.deleted_at && (
                      <div className="pmReactions">
                        {feature?.reactions &&
                          Object.entries(feature.reactions).map(
                            ([emoji, count]) => (
                              <button
                                type="button"
                                key={emoji}
                                disabled={busy}
                                title="View reaction"
                                aria-label={`View ${emoji} reactions`}
                                onClick={() =>
                                  setReactionDetails({
                                    message,
                                    emoji,
                                  })
                                }
                              >
                                {emoji} {count}
                              </button>
                            ),
                          )}

                        <FullEmojiPicker
                          quickReactions
                          className="pmFullReactionButton"
                          label="Choose a reaction"
                          size={15}
                          disabled={busy}
                          onSelect={(emoji) => {
                            void react(message, emoji);
                          }}
                        />
                      </div>
                    )}
                  </article>
                </div>
              );
            })
          )}
        </div>

        {typingIds.length > 0 && (
          <div className="pmTyping" role="status">
            <span className="pmTypingDots">
              <i /><i /><i />
            </span>
            {typingNames || "Someone"} is typing…
          </div>
        )}

        {replyTo && (
          <div className="pmReplyBar">
            <span>
              Replying to: <strong>{replyTo.content}</strong>
            </span>
            <button
              type="button"
              className="pmIconButton"
              aria-label="Cancel reply"
              onClick={() => setReplyTo(null)}
            >
              <X size={17} />
            </button>
          </div>
        )}

        {!conversation.can_message && (
          <p className="pmInlineError">
            Messaging is unavailable until the friendship is accepted.
          </p>
        )}

        {recording && (
          <VoiceRecordingIndicator
            stream={recorderRef.current?.stream ?? null}
            disabled={busy}
            onCancel={cancelVoiceRecording}
            onPause={(paused: boolean) => {
              const recorder = recorderRef.current;

              if (!recorder) {
                throw new Error("No active recording.");
              }

              if (paused) {
                recorder.pause();
              } else {
                recorder.resume();
              }
            }}
            onSend={() => void toggleVoiceRecording()}
          />
        )}

        <form
          style={recording ? { display: "none" } : undefined}
          className={`pmComposer ${files.length ? "pmComposer--files" : ""}`}
          onSubmit={(event) => void sendMessage(event)}
        >
          <div className="pmAttachmentPicker">
            <ChatAttachmentPicker
              files={files}
              disabled={
                busy ||
                recording ||
                !conversation.can_message
              }
              onChange={setFiles}
            />
          </div>
          <FullEmojiPicker
            className="pmIconButton pmEmojiButton"
            label="Insert emoji"
            size={23}
            disabled={busy || !conversation.can_message}
            open={emojiOpen}
            onOpenChange={setEmojiOpen}
            onSelect={(emoji) => {
              changeDraft(draft + emoji);

              requestAnimationFrame(() => {
                composerRef.current?.focus();
              });
            }}
          />
          <textarea
            ref={composerRef}
            rows={1}
            value={draft}
            disabled={busy || !conversation.can_message}
            aria-label="Message"
            placeholder="Write a message…"
            onChange={(event) => changeDraft(event.target.value)}
            onBlur={stopTyping}
            onKeyDown={(event) => {
              if (
                event.key === "Enter" &&
                !event.shiftKey &&
                !event.nativeEvent.isComposing
              ) {
                event.preventDefault();
                void sendMessage();
              }
            }}
          />
          <button
            type="button"
            className={`pmIconButton pmMicButton ${
              recording ? "isRecording" : ""
            }`}
            aria-label={
              recording ? "Stop recording" : "Record voice message"
            }
            disabled={busy || !conversation.can_message}
            onClick={() => void toggleVoiceRecording()}
          >
            <Mic size={23} />
          </button>
          <button
            type="submit"
            className="pmSendButton"
            aria-label="Send message"
            disabled={
              busy ||
              !conversation.can_message ||
              (!draft.trim() && !files.length)
            }
          >
            <Send size={23} />
          </button>
        </form>
      </section>

      {detailsOpen && (
        <aside className="pmDetails">
          <header className="pmDetailsHeader">
            <h2>Conversation details</h2>
            <button
              type="button"
              className="pmIconButton"
              aria-label="Close conversation details"
              onClick={onCloseDetails}
            >
              <X size={21} />
            </button>
          </header>

          <div className="pmDetailsPerson">
            <Avatar
              conversation={conversation}
              userId={userId}
              size="lg"
              online={presence === "online"}
            />
            <div>
              <h3>{name}</h3>
              <p>{statusLabel}</p>
              <small>
                {conversation.conversation_type === "group"
                  ? "Group conversation"
                  : "Personal conversation"}
              </small>
            </div>
          </div>

          <div className="pmDetailCalls">
            <button
              type="button"
              disabled={!conversation.can_message}
              onClick={() => setPendingPermission("VOICE")}
            >
              <Phone size={25} />
              Call
            </button>
            <button
              type="button"
              disabled={!conversation.can_message}
              onClick={() => setPendingPermission("VIDEO")}
            >
              <Video size={25} />
              Video
            </button>
            <div className="pmMenuAnchor">
              <button
                type="button"
                aria-expanded={moreOpen}
                onClick={() => setMoreOpen((current) => !current)}
              >
                <MoreHorizontal size={25} />
                More
              </button>

              {moreOpen && (
                <div className="pmMenu">
                  <button
                    type="button"
                    disabled={busy}
                    onClick={() =>
                      void updatePreference({
                        archived: !preference?.archived,
                      })
                    }
                  >
                    <Archive size={16} />
                    {preference?.archived ? "Unarchive" : "Archive"}
                  </button>
                  <button
                    type="button"
                    disabled={busy}
                    onClick={() =>
                      void updatePreference({
                        muted: !preference?.muted,
                      })
                    }
                  >
                    <Bell size={16} />
                    {preference?.muted
                      ? "Enable notifications"
                      : "Mute notifications"}
                  </button>
                </div>
              )}
            </div>
          </div>

          <div className="pmDetailsNavigation">
            <button
              type="button"
              className={detailView === "search" ? "isActive" : ""}
              onClick={() => showDetail("search")}
            >
              <Search size={23} />
              Search messages
              <ChevronRight size={20} />
            </button>
            <button
              type="button"
              className={detailView === "pinned" ? "isActive" : ""}
              onClick={() => showDetail("pinned")}
            >
              <Pin size={23} />
              Pinned messages
              <ChevronRight size={20} />
            </button>
            <button
              type="button"
              className={detailView === "media" ? "isActive" : ""}
              onClick={() => showDetail("media")}
            >
              <ImageIcon size={23} />
              Shared media
              <ChevronRight size={20} />
            </button>
          </div>

          {detailView !== "overview" && (
            <section className="pmDetailResults">
              <button
                type="button"
                className="pmTextButton"
                onClick={() => setDetailView("overview")}
              >
                Back to overview
              </button>

              {detailView === "search" && (
                <>
                  <h3>Search loaded messages</h3>
                  <label className="pmSearch">
                    <Search size={17} />
                    <input
                      value={messageSearch}
                      onChange={(event) =>
                        setMessageSearch(event.target.value)
                      }
                      placeholder="Search message text"
                      aria-label="Search message text"
                    />
                  </label>
                  <p className="pmMutedText">
                    {query
                      ? `${searchedMessages.length} matching messages`
                      : "Enter text to filter the conversation."}
                  </p>
                </>
              )}

              {detailView === "pinned" && (
                <>
                  <h3>Pinned messages</h3>
                  {!pinnedMessages.length && (
                    <p className="pmMutedText">
                      No pinned messages in the loaded history.
                    </p>
                  )}
                  {pinnedMessages.map((message) => (
                    <div className="pmPinnedResult" key={message.id}>
                      <p>{message.content}</p>
                      <small>{timeLabel(message.created_at)}</small>
                      <button
                        type="button"
                        className="pmTextButton"
                        disabled={busy}
                        onClick={() => void toggleMessagePin(message)}
                      >
                        Unpin
                      </button>
                    </div>
                  ))}
                </>
              )}

              {detailView === "media" && (
                <>
                  <h3>Shared media</h3>
                  <p className="pmMutedText">
                    Files from the loaded message history.
                  </p>
                  {mediaLoading ? (
                    <p role="status">Loading shared files…</p>
                  ) : !sharedFiles.length ? (
                    <p className="pmMutedText">No shared files found.</p>
                  ) : (
                    sharedFiles.map((attachment) => (
                      <button
                        type="button"
                        className="pmSharedFile"
                        key={attachment.attachment_id}
                        disabled={busy}
                        onClick={() =>
                          void downloadAttachment(attachment.attachment_id)
                        }
                      >
                        <FileText size={25} />
                        <span>
                          <strong>{attachment.filename}</strong>
                          <small>
                            {(attachment.size_bytes / 1024).toFixed(1)} KB
                          </small>
                        </span>
                        <Download size={18} />
                      </button>
                    ))
                  )}
                </>
              )}
            </section>
          )}

          <div className="pmSwitchPanel">
            <div className="pmSwitchRow">
              <Bell size={23} />
              <span>Notifications</span>
              <button
                type="button"
                role="switch"
                aria-label="Conversation notifications"
                aria-checked={!preference?.muted}
                className={`pmSwitch ${
                  !preference?.muted ? "isOn" : ""
                }`}
                disabled={busy || !preference}
                onClick={() =>
                  void updatePreference({
                    muted: !preference?.muted,
                  })
                }
              >
                <span />
              </button>
            </div>
            <div className="pmSwitchRow">
              <Pin size={23} />
              <span>Pin conversation</span>
              <button
                type="button"
                role="switch"
                aria-label="Pin conversation"
                aria-checked={Boolean(preference?.pinned)}
                className={`pmSwitch ${
                  preference?.pinned ? "isOn" : ""
                }`}
                disabled={busy || !preference}
                onClick={() =>
                  void updatePreference({
                    pinned: !preference?.pinned,
                  })
                }
              >
                <span />
              </button>
            </div>
          </div>
        </aside>
      )}
      {infoTarget && (
        <MessageInfoDialog
          key={infoTarget.id}
          message={infoTarget}
          userId={userId}
          members={conversation.members}
          onClose={() => setInfoTarget(null)}
        />
      )}
      {reactionDetails && (
        <MessageReactionDialog
          key={`${userId}:${conversationId}:${reactionDetails.message.id}`}
          conversationId={conversationId}
          messageId={reactionDetails.message.id}
          currentUserId={userId}
          initialEmoji={reactionDetails.emoji}
          initialCounts={
            features[reactionDetails.message.id]?.reactions ?? {}
          }
          onClose={() => setReactionDetails(null)}
          onCountsChange={(counts) => {
            const messageId = reactionDetails.message.id;

            setFeatures((current) => {
              const feature = current[messageId];

              if (!feature) {
                return current;
              }

              return {
                ...current,
                [messageId]: {
                  ...feature,
                  reactions: counts,
                },
              };
            });
          }}
        />
      )}

      {pendingPermission && (
        <PermissionDialog
          action={pendingPermission}
          onClose={() => setPendingPermission(null)}
          onAllowed={onPermissionAllowed}
        />
      )}

      {callKind && (
        <ConversationCallPanel
          conversationId={conversationId}
          conversationName={name}
          currentUserId={userId}
          initialKind={callKind}
          invitedUserIds={invitedUserIds}
          onClose={closeCall}
        />
      )}
    </>
  );
}
const MESSAGES_CSS = `
.personalMessages {
  --pm-ink: #111722;
  --pm-muted: #666970;
  --pm-line: #ece7dc;
  --pm-surface: #fdfbf6;
  --pm-yellow: #fff1bd;
  --pm-accent: #f7c500;
  width: 100%;
  min-width: 0;
  color: var(--pm-ink);
  background: transparent;
  font-family: inherit;
  font-size: 14px;
  line-height: 1.5;
  color-scheme: light;
}
.personalMessages *, .pmModal * { box-sizing: border-box; }
.personalMessages button, .personalMessages input,
.personalMessages textarea, .pmModal button,
.pmModal input, .pmModal textarea { font: inherit; }
.personalMessages button, .pmModal button { cursor: pointer; }
.personalMessages button:disabled, .pmModal button:disabled {
  opacity: .45;
  cursor: not-allowed;
}
.personalMessages button:focus-visible,
.personalMessages a:focus-visible,
.personalMessages summary:focus-visible,
.pmModal button:focus-visible {
  outline: 2px solid #947400;
  outline-offset: 3px;
}
.personalMessages input, .personalMessages textarea,
.pmModal input { caret-color: #846700; }
.personalMessages ::selection, .pmModal ::selection {
  background: #ffe58d;
  color: #111722;
}
.personalMessages ::-webkit-scrollbar,
.pmModal ::-webkit-scrollbar { width: 5px; height: 5px; }
.personalMessages ::-webkit-scrollbar-thumb,
.pmModal ::-webkit-scrollbar-thumb {
  background: #d8d3c7;
  border-radius: 8px;
}
.personalMessages ::-webkit-scrollbar-track { background: transparent; }

.pmPageHeader {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  margin: 0 0 23px;
  padding: 0 18px;
  min-height: 86px;
}
.pmPageHeader h1 {
  margin: 0;
  font-size: clamp(30px, 2.8vw, 43px);
  line-height: 1.2;
  font-weight: 500;
  letter-spacing: -.035em;
}
.pmPageHeader p {
  margin: 4px 0 0;
  color: #77777b;
  font-size: 16px;
}
.pmPrimaryButton, .pmSecondaryButton {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  min-height: 46px;
  padding: 11px 20px;
  border-radius: 11px;
  border: 1px solid #242424;
  background: #242424;
  color: #fff;
  white-space: nowrap;
}
.pmPrimaryButton:hover { background: #393939; }
.pmSecondaryButton {
  border-color: #e4ded2;
  background: #fffdf8;
  color: #252a34;
}
.pmSecondaryButton:hover { background: #fff2c7; }

.pmShell {
  display: grid;
  grid-template-columns: minmax(270px, 29%) minmax(0, 1fr) minmax(270px, 25%);
  gap: 6px;
  height: max(620px, calc(100dvh - 168px));
  min-width: 0;
}
.pmShell--noDetails {
  grid-template-columns: minmax(270px, 30%) minmax(0, 1fr);
}
.pmInbox, .pmThread, .pmDetails {
  min-width: 0;
  min-height: 0;
  border: 1px solid var(--pm-line);
  border-radius: 17px;
  background: var(--pm-surface);
}
.pmInbox {
  display: flex;
  flex-direction: column;
  padding: 21px 4px 12px;
}
.pmInboxHeader {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 0 18px 15px;
}
.pmInboxHeader h2, .pmDetailsHeader h2 {
  margin: 0;
  font-size: 19px;
  line-height: 1.35;
  font-weight: 600;
  letter-spacing: -.02em;
}
.pmIconButton {
  display: inline-flex;
  flex: 0 0 auto;
  align-items: center;
  justify-content: center;
  width: 35px;
  height: 35px;
  padding: 6px;
  border: 0;
  border-radius: 9px;
  background: transparent;
  color: #111722;
}
.pmIconButton:hover { background: #fff0bb; }
.pmBorderButton {
  border: 1px solid #e6dfd1;
  background: #fffdf9;
}

.pmSearch {
  display: flex;
  align-items: center;
  gap: 11px;
  min-width: 0;
  min-height: 45px;
  padding: 9px 13px;
  border: 1px solid #e5ded1;
  border-radius: 11px;
  background: #fffdf9;
  color: #535962;
}
.pmInbox > .pmSearch { margin: 0 15px; }
.pmSearch input {
  width: 100%;
  min-width: 0;
  padding: 0;
  border: 0;
  outline: 0;
  color: #202631;
  background: transparent;
  font-size: 14px;
}
.pmSearch input::placeholder {
  color: #72747b;
  opacity: 1;
}
.pmSearch:focus-within { border-color: #b49a42; }
.pmSearch svg { flex-shrink: 0; }

.pmFilters {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 7px;
  padding: 15px 15px 14px;
}
.pmFilters button, .pmTabs button {
  min-height: 34px;
  padding: 6px 15px;
  border: 1px solid #e3dccf;
  border-radius: 999px;
  background: #fffdf9;
  color: #51535c;
  font-size: 13px;
  line-height: 20px;
}
.pmFilters button.isActive, .pmTabs button.isActive {
  border-color: #242424;
  background: #242424;
  color: #fff;
}
.pmFilters button:hover:not(.isActive) { background: #fff2c7; }

.pmConversationList {
  flex: 1;
  min-height: 0;
  overflow: auto;
  padding: 0;
  scrollbar-width: thin;
}
.pmConversation {
  display: grid;
  grid-template-columns: 58px minmax(0, 1fr) auto;
  align-items: center;
  gap: 13px;
  width: 100%;
  min-height: 96px;
  padding: 15px 17px;
  border: 0;
  border-bottom: 1px solid #eee9df;
  border-radius: 0;
  color: #111722;
  background: transparent;
  text-align: left;
}
.pmConversation:hover { background: #f8f3e8; }
.pmConversation.isActive {
  border-bottom-color: transparent;
  border-radius: 13px;
  background: #fff2c8;
}
.pmConversationText { min-width: 0; }
.pmConversationText strong, .pmConversationText small {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.pmConversationText strong {
  font-size: 16px;
  font-weight: 600;
  letter-spacing: -.025em;
}
.pmConversationText small {
  margin-top: 5px;
  color: #656b73;
  font-size: 13px;
}
.pmConversationMeta {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  align-self: stretch;
  justify-content: center;
  gap: 10px;
  min-width: 32px;
}
.pmConversationMeta time {
  font-size: 12px;
  color: #666b72;
  font-variant-numeric: tabular-nums;
}
.pmConversationIndicators {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 6px;
}
.pmUnread {
  display: inline-grid;
  place-items: center;
  min-width: 24px;
  height: 24px;
  padding: 0 6px;
  border-radius: 50%;
  background: #ffcf00;
  color: #17202b;
  font-size: 12px;
  font-weight: 600;
}
.pmListNotice { padding: 16px; color: #666970; }

.pmAvatar {
  position: relative;
  display: inline-block;
  flex: 0 0 auto;
  width: 56px;
  height: 56px;
}
.pmAvatarImage {
  display: grid;
  place-items: center;
  width: 100%;
  height: 100%;
  overflow: hidden;
  border-radius: 50%;
  background: #e9e4da;
  color: #25303a;
  font-size: 18px;
  font-weight: 600;
}
.pmAvatarImage img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.pmAvatarImage--group { background: #ffecab; }
.pmAvatar--lg { width: 76px; height: 76px; }
.pmAvatar--sm { width: 42px; height: 42px; }
.pmPresenceDot {
  position: absolute;
  right: 0;
  bottom: 0;
  width: 15px;
  height: 15px;
  border: 2px solid #fdfbf6;
  border-radius: 50%;
  background: #0aa66a;
}
.pmStatusDot {
  display: inline-block;
  width: 10px;
  height: 10px;
  margin-right: 7px;
  border-radius: 50%;
  background: #0aa66a;
}

.pmThread {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.pmThreadHeader {
  display: flex;
  flex: 0 0 auto;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  min-height: 82px;
  padding: 13px 20px;
  border-bottom: 1px solid var(--pm-line);
}
.pmThreadIdentity {
  display: flex;
  align-items: center;
  gap: 15px;
  min-width: 0;
}
.pmThreadIdentity > div { min-width: 0; }
.pmThreadIdentity h2 {
  overflow: hidden;
  margin: 0;
  color: #111722;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 18px;
  font-weight: 600;
  letter-spacing: -.02em;
}
.pmThreadIdentity p {
  display: flex;
  align-items: center;
  margin: 2px 0 0;
  color: #686b72;
  font-size: 14px;
}
.pmThreadActions {
  display: flex;
  align-items: center;
  flex-shrink: 0;
  gap: 10px;
}
.pmThreadSearch {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 15px;
  border-bottom: 1px solid var(--pm-line);
}
.pmThreadSearch .pmSearch { flex: 1; }

.pmMessagesViewport {
  flex: 1;
  min-height: 0;
  overflow: auto;
  padding: 0 23px 14px;
  scrollbar-width: thin;
  overflow-anchor: auto;
}
.pmDayDivider {
  display: flex;
  justify-content: center;
  margin: 14px 0 12px;
}
.pmDayDivider span {
  padding: 3px 16px;
  border: 1px solid #eae4d7;
  border-radius: 999px;
  background: #faf7ef;
  color: #54575e;
  font-size: 13px;
}
.pmMessage {
  position: relative;
  width: fit-content;
  max-width: 84%;
  margin: 0 0 15px;
}
.pmMessage.isOwn { margin-left: auto; }
.pmBubble {
  position: relative;
  min-width: 110px;
  padding: 9px 15px 6px;
  border: 1px solid #ece8df;
  border-radius: 16px;
  background: #fff;
  color: #1f2636;
}
.pmMessage.isOwn .pmBubble {
  border-color: transparent;
  background: #fff0bd;
}
.pmBubble::before {
  position: absolute;
  bottom: 8px;
  left: -5px;
  width: 10px;
  height: 10px;
  border-left: 1px solid #ece8df;
  border-bottom: 1px solid #ece8df;
  background: #fff;
  transform: rotate(45deg);
  content: "";
}
.pmMessage.isOwn .pmBubble::before {
  left: auto;
  right: -5px;
  border: 0;
  background: #fff0bd;
}
.pmSender {
  display: block;
  margin-bottom: 3px;
  color: #555861;
  font-size: 12px;
  font-weight: 600;
}
.pmMessageBody {
  margin: 0;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  font-size: 15px;
  line-height: 1.5;
}
.pmDeleted { margin: 0; color: #76716a; font-style: italic; }
.pmMessageFooter {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 5px;
  min-height: 19px;
  margin-top: 2px;
  color: #74777b;
  font-size: 11px;
  font-variant-numeric: tabular-nums;
}
.pmMessage.isOwn .pmMessageFooter { color: #6e644c; }
.pmRead { color: #d0a000; }
.pmReplyQuote {
  margin: 0 0 7px;
  padding: 7px 9px;
  border: 1px solid #e8dbb2;
  border-radius: 7px;
  background: #fff8df;
  color: #625b4d;
  font-size: 12px;
  overflow-wrap: anywhere;
}

.pmMenuAnchor { position: relative; }
.pmMenu {
  position: absolute;
  top: calc(100% + 5px);
  right: 0;
  z-index: 30;
  display: grid;
  width: 210px;
  padding: 5px;
  border: 1px solid #e8e1d5;
  border-radius: 10px;
  background: #fffdf8;
  box-shadow: 0 12px 28px rgba(31, 26, 14, .13);
}
.pmMenu button {
  display: flex;
  align-items: center;
  gap: 9px;
  min-height: 35px;
  padding: 8px 10px;
  border: 0;
  border-radius: 6px;
  background: transparent;
  color: #252b36;
  text-align: left;
  font-size: 12px;
}
.pmMenu button:hover { background: #fff0bd; }
.pmMessageMenu {
  position: absolute;
  top: 4px;
  right: 5px;
  z-index: 8;
}
.pmMessageMenu > summary {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 6px;
  background: #fffdf8;
  color: #333944;
  list-style: none;
  opacity: 0;
  cursor: pointer;
}
.pmMessageMenu > summary::-webkit-details-marker { display: none; }
.pmMessage:hover .pmMessageMenu > summary,
.pmMessage:focus-within .pmMessageMenu > summary,
.pmMessageMenu[open] > summary { opacity: 1; }
.pmMessage:not(.isOwn) .pmMessageMenu .pmMenu { right: auto; left: 0; }

.pmReactions {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 3px;
}
.pmReactions > button {
  padding: 2px 9px;
  border: 1px solid #e8e1d2;
  border-radius: 999px;
  background: #fffdf7;
  color: #403a30;
  font-size: 12px;
}
.pmReactionPicker { position: relative; }
.pmReactionPicker > summary {
  display: flex;
  padding: 3px;
  color: #77746b;
  list-style: none;
  cursor: pointer;
  opacity: 0;
}
.pmReactionPicker > summary::-webkit-details-marker { display: none; }
.pmMessage:hover .pmReactionPicker > summary,
.pmMessage:focus-within .pmReactionPicker > summary,
.pmReactionPicker[open] > summary { opacity: 1; }
.pmReactionPicker > div {
  position: absolute;
  bottom: 25px;
  left: 0;
  z-index: 20;
  display: flex;
  flex-wrap: wrap;
  gap: 3px;
  width: 190px;
  padding: 7px;
  border: 1px solid #e8e0d0;
  border-radius: 10px;
  background: #fffdf8;
}
.pmReactionPicker button, .pmEmojiPicker button {
  padding: 4px 6px;
  border: 0;
  border-radius: 6px;
  background: transparent;
  font-size: 20px;
}
.pmReactionPicker button:hover, .pmEmojiPicker button:hover {
  background: #fff0bd;
}
.pmEditForm textarea {
  width: 100%;
  min-height: 70px;
  padding: 8px;
  border: 1px solid #ded5c4;
  border-radius: 8px;
  color: #202631;
  background: #fff;
}
.pmEditForm button {
  min-height: 30px;
  margin: 6px 5px 0 0;
  padding: 5px 10px;
  font-size: 12px;
}

.pmTyping {
  display: flex;
  align-items: center;
  gap: 9px;
  flex: 0 0 auto;
  min-height: 36px;
  padding: 0 23px 7px;
  color: #72716d;
  font-size: 12px;
}
.pmTypingDots {
  display: flex;
  gap: 4px;
  padding: 10px 13px;
  border: 1px solid #e9e2d5;
  border-radius: 999px;
}
.pmTypingDots i {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #aaa59b;
}
.pmComposer {
  display: grid;
  grid-template-columns: 35px 35px minmax(0, 1fr) 39px 47px;
  align-items: center;
  gap: 8px;
  flex: 0 0 auto;
  margin: 0 10px 10px;
  padding: 7px 9px;
  border: 1px solid #e3ddd0;
  border-radius: 17px;
  background: #fffefa;
}
.pmComposer:focus-within { border-color: #bca05a; }
.pmComposer textarea {
  width: 100%;
  min-width: 0;
  min-height: 42px;
  max-height: 100px;
  padding: 10px 3px;
  resize: vertical;
  border: 0;
  outline: 0;
  color: #202631;
  background: transparent;
  font-size: 14px;
  line-height: 22px;
}
.pmComposer textarea::placeholder { color: #777a80; opacity: 1; }
.pmAttachmentPicker { min-width: 0; }
.pmAttachmentPicker .attachmentTrigger {
  padding: 5px;
  border: 0;
  background: transparent;
  color: #151c27;
  font-size: 0;
}
.pmAttachmentPicker .attachmentTrigger svg {
  width: 23px;
  height: 23px;
}
.pmComposer--files .pmAttachmentPicker {
  grid-column: 1 / -1;
  grid-row: 2;
}
.pmComposer--files .pmAttachmentPicker .attachmentTrigger {
  font-size: 12px;
}
.pmComposer--files .pmEmojiButton { grid-column: 2; grid-row: 1; }
.pmComposer--files textarea { grid-column: 3; grid-row: 1; }
.pmComposer--files .pmMicButton { grid-column: 4; grid-row: 1; }
.pmComposer--files .pmSendButton { grid-column: 5; grid-row: 1; }
.pmMicButton {
  border-left: 1px solid #e6dfd2;
  border-radius: 0;
}
.pmMicButton.isRecording { color: #b42318; background: #fff0ed; }
.pmSendButton {
  display: grid;
  place-items: center;
  width: 47px;
  height: 47px;
  padding: 8px;
  border: 1px solid #242424;
  border-radius: 13px;
  background: #242424;
  color: #fff;
}
.pmSendButton:hover { background: #3d3d3d; }
.pmEmojiPicker {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin: 0 11px 8px;
  padding: 8px;
  border: 1px solid #e8e1d3;
  border-radius: 10px;
  background: #fffdf8;
}
.pmReplyBar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 7px 14px;
  background: #fff3ca;
  color: #625843;
  font-size: 12px;
}
.pmReplyBar > span {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.pmDetails { overflow: auto; padding: 0 20px 20px; }
.pmDetailsHeader {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  min-height: 69px;
  padding: 11px 4px;
  border-bottom: 1px solid var(--pm-line);
}
.pmDetailsHeader h2 { font-size: 17px; white-space: nowrap; }
.pmDetailsPerson {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 22px 4px 0;
}
.pmDetailsPerson > div { min-width: 0; }
.pmDetailsPerson h3 {
  margin: 3px 0 0;
  font-size: 18px;
  font-weight: 600;
  line-height: 1.3;
  overflow-wrap: anywhere;
}
.pmDetailsPerson p {
  display: flex;
  align-items: center;
  margin: 4px 0 5px;
  color: #686b72;
  font-size: 14px;
}
.pmDetailsPerson small { color: #77777b; font-size: 13px; }

.pmDetailCalls {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin: 23px 0 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--pm-line);
}
.pmDetailCalls > button, .pmDetailCalls > .pmMenuAnchor > button {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  width: 100%;
  min-height: 75px;
  padding: 9px 5px;
  border: 1px solid #e9e2d6;
  border-radius: 13px;
  color: #202631;
  background: #fefcf7;
  font-size: 14px;
}
.pmDetailCalls button:hover { background: #fff0bd; }
.pmDetailsNavigation { display: grid; gap: 12px; }
.pmDetailsNavigation > button {
  display: grid;
  grid-template-columns: 24px minmax(0, 1fr) 20px;
  align-items: center;
  gap: 13px;
  min-height: 54px;
  padding: 11px 16px;
  border: 1px solid #e8e1d4;
  border-radius: 12px;
  background: #fefcf7;
  color: #242a37;
  text-align: left;
  font-size: 14px;
}
.pmDetailsNavigation > button:hover,
.pmDetailsNavigation > button.isActive { background: #fff1c4; }
.pmDetailsNavigation > button > svg:last-child { color: #777; }
.pmSwitchPanel {
  margin-top: 26px;
  padding: 0 15px;
  border: 1px solid #e8e1d4;
  border-radius: 13px;
  background: #fefcf7;
}
.pmSwitchRow {
  display: flex;
  align-items: center;
  gap: 12px;
  min-height: 60px;
  color: #242a37;
  font-size: 14px;
}
.pmSwitchRow + .pmSwitchRow { border-top: 1px solid #e8e1d4; }
.pmSwitchRow > span { flex: 1; }
.pmSwitch {
  display: inline-flex;
  align-items: center;
  flex: 0 0 auto;
  width: 47px;
  height: 27px;
  padding: 3px;
  border: 0;
  border-radius: 999px;
  background: #c9c9cb;
}
.pmSwitch > span {
  width: 21px;
  height: 21px;
  border-radius: 50%;
  background: #fff;
}
.pmSwitch.isOn { background: #f3c400; }
.pmSwitch.isOn > span { margin-left: auto; }
.pmDetailResults {
  margin-top: 18px;
  padding-top: 14px;
  border-top: 1px solid #e8e1d4;
}
.pmDetailResults h3 {
  margin: 13px 0 10px;
  font-size: 15px;
  font-weight: 600;
}
.pmTextButton, .pmLoadOlder {
  padding: 5px 0;
  border: 0;
  color: #725a13;
  background: transparent;
  font-size: 12px;
  text-decoration: underline;
  text-underline-offset: 3px;
}
.pmLoadOlder { display: block; margin: 12px auto; }
.pmPinnedResult {
  margin-top: 9px;
  padding: 10px;
  border: 1px solid #e7dfcf;
  border-radius: 9px;
  background: #fff8df;
}
.pmPinnedResult p { margin: 0; overflow-wrap: anywhere; }
.pmPinnedResult small { display: block; color: #726d61; }
.pmSharedFile {
  display: flex;
  align-items: center;
  gap: 9px;
  width: 100%;
  margin-top: 8px;
  padding: 10px;
  border: 1px solid #e6ded0;
  border-radius: 10px;
  color: #252b35;
  background: #fffdf9;
  text-align: left;
}
.pmSharedFile > span { flex: 1; min-width: 0; }
.pmSharedFile strong {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 12px;
}
.pmSharedFile small { color: #777; font-size: 11px; }
.pmMutedText { color: #6c6d72; font-size: 13px; }
.pmEmpty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 260px;
  padding: 25px;
  color: #6b6d74;
  text-align: center;
}
.pmEmpty h2 { margin: 0; color: #27303c; font-size: 18px; }
.pmEmpty p { margin: 0; font-size: 13px; }
.pmPageError, .pmThreadError {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 9px 12px;
  border: 1px solid #e8bcb3;
  border-radius: 9px;
  background: #fff1ed;
  color: #9a3223;
  font-size: 12px;
  overflow-wrap: anywhere;
}
.pmPageError { margin-bottom: 10px; }
.pmThreadError { margin: 8px 12px; }
.pmPageError button {
  border: 0;
  background: transparent;
  color: inherit;
  text-decoration: underline;
}
.pmConnectionStatus {
  padding: 4px 15px;
  background: #fff6d8;
  color: #77642d;
  font-size: 12px;
}
.pmInlineError {
  margin: 12px 0;
  padding: 10px 12px;
  border: 1px solid #e8bcb3;
  border-radius: 9px;
  background: #fff1ed;
  color: #9a3223;
  font-size: 13px;
  overflow-wrap: anywhere;
}

.pmModal {
  width: min(470px, calc(100vw - 30px));
  max-height: calc(100dvh - 40px);
  margin: auto;
  padding: 0;
  overflow: auto;
  border: 1px solid #e6dfd1;
  border-radius: 16px;
  background: #fffdf7;
  color: #17202b;
  font-family: inherit;
  box-shadow: 0 18px 50px rgba(0, 0, 0, .2);
}
.pmModal::backdrop { background: rgba(24, 23, 20, .45); }
.pmModalContent { padding: 22px; }
.pmModalHeader {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 17px;
}
.pmModalHeader h2 {
  margin: 0;
  font-size: 20px;
  line-height: 1.3;
  font-weight: 600;
}
.pmModalFooter {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 20px;
}
.pmModalDescription { margin: 13px 0 8px; font-size: 15px; }
.pmPermissionIcon {
  display: grid;
  place-items: center;
  width: 64px;
  height: 64px;
  border-radius: 16px;
  background: #fff0bd;
}
.pmTabs { display: flex; gap: 8px; margin-bottom: 18px; }
.pmField {
  display: grid;
  gap: 7px;
  margin-bottom: 14px;
  color: #464c55;
  font-size: 13px;
}
.pmField input {
  min-height: 42px;
  padding: 9px 12px;
  border: 1px solid #e5ded1;
  border-radius: 9px;
  color: #202631;
  background: #fff;
}
.pmFriendList {
  max-height: 300px;
  overflow: auto;
  margin-top: 12px;
}
.pmFriendChoice {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 11px 7px;
  border: 0;
  border-bottom: 1px solid #ebe5d9;
  color: #252b36;
  background: transparent;
  text-align: left;
}
.pmFriendChoice > span { flex: 1; }
.pmFriendChoice strong, .pmFriendChoice small { display: block; }
.pmFriendChoice small { color: #777; font-size: 12px; }
.pmFriendChoice input { accent-color: #d7a900; }

@media (max-width: 1300px) {
  .pmShell {
    grid-template-columns: minmax(240px, 29%) minmax(0, 1fr) minmax(240px, 25%);
  }
  .pmShell--noDetails {
    grid-template-columns: minmax(240px, 30%) minmax(0, 1fr);
  }
  .pmConversation { gap: 10px; padding: 13px 11px; }
  .pmConversationText strong { font-size: 14px; }
  .pmConversationText small { font-size: 12px; }
  .pmThreadHeader { padding: 13px; }
  .pmThreadActions { gap: 3px; }
  .pmThreadIdentity { gap: 10px; }
  .pmThreadIdentity h2 { font-size: 16px; }
  .pmDetails { padding-left: 14px; padding-right: 14px; }
  .pmDetailsPerson { gap: 11px; }
  .pmDetailsPerson .pmAvatar--lg { width: 62px; height: 62px; }
  .pmDetailsNavigation > button { gap: 9px; padding: 11px; font-size: 13px; }
  .pmDetailCalls { gap: 8px; }
  .pmSwitchRow { gap: 9px; font-size: 13px; }
}
@media (max-width: 1100px) {
  .pmShell, .pmShell--noDetails {
    grid-template-columns: minmax(240px, 32%) minmax(0, 1fr);
    height: auto;
  }
  .pmInbox { max-height: 720px; }
  .pmThread { height: max(600px, calc(100dvh - 175px)); }
  .pmDetails { grid-column: 1 / -1; }
  .pmDetailsPerson { align-items: center; }
  .pmDetailsNavigation { grid-template-columns: repeat(3, minmax(0, 1fr)); }
  .pmDetailsHeader h2 { font-size: 18px; }
}
@media (max-width: 740px) {
  .pmPageHeader { padding: 0; gap: 12px; margin-bottom: 16px; }
  .pmPageHeader h1 { font-size: 31px; }
  .pmPageHeader p { font-size: 12px; }
  .pmPageHeader > button { min-height: 40px; padding: 9px 12px; font-size: 12px; }
  .pmShell, .pmShell--noDetails { grid-template-columns: 1fr; gap: 10px; }
  .pmInbox { max-height: 350px; }
  .pmConversation { min-height: 82px; }
  .pmThread { height: 75dvh; min-height: 480px; }
  .pmThreadHeader { gap: 7px; padding: 10px; }
  .pmThreadIdentity .pmAvatar { width: 42px; height: 42px; }
  .pmThreadIdentity h2 { max-width: 145px; font-size: 15px; }
  .pmThreadIdentity p { font-size: 12px; }
  .pmThreadActions { gap: 0; }
  .pmThreadActions .pmIconButton { width: 30px; height: 33px; padding: 5px; }
  .pmMessagesViewport { padding: 0 14px 12px; }
  .pmMessage { max-width: 91%; }
  .pmMessageBody { font-size: 14px; }
  .pmComposer { grid-template-columns: 29px 29px minmax(0, 1fr) 32px 40px; gap: 3px; margin: 0 7px 7px; padding: 6px; }
  .pmComposer .pmIconButton { width: 29px; }
  .pmSendButton { width: 40px; height: 42px; }
  .pmDetails { grid-column: auto; }
  .pmDetailsNavigation { grid-template-columns: 1fr; }
  .pmDetailsPerson .pmAvatar--lg { width: 76px; height: 76px; }
  .pmModalFooter { flex-wrap: wrap; }
}
@media (hover: none) {
  .pmMessageMenu > summary, .pmReactionPicker > summary { opacity: 1; }
  .pmMessageBody { padding-right: 14px; }
}

/* Compact sizing */
.personalMessages {
  font-size: 13px;
}

.pmPageHeader {
  min-height: 72px;
  margin-bottom: 17px;
  gap: 18px;
}

.pmPageHeader h1 {
  font-size: 34px;
}

.pmPageHeader p {
  font-size: 14px;
}

.pmPrimaryButton,
.pmSecondaryButton {
  min-height: 39px;
  padding: 9px 15px;
  font-size: 12px;
}

.pmInboxHeader h2 {
  font-size: 17px;
}

.pmSearch {
  min-height: 38px;
  padding: 7px 11px;
}

.pmSearch input {
  font-size: 12px;
}

.pmFilters {
  gap: 6px;
  padding-top: 11px;
  padding-bottom: 11px;
}

.pmFilters button {
  min-height: 29px;
  padding: 4px 12px;
  font-size: 12px;
}

.pmConversation {
  grid-template-columns: 48px minmax(0, 1fr) auto;
  min-height: 82px;
  padding: 12px 14px;
  gap: 11px;
}

.pmConversationText strong {
  font-size: 14px;
}

.pmConversationText small {
  font-size: 12px;
}

.pmAvatar {
  width: 48px;
  height: 48px;
}

.pmAvatar--lg,
.pmDetailsPerson .pmAvatar--lg {
  width: 66px;
  height: 66px;
}

.pmAvatarImage > svg {
  width: 22px;
  height: 22px;
}

.pmIconButton {
  width: 30px;
  height: 30px;
  padding: 5px;
}

.pmIconButton > svg {
  width: 20px;
  height: 20px;
}

.pmThreadHeader {
  min-height: 70px;
  padding: 10px 15px;
}

.pmThreadIdentity {
  gap: 11px;
}

.pmThreadIdentity h2 {
  font-size: 16px;
}

.pmThreadIdentity p {
  font-size: 12px;
}

.pmThreadActions {
  gap: 6px;
}

.pmMessagesViewport {
  padding-left: 18px;
  padding-right: 18px;
}

.pmBubble {
  padding: 8px 12px 5px;
  border-radius: 13px;
}

.pmMessageBody {
  font-size: 13px;
  line-height: 1.5;
}

.pmMessage {
  margin-bottom: 12px;
}

.pmMenu {
  width: 185px;
}

.pmMenu button {
  min-height: 31px;
  padding: 6px 9px;
  font-size: 11px;
}

.pmComposer {
  grid-template-columns: 30px 30px minmax(0, 1fr) 34px 41px;
  gap: 6px;
  padding: 6px 8px;
}

.pmComposer textarea {
  min-height: 37px;
  padding: 8px 3px;
  font-size: 13px;
}

.pmSendButton {
  width: 41px;
  height: 41px;
  border-radius: 12px;
}

.pmDetailsHeader {
  min-height: 60px;
}

.pmDetailsHeader h2 {
  font-size: 15px;
}

.pmDetailsPerson h3 {
  font-size: 16px;
}

.pmDetailsPerson p,
.pmDetailsPerson small {
  font-size: 12px;
}

.pmDetailCalls > button,
.pmDetailCalls > .pmMenuAnchor > button {
  min-height: 64px;
  font-size: 12px;
}

.pmDetailCalls svg {
  width: 22px;
  height: 22px;
}

.pmDetailsNavigation > button {
  min-height: 47px;
  padding: 9px 13px;
  font-size: 12px;
}

.pmDetailsNavigation > button > svg {
  width: 20px;
  height: 20px;
}

.pmSwitchRow {
  min-height: 52px;
  font-size: 12px;
}

.pmSwitch {
  width: 42px;
  height: 24px;
}

.pmSwitch > span {
  width: 18px;
  height: 18px;
}

@media (max-width: 740px) {
  .pmPageHeader h1 {
    font-size: 29px;
  }

  .pmComposer {
    grid-template-columns: 27px 27px minmax(0, 1fr) 29px 37px;
    gap: 3px;
  }

  .pmSendButton {
    width: 37px;
    height: 38px;
  }
}
/* Remove the attachment button rectangle */
.personalMessages .pmAttachmentPicker .attachmentTrigger,
.personalMessages .pmAttachmentPicker .attachmentTrigger:hover,
.personalMessages .pmAttachmentPicker .attachmentTrigger:active {
  border: 0;
  background: transparent;
  box-shadow: none;
}

/* Add 2px of space before the emoji button */
.personalMessages .pmComposer > .pmEmojiButton {
  margin-left: 4px;
}
.personalMessages .pmMessageMenu > summary,
.personalMessages .pmMessageMenu > summary:hover,
.personalMessages .pmMessageMenu > summary:active,
.personalMessages .pmMessageMenu[open] > summary {
  background: transparent;
  border: 0;
  box-shadow: none;
}

.personalMessages .pmMessageMenu > summary:focus:not(:focus-visible) {
  outline: none;
}
.personalMessages .pmReactionPicker > div {
  box-sizing: border-box;
  display: grid;
  grid-template-columns: repeat(4, 34px);
  gap: 4px;
  width: max-content;
  padding: 8px;
  bottom: calc(100% + 8px);
  left: 0;
  right: auto;
}

.personalMessages .pmMessage.isOwn .pmReactionPicker > div {
  left: auto;
  right: 0;
}

.personalMessages .pmReactionPicker > div > button {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  padding: 0;
  line-height: 1;
}
.pmReactionDetails {
  display: grid;
  gap: 16px;
  padding: 4px 0 8px;
}

.pmReactionDetailsSummary {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
}

.pmReactionDetailsEmoji {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 48px;
  height: 42px;
  border-radius: 999px;
  background: #fff1bd;
  font-size: 25px;
}

.pmReactionRemoveButton {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  width: 100%;
  padding: 12px;
  border: 1px solid #ece7dc;
  border-radius: 10px;
  background: transparent;
  color: #a33232;
  cursor: pointer;
}

.pmReactionRemoveButton:disabled {
  opacity: 0.5;
  cursor: default;
}

.pmReactionDetailsHint {
  margin: 0;
  color: #666970;
  font-size: 12px;
}

.personalMessages .pmGroupHost {
  grid-column: 2 / -1;
  min-width: 0;
  min-height: 0;
  align-self: stretch;
}

@media (max-width: 760px) {
  .personalMessages .pmGroupHost {
    grid-column: 1 / -1;
  }
}
.personalMessages .gp.gp-embedded {
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
  min-width: 0;
  min-height: 0;
  margin: 0;
  padding: 0;
}

.personalMessages .gp.gp-embedded > .gp-page-header,
.personalMessages .gp.gp-embedded .gp-inbox,
.personalMessages .gp.gp-embedded .gp-back {
  display: none;
}

.personalMessages .gp.gp-embedded > .gp-grid {
  flex: 1;
  grid-template-columns:
    minmax(0, 1fr)
    minmax(220px, 0.55fr);
  width: 100%;
  height: 100%;
  min-height: 0;
}

.personalMessages .gp.gp-embedded.gp-details-hidden > .gp-grid {
  grid-template-columns: minmax(0, 1fr);
}

.personalMessages .gp.gp-embedded .gp-conversation {
  display: flex;
  min-width: 0;
  min-height: 0;
}

@media (max-width: 1100px) {
  .personalMessages .gp.gp-embedded > .gp-grid {
    grid-template-columns: minmax(0, 1fr);
  }
}
.personalMessages .pmFullReactionButton {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  padding: 3px;
  border: 0;
  background: transparent;
  color: #77746b;
  cursor: pointer;
}

.personalMessages .pmInboxGroupAvatar {
  display: block;
  width: 100%;
  height: 100%;
}

.personalMessages .pmInboxGroupAvatar > .gp-avatar {
  position: relative;
  display: grid;
  place-items: center;
  width: 100%;
  height: 100%;
  overflow: hidden;
  border-radius: 50%;
  background: #fff0bc;
  color: #514b42;
}

.personalMessages .pmInboxGroupAvatar > .gp-group-avatar-stack {
  display: block;
  overflow: visible;
  background: transparent;
  isolation: isolate;
}

.personalMessages .pmInboxGroupAvatar .gp-avatar-part {
  position: absolute;
  display: grid;
  place-items: center;
  box-sizing: border-box;
  width: 70%;
  height: 70%;
  overflow: hidden;
  border: 2px solid #fffdf7;
  border-radius: 50%;
  background: #ebe5d6;
  color: #514b42;
  font-size: 11px;
  font-weight: 600;
}

.personalMessages .pmInboxGroupAvatar .gp-avatar-part-0 {
  top: 0;
  left: 0;
  z-index: 1;
}

.personalMessages .pmInboxGroupAvatar .gp-avatar-part-1 {
  right: 0;
  bottom: 0;
  z-index: 2;
}

.personalMessages .pmInboxGroupAvatar .gp-avatar-part-2 {
  bottom: 0;
  left: 0;
  z-index: 3;
  width: 58%;
  height: 58%;
}

.personalMessages .pmInboxGroupAvatar img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.personalMessages .pmMessage .pmBubble.pmBubble--singleEmoji {
  min-width: 0;
  padding: 4px 8px;
  border-color: transparent;
  background: transparent;
  box-shadow: none;
}

.personalMessages .pmBubble.pmBubble--singleEmoji::before,
.personalMessages .pmBubble.pmBubble--singleEmoji::after {
  display: none;
}

.personalMessages .pmBubble.pmBubble--singleEmoji .pmMessageBody {
  margin: 0;
  padding: 4px 0;
  font-family: "Segoe UI Emoji", "Apple Color Emoji", sans-serif;
  font-size: 56px;
  line-height: 1.2;
  overflow: visible;
}
.personalMessages button.pmReplyQuote {
  display: block;
  width: 100%;
  text-align: left;
  font: inherit;
  font-size: 12px;
  cursor: pointer;
}

/* read-tick-yellow-v2 */
.personalMessages .pmMessageFooter .pmRead { color:#d2a000; }
`;
