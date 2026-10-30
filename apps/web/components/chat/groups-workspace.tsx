"use client";

import { UserAvatar } from "@/components/account/user-avatar";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import {
  Archive,
  ArrowLeft,
  Bell,
  BellOff,
  Check,
  CheckCheck,
  ChevronRight,
  Download,
  FileText,
  Image as ImageIcon,
  Info,
  Copy,
  Reply,
  Edit3,
  Trash2,
  LogOut,
  MessageCircle,
  Mic,
  MoreHorizontal,
  Paperclip,
  Phone,
  Pin,
  Plus,
  Search,
  Send,
  Settings,
  Shield,
  Smile,
  Square,
  UserPlus,
  Users,
  Video,
  X,
} from "lucide-react";
import {
  Suspense,
  useCallback,
  useEffect,
  useMemo,
  useLayoutEffect,
  useRef,
  useState,
} from "react";
import type { FormEvent, ReactNode } from "react";
import { createPortal } from "react-dom";
import { api } from "@/lib/api/client";
import { isAutomaticVoiceText } from "@/components/chat/message-attachments";
import { chatFeaturesService } from "@/services/chat-features.service";
import { socialChatService as chat } from "@/services/social-chat.service";
import { ConversationCallPanel } from "@/components/chat/conversation-call-panel";
import type { CallKind } from "@/types/conversation-call";
import { AudioAttachmentPlayer } from "@/components/chat/audio-attachment-player";
import { VoiceRecordingIndicator } from "@/components/chat/voice-recording-indicator";
import { useWorkspace } from "@/contexts/workspace-context";
import { personalSocialService } from "@/services/personal-social.service";
import {
  groupsChatService as socialChatService,
} from "@/services/groups-chat.service";
import type {
  ChatMessagePublic,
  ConversationPublic,
  MessageReceiptPublic,
} from "@/types/social-chat";
import { FullEmojiPicker } from "@/components/chat/full-emoji-picker";
import { isSingleEmojiMessage } from "@/lib/chat-emoji";
import { jumpToMessage } from "@/lib/jump-to-message";
import { ChatAttachmentPicker } from "@/components/chat/chat-attachment-picker";

type FriendItem = {
  id: string;
  status: string;
  person: {
    id: string;
    name?: string | null;
    username?: string | null;
    avatar_url?: string | null;
  };
};

type Summary = {
  conversation_id: string;
  unread_count: number;
  pinned: boolean;
  muted: boolean;
  archived: boolean;
  last_read_at?: string | null;
};

type Member = {
  user_id: string;
  name?: string | null;
  username?: string | null;
  avatar_url?: string | null;
  role: "owner" | "admin" | "member";
  online?: boolean;
};

type AvatarMode = "auto" | "photo" | "members";

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

type GroupDetails = {
  avatar_attachment_id?: string | null;
  avatar_mode?: AvatarMode;
  avatar_error?: string | null;
  description?: string | null;
  avatar_url?: string | null;
  members: Member[];
  can_manage: boolean;
};

type Attachment = {
  attachment_id: string;
  message_id: string;
  filename: string;
  content_type: string;
  size_bytes: number;
  kind: "IMAGE" | "VIDEO" | "AUDIO" | "FILE";
};

type Message = ChatMessagePublic & {
  reply_to_message_id?: string | null;
  reactions?: Record<string, number>;
  pinned?: boolean;
  delivered_at?: string | null;
  read_at?: string | null;
  attachments?: Attachment[];
};

const EMOJIS = [
  "ðŸ˜€", "ðŸ˜‚", "ðŸ˜", "â¤ï¸", "ðŸ‘",
  "ðŸ‘", "ðŸŽ‰", "ðŸ™", "ðŸ”¥", "ðŸ˜®",
];

type GroupInboxState = {
  conversation_id: string;
  cleared_before: string | null;
};

type BulkAction = "mute" | "unmute" | "clear" | "delete" | "leave";
type BulkRequest = { action: BulkAction; groupIds: string[] };
const BULK_LABELS: Record<BulkAction, string> = {
  mute: "Mute groups",
  unmute: "Unmute groups",
  clear: "Clear my chats",
  delete: "Delete groups",
  leave: "Leave groups",
};
const inboxRoute = (id: string) => `/chat/group-inbox/${encodeURIComponent(id)}`;

type Tab = "all" | "unread" | "recent" | "archived";

type Panel =
  | "create"
  | "members"
  | "admins"
  | "files"
  | "pinned"
  | "manage"
  | "add"
  | "leave"
  | "info"
  | "reactions"
  | "bulk"
  | null;

/*
 * These are frontend adapter contracts, not assertions that these methods
 * already exist in your service.
 *
 * Implement them in social-chat.service.ts using your authenticated
 * HTTP client and the endpoints described after this file.
 */
type Extensions = {
  listConversationFeatures?: () => Promise<Summary[]>;
  listFeatureMessages?: (id: string) => Promise<Message[]>;
  getGroupDetails?: (id: string) => Promise<GroupDetails>;
  listSharedFiles?: (id: string) => Promise<Attachment[]>;
  sendFeatureMessage?: (
    id: string,
    body: {
      content: string;
      client_message_id: string;
      reply_to_message_id: string | null;
    },
  ) => Promise<Message>;
  uploadMessageAttachment?: (
    id: string,
    file: File,
  ) => Promise<Message>;
  downloadAttachment?: (
    attachmentId: string,
  ) => Promise<{ download_url: string }>;
  addMember?: (id: string, userId: string) => Promise<unknown>;
  removeMember?: (id: string, userId: string) => Promise<unknown>;
  updateMemberRole?: (
    id: string,
    userId: string,
    role: "admin" | "member",
  ) => Promise<unknown>;
  updateGroup?: (
    id: string,
    body: {
      name: string;
      description: string;
      avatar_attachment_id?: string | null;
      avatar_mode?: AvatarMode;
    },
  ) => Promise<unknown>;
  leaveGroup?: (id: string) => Promise<unknown>;
  setMessagePinned?: (
    id: string,
    messageId: string,
    pinned: boolean,
  ) => Promise<unknown>;
  editMessage?: (
    id: string,
    messageId: string,
    content: string,
  ) => Promise<Message>;
  startTyping?: (id: string) => Promise<unknown>;
  stopTyping?: (id: string) => Promise<unknown>;
  /*
   * This must start your real media controller, not merely create a
   * database call record. It owns capture, signaling, remote playback,
   * screen sharing, and cleanup.
   */
  startGroupCall?: (
    id: string,
    kind: "voice" | "video" | "screen",
  ) => Promise<void>;
  /*
   * Adapt the existing realtime client to this callback.
   * Return an unsubscribe function.
   */
  subscribeConversation?: (
    id: string,
    onEvent: (
      event:
        | { type: "messages" }
        | { type: "group" }
        | { type: "typing"; user_ids: string[] },
    ) => void,
  ) => () => void;
};

const service = socialChatService as typeof socialChatService & Extensions;

function extension<K extends keyof Extensions>(
  name: K,
): NonNullable<Extensions[K]> {
  const method = service[name];

  if (typeof method !== "function") {
    throw new Error(
      `This control needs socialChatService.${name}() connected. ` +
        "See the backend/service mapping supplied with this page.",
    );
  }

  return method.bind(service) as NonNullable<Extensions[K]>;
}

function errorText(cause: unknown) {
  return cause instanceof Error
    ? cause.message
    : "The request failed. Please try again.";
}

function initials(name?: string | null) {
  return (name?.trim() || "G")
    .split(/\s+/)
    .map((part) => part[0] || "")
    .join("")
    .slice(0, 2)
    .toUpperCase();
}

function time(value?: string | null) {
  if (!value) return "";

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";

  return date.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });
}

function day(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";

  const today = new Date();
  const yesterday = new Date();
  yesterday.setDate(today.getDate() - 1);

  if (date.toDateString() === today.toDateString()) return "Today";
  if (date.toDateString() === yesterday.toDateString()) return "Yesterday";

  return date.toLocaleDateString([], {
    month: "short",
    day: "numeric",
    year: date.getFullYear() === today.getFullYear() ? undefined : "numeric",
  });
}

function fileSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function sortMessages(items: Message[]) {
  return [...items].sort(
    (a, b) =>
      new Date(a.created_at).getTime() -
        new Date(b.created_at).getTime() ||
      a.id.localeCompare(b.id),
  );
}

function mergeMessage(items: Message[], next: Message) {
  const previous = items.find(
    (item) => item.id === next.id,
  );

  const merged: Message = {
    ...previous,
    ...next,
    attachments:
      next.attachments ??
      previous?.attachments,
  };

  return sortMessages([
    ...items.filter(
      (item) => item.id !== next.id,
    ),
    merged,
  ]);
}

function Avatar({ name, src, userId, group = false, online = false }: {
  name?: string | null; src?: string | null; userId?: string | null;
  group?: boolean; online?: boolean;
}) {
  return <span className={`gp-avatar ${group ? "is-group" : ""}`}>
    <UserAvatar userId={userId} src={src} name={name}
      fallback={group ? <Users size={25} /> : initials(name)} />
    {online && <i className="gp-online-badge" />}
  </span>;
}

export function GroupAvatar({
  name,
  details,
  mode,
  preview,
}: {
  name?: string | null;
  details?: GroupDetails;
  mode?: AvatarMode;
  preview?: string | null;
}) {
  const selectedMode = mode ?? details?.avatar_mode ?? "auto";
  const image = preview ?? details?.avatar_url;
  if (selectedMode !== "members" && image) return <Avatar group name={name} src={image} />;
  const people = [...(details?.members || [])]
    .sort((a, b) => Number(Boolean(b.avatar_url)) - Number(Boolean(a.avatar_url)))
    .slice(0, 3);
  if (!people.length) return <Avatar group name={name} />;
  return (
    <span
      className="gp-avatar gp-group-avatar-stack"
      role="img"
      aria-label={`${name || "Group"} member photos`}
    >
      {people.map((person, index) => (
        <span
          className={`gp-avatar-part gp-avatar-part-${index}`}
          key={person.user_id}
        >
          <UserAvatar userId={person.user_id} name={person.name || person.username} src={person.avatar_url} />
        </span>
      ))}
    </span>
  );
}

async function prepareGroupPhoto(file: File): Promise<File> {
  if (!file.type.startsWith("image/")) throw new Error("Choose an image for the group photo.");
  if (file.size > 10 * 1024 * 1024) throw new Error("Choose an image smaller than 10 MB.");
  const url = URL.createObjectURL(file);
  try {
    const image = await new Promise<HTMLImageElement>((resolve, reject) => {
      const element = new Image();
      element.onload = () => resolve(element);
      element.onerror = () => reject(new Error("This image could not be opened. Try PNG or JPEG."));
      element.src = url;
    });
    const side = Math.min(image.naturalWidth, image.naturalHeight);
    if (!side) throw new Error("The image has no usable dimensions.");
    const canvas = document.createElement("canvas");
    canvas.width = 512;
    canvas.height = 512;
    const context = canvas.getContext("2d");
    if (!context) throw new Error("Image processing is unavailable in this browser.");
    context.drawImage(image, (image.naturalWidth - side) / 2, (image.naturalHeight - side) / 2, side, side, 0, 0, 512, 512);
    const blob = await new Promise<Blob>((resolve, reject) => canvas.toBlob(
      (value) => value ? resolve(value) : reject(new Error("Could not prepare this photo.")), "image/png",
    ));
    if (blob.size > 2 * 1024 * 1024) throw new Error("The prepared group photo exceeds 2 MB. Try a simpler image.");
    return new File([blob], "group-photo.png", { type: "image/png" });
  } finally {
    URL.revokeObjectURL(url);
  }
}

function IconButton({
  label,
  children,
  onClick,
  disabled,
}: {
  label: string;
  children: ReactNode;
  onClick: () => void;
  disabled?: boolean;
}) {
  return (
    <button
      type="button"
      className="gp-icon"
      title={label}
      aria-label={label}
      onClick={onClick}
      disabled={disabled}
    >
      {children}
    </button>
  );
}

function FloatingMenu({
  anchor,
  label,
  children,
  onClose,
  inbox = false,
}: {
  anchor: HTMLElement;
  label: string;
  children: ReactNode;
  onClose: () => void;
  inbox?: boolean;
}) {
  const menuRef = useRef<HTMLDivElement>(null);
  const closeRef = useRef(onClose);
  closeRef.current = onClose;
  const [position, setPosition] = useState<{ top: number; left: number } | null>(null);

  useLayoutEffect(() => {
    const menu = menuRef.current;
    if (!menu) return;
    function place() {
      if (!anchor.isConnected || !menu) {
        closeRef.current();
        return;
      }
      const target = anchor.getBoundingClientRect();
      const box = menu.getBoundingClientRect();
      const viewport = window.visualViewport;
      const height = viewport?.height ?? window.innerHeight;
      const width = viewport?.width ?? window.innerWidth;
      const offsetTop = viewport?.offsetTop ?? 0;
      const offsetLeft = viewport?.offsetLeft ?? 0;
      const gap = 6;
      const minTop = offsetTop + 8;
      const maxTop = Math.max(minTop, offsetTop + height - box.height - 8);
      const below = target.bottom + gap;
      const top = below + box.height <= offsetTop + height - 8
        ? below
        : target.top - box.height - gap;
      setPosition({
        top: Math.max(minTop, Math.min(top, maxTop)),
        left: Math.max(offsetLeft + 8, Math.min(target.right - box.width, offsetLeft + width - box.width - 8)),
      });
    }
    place();
    function outside(event: PointerEvent) {
      const target = event.target as Node;
      if (!menu?.contains(target) && !anchor.contains(target)) closeRef.current();
    }
    function onKey(event: KeyboardEvent) {
      if (!menu) return;
      const buttons = Array.from(menu.querySelectorAll<HTMLButtonElement>("button:not(:disabled)"));
      const index = buttons.indexOf(document.activeElement as HTMLButtonElement);
      if (event.key === "Escape") {
        event.preventDefault();
        closeRef.current();
        anchor.focus();
      } else if (["ArrowDown", "ArrowUp", "Home", "End"].includes(event.key)) {
        event.preventDefault();
        const next = event.key === "Home" ? 0 : event.key === "End" ? buttons.length - 1
          : (index + (event.key === "ArrowDown" ? 1 : -1) + buttons.length) % buttons.length;
        buttons[next]?.focus();
      } else if (event.key === "Tab") {
        closeRef.current();
      }
    }
    function scroll(event: Event) {
      if (!menu?.contains(event.target as Node)) place();
    }
    menu.querySelector<HTMLButtonElement>("button:not(:disabled)")?.focus();
    document.addEventListener("pointerdown", outside);
    document.addEventListener("keydown", onKey);
    window.addEventListener("resize", place);
    window.addEventListener("scroll", scroll, true);
    window.visualViewport?.addEventListener("resize", place);
    return () => {
      document.removeEventListener("pointerdown", outside);
      document.removeEventListener("keydown", onKey);
      window.removeEventListener("resize", place);
      window.removeEventListener("scroll", scroll, true);
      window.visualViewport?.removeEventListener("resize", place);
    };
  }, [anchor]);

  if (typeof document === "undefined") return null;
  return createPortal(
    <div
      ref={menuRef}
      className="gp-floating-menu"
      data-group-inbox-menu={inbox || undefined}
      role="group"
      aria-label={label}
      style={{
        top: position?.top ?? 0,
        left: position?.left ?? 0,
        visibility: position ? "visible" : "hidden",
      }}
      onClick={(event) => {
        if ((event.target as HTMLElement).closest("button:not(:disabled)")) onClose();
      }}
    >
      {children}
    </div>,
    document.body,
  );
}

export default function GroupsPage() {
  return (
    <Suspense fallback={<div className="gp-route-loading">Loading groups</div>}>
      <GroupsContent />
    </Suspense>
  );
}

export function GroupsContent({
  conversationId = null,
  embedded = false,
}: {
  conversationId?: string | null;
  embedded?: boolean;
} = {}) {
  const router = useRouter();
  const params = useSearchParams();
  const { user, loading: accountLoading } = useWorkspace();

  const requestedId = conversationId ?? params.get("conversation");

  const [groups, setGroups] = useState<ConversationPublic[]>([]);
  const [friends, setFriends] = useState<FriendItem[]>([]);
  const [summaries, setSummaries] = useState<Record<string, Summary>>({});
  const [details, setDetails] = useState<Record<string, GroupDetails>>({});
  const [messages, setMessages] = useState<Message[]>([]);
  const [activeId, setActiveId] = useState<string | null>(requestedId);
  const [tab, setTab] = useState<Tab>("all");
  const [search, setSearch] = useState("");
  const [messageSearch, setMessageSearch] = useState("");
  const [showSearch, setShowSearch] = useState(false);
  const [draft, setDraft] = useState("");
  const [reply, setReply] = useState<Message | null>(null);
  const [editing, setEditing] = useState<Message | null>(null);
  const [emojiOpen, setEmojiOpen] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const [messageMenu, setMessageMenu] = useState<string | null>(null);
  const [messageMenuAnchor, setMessageMenuAnchor] = useState<HTMLElement | null>(null);
  const [inboxMenuAnchor, setInboxMenuAnchor] = useState<HTMLElement | null>(null);
  const [inboxMenuOpen, setInboxMenuOpen] = useState(false);
  const [selectionMode, setSelectionMode] = useState(false);
  const [selectedGroupIds, setSelectedGroupIds] = useState<string[]>([]);
  const [bulkRequest, setBulkRequest] = useState<BulkRequest | null>(null);
  const [clearStates, setClearStates] = useState<Record<string, string | null>>({});
  const clearStatesRef = useRef<Record<string, string | null>>({});
  const callStartingRef = useRef(false);
  const [reactionPicker, setReactionPicker] = useState<string | null>(null);
  const [detailsOpen, setDetailsOpen] = useState(true);
  const [mobileChat, setMobileChat] = useState(false);
  const [panel, setPanel] = useState<Panel>(null);
  const panelRef = useRef<Panel>(panel);
  panelRef.current = panel;
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [avatarMode, setAvatarMode] = useState<AvatarMode>("auto");
  const [avatarAttachmentId, setAvatarAttachmentId] = useState<string | null>(null);
  const [avatarFile, setAvatarFile] = useState<File | null>(null);
  const [avatarPreview, setAvatarPreview] = useState<string | null>(null);
  const [avatarPreparing, setAvatarPreparing] = useState(false);
  const avatarUploadRef = useRef<{ groupId: string; file: File; message: Message } | null>(null);
  const avatarInputRef = useRef<HTMLInputElement>(null);
  const avatarPreparationRef = useRef(0);
  const detailsFetchedRef = useRef<Record<string, number>>({});
  const inboxRef = useRef<HTMLElement>(null);
  const [reactionTarget, setReactionTarget] = useState<Message | null>(null);
  const [reactionPeople, setReactionPeople] = useState<ReactionPeople | null>(null);
  const [reactionTab, setReactionTab] = useState("all");
  const [reactionLoading, setReactionLoading] = useState(false);
  const [reactionError, setReactionError] = useState("");
  const [reactionRemoving, setReactionRemoving] = useState<string | null>(null);
  const reactionViewRef = useRef<{ groupId: string; messageId: string; owner: string | undefined } | null>(null);
  const reactionRequestRef = useRef(0);
  const reactionRemovingRef = useRef(false);
  const [selectedFriends, setSelectedFriends] = useState<string[]>([]);
  const [sharedFiles, setSharedFiles] = useState<Attachment[]>([]);
  const [typingIds, setTypingIds] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [messagesLoading, setMessagesLoading] = useState(false);
  const [busy, setBusy] = useState(false);
  const busyRef = useRef(busy);
  busyRef.current = busy;
  const [recording, setRecording] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [infoMessage, setInfoMessage] = useState<Message | null>(null);
  const [receipts, setReceipts] = useState<Record<string, MessageReceiptPublic[]>>({});
  const [infoLoading, setInfoLoading] = useState(false);
  const [infoError, setInfoError] = useState("");
  const [call, setCall] = useState<{
    conversationId: string;
    name: string;
    kind: CallKind;
    invitedUserIds: string[];
  } | null>(null);
  const closeCall = useCallback(() => setCall(null), []);
  const reactionInFlightRef = useRef(false);
  const ownReactionsRef = useRef(new Set<string>());
  const infoRequestRef = useRef(0);

  const activeIdRef = useRef<string | null>(activeId);
  const accountRef = useRef<string | undefined>(user?.id);
  const listVersionRef = useRef(0);
  const messageVersionRef = useRef(0);
  const listInFlightRef = useRef(false);
  const initialLoadCompleteRef = useRef(false);
  const scrollBottomRef = useRef(true);
  const draftCacheRef = useRef<Record<string, string>>({});
  const composerRef = useRef<HTMLTextAreaElement>(null);
  const messagesRef = useRef<HTMLDivElement>(null);
  const uploadRef = useRef<HTMLInputElement>(null);
  const searchRef = useRef<HTMLInputElement>(null);
  const modalRef = useRef<HTMLDivElement>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const mediaRef = useRef<MediaStream | null>(null);
  const typingTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const lastTypingRef = useRef(0);

  activeIdRef.current = activeId;
  accountRef.current = user?.id;

  const activeGroup = groups.find((group) => group.id === activeId);
  const activeSummary = activeId ? summaries[activeId] : undefined;
  const activeDetails = activeId ? details[activeId] : undefined;
  const members = activeDetails?.members || [];
  const canManage = Boolean(activeDetails?.can_manage);

  const directory = useMemo(() => {
    const result = new Map<string, Member>();

    friends.forEach((friend) => {
      result.set(friend.person.id, {
        user_id: friend.person.id,
        name: friend.person.name,
        username: friend.person.username,
        avatar_url: friend.person.avatar_url,
        role: "member",
      });
    });

    Object.values(details).forEach((group) => {
      group.members.forEach((member) => result.set(member.user_id, member));
    });

    return result;
  }, [friends, details]);

  const displayName = useCallback(
    (id?: string | null) => {
      if (id === user?.id) return "You";
      const person = id ? directory.get(id) : undefined;
      return person?.name || person?.username || "Member";
    },
    [directory, user?.id],
  );

  const visibleGroups = useMemo(() => {
    const term = search.trim().toLowerCase();

    return groups
      .filter((group) => {
        const summary = summaries[group.id];

        if (!(group.name || "").toLowerCase().includes(term)) return false;
        if (tab === "archived") return summary?.archived === true;
        if (summary?.archived) return false;
        if (tab === "unread") return (summary?.unread_count || 0) > 0;

        return true;
      })
      .sort((a, b) => {
        if (tab !== "recent") {
          const pinned =
            Number(Boolean(summaries[b.id]?.pinned)) -
            Number(Boolean(summaries[a.id]?.pinned));

          if (pinned) return pinned;
        }

        return (
          new Date(b.updated_at).getTime() -
          new Date(a.updated_at).getTime()
        );
      });
  }, [groups, summaries, search, tab]);

  const visibleMessages = useMemo(() => {
    const term = messageSearch.trim().toLowerCase();

    return messages.filter(
      (item) =>
        !item.deleted_at &&
        (!activeId || !clearStates[activeId] || Date.parse(item.created_at) > Date.parse(clearStates[activeId]!)) &&
        (!term || item.content.toLowerCase().includes(term)),
    );
  }, [messages, messageSearch, activeId, clearStates]);

  async function run(action: () => Promise<void>) {
    if (busy) return;

    setBusy(true);
    setError("");
    setNotice("");

    try {
      await action();
    } catch (cause) {
      setError(errorText(cause));
    } finally {
      setBusy(false);
    }
  }

  const loadGroups = useCallback(async () => {
    if (!user?.id || !user.is_email_verified) {
      setLoading(false);
      return;
    }

    if (listInFlightRef.current) return;

    listInFlightRef.current = true;
    const version = ++listVersionRef.current;
    const owner = user.id;

    if (!initialLoadCompleteRef.current) setLoading(true);

    try {
      const results = await Promise.allSettled([
        socialChatService.listConversations(),
        personalSocialService.friends(),
        service.listConversationFeatures
          ? service.listConversationFeatures()
          : Promise.resolve<Summary[] | null>(null),
        api.get<GroupInboxState[]>("/chat/group-inbox/states"),
      ]);

      if (
        version !== listVersionRef.current ||
        accountRef.current !== owner
      ) {
        return;
      }

      const failures: string[] = [];
      const conversationResult = results[0];
      const friendResult = results[1];
      const summaryResult = results[2];
      const clearResult = results[3];
      if (clearResult.status === "fulfilled") {
        const next = Object.fromEntries(clearResult.value.map((item) => [item.conversation_id, item.cleared_before]));
        clearStatesRef.current = next;
        setClearStates(next);
      } else {
        failures.push("Group inbox actions need group_inbox_router.py and its database setup installed.");
      }

      if (conversationResult.status === "fulfilled") {
        const next = conversationResult.value.filter(
          (item) => item.conversation_type === "group" && item.is_active,
        );

        setGroups(next);
        setActiveId((previous) => {
          if (previous && next.some((item) => item.id === previous)) {
            return previous;
          }

          if (requestedId && next.some((item) => item.id === requestedId)) {
            return requestedId;
          }

          return embedded ? null : next[0]?.id || null;
        });
      } else {
        failures.push(errorText(conversationResult.reason));
      }

      if (friendResult.status === "fulfilled") {
        const items = friendResult.value.items as FriendItem[];
        setFriends(
          items.filter(
            (item) =>
              item.status === "accepted" &&
              item.person.id !== owner,
          ),
        );
      } else {
        failures.push(errorText(friendResult.reason));
      }

      if (summaryResult.status === "fulfilled") {
        const values = summaryResult.value;

        if (values) {
          setSummaries(
            Object.fromEntries(
              values.map((item) => [item.conversation_id, item]),
            ),
          );
        }
      } else {
        failures.push(errorText(summaryResult.reason));
      }

      if (failures.length) setError([...new Set(failures)].join(" "));
    } finally {
      if (version === listVersionRef.current) {
        initialLoadCompleteRef.current = true;
        listInFlightRef.current = false;
        setLoading(false);
      }
    }
  }, [user?.id, user?.is_email_verified, requestedId, embedded]);

  const loadMessages = useCallback(
    async (id: string, initial = false) => {
      const version = ++messageVersionRef.current;
      const owner = accountRef.current;

      if (initial) setMessagesLoading(true);

      try {
        const [data, inboxState, hiddenState] = await Promise.all([
          service.listFeatureMessages
            ? service.listFeatureMessages(id)
            : socialChatService.getMessages(id),
          api.get<GroupInboxState>(`${inboxRoute(id)}/state`),
          api.get<{ message_ids: string[] }>(
            `/chat/group-controls/${id}/hidden-messages`,
          ),
        ]);

        if (
          version !== messageVersionRef.current ||
          activeIdRef.current !== id ||
          accountRef.current !== owner
        ) {
          return;
        }

        const cutoff = inboxState.cleared_before;
        clearStatesRef.current = { ...clearStatesRef.current, [id]: cutoff };
        setClearStates((current) => ({ ...current, [id]: cutoff }));
        const hiddenMessageIds = new Set(
          hiddenState.message_ids,
        );

        const ordered = sortMessages(data).filter(
          (item) =>
            !hiddenMessageIds.has(item.id) &&
            (
              !cutoff ||
              Date.parse(item.created_at) > Date.parse(cutoff)
            ),
        );
        setMessages(ordered);

        // Match Chat's per-message read receipts without blocking message rendering.
        const sent = ordered.filter((item) => item.sender_user_id === owner && !item.deleted_at).slice(-20);
        void Promise.allSettled(
          sent.map(async (item) => [item.id, await chat.listReadReceipts(id, item.id)] as const),
        ).then((results) => {
          if (version !== messageVersionRef.current || activeIdRef.current !== id || accountRef.current !== owner) return;
          setReceipts((current) => {
            const next = { ...current };
            for (const result of results) {
              if (result.status === "fulfilled") {
                next[result.value[0]] = result.value[1].filter((receipt) => receipt.user_id !== owner);
              }
            }
            return next;
          });
        });

        const last = ordered.filter((item) => !item.deleted_at).at(-1);

        if (last && document.visibilityState === "visible" && document.hasFocus() && scrollBottomRef.current && !panelRef.current && messagesRef.current?.getClientRects().length) {
          try {
            const updated = await socialChatService.markReadThrough(id, last.id);

            if (activeIdRef.current === id) {
              setSummaries((current) => {
                const existing = current[id];

                return existing
                  ? {
                      ...current,
                      [id]: { ...existing, ...updated },
                    }
                  : current;
              });
            }
          } catch (cause) {
            if (activeIdRef.current === id) {
              setError(`Messages loaded, but marking read failed: ${errorText(cause)}`);
            }
          }
        }
      } catch (cause) {
        if (
          version === messageVersionRef.current &&
          activeIdRef.current === id
        ) {
          setError(errorText(cause));
        }
      } finally {
        if (version === messageVersionRef.current) {
          setMessagesLoading(false);
        }
      }
    },
    [],
  );

  const loadDetails = useCallback(async (id: string) => {
    detailsFetchedRef.current[id] = Date.now();
    if (!service.getGroupDetails) return;
    const owner = accountRef.current;

    try {
      const result = await service.getGroupDetails(id);

      if (accountRef.current === owner) {
        setDetails((current) => ({ ...current, [id]: result }));
      }
    } catch (cause) {
      if (activeIdRef.current === id) setError(errorText(cause));
    }
  }, []);

  useEffect(() => {
    if (!user?.is_email_verified || !service.getGroupDetails) return;
    const pending = groups.filter((group) => group.id !== activeIdRef.current && Date.now() - (detailsFetchedRef.current[group.id] || 0) > 120000);
    let cursor = 0;
    let cancelled = false;
    void Promise.all(Array.from({ length: Math.min(3, pending.length) }, async () => {
      while (!cancelled && cursor < pending.length) {
        const group = pending[cursor++];
        if (group) await loadDetails(group.id);
      }
    }));
    return () => { cancelled = true; };
  }, [groups, loadDetails, user?.is_email_verified]);

  useEffect(() => {
    if (!avatarFile) {
      setAvatarPreview(null);
      return;
    }
    const url = URL.createObjectURL(avatarFile);
    setAvatarPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [avatarFile]);

  useEffect(() => {
    if (panel !== "manage") {
      avatarPreparationRef.current += 1;
      setAvatarPreparing(false);
    }
  }, [panel]);

  useEffect(() => {
    if (!selectionMode || panel === "bulk") return;
    function cancelOutside(event: PointerEvent) {
      const target = event.target;
      if (!(target instanceof Element)) return;
      if (inboxRef.current?.contains(target) || target.closest("[data-group-inbox-menu]")) return;
      setInboxMenuOpen(false);
      setSelectionMode(false);
      setSelectedGroupIds([]);
    }
    function escape(event: KeyboardEvent) {
      if (event.key !== "Escape") return;
      setInboxMenuOpen(false);
      setSelectionMode(false);
      setSelectedGroupIds([]);
    }
    document.addEventListener("pointerdown", cancelOutside);
    document.addEventListener("keydown", escape);
    return () => {
      document.removeEventListener("pointerdown", cancelOutside);
      document.removeEventListener("keydown", escape);
    };
  }, [selectionMode, panel]);

  useEffect(() => {
    if (panel === "reactions") return;
    reactionViewRef.current = null;
    reactionRequestRef.current += 1;
  }, [panel, activeId, user?.id]);

  useEffect(() => {
    listVersionRef.current += 1;
    messageVersionRef.current += 1;
    listInFlightRef.current = false;
    initialLoadCompleteRef.current = false;

    setGroups([]);
    setFriends([]);
    setSummaries({});
    setDetails({});
    setMessages([]);
    setPanel(null);
    setError("");
    setNotice("");
    setReceipts({});
    detailsFetchedRef.current = {};
    reactionViewRef.current = null;
    reactionRequestRef.current += 1;
    setReactionTarget(null);
    setReactionPeople(null);
    setReactionRemoving(null);
    avatarPreparationRef.current += 1;
    avatarUploadRef.current = null;
    setAvatarFile(null);
    setAvatarPreparing(false);
    setClearStates({});
    clearStatesRef.current = {};
    setSelectionMode(false);
    setSelectedGroupIds([]);
    setBulkRequest(null);
    setInboxMenuOpen(false);
    setInfoMessage(null);
    setCall(null);
    ownReactionsRef.current.clear();
    infoRequestRef.current += 1;
    draftCacheRef.current = {};

    return () => {
      listVersionRef.current += 1;
      messageVersionRef.current += 1;
    };
  }, [user?.id]);

  useEffect(() => {
    if (!accountLoading) void loadGroups();
  }, [accountLoading, loadGroups]);

  useEffect(() => {
    if (
      requestedId &&
      groups.some((group) => group.id === requestedId)
    ) {
      setActiveId(requestedId);
    }
  }, [requestedId, groups]);

  useEffect(() => {
    setMessages([]);
    reactionViewRef.current = null;
    reactionRequestRef.current += 1;
    setPanel((current) => current === "reactions" || current === "manage" ? null : current);
    setAvatarFile(null);
    avatarUploadRef.current = null;
    avatarPreparationRef.current += 1;
    setTypingIds([]);
    setReply(null);
    setEditing(null);
    setMessageSearch("");
    setMessageMenu(null);
    setMessageMenuAnchor(null);
    setMenuOpen(false);
    setDraft(activeId ? draftCacheRef.current[activeId] || "" : "");
    scrollBottomRef.current = true;

    if (!activeId || !user?.is_email_verified) {
      setMessagesLoading(false);
      return;
    }

    void loadMessages(activeId, true);
    void loadDetails(activeId);

    const unsubscribe = service.subscribeConversation?.(
      activeId,
      (event) => {
        if (event.type === "typing") {
          setTypingIds(
            event.user_ids.filter((id) => id !== accountRef.current),
          );
        } else if (event.type === "messages") {
          void loadMessages(activeId);
          void loadGroups();
        } else {
          void loadDetails(activeId);
          void loadGroups();
        }
      },
    );

    return () => {
      messageVersionRef.current += 1;
      unsubscribe?.();

      if (typingTimerRef.current) clearTimeout(typingTimerRef.current);
      void service.stopTyping?.(activeId).catch(() => undefined);
    };
  }, [
    activeId,
    user?.is_email_verified,
    loadMessages,
    loadDetails,
    loadGroups,
  ]);

  useEffect(() => {
    if (!user?.is_email_verified) return;
    let stopped = false;
    let refreshing = false;
    let lastDetails = 0;
    async function refreshVisibleGroups() {
      if (stopped || refreshing || busyRef.current || document.visibilityState !== "visible") return;
      refreshing = true;
      try {
        await loadGroups();
        if (stopped) return;
        const id = activeIdRef.current;
        if (id && !service.subscribeConversation) await loadMessages(id);
        if (id && Date.now() - lastDetails > 30000) {
          lastDetails = Date.now();
          await loadDetails(id);
        }
      } finally {
        refreshing = false;
      }
    }
    function focus() { void refreshVisibleGroups(); }
    const timer = window.setInterval(focus, 8000);
    window.addEventListener("focus", focus);
    document.addEventListener("visibilitychange", focus);
    return () => {
      stopped = true;
      window.clearInterval(timer);
      window.removeEventListener("focus", focus);
      document.removeEventListener("visibilitychange", focus);
    };
  }, [user?.id, user?.is_email_verified, loadGroups, loadMessages, loadDetails]);

  useEffect(() => {
    if (!scrollBottomRef.current) return;

    const element = messagesRef.current;
    if (element) element.scrollTop = element.scrollHeight;
  }, [messages, typingIds, messagesLoading]);

  useEffect(() => {
    if (showSearch) searchRef.current?.focus();
  }, [showSearch]);

  useEffect(() => {
    if (!panel) return;

    const previousFocus = document.activeElement as HTMLElement | null;
    const root = modalRef.current;

    root?.querySelector<HTMLElement>(
      "input, textarea, button, [tabindex='0']",
    )?.focus();

    function onKey(event: KeyboardEvent) {
      if (event.key === "Escape") setPanel(null);
      if (event.key !== "Tab" || !root) return;

      const items = Array.from(
        root.querySelectorAll<HTMLElement>(
          "button:not(:disabled), input:not(:disabled), textarea:not(:disabled), a[href]",
        ),
      );

      const first = items[0];
      const last = items.at(-1);

      if (!first || !last) return;

      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    }

    document.addEventListener("keydown", onKey);

    return () => {
      document.removeEventListener("keydown", onKey);
      previousFocus?.focus();
    };
  }, [panel]);

  useEffect(() => {
    return () => {
      const recorder = recorderRef.current;
      if (recorder) {
        recorder.onstop = null;
        if (recorder.state !== "inactive") recorder.stop();
      }

      mediaRef.current?.getTracks().forEach((track) => track.stop());
      if (typingTimerRef.current) clearTimeout(typingTimerRef.current);
    };
  }, []);
  useEffect(() => {
    setReactionPicker(null);
    setInfoMessage(null);
    setInfoLoading(false);
    infoRequestRef.current += 1;
    setPanel((current) => current === "info" ? null : current);
  }, [
    activeId,
    user?.id,
  ]);

  useEffect(() => {
    if (!reactionPicker) {
      return;
    }

    function onPointerDown(event: PointerEvent) {
      const target = event.target;

      if (
        target instanceof Element &&
        target.closest(
          ".gp-message-reaction, .gp-reaction-picker",
        )
      ) {
        return;
      }

      setReactionPicker(null);
    }

    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setReactionPicker(null);
      }
    }

    document.addEventListener(
      "pointerdown",
      onPointerDown,
    );

    document.addEventListener(
      "keydown",
      onKeyDown,
    );

    return () => {
      document.removeEventListener(
        "pointerdown",
        onPointerDown,
      );

      document.removeEventListener(
        "keydown",
        onKeyDown,
      );
    };
  }, [reactionPicker]);

  function openConversation(id: string) {
    if (recording) {
      setError("Stop your voice recording before changing groups.");
      return;
    }

    if (activeId) draftCacheRef.current[activeId] = draft;

    activeIdRef.current = id;
    setActiveId(id);
    setMobileChat(true);

    router.replace(
      `/groups?conversation=${encodeURIComponent(id)}`,
      { scroll: false },
    );
  }

  function changeDraft(value: string) {
    setDraft(value);

    if (!activeId) return;
    draftCacheRef.current[activeId] = value;

    if (service.startTyping && Date.now() - lastTypingRef.current > 2500) {
      lastTypingRef.current = Date.now();
      void service.startTyping(activeId).catch(() => undefined);
    }

    if (typingTimerRef.current) clearTimeout(typingTimerRef.current);

    const id = activeId;
    typingTimerRef.current = setTimeout(() => {
      void service.stopTyping?.(id).catch(() => undefined);
    }, 1800);
  }

  function toggleFriend(id: string) {
    setSelectedFriends((current) =>
      current.includes(id)
        ? current.filter((item) => item !== id)
        : [...current, id],
    );
  }

  async function createGroup(event: FormEvent) {
    event.preventDefault();

    const cleanName = name.trim();

    if (!cleanName || !selectedFriends.length) {
      setError("Enter a group name and choose at least one friend.");
      return;
    }

    await run(async () => {
      const created = await socialChatService.createGroup({
        name: cleanName,
        member_user_ids: selectedFriends,
      });

      setGroups((current) => [
        created,
        ...current.filter((item) => item.id !== created.id),
      ]);

      setName("");
      setSelectedFriends([]);
      setPanel(null);
      openConversation(created.id);
      void loadGroups();
    });
  }

  async function sendMessage(event?: FormEvent) {
    event?.preventDefault();

    const id = activeId;
    const content = draft.trim();
    const replyTarget = reply;
    const editTarget = editing;

    if (!id || !content || busy || recording) return;

    await run(async () => {
      let sent: Message;

      if (editTarget) {
        sent = await extension("editMessage")(id, editTarget.id, content);
      } else if (replyTarget) {
        sent = await extension("sendFeatureMessage")(id, {
          content,
          client_message_id: crypto.randomUUID(),
          reply_to_message_id: replyTarget.id,
        });
      } else if (service.sendFeatureMessage) {
        sent = await service.sendFeatureMessage(id, {
          content,
          client_message_id: crypto.randomUUID(),
          reply_to_message_id: null,
        });
      } else {
        sent = await socialChatService.sendMessage(id, { content });
      }

      if (activeIdRef.current === id) {
        messageVersionRef.current += 1;
        scrollBottomRef.current = true;
        setMessagesLoading(false);
        setMessages((current) => mergeMessage(current, sent));

        if (draftCacheRef.current[id] === draft) {
          setDraft("");
          draftCacheRef.current[id] = "";
        }

        setReply(null);
        setEditing(null);
        composerRef.current?.focus();
      }

      void service.stopTyping?.(id).catch(() => undefined);
      void loadGroups();
    });
  }

  async function updatePreference(
    key: "muted" | "pinned" | "archived",
    value: boolean,
  ) {
    const id = activeId;
    if (!id) return;

    await run(async () => {
      await socialChatService.updatePreferences(id, { [key]: value });

      setSummaries((current) => ({
        ...current,
        [id]: {
          conversation_id: id,
          unread_count: current[id]?.unread_count || 0,
          pinned: current[id]?.pinned || false,
          muted: current[id]?.muted || false,
          archived: current[id]?.archived || false,
          ...current[id],
          [key]: value,
        },
      }));

      setMenuOpen(false);
      setNotice(
        key === "muted"
          ? value
            ? "Group notifications muted."
            : "Group notifications enabled."
          : key === "pinned"
            ? value
              ? "Group pinned."
              : "Group unpinned."
            : value
              ? "Group archived."
              : "Group restored.",
      );
    });
  }

  async function callGroup(kind: "voice" | "video" | "screen") {
    const id = activeId;
    const owner = accountRef.current;
    if (!id || busy || call || callStartingRef.current) return;
    if (kind === "screen") {
      setNotice("Start a voice or video call, then use its screen-share control.");
      return;
    }
    callStartingRef.current = true;
    setError("");
    try {
      if (!navigator.mediaDevices?.getUserMedia) {
        throw new Error("Calling needs microphone access through HTTPS or localhost.");
      }
      // Use default devices, never a cached device ID from a disconnected headset.
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: true,
        video: kind === "video",
      });
      stream.getTracks().forEach((track) => track.stop());
      if (activeIdRef.current !== id || accountRef.current !== owner) return;
      const group = activeDetails ?? await extension("getGroupDetails")(id);
      if (activeIdRef.current !== id || accountRef.current !== owner) return;
      setCall({
        conversationId: id,
        name: activeGroup?.name || "Group call",
        kind: kind === "video" ? "VIDEO" : "VOICE",
        invitedUserIds: group.members.filter((member) => member.user_id !== owner).map((member) => member.user_id),
      });
    } catch (cause) {
      if (activeIdRef.current !== id || accountRef.current !== owner) return;
      const name = cause instanceof Error ? cause.name : "";
      setError(name === "NotFoundError" || name === "DevicesNotFoundError"
        ? kind === "video"
          ? "No usable microphone or camera was found. Connect both devices, check Windows input settings, then retry. You can use a voice call if only the camera is missing."
          : "No microphone was found. Connect or enable a microphone in Windows sound settings, then retry."
        : name === "NotAllowedError" || name === "PermissionDeniedError"
          ? "Microphone/camera permission was blocked. Allow access in this site's browser settings and retry."
          : name === "NotReadableError"
            ? "The microphone or camera is busy or unavailable. Close other apps using it, then retry."
            : errorText(cause));
    } finally {
      callStartingRef.current = false;
    }
  }

  function toggleGroupSelection(id: string) {
    setInboxMenuOpen(false);
    setSelectedGroupIds((current) => current.includes(id)
      ? current.filter((item) => item !== id) : [...current, id]);
  }

  function requestBulkAction(action: BulkAction) {
    const ids = selectedGroupIds.filter((id) => groups.some((group) => group.id === id));
    if (!ids.length) {
      setNotice("Select one or more groups first.");
      return;
    }
    setInboxMenuOpen(false);
    setError("");
    setBulkRequest({ action, groupIds: ids });
    setPanel("bulk");
  }

  async function executeBulkAction() {
    const request = bulkRequest;
    const owner = accountRef.current;
    if (!request || !owner || busy) return;
    setBusy(true);
    setError("");
    setNotice("");
    const succeeded: string[] = [];
    const failed: string[] = [];
    try {
      for (const id of request.groupIds) {
        if (accountRef.current !== owner) break;
        const group = groups.find((item) => item.id === id);
        try {
          if ((request.action === "delete" || request.action === "leave") && call?.conversationId === id) {
            throw new Error("End your active call in this group first.");
          }
          if (request.action === "mute" || request.action === "unmute") {
            const muted = request.action === "mute";
            await socialChatService.updatePreferences(id, { muted });
            if (accountRef.current !== owner) return;
            setSummaries((current) => ({
              ...current,
              [id]: {
                conversation_id: id, unread_count: 0, pinned: false, archived: false,
                ...current[id], muted,
              },
            }));
          } else if (request.action === "clear") {
            const state = await api.post<GroupInboxState>(`${inboxRoute(id)}/clear`, {});
            if (accountRef.current !== owner) return;
            clearStatesRef.current = { ...clearStatesRef.current, [id]: state.cleared_before };
            setClearStates((current) => ({ ...current, [id]: state.cleared_before }));
            setSummaries((current) => current[id]
              ? { ...current, [id]: { ...current[id], unread_count: 0 } } : current);
            if (activeIdRef.current === id) {
              messageVersionRef.current += 1;
              setMessagesLoading(false);
              setMessages((current) => current.filter((item) => !state.cleared_before || Date.parse(item.created_at) > Date.parse(state.cleared_before)));
              setReply(null);
              setEditing(null);
              setMessageMenu(null);
            }
          } else if (request.action === "delete") {
            if (group?.created_by_user_id !== owner) throw new Error("Only the group creator can delete this group.");
            await api.delete<void>(inboxRoute(id));
          } else {
            await extension("leaveGroup")(id);
          }
          if (accountRef.current !== owner) return;
          succeeded.push(id);
          if (request.action === "delete" || request.action === "leave") {
            setGroups((current) => current.filter((item) => item.id !== id));
            setActiveId((current) => current === id ? null : current);
          }
        } catch (cause) {
          failed.push(`${group?.name || "Group"}: ${errorText(cause)}`);
        }
      }
      if (accountRef.current !== owner) return;
      listVersionRef.current += 1;
      listInFlightRef.current = false;
      setSelectedGroupIds((current) => current.filter((id) => !succeeded.includes(id)));
      setPanel(null);
      setBulkRequest(null);
      if (succeeded.length) {
        setNotice(`${BULK_LABELS[request.action]} completed for ${succeeded.length} group${succeeded.length === 1 ? "" : "s"}.`);
      }
      if (failed.length) setError(failed.join(" "));
      if (failed.length === 0) setSelectionMode(false);
      void loadGroups();
    } finally {
      if (accountRef.current === owner) setBusy(false);
    }
  }
  async function deleteMessageForMe(id: string) {
    const conversationId = activeId;
    const owner = accountRef.current;

    if (!conversationId) return;

    await run(async () => {
      await api.post(
        `/chat/group-controls/${conversationId}/messages/${id}/hide`,
        {},
      );

      if (
        activeIdRef.current !== conversationId ||
        accountRef.current !== owner
      ) {
        return;
      }

      messageVersionRef.current += 1;
      setMessagesLoading(false);

      setMessages((current) =>
        current.filter((message) => message.id !== id),
      );

      setMessageMenu(null);
      setReactionPicker(null);

      setReply((current) =>
        current?.id === id ? null : current,
      );

      setEditing((current) =>
        current?.id === id ? null : current,
      );
    });
  }
  async function deleteMessage(id: string) {
    const conversationId = activeId;
    if (!conversationId) return;

    await run(async () => {
      await socialChatService.deleteMessage(conversationId, id);

      if (activeIdRef.current === conversationId) {
        messageVersionRef.current += 1;
        setMessagesLoading(false);
        setMessages((current) => current.filter((item) => item.id !== id));
        setMessageMenu(null);
      }
    });
  }

  async function reactToMessage(
    messageId: string,
    emoji: string,
    remove = false,
  ) {
    const id = activeId;
    const owner = accountRef.current;
    if (!id || busy || reactionInFlightRef.current) return;
    reactionInFlightRef.current = true;
    setMessageMenu(null);
    setReactionPicker(null);
    const key = JSON.stringify([owner, id, messageId, emoji]);

    try {
      await run(async () => {
        // Counts are shared by everyone; never treat a count as ownership.
        // Existing pills remove only this user's reaction, just like Chat.
        if (remove) {
          await chatFeaturesService.removeReaction(id, messageId, emoji);
          ownReactionsRef.current.delete(key);
        } else {
          await chatFeaturesService.addReaction(id, messageId, emoji);
          ownReactionsRef.current.add(key);
        }
        if (activeIdRef.current !== id || accountRef.current !== owner) return;
        const updated = await chatFeaturesService.listMessages(id);
        if (activeIdRef.current !== id || accountRef.current !== owner) return;
        messageVersionRef.current += 1;
        setMessagesLoading(false);
        setMessages((current) =>
          updated
            .filter((message) => !clearStatesRef.current[id] || Date.parse(message.created_at) > Date.parse(clearStatesRef.current[id]!))
            .reduce<Message[]>((items, message) => mergeMessage(items, message), current),
        );
      });
    } finally {
      reactionInFlightRef.current = false;
    }
  }

  async function refreshReactionPeople(initial = false) {
    const view = reactionViewRef.current;
    if (!view || reactionRemovingRef.current) return;
    const request = ++reactionRequestRef.current;
    if (initial) setReactionLoading(true);
    try {
      const result = await api.get<ReactionPeople>(
        `/chat/group-controls/${encodeURIComponent(view.groupId)}/messages/${encodeURIComponent(view.messageId)}/reactions`,
      );
      if (reactionViewRef.current !== view || request !== reactionRequestRef.current || accountRef.current !== view.owner || activeIdRef.current !== view.groupId) return;
      setReactionPeople(result);
      setReactionError("");
      setMessages((current) => current.map((message) => message.id === view.messageId
        ? { ...message, reactions: result.counts } : message));
      setReactionTab((current) => current === "all" || result.counts[current] ? current : "all");
    } catch (cause) {
      if (reactionViewRef.current === view && request === reactionRequestRef.current) setReactionError(errorText(cause));
    } finally {
      if (reactionViewRef.current === view && request === reactionRequestRef.current) setReactionLoading(false);
    }
  }

  async function openReactionPeople(item: Message, emoji: string) {
    if (!activeId) return;
    reactionViewRef.current = { groupId: activeId, messageId: item.id, owner: accountRef.current };
    setReactionTarget(item);
    setReactionPeople(null);
    setReactionError("");
    setReactionTab(emoji);
    setMessageMenu(null);
    setReactionPicker(null);
    setPanel("reactions");
    await refreshReactionPeople(true);
  }

  async function removeOwnReaction(person: ReactionPerson) {
    const view = reactionViewRef.current;
    if (!view || person.user_id !== accountRef.current || !person.mine || reactionRemovingRef.current) return;
    reactionRemovingRef.current = true;
    reactionRequestRef.current += 1;
    setReactionRemoving(person.emoji);
    setReactionError("");
    let removed = false;
    try {
      await chatFeaturesService.removeReaction(view.groupId, view.messageId, person.emoji);
      removed = true;
      ownReactionsRef.current.delete(JSON.stringify([view.owner, view.groupId, view.messageId, person.emoji]));
    } catch (cause) {
      if (reactionViewRef.current === view) setReactionError(errorText(cause));
    } finally {
      reactionRemovingRef.current = false;
      setReactionRemoving(null);
    }
    if (removed && reactionViewRef.current === view && activeIdRef.current === view.groupId && accountRef.current === view.owner) {
      await refreshReactionPeople();
    }
  }

  useEffect(() => {
    if (panel !== "reactions") return;
    const timer = window.setInterval(() => { void refreshReactionPeople(); }, 4000);
    return () => window.clearInterval(timer);
  }, [panel, reactionTarget?.id]);

  async function chooseGroupPhoto(file: File) {
    const id = activeId;
    const owner = accountRef.current;
    const request = ++avatarPreparationRef.current;
    setAvatarPreparing(true);
    setError("");
    try {
      const prepared = await prepareGroupPhoto(file);
      if (request !== avatarPreparationRef.current || activeIdRef.current !== id || accountRef.current !== owner) return;
      setAvatarFile(prepared);
      avatarUploadRef.current = null;
      setAvatarMode("photo");
    } catch (cause) {
      if (request === avatarPreparationRef.current) setError(errorText(cause));
    } finally {
      if (request === avatarPreparationRef.current) setAvatarPreparing(false);
    }
  }

  async function openMessageInfo(item: Message) {
    const id = activeId;
    const owner = accountRef.current;
    if (!id || item.sender_user_id !== owner) return;
    const requestId = ++infoRequestRef.current;
    setMessageMenu(null);
    setReactionPicker(null);
    setInfoMessage(item);
    setInfoError("");
    setInfoLoading(true);
    setPanel("info");
    try {
      const result = await chat.listReadReceipts(id, item.id);
      if (requestId !== infoRequestRef.current || activeIdRef.current !== id || accountRef.current !== owner) return;
      setReceipts((current) => ({
        ...current,
        [item.id]: result.filter((receipt) => receipt.user_id !== owner),
      }));
    } catch (cause) {
      if (requestId === infoRequestRef.current && activeIdRef.current === id && accountRef.current === owner) {
        setInfoError(`Could not load message views: ${errorText(cause)}`);
      }
    } finally {
      if (requestId === infoRequestRef.current) setInfoLoading(false);
    }
  }

  async function pinMessage(item: Message) {
    const id = activeId;
    if (!id) return;

    await run(async () => {
      await extension("setMessagePinned")(id, item.id, !item.pinned);

      if (activeIdRef.current === id) {
        setMessages((current) =>
          current.map((message) =>
            message.id === item.id
              ? { ...message, pinned: !item.pinned }
              : message,
          ),
        );
      }

      setMessageMenu(null);
    });
  }

  async function uploadFile(file: File, id = activeId) {
    if (!id) return;

    await run(async () => {
      const uploaded = await extension("uploadMessageAttachment")(id, file);

      if (activeIdRef.current === id) {
        messageVersionRef.current += 1;
        scrollBottomRef.current = true;
        setMessagesLoading(false);
        setMessages((current) => mergeMessage(current, uploaded));
      }

      void loadGroups();
    });
  }

  async function downloadFile(file: Attachment) {
    await run(async () => {
      const result = await extension("downloadAttachment")(file.attachment_id);
      const url = new URL(result.download_url, window.location.origin);

      if (!["https:", "http:"].includes(url.protocol)) {
        throw new Error("The attachment service returned an invalid download URL.");
      }

      const link = document.createElement("a");
      link.href = url.href;
      link.download = file.filename;
      link.rel = "noopener noreferrer";
      link.target = "_blank";
      document.body.appendChild(link);
      link.click();
      link.remove();
    });
  }
  function cancelGroupRecording(): void {
    const recorder = recorderRef.current;

    recorderRef.current = null;

    try {
      if (recorder) {
        recorder.onstop = null;
        recorder.ondataavailable = null;
        recorder.onerror = null;

        if (recorder.state !== "inactive") {
          recorder.stop();
        }
      }
    } finally {
      mediaRef.current
        ?.getTracks()
        .forEach(track => track.stop());

      mediaRef.current = null;

      setRecording(false);
    }
  }
  async function toggleRecording() {
    if (recording) {
      recorderRef.current?.stop();
      return;
    }

    const id = activeId;
    if (!id || busy) return;

    try {
      extension("uploadMessageAttachment");

      if (
        !navigator.mediaDevices?.getUserMedia ||
        typeof MediaRecorder === "undefined"
      ) {
        throw new Error(
          "Voice recording requires a supported browser on HTTPS or localhost.",
        );
      }

      setError("");

      const stream = await navigator.mediaDevices.getUserMedia({
        audio: true,
      });

      if (activeIdRef.current !== id) {
        stream.getTracks().forEach((track) => track.stop());
        return;
      }

      mediaRef.current = stream;

      const preferredType = [
        "audio/webm;codecs=opus",
        "audio/webm",
        "audio/mp4",
      ].find((type) => MediaRecorder.isTypeSupported(type));

      const recorder = new MediaRecorder(
        stream,
        preferredType ? { mimeType: preferredType } : undefined,
      );

      const chunks: Blob[] = [];
      recorderRef.current = recorder;

      recorder.ondataavailable = (event) => {
        if (event.data.size) chunks.push(event.data);
      };

      recorder.onstop = () => {
        stream.getTracks().forEach((track) => track.stop());
        mediaRef.current = null;
        recorderRef.current = null;
        setRecording(false);

        const contentType = recorder.mimeType || "audio/webm";
        const blob = new Blob(chunks, { type: contentType });

        if (!blob.size) {
          setError("The recording was empty. Please try again.");
          return;
        }

        const suffix = contentType.includes("mp4") ? "m4a" : "webm";

        void uploadFile(
          new File(
            [blob],
            `voice-${Date.now()}.${suffix}`,
            { type: contentType },
          ),
          id,
        );
      };

      recorder.onerror = () => {
        recorder.onstop = null;
        stream.getTracks().forEach((track) => track.stop());
        recorderRef.current = null;
        mediaRef.current = null;
        setRecording(false);
        setError("Voice recording failed. Please try again.");
      };

      recorder.start();
      setRecording(true);
    } catch (cause) {
      mediaRef.current?.getTracks().forEach((track) => track.stop());
      mediaRef.current = null;
      setError(errorText(cause));
    }
  }

  async function openPanel(next: Panel) {
    setMenuOpen(false);
    if (next === "manage") {
      setAvatarFile(null);
      avatarUploadRef.current = null;
      avatarPreparationRef.current += 1;
      setAvatarPreparing(false);
      setAvatarMode(activeDetails?.avatar_mode || "auto");
      setAvatarAttachmentId(activeDetails?.avatar_attachment_id || null);
    }

    if (next === "create") {
      setName("");
      setDescription("");
      setSelectedFriends([]);
      setPanel(next);
      return;
    }

    if (!activeId) return;
    const id = activeId;

    if (next === "files") {
      await run(async () => {
        const files = await extension("listSharedFiles")(id);
        if (activeIdRef.current !== id) return;
        setSharedFiles(files);
        setPanel(next);
      });
      return;
    }

    if (
      ["members", "admins", "manage", "add", "leave"].includes(next || "") &&
      !activeDetails
    ) {
      await run(async () => {
        const value = await extension("getGroupDetails")(id);
        if (activeIdRef.current !== id) return;
        setDetails((current) => ({ ...current, [id]: value }));
        setName(activeGroup?.name || "");
        setDescription(value.description || "");
        setAvatarMode(value.avatar_mode || "auto");
        setAvatarAttachmentId(value.avatar_attachment_id || null);
        setSelectedFriends([]);
        setPanel(next);
      });
      return;
    }

    setName(activeGroup?.name || "");
    setDescription(activeDetails?.description || "");
    setSelectedFriends([]);
    setPanel(next);
  }

  async function saveGroup(event: FormEvent) {
    event.preventDefault();
    const id = activeId;
    if (!id || !name.trim() || !canManage || avatarPreparing) return;
    const owner = accountRef.current;
    const selectedFile = avatarFile;
    const selectedMode = avatarMode;

    await run(async () => {
      let photoId = avatarAttachmentId;
      if (selectedFile && selectedMode !== "members") {
        let upload = avatarUploadRef.current;
        if (!upload || upload.groupId !== id || upload.file !== selectedFile) {
          const message = await extension("uploadMessageAttachment")(id, selectedFile);
          upload = { groupId: id, file: selectedFile, message };
          avatarUploadRef.current = upload;
        }
        photoId = upload.message.attachments?.[0]?.attachment_id || null;
        if (!photoId) throw new Error("The photo uploaded but no attachment ID was returned.");
        if (activeIdRef.current === id && accountRef.current === owner) {
          setMessages((current) => mergeMessage(current, upload!.message));
          setAvatarAttachmentId(photoId);
        }
      }
      if (activeIdRef.current !== id || accountRef.current !== owner) return;
      await extension("updateGroup")(id, {
        name: name.trim(),
        description: description.trim(),
        avatar_mode: selectedMode,
        avatar_attachment_id: photoId,
      });

      if (activeIdRef.current !== id || accountRef.current !== owner) return;
      setGroups((current) =>
        current.map((group) =>
          group.id === id ? { ...group, name: name.trim() } : group,
        ),
      );

      await loadDetails(id);
      if (activeIdRef.current !== id || accountRef.current !== owner) return;
      setAvatarFile(null);
      avatarUploadRef.current = null;
      setPanel(null);

      window.dispatchEvent(
        new CustomEvent("workforce:group-avatar-updated", {
          detail: {
            conversationId: id,
          },
        }),
      );

      setNotice("Group updated.");
    });
  }

  async function addMembers(event: FormEvent) {
    event.preventDefault();
    const id = activeId;
    if (!id || !selectedFriends.length) return;

    await run(async () => {
      const add = extension("addMember");

      /*
       * Update the pending selection after each success so retrying a
       * partially failed operation does not repeat successful additions.
       */
      for (const memberId of selectedFriends) {
        await add(id, memberId);
        setSelectedFriends((current) =>
          current.filter((item) => item !== memberId),
        );
      }

      await loadDetails(id);
      setPanel(null);
      setNotice("Members added.");
    });
  }

  async function changeRole(member: Member) {
    const id = activeId;
    if (!id || member.role === "owner") return;

    await run(async () => {
      await extension("updateMemberRole")(
        id,
        member.user_id,
        member.role === "admin" ? "member" : "admin",
      );

      await loadDetails(id);
    });
  }

  async function removeMember(member: Member) {
    const id = activeId;
    if (!id || member.role === "owner") return;

    await run(async () => {
      await extension("removeMember")(id, member.user_id);
      await loadDetails(id);
    });
  }

  async function leaveGroup() {
    const id = activeId;
    if (!id) return;

    await run(async () => {
      await extension("leaveGroup")(id);
      setGroups((current) => current.filter((group) => group.id !== id));
      setPanel(null);
      setActiveId(null);
      setMobileChat(false);
      router.replace(embedded ? window.location.pathname : "/groups", { scroll: false });
      void loadGroups();
    });
  }

  function beginReply(item: Message) {
    setReply(item);
    setEditing(null);
    setMessageMenu(null);
    composerRef.current?.focus();
  }

  function beginEdit(item: Message) {
    setEditing(item);
    setReply(null);
    changeDraft(item.content);
    setMessageMenu(null);
    composerRef.current?.focus();
  }

  const panelTitle: Record<Exclude<Panel, null>, string> = {
    create: "Create group",
    members: "Group members",
    admins: "Group admins",
    files: "Shared files",
    pinned: "Pinned messages",
    manage: "Manage group",
    add: "Add members",
    leave: "Leave group",
    info: "Message info",
    reactions: "Reactions",
    bulk: bulkRequest ? BULK_LABELS[bulkRequest.action] : "Group actions",
  };

  const panelMembers =
    panel === "admins"
      ? members.filter((member) => member.role !== "member")
      : members;

  const availableFriends = friends.filter(
    (friend) =>
      panel !== "add" ||
      !members.some((member) => member.user_id === friend.person.id),
  );

  const latestMessage = messages.filter((item) => !item.deleted_at).at(-1);

    return (
    <main
      className={[
        "gp",
        embedded ? "gp-embedded gp-mobile-chat" : mobileChat ? "gp-mobile-chat" : "",
        detailsOpen ? "" : "gp-details-hidden",
      ].join(" ")}
    >
      <header className="gp-page-header">
        <div>
          <h1>Groups</h1>
          <p>Collaborate, connect and keep your communities organized</p>
        </div>

        <button
          type="button"
          className="gp-primary"
          onClick={() => void openPanel("create")}
          disabled={!user?.is_email_verified || busy}
        >
          <Plus size={23} />
          Create group
        </button>
      </header>

      {error && (
        <div className="gp-feedback gp-error" role="alert">
          <span>{error}</span>
          <IconButton label="Dismiss error" onClick={() => setError("")}>
            <X size={18} />
          </IconButton>
        </div>
      )}

      {notice && (
        <div className="gp-feedback" role="status">
          <span>{notice}</span>
          <IconButton label="Dismiss notice" onClick={() => setNotice("")}>
            <X size={18} />
          </IconButton>
        </div>
      )}

      {!accountLoading && !user ? (
        <div className="gp-account">
          Please <Link href="/login">sign in</Link> to view your groups.
        </div>
      ) : !accountLoading && user && !user.is_email_verified ? (
        <div className="gp-account">
          Verify your email before using group conversations.
        </div>
      ) : (
        <section className="gp-grid">
          <aside className="gp-card gp-inbox" ref={inboxRef}>
            <div className="gp-panel-heading">
              <h2>Your groups</h2>

              <button
                type="button"
                className="gp-icon"
                aria-label="Group inbox actions"
                aria-expanded={inboxMenuOpen}
                disabled={loading || busy}
                onClick={(event) => {
                  setInboxMenuAnchor(event.currentTarget);
                  setSelectionMode(true);
                  setInboxMenuOpen((current) => !current);
                }}
              >
                <MoreHorizontal size={21} />
              </button>
              {inboxMenuOpen && inboxMenuAnchor && (
                <FloatingMenu inbox anchor={inboxMenuAnchor} label="Group inbox actions" onClose={() => setInboxMenuOpen(false)}>
                  <button type="button" onClick={() => {
                    setSelectionMode(true);
                    setSelectedGroupIds((current) => [...new Set([...current, ...visibleGroups.map((group) => group.id)])]);
                  }}><Check size={15} /> Select all shown</button>
                  <button type="button" disabled={!selectedGroupIds.length} onClick={() => requestBulkAction("mute")}><BellOff size={15} /> Mute groups</button>
                  <button type="button" disabled={!selectedGroupIds.length} onClick={() => requestBulkAction("unmute")}><Bell size={15} /> Unmute groups</button>
                  <button type="button" disabled={!selectedGroupIds.length} onClick={() => requestBulkAction("clear")}><MessageCircle size={15} /> Clear my chats</button>
                  <button type="button" disabled={!selectedGroupIds.length} onClick={() => requestBulkAction("leave")}><LogOut size={15} /> Leave groups</button>
                  <button type="button" className="gp-danger" disabled={!selectedGroupIds.length} onClick={() => requestBulkAction("delete")}><Trash2 size={15} /> Delete groups</button>
                  <button type="button" onClick={() => {
                    void loadGroups();
                    if (activeId) void loadMessages(activeId);
                  }}>Refresh groups</button>
                  <button type="button" onClick={() => {
                    setSelectionMode(false);
                    setSelectedGroupIds([]);
                  }}><X size={15} /> Finish selection</button>
                </FloatingMenu>
              )}
            </div>

            <label className="gp-search">
              <Search size={19} />
              <input
                aria-label="Search groups"
                value={search}
                placeholder="Search groups"
                onChange={(event) => setSearch(event.target.value)}
              />
              {search && (
                <button
                  type="button"
                  aria-label="Clear group search"
                  onClick={() => setSearch("")}
                >
                  <X size={15} />
                </button>
              )}
            </label>

            <div className="gp-tabs" aria-label="Group filters">
              {(
                [
                  ["all", "All"],
                  ["unread", "Unread"],
                  ["recent", "Recent"],
                  ["archived", "Archived"],
                ] as const
              ).map(([value, label]) => (
                <button
                  type="button"
                  key={value}
                  className={tab === value ? "is-active" : ""}
                  aria-pressed={tab === value}
                  onClick={() => {
                    setTab(value);

                    if (
                      (value === "unread" || value === "archived") &&
                      !service.listConversationFeatures
                    ) {
                      setNotice(
                        "Connect listConversationFeatures() to load server unread and archive status.",
                      );
                    }
                  }}
                >
                  {label}
                </button>
              ))}
            </div>

            {selectionMode && (
              <div className="gp-selection-bar">
                <div>
                  <strong>{selectedGroupIds.length} selected</strong>
                  <button type="button" disabled={busy} onClick={() => {
                    setSelectionMode(false);
                    setSelectedGroupIds([]);
                    setInboxMenuOpen(false);
                  }}>Cancel</button>
                </div>
                <p>Select groups below, then choose an action.</p>
                <div className="gp-selection-actions">
                  <button type="button" disabled={busy || !selectedGroupIds.length} onClick={() => requestBulkAction("mute")}><BellOff size={14} /> Mute</button>
                  <button type="button" disabled={busy || !selectedGroupIds.length} onClick={() => requestBulkAction("clear")}><MessageCircle size={14} /> Clear</button>
                  <button type="button" disabled={busy || !selectedGroupIds.length} onClick={() => requestBulkAction("leave")}><LogOut size={14} /> Leave</button>
                  <button type="button" disabled={busy || !selectedGroupIds.length} onClick={() => requestBulkAction("delete")}><Trash2 size={14} /> Delete</button>
                </div>
              </div>
            )}

            <div className="gp-group-list">
              {(accountLoading || loading) && (
                <div className="gp-empty">Loading your groups</div>
              )}

              {!accountLoading &&
                !loading &&
                visibleGroups.map((group) => {
                  const summary = summaries[group.id];
                  const metadata = details[group.id];
                  const selected = group.id === activeId;
                  const unread = summary?.unread_count || 0;

                  return (
                    <button
                      type="button"
                      key={group.id}
                      className={`gp-group-row ${selected ? "is-selected" : ""} ${selectionMode && selectedGroupIds.includes(group.id) ? "is-checked" : ""}`}
                      role={selectionMode ? "checkbox" : undefined}
                      aria-checked={selectionMode ? selectedGroupIds.includes(group.id) : undefined}
                      aria-current={!selectionMode && selected ? "true" : undefined}
                      disabled={busy && selectionMode}
                      onClick={() => selectionMode ? toggleGroupSelection(group.id) : openConversation(group.id)}
                    >
                      {selectionMode && (
                        <span className={`gp-select-check ${selectedGroupIds.includes(group.id) ? "is-checked" : ""}`} aria-hidden="true">
                          {selectedGroupIds.includes(group.id) && <Check size={13} />}
                        </span>
                      )}
                      <GroupAvatar name={group.name} details={metadata} />

                      <span className="gp-group-copy">
                        <strong>{group.name || "Untitled group"}</strong>
                        <span>
                          {selected && latestMessage
                            ? `${displayName(latestMessage.sender_user_id)}: ${latestMessage.content}`
                            : metadata
                              ? `${metadata.members.length} members`
                              : "Group conversation"}
                        </span>
                      </span>

                      <span className="gp-row-trailing">
                        <time>{time(group.updated_at)}</time>

                        <span className="gp-row-indicators">
                          {summary?.muted && <BellOff size={17} />}
                          {summary?.pinned && <Pin size={17} />}
                          {unread > 0 && (
                            <b className="gp-unread">
                              {unread > 99 ? "99+" : unread}
                            </b>
                          )}
                        </span>
                      </span>
                    </button>
                  );
                })}

              {!accountLoading && !loading && !visibleGroups.length && (
                <div className="gp-empty">
                  <Users size={29} />
                  <strong>No groups found</strong>
                  <span>
                    {search
                      ? "Try another group name."
                      : tab === "archived"
                        ? "No archived groups are available."
                        : tab === "unread"
                          ? "No unread groups are available."
                          : "Create a group to start a conversation."}
                  </span>
                </div>
              )}
            </div>

            <button
              type="button"
              className="gp-archive-link"
              onClick={() => {
                setTab("archived");

                if (!service.listConversationFeatures) {
                  setNotice(
                    "Connect listConversationFeatures() to load archived groups.",
                  );
                }
              }}
            >
              <Archive size={19} />
              Archived groups
              <ChevronRight size={17} />
            </button>
          </aside>

          <section className="gp-card gp-conversation">
            {!activeGroup ? (
              <div className="gp-empty gp-conversation-empty">
                <MessageCircle size={34} />
                <strong>Select a group</strong>
                <span>Your conversation will appear here.</span>
              </div>
            ) : (
              <>
                <header className="gp-conversation-header">
                  <button
                    type="button"
                    className="gp-icon gp-back"
                    aria-label="Back to groups"
                    onClick={() => setMobileChat(false)}
                  >
                    <ArrowLeft size={20} />
                  </button>

                  <GroupAvatar name={activeGroup.name} details={activeDetails} />

                  <button
                    type="button"
                    className="gp-conversation-title"
                    onClick={() => setDetailsOpen(true)}
                  >
                    <strong>{activeGroup.name || "Untitled group"}</strong>
                    <span>
                      {activeDetails
                        ? `${members.length} members${
                            members.some((member) => member.online !== undefined)
                              ? ` Ã‚Â· ${members.filter((member) => member.online).length} online`
                              : ""
                          }`
                        : "Group conversation"}
                    </span>
                  </button>

                  <div className="gp-header-actions">
                    <IconButton
                      label="Search messages"
                      onClick={() => setShowSearch((value) => !value)}
                    >
                      <Search size={22} />
                    </IconButton>

                    <IconButton
                      label="Voice call"
                      disabled={busy}
                      onClick={() => void callGroup("voice")}
                    >
                      <Phone size={22} />
                    </IconButton>

                    <IconButton
                      label="Video call"
                      disabled={busy}
                      onClick={() => void callGroup("video")}
                    >
                      <Video size={23} />
                    </IconButton>

                    <IconButton
                      label="Conversation options"
                      onClick={() => setMenuOpen((value) => !value)}
                    >
                      <MoreHorizontal size={22} />
                    </IconButton>

                    {menuOpen && (
                      <div className="gp-menu gp-conversation-menu">
                        <button
                          type="button"
                          onClick={() => setDetailsOpen(true)}
                        >
                          <Users size={17} />
                          Group details
                        </button>

                        <button
                          type="button"
                          disabled={busy}
                          onClick={() => void callGroup("screen")}
                        >
                          <Video size={17} />
                          Share screen
                        </button>

                        <button
                          type="button"
                          disabled={busy}
                          onClick={() =>
                            void updatePreference(
                              "pinned",
                              !activeSummary?.pinned,
                            )
                          }
                        >
                          <Pin size={17} />
                          {activeSummary?.pinned ? "Unpin group" : "Pin group"}
                        </button>

                        <button
                          type="button"
                          disabled={busy}
                          onClick={() =>
                            void updatePreference(
                              "muted",
                              !activeSummary?.muted,
                            )
                          }
                        >
                          <BellOff size={17} />
                          {activeSummary?.muted
                            ? "Enable notifications"
                            : "Mute notifications"}
                        </button>

                        <button
                          type="button"
                          disabled={busy}
                          onClick={() =>
                            void updatePreference(
                              "archived",
                              !activeSummary?.archived,
                            )
                          }
                        >
                          <Archive size={17} />
                          {activeSummary?.archived
                            ? "Restore group"
                            : "Archive group"}
                        </button>

                        <button
                          type="button"
                          onClick={() => void openPanel("manage")}
                        >
                          <Settings size={17} />
                          Manage group
                        </button>
                      </div>
                    )}
                  </div>
                </header>

                {showSearch && (
                  <div className="gp-message-search">
                    <Search size={18} />
                    <input
                      ref={searchRef}
                      aria-label="Search loaded messages"
                      placeholder="Search loaded messages..."
                      value={messageSearch}
                      onChange={(event) =>
                        setMessageSearch(event.target.value)
                      }
                    />
                    <IconButton
                      label="Close message search"
                      onClick={() => {
                        setShowSearch(false);
                        setMessageSearch("");
                      }}
                    >
                      <X size={17} />
                    </IconButton>
                  </div>
                )}

                <div
                  className="gp-messages"
                  ref={messagesRef}
                  aria-label="Group messages"
                  onScroll={(event) => {
                    const element = event.currentTarget;

                    scrollBottomRef.current =
                      element.scrollHeight -
                        element.scrollTop -
                        element.clientHeight <
                      90;
                  }}
                >
                  {messagesLoading && (
                    <div className="gp-empty">Loading messages</div>
                  )}

                  {!messagesLoading &&
                    activeId &&
                    clearStates[activeId] && (
                      <div className="gp-clear-notice" role="status">
                        <span>
                          {directory.get(user?.id || "")?.username ||
                            directory.get(user?.id || "")?.name ||
                            "You"}{" "}
                          cleared their chat history.
                        </span>
                        <small>Only visible to you.</small>
                      </div>
                    )}

                  {visibleMessages.map((item, index) => {
                    const own = item.sender_user_id === user?.id;
                    const previous = visibleMessages[index - 1];
                    const showDay =
                      !previous ||
                      day(previous.created_at) !== day(item.created_at);
                    const replyMessage = item.reply_to_message_id
                      ? messages.find(
                          (message) =>
                            message.id === item.reply_to_message_id,
                        )
                      : undefined;
                    const reactions = Object.entries(item.reactions || {}).filter(([, count]) => count > 0);

                    return (
                      <div className="gp-message-entry" key={item.id}>
                        {showDay && (
                          <div className="gp-day">
                            <span>{day(item.created_at)}</span>
                          </div>
                        )}

                        <article
                          id={`gp-message-${item.id}`}
                          tabIndex={-1}
                          className={[
                            "gp-message",
                            own ? "is-own" : "",
                            messageMenu === item.id || reactionPicker === item.id
                              ? "is-menu-open"
                              : "",
                          ].join(" ")}
                        >
                          <div className="gp-message-body">
                            <div
                              className={[
                                "gp-bubble",
                                isSingleEmojiMessage(item.content) &&
                                !item.deleted_at &&
                                !item.reply_to_message_id &&
                                !item.attachments?.length
                                  ? "gp-bubble--singleEmoji"
                                  : "",
                              ].join(" ")}
                            >

                              <div
                                className="gp-bubble-author"
                                title={
                                  directory.get(item.sender_user_id ?? "")?.username ||
                                  displayName(item.sender_user_id)
                                }
                              >
                                {directory.get(item.sender_user_id ?? "")?.username
                                  ? `@${directory.get(item.sender_user_id ?? "")?.username}`
                                  : own && user?.username
                                    ? `@${user.username}`
                                    : displayName(item.sender_user_id)}
                              </div>

                              {item.reply_to_message_id && (
                                <button
                                  type="button"
                                  className="gp-quoted"
                                  onClick={() => {
                                    const found = jumpToMessage(
                                      `gp-message-${item.reply_to_message_id}`,
                                    );

                                    if (!found) {
                                      setNotice(
                                        "The original message is not loaded in this view.",
                                      );
                                    }
                                  }}
                                >
                                  <strong>
                                    {replyMessage
                                      ? displayName(replyMessage.sender_user_id)
                                      : "Earlier message"}
                                  </strong>

                                  <span>
                                    {replyMessage?.attachments?.some(
                                      (file) => file.kind === "AUDIO",
                                    )
                                      ? "Voice message"
                                      : replyMessage?.content ||
                                        "View original message"}
                                  </span>
                                </button>
                              )}

                              {!(
                                item.attachments?.length &&
                                item.attachments.every(
                                  file => file.kind === "AUDIO",
                                ) &&
                                isAutomaticVoiceText(
                                  item.content,
                                  item.attachments.map(
                                    file => file.filename,
                                  ),
                                )
                              ) && (
                                <div className="gp-message-text">
                                  {item.content}
                                </div>
                              )}
                              {item.attachments?.map((file) =>
                                file.kind === "AUDIO" ? (
                                  <AudioAttachmentPlayer
                                    key={file.attachment_id}
                                    attachmentId={file.attachment_id}
                                    filename={file.filename}
                                  />
                                ) : (
                                <button
                                  type="button"
                                  className="gp-file gp-message-file"
                                  key={file.attachment_id}
                                  disabled={busy}
                                  onClick={() =>
                                    void downloadFile(file)
                                  }
                                >
                                  <span className="gp-file-icon">
                                    {file.kind === "IMAGE" ? (
                                      <ImageIcon size={21} />
                                    ) : (
                                      <FileText size={21} />
                                    )}
                                  </span>

                                  <span className="gp-file-copy">
                                    <strong>{file.filename}</strong>
                                    <small>
                                      {fileSize(file.size_bytes)}
                                      {" Â· "}
                                      {file.kind.toLowerCase()}
                                    </small>
                                  </span>

                                  <Download
                                    size={18}
                                    className="gp-message-file-download"
                                  />
                                </button>
                              ))}

                              <div className="gp-message-time">
                                {item.pinned && <Pin size={12} />}
                                {item.edited_at && <span>edited</span>}
                                <time>{time(item.created_at)}</time>

                                {own &&
                                  ((receipts[item.id]?.length || 0) > 0 ? (
                                    <CheckCheck
                                      size={18}
                                      className="gp-read"
                                      aria-label="Read"
                                    />
                                  ) : item.delivered_at ? (
                                    <CheckCheck size={18} aria-label="Delivered" />
                                  ) : (
                                    <Check size={17} aria-label="Sent" />
                                  ))}
                              </div>

                              <button
                                type="button"
                                className="gp-message-more"
                                aria-label={`Options for message at ${time(item.created_at)}`}
                                aria-expanded={
                                  messageMenu === item.id
                                }
                                onClick={(event) => {
                                  setMessageMenuAnchor(event.currentTarget);
                                  setReactionPicker(null);

                                  setMessageMenu((current) =>
                                    current === item.id
                                      ? null
                                      : item.id,
                                  );
                                }}
                              >
                                <MoreHorizontal size={17} />
                              </button>
                              {messageMenu === item.id && messageMenuAnchor && (
                                <FloatingMenu
                                  anchor={messageMenuAnchor}
                                  label="Message options"
                                  onClose={() => setMessageMenu(null)}
                                >
                                  <button
                                    type="button"
                                    onClick={() => beginReply(item)}
                                  >
                                    <Reply size={15} /> Reply
                                  </button>
                                  {(item.attachments ?? []).map(
                                    (file, fileIndex, attachments) => (
                                      <button
                                        key={file.attachment_id}
                                        type="button"
                                        disabled={busy}
                                        onClick={() => {
                                          setMessageMenu(null);

                                          void downloadFile(file);
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
                                    disabled={busy}
                                    onClick={() => {
                                      setMessageMenu(null);
                                      setReactionPicker(item.id);
                                    }}
                                  >
                                    <Smile size={16} />
                                    React
                                  </button>
                                  <button
                                    type="button"
                                    disabled={busy}
                                    onClick={() => void pinMessage(item)}
                                  >
                                    <Pin size={15} /> {item.pinned ? "Unpin" : "Pin"}
                                  </button>
                                  <button
                                    type="button"
                                    onClick={() => void run(async () => {
                                      if (!navigator.clipboard) throw new Error("Clipboard access is unavailable.");
                                      await navigator.clipboard.writeText(item.content);
                                    })}
                                  >
                                    <Copy size={16} /> Copy
                                  </button>
                                  <button
                                    type="button"
                                    className="gp-danger"
                                    disabled={busy}
                                    onClick={() =>
                                      void deleteMessageForMe(item.id)
                                    }
                                  >
                                    <Trash2 size={15} />
                                    Delete for me
                                  </button>
                                  {own && (
                                    <>
                                      <button
                                        type="button"
                                        onClick={() => void openMessageInfo(item)}
                                      >
                                        <Info size={16} /> Message info
                                      </button>
                                      <button
                                        type="button"
                                        onClick={() => beginEdit(item)}
                                      >
                                        <Edit3 size={15} /> Edit
                                      </button>
                                      <button
                                        type="button"
                                        className="gp-danger"
                                        disabled={busy}
                                        onClick={() =>
                                          void deleteMessage(item.id)
                                        }
                                      >
                                        <Trash2 size={15} /> Delete for everyone
                                      </button>
                                    </>
                                  )}
                                </FloatingMenu>
                              )}
                            </div>

                            <div className="gp-message-footer">
                              <FullEmojiPicker
                                quickReactions
                                className="gp-message-reaction"
                                label="Choose a reaction"
                                size={16}
                                disabled={busy}
                                open={reactionPicker === item.id}
                                onOpenChange={(value) => {
                                  if (value) {
                                    setMessageMenu(null);
                                  }

                                  setReactionPicker(
                                    value ? item.id : null,
                                  );
                                }}
                                onSelect={(emoji) => {
                                  void reactToMessage(
                                    item.id,
                                    emoji,
                                  );
                                }}
                              />
                              {reactions.length > 0 && (
                                <div className="gp-reactions">
                                  {reactions.map(([emoji, count]) => (
                                    <button
                                      type="button"
                                      key={emoji}
                                      disabled={busy}
                                      title="See who reacted"
                                      aria-label={`See who reacted with ${emoji}`}
                                      onClick={() =>
                                        void openReactionPeople(item, emoji)
                                      }
                                    >
                                      {emoji} {count}
                                    </button>
                                  ))}
                                </div>
                              )}
                            </div>
                          </div>

                        </article>
                      </div>
                    );
                  })}

                  {!messagesLoading &&
                    !visibleMessages.length &&
                    (!activeId || !clearStates[activeId] || messageSearch) && (
                    <div className="gp-empty">
                      {messageSearch
                        ? "No loaded messages match your search."
                        : "No messages yet. Start the conversation."}
                    </div>
                  )}
                </div>

                <div className="gp-composer-section">
                  <div className="gp-typing" aria-live="polite">
                    {typingIds.length > 0 && (
                      <>
                        <span className="gp-typing-dots">
                          <i />
                          <i />
                          <i />
                        </span>
                        <span>
                          {typingIds.length === 1
                            ? `${displayName(typingIds[0])} is typing...`
                            : `${typingIds.length} people are typing...`}
                        </span>
                      </>
                    )}
                  </div>

                  {(reply || editing) && (
                    <div className="gp-reply-banner">
                      <div>
                        <strong>
                          {editing
                            ? "Editing message"
                            : `Replying to ${displayName(reply?.sender_user_id)}`}
                        </strong>
                        <span>{editing?.content || reply?.content}</span>
                      </div>
                      <IconButton
                        label="Cancel reply or edit"
                        onClick={() => {
                          setReply(null);
                          if (editing) changeDraft("");
                          setEditing(null);
                        }}
                      >
                        <X size={17} />
                      </IconButton>
                    </div>
                  )}

                  {recording && (
                    <VoiceRecordingIndicator
                      stream={mediaRef.current}
                      disabled={busy}
                      onCancel={cancelGroupRecording}
                      onPause={(paused: boolean) => {
                        const recorder = recorderRef.current;

                        if (!recorder) {
                          throw new Error(
                            "No active recording.",
                          );
                        }

                        if (
                          paused &&
                          recorder.state === "recording"
                        ) {
                          recorder.pause();
                        } else if (
                          !paused &&
                          recorder.state === "paused"
                        ) {
                          recorder.resume();
                        }
                      }}
                      onSend={() => void toggleRecording()}
                    />
                  )}
                  <form
                    style={recording ? { display: "none" } : undefined}
                    className="gp-composer"
                    onSubmit={(event) => void sendMessage(event)}
                  >
                    <ChatAttachmentPicker
                      files={[]}
                      disabled={busy || recording}
                      onChange={selected => {
                        void (async () => {
                          for (const file of selected) {
                            await uploadFile(file);
                          }
                        })();
                      }}
                    />

                    <div className="gp-emoji-wrap">
                      <FullEmojiPicker
                        className="gp-icon"
                        label="Insert emoji"
                        size={23}
                        disabled={busy}
                        open={emojiOpen}
                        onOpenChange={setEmojiOpen}
                        onSelect={(emoji) => {
                          changeDraft(draft + emoji);

                          requestAnimationFrame(() => {
                            composerRef.current?.focus();
                          });
                        }}
                      />
                    </div>
                    <textarea
                      ref={composerRef}
                      aria-label="Message"
                      rows={1}
                      value={draft}
                      maxLength={10000}
                      disabled={recording}
                      placeholder="Write a message..."
                      onChange={(event) => changeDraft(event.target.value)}
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

                    <span className="gp-composer-divider" />

                    <IconButton
                      label={recording ? "Stop voice recording" : "Record voice message"}
                      disabled={busy}
                      onClick={() => void toggleRecording()}
                    >
                      {recording ? <Square size={21} /> : <Mic size={22} />}
                    </IconButton>

                    <button
                      type="submit"
                      className="gp-send"
                      aria-label={editing ? "Save edited message" : "Send message"}
                      disabled={!draft.trim() || busy || recording}
                    >
                      <Send size={23} />
                    </button>
                  </form>
                </div>
              </>
            )}
          </section>

          {detailsOpen && (
            <aside className="gp-card gp-details">
              <div className="gp-details-heading">
                <h2>Group details</h2>
                <IconButton
                  label="Close group details"
                  onClick={() => setDetailsOpen(false)}
                >
                  <X size={20} />
                </IconButton>
              </div>

              {activeGroup ? (
                <>
                  <div className="gp-details-person">
                    <GroupAvatar name={activeGroup.name} details={activeDetails} />
                    <div>
                      <h3>{activeGroup.name || "Untitled group"}</h3>
                      <p>
                        {activeDetails
                          ? `${members.length} members`
                          : "Group conversation"}
                      </p>
                      <p>
                        Created by{" "}
                        {activeGroup.created_by_user_id === user?.id
                          ? "you"
                          : displayName(activeGroup.created_by_user_id)}
                      </p>
                    </div>
                  </div>

                  {activeDetails?.description && (
                    <p className="gp-description">
                      {activeDetails.description}
                    </p>
                  )}

                  <div className="gp-detail-actions">
                    <button
                      type="button"
                      disabled={busy}
                      onClick={() => void callGroup("voice")}
                    >
                      <Phone size={25} />
                      Call
                    </button>
                    <button
                      type="button"
                      disabled={busy}
                      onClick={() => void callGroup("video")}
                    >
                      <Video size={25} />
                      Video
                    </button>
                    <button
                      type="button"
                      onClick={() => void openPanel("manage")}
                    >
                      <MoreHorizontal size={25} />
                      More
                    </button>
                  </div>

                  <div className="gp-details-links">
                    <button
                      type="button"
                      className="gp-detail-link"
                      onClick={() => setShowSearch(true)}
                    >
                      <Search size={22} />
                      Search messages
                      <ChevronRight size={20} />
                    </button>

                    <button
                      type="button"
                      className="gp-detail-link"
                      onClick={() => {
                        if (!service.listFeatureMessages) {
                          setNotice(
                            "Connect listFeatureMessages() to load pinned message status.",
                          );
                        }
                        setPanel("pinned");
                      }}
                    >
                      <Pin size={22} />
                      Pinned messages
                      <ChevronRight size={20} />
                    </button>

                    <button
                      type="button"
                      className="gp-detail-link"
                      onClick={() => void openPanel("files")}
                    >
                      <ImageIcon size={22} />
                      Shared media
                      <ChevronRight size={20} />
                    </button>
                  </div>

                  <div className="gp-switches">
                    <div className="gp-switch-row">
                      <Bell size={22} />
                      <span>Notifications</span>
                      <button
                        type="button"
                        role="switch"
                        aria-label="Group notifications"
                        aria-checked={!activeSummary?.muted}
                        className={`gp-switch ${
                          !activeSummary?.muted ? "is-on" : ""
                        }`}
                        disabled={busy}
                        onClick={() =>
                          void updatePreference(
                            "muted",
                            !activeSummary?.muted,
                          )
                        }
                      >
                        <span />
                      </button>
                    </div>

                    <div className="gp-switch-row">
                      <Pin size={22} />
                      <span>Pin conversation</span>
                      <button
                        type="button"
                        role="switch"
                        aria-label="Pin group"
                        aria-checked={Boolean(activeSummary?.pinned)}
                        className={`gp-switch ${
                          activeSummary?.pinned ? "is-on" : ""
                        }`}
                        disabled={busy}
                        onClick={() =>
                          void updatePreference(
                            "pinned",
                            !activeSummary?.pinned,
                          )
                        }
                      >
                        <span />
                      </button>
                    </div>
                  </div>

                  <div className="gp-group-controls">
                    <div className="gp-controls-heading">
                      <h3>Group controls</h3>
                      <button
                        type="button"
                        onClick={() => void openPanel("manage")}
                      >
                        Manage
                      </button>
                    </div>

                    <button
                      type="button"
                      className="gp-control"
                      onClick={() => void openPanel("members")}
                    >
                      <Users size={19} />
                      Members
                      <span>{activeDetails ? members.length : "Ã¢â‚¬â€"}</span>
                      <ChevronRight size={17} />
                    </button>

                    <button
                      type="button"
                      className="gp-control"
                      onClick={() => void openPanel("admins")}
                    >
                      <Shield size={19} />
                      Admins
                      <span>
                        {activeDetails
                          ? members.filter((member) => member.role === "admin").length
                          : "Ã¢â‚¬â€"}
                      </span>
                      <ChevronRight size={17} />
                    </button>

                    <button
                      type="button"
                      className="gp-control"
                      onClick={() => void openPanel("add")}
                    >
                      <UserPlus size={19} />
                      Add member
                      <ChevronRight size={17} />
                    </button>

                    <button
                      type="button"
                      className="gp-control gp-danger"
                      onClick={() => void openPanel("leave")}
                    >
                      <LogOut size={19} />
                      Leave group
                      <ChevronRight size={17} />
                    </button>
                  </div>
                </>
              ) : (
                <div className="gp-empty">
                  Select a group to view its details.
                </div>
              )}
            </aside>
          )}
        </section>
      )}

      {panel && (
        <div
          className="gp-modal-backdrop"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget && !busy) {
              setPanel(null);
            }
          }}
        >
          <div
            ref={modalRef}
            className="gp-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="gp-modal-title"
          >
            <div className="gp-modal-heading">
              <h2 id="gp-modal-title">{panelTitle[panel]}</h2>
              <IconButton
                label="Close dialog"
                disabled={busy}
                onClick={() => setPanel(null)}
              >
                <X size={21} />
              </IconButton>
            </div>

            {error && (
              <p className="gp-modal-error" role="alert">
                {error}
              </p>
            )}

            {panel === "bulk" && bulkRequest && (
              <div className="gp-bulk-confirm">
                <p>Apply <strong>{BULK_LABELS[bulkRequest.action].toLowerCase()}</strong> to {bulkRequest.groupIds.length} selected group{bulkRequest.groupIds.length === 1 ? "" : "s"}?</p>
                {bulkRequest.action === "clear" && <p>This hides older messages in your Groups timeline across your devices. Other members keep their history. Shared files are retained.</p>}
                {bulkRequest.action === "delete" && <p>This closes the group for everyone. Only the group creator can delete it. Messages and files are retained in the database.</p>}
                {bulkRequest.action === "leave" && <p>You will leave the selected groups. A groupÃ¢â‚¬â„¢s last admin may need to appoint another admin first.</p>}
                <div className="gp-bulk-confirm-actions">
                  <button type="button" disabled={busy} onClick={() => setPanel(null)}>Cancel</button>
                  <button type="button" className="gp-primary" disabled={busy} onClick={() => void executeBulkAction()}>
                    {busy ? "ApplyingÃ¢â‚¬Â¦" : "Confirm"}
                  </button>
                </div>
              </div>
            )}

            {panel === "reactions" && reactionTarget && (
              <section className="gp-reaction-details" aria-busy={reactionLoading}>
                <div className="gp-reaction-tabs" aria-label="Filter reactions">
                  <button type="button" aria-pressed={reactionTab === "all"} onClick={() => setReactionTab("all")}>
                    All {reactionPeople?.items.length ?? 0}
                  </button>
                  {Object.entries(reactionPeople?.counts || reactionTarget.reactions || {}).filter(([, count]) => count > 0).map(([emoji, count]) => (
                    <button key={emoji} type="button" aria-pressed={reactionTab === emoji} onClick={() => setReactionTab(emoji)}>{emoji} {count}</button>
                  ))}
                </div>
                {reactionError && <p className="gp-modal-error" role="alert">{reactionError} <button type="button" onClick={() => void refreshReactionPeople(true)}>Retry</button></p>}
                {reactionLoading ? <p className="gp-modal-note">Loading reactionsâ€¦</p> : (
                  <div className="gp-reaction-people" aria-live="polite">
                    {(reactionPeople?.items || []).filter((person) => reactionTab === "all" || person.emoji === reactionTab).map((person) => {
                      const own = person.mine && person.user_id === user?.id;
                      const content = <>
                        <Avatar userId={person.user_id} name={person.name || person.username} src={person.avatar_url} />
                        <span className="gp-reaction-person-copy">
                          <strong>{own ? "You" : person.name || person.username || "Member"}</strong>
                          <small>{own ? reactionRemoving === person.emoji ? "Removingâ€¦" : "Click to remove" : person.username ? `@${person.username.replace(/^@/, "")}` : "Reacted to this message"}</small>
                        </span>
                        <span className="gp-reaction-person-emoji">{person.emoji}</span>
                      </>;
                      return own ? (
                        <button className="gp-reaction-person" type="button" key={`${person.user_id}:${person.emoji}`} disabled={reactionRemoving !== null} onClick={() => void removeOwnReaction(person)}>{content}</button>
                      ) : (
                        <div className="gp-reaction-person" key={`${person.user_id}:${person.emoji}`}>{content}</div>
                      );
                    })}
                    {reactionPeople && reactionPeople.items.length === 0 && <p className="gp-modal-note">No reactions yet.</p>}
                  </div>
                )}
              </section>
            )}

            {panel === "info" && infoMessage && (
              <section className="gp-message-info" aria-busy={infoLoading}>
                <div className="gp-info-preview">
                  <strong>You</strong>
                  <p>{infoMessage.content || "Attachment"}</p>
                  <time>{new Date(infoMessage.created_at).toLocaleString()}</time>
                </div>
                <div className="gp-info-heading">
                  <h3><CheckCheck size={17} /> Read by</h3>
                  <button
                    type="button"
                    disabled={infoLoading}
                    onClick={() => void openMessageInfo(infoMessage)}
                  >
                    {infoLoading ? "RefreshingÃ¢â‚¬Â¦" : "Refresh"}
                  </button>
                </div>
                <div aria-live="polite">
                  {infoLoading ? (
                    <p className="gp-modal-note">Loading message viewsÃ¢â‚¬Â¦</p>
                  ) : infoError ? (
                    <p className="gp-modal-error" role="alert">{infoError}</p>
                  ) : (receipts[infoMessage.id] || []).length === 0 ? (
                    <p className="gp-modal-note">No read receipts yet.</p>
                  ) : (
                    <ul className="gp-viewers">
                      {(receipts[infoMessage.id] || []).map((receipt) => {
                        const person = directory.get(receipt.user_id);
                        return (
                          <li key={receipt.user_id}>
                            <Avatar userId={receipt.user_id} name={displayName(receipt.user_id)} src={person?.avatar_url} />
                            <div>
                              <strong>{person ? displayName(receipt.user_id) : `Member ${receipt.user_id.slice(0, 8)}`}</strong>
                              <time dateTime={receipt.read_at}>
                                {new Date(receipt.read_at).toLocaleString()}
                              </time>
                            </div>
                            <CheckCheck size={17} className="gp-read" />
                          </li>
                        );
                      })}
                    </ul>
                  )}
                </div>
              </section>
            )}

            {(panel === "create" || panel === "add") && (
              <form
                onSubmit={(event) =>
                  void (
                    panel === "create"
                      ? createGroup(event)
                      : addMembers(event)
                  )
                }
              >
                {panel === "create" && (
                  <label className="gp-field">
                    Group name
                    <input
                      value={name}
                      maxLength={120}
                      required
                      placeholder="Product Team"
                      onChange={(event) => setName(event.target.value)}
                    />
                  </label>
                )}

                {panel === "add" && !canManage && (
                  <p className="gp-modal-note">
                    Adding members requires permission from the group owner
                    or an admin.
                  </p>
                )}

                <div className="gp-friend-list">
                  {availableFriends.map((friend) => (
                    <label className="gp-friend" key={friend.id}>
                      <input
                        type="checkbox"
                        checked={selectedFriends.includes(friend.person.id)}
                        onChange={() => toggleFriend(friend.person.id)}
                      />
                      <Avatar userId={friend.person.id}
                        name={friend.person.name || friend.person.username}
                        src={friend.person.avatar_url}
                      />
                      <span>
                        {friend.person.name ||
                          friend.person.username ||
                          "Friend"}
                      </span>
                    </label>
                  ))}

                  {!availableFriends.length && (
                    <p className="gp-modal-note">
                      No eligible friends are available.
                    </p>
                  )}
                </div>

                <button
                  type="submit"
                  className="gp-primary gp-modal-submit"
                  disabled={
                    busy ||
                    !selectedFriends.length ||
                    (panel === "add" && !canManage)
                  }
                >
                  {busy
                    ? "SavingÃ¢â‚¬Â¦"
                    : panel === "create"
                      ? "Create group"
                      : "Add selected members"}
                </button>
              </form>
            )}

            {(panel === "members" || panel === "admins") && (
              <div className="gp-member-list">
                {panelMembers.map((member) => (
                  <div className="gp-member" key={member.user_id}>
                    <Avatar userId={member.user_id}
                      name={member.name || member.username}
                      src={member.avatar_url}
                      online={member.online}
                    />
                    <div>
                      <strong>
                        {member.name || member.username || "Member"}
                      </strong>
                      <small>
                        {member.role === "owner" ? "Group owner" : member.role}
                      </small>
                    </div>

                    {canManage &&
                      member.role !== "owner" &&
                      member.user_id !== user?.id && (
                        <div className="gp-member-actions">
                          <button
                            type="button"
                            disabled={
                              busy ||
                              !members.some(
                                (item) =>
                                  item.user_id === user?.id &&
                                  item.role === "owner",
                              )
                            }
                            onClick={() => void changeRole(member)}
                          >
                            {member.role === "admin" ? "Demote" : "Make admin"}
                          </button>
                          <button
                            type="button"
                            className="gp-danger"
                            disabled={busy}
                            onClick={() => void removeMember(member)}
                          >
                            Remove
                          </button>
                        </div>
                      )}
                  </div>
                ))}

                {!panelMembers.length && (
                  <p className="gp-modal-note">No members to display.</p>
                )}
              </div>
            )}

            {panel === "files" && (
              <div className="gp-modal-files">
                {sharedFiles.map((file) => (
                  <button
                    type="button"
                    className="gp-file"
                    key={file.attachment_id}
                    disabled={busy}
                    onClick={() => void downloadFile(file)}
                  >
                    <span className="gp-file-icon">
                      <FileText size={25} />
                    </span>
                    <span className="gp-file-copy">
                      <strong>{file.filename}</strong>
                      <small>{fileSize(file.size_bytes)}</small>
                    </span>
                    <Download size={20} />
                  </button>
                ))}
                {!sharedFiles.length && (
                  <p className="gp-modal-note">No shared files yet.</p>
                )}
              </div>
            )}

            {panel === "pinned" && (
              <div className="gp-pinned-list">
                {messages
                  .filter((item) => item.pinned && !item.deleted_at)
                  .map((item) => (
                    <div className="gp-pinned-message" key={item.id}>
                      <strong>{displayName(item.sender_user_id)}</strong>
                      <p>{item.content}</p>
                      <small>{time(item.created_at)}</small>
                    </div>
                  ))}

                {!messages.some((item) => item.pinned && !item.deleted_at) && (
                  <p className="gp-modal-note">
                    No pinned messages in the loaded history.
                  </p>
                )}
              </div>
            )}

            {panel === "manage" && (
              <form onSubmit={(event) => void saveGroup(event)}>
                <fieldset className="gp-avatar-settings" disabled={!canManage || busy || avatarPreparing}>
                  <legend>Group image</legend>
                  <div className="gp-avatar-preview">
                    <GroupAvatar name={name} details={activeDetails ? { ...activeDetails, avatar_url: avatarAttachmentId ? activeDetails.avatar_url : null } : undefined} mode={avatarMode} preview={avatarPreview} />
                    <div>
                      <button type="button" onClick={() => avatarInputRef.current?.click()}>{avatarPreparing ? "Preparingâ€¦" : avatarAttachmentId || avatarFile ? "Change photo" : "Upload photo"}</button>
                      <button type="button" disabled={!avatarFile && !avatarAttachmentId} onClick={() => {
                        setAvatarFile(null);
                        setAvatarAttachmentId(null);
                        avatarUploadRef.current = null;
                        setAvatarMode("auto");
                      }}>Remove photo</button>
                      <small>Square crop, up to 512 Ã— 512 pixels.</small>
                    </div>
                  </div>
                  <input ref={avatarInputRef} type="file" accept="image/*" hidden onChange={(event) => {
                    const file = event.target.files?.[0];
                    event.target.value = "";
                    if (file) void chooseGroupPhoto(file);
                  }} />
                  <div className="gp-avatar-modes">
                    <label><input type="radio" name="group-avatar-mode" checked={avatarMode === "auto"} onChange={() => setAvatarMode("auto")} /> Automatic â€” photo, otherwise members</label>
                    <label><input type="radio" name="group-avatar-mode" checked={avatarMode === "photo"} disabled={!avatarAttachmentId && !avatarFile} onChange={() => setAvatarMode("photo")} /> Group photo</label>
                    <label><input type="radio" name="group-avatar-mode" checked={avatarMode === "members"} onChange={() => setAvatarMode("members")} /> Member photos</label>
                  </div>
                  {activeDetails?.avatar_error && <p className="gp-modal-error">{activeDetails.avatar_error}</p>}
                  <p className="gp-avatar-help">New photos use your existing shared-file upload and appear in the groupâ€™s chat/media. Save changes to apply the image.</p>
                </fieldset>
                <label className="gp-field">
                  Group name
                  <input
                    value={name}
                    maxLength={120}
                    required
                    disabled={!canManage}
                    onChange={(event) => setName(event.target.value)}
                  />
                </label>

                <label className="gp-field">
                  Description
                  <textarea
                    value={description}
                    maxLength={2000}
                    rows={4}
                    disabled={!canManage}
                    onChange={(event) => setDescription(event.target.value)}
                  />
                </label>

                {!canManage && (
                  <p className="gp-modal-note">
                    Only authorized group managers can edit these details.
                  </p>
                )}

                <button
                  type="submit"
                  className="gp-primary gp-modal-submit"
                  disabled={busy || avatarPreparing || !canManage || !name.trim()}
                >
                  {busy ? "SavingÃ¢â‚¬Â¦" : "Save changes"}
                </button>
              </form>
            )}

            {panel === "leave" && (
              <>
                <p className="gp-modal-note">
                  Leave <strong>{activeGroup?.name}</strong>? You will need
                  to be added again to participate.
                </p>

                {members.some(
                  (member) =>
                    member.user_id === user?.id && member.role === "owner",
                ) && (
                  <p className="gp-modal-note">
                    If you leave as the owner, ownership passes to
                    another active admin or member. If you are the
                    last member, the group will close.
                  </p>
                )}

                <button
                  type="button"
                  className="gp-primary gp-leave-button"
                  disabled={busy}
                  onClick={() => void leaveGroup()}
                >
                  {busy ? "LeavingÃ¢â‚¬Â¦" : "Leave group"}
                </button>
              </>
            )}
          </div>
        </div>
      )}

      {call && user?.id && (
        <ConversationCallPanel
          key={call.conversationId}
          conversationId={call.conversationId}
          conversationName={call.name}
          currentUserId={user.id}
          initialKind={call.kind}
          invitedUserIds={call.invitedUserIds}
          onClose={closeCall}
        />
      )}

            <style jsx global>{`
        .gp {
          --gp-text: #171a23;
          --gp-muted: #73777d;
          --gp-border: #e9e5dc;
          --gp-yellow: #ffc600;
          --gp-selection: #fff3c8;
          --gp-own: #fff0bc;
          --gp-green: #00a66b;
          width: 100%;
          min-width: 0;
          min-height: 100%;
          padding: 25px 12px 20px;
          color: var(--gp-text);
          background:
            radial-gradient(ellipse at 65% 75%, #fbf7eb 0%, transparent 60%),
            #fdfcf8;
          font-family: inherit;
          font-size: 15px;
          line-height: 1.45;
        }

        .gp *,
        .gp *::before,
        .gp *::after {
          box-sizing: border-box;
        }

        .gp button,
        .gp input,
        .gp textarea {
          font: inherit;
        }

        .gp button {
          color: inherit;
          cursor: pointer;
          -webkit-tap-highlight-color: transparent;
        }

        .gp button:disabled {
          cursor: not-allowed;
          opacity: 0.48;
        }

        .gp button:focus-visible,
        .gp input:focus-visible,
        .gp textarea:focus-visible,
        .gp a:focus-visible {
          outline: 0px solid #a77500;
          outline-offset: 0px;
        }

        .gp ::selection {
          color: #171a23;
          background: #ffe58a;
        }

        .gp input,
        .gp textarea {
          caret-color: #a77500;
        }

        .gp input::placeholder,
        .gp textarea::placeholder {
          color: #777b81;
          opacity: 1;
        }

        .gp h1,
        .gp h2,
        .gp h3,
        .gp p {
          margin: 0;
        }

        .gp strong,
        .gp h2,
        .gp h3 {
          font-weight: 600;
        }

        .gp svg {
          flex-shrink: 0;
          stroke-width: 1.8;
        }

        .gp-page-header {
          display: flex;
          align-items: flex-start;
          justify-content: space-between;
          gap: 24px;
          padding: 0 20px 22px;
          min-height: 99px;
        }

        .gp-page-header h1 {
          color: #101521;
          font-size: clamp(30px, 2.7vw, 40px);
          line-height: 1.2;
          font-weight: 500;
          letter-spacing: -0.025em;
        }

        .gp-page-header p {
          margin-top: 6px;
          color: #808286;
          font-size: 17px;
          line-height: 1.5;
        }

        .gp-primary {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          gap: 12px;
          min-height: 49px;
          padding: 0 23px;
          border: 1px solid #191919;
          border-radius: 12px;
          background: linear-gradient(155deg, #30312f, #202120);
          color: #fff !important;
          font-size: 17px;
          font-weight: 500;
          white-space: nowrap;
        }

        .gp-primary:hover:not(:disabled),
        .gp-send:hover:not(:disabled) {
          background: #111;
        }

        .gp-grid {
          display: grid;
          grid-template-columns:
            minmax(255px, 0.98fr)
            minmax(365px, 1.51fr)
            minmax(270px, 0.85fr);
          gap: 6px;
          min-width: 0;
          height: calc(100dvh - 150px);
          min-height: 620px;
        }

        .gp-details-hidden .gp-grid {
          grid-template-columns: minmax(255px, 0.98fr) minmax(365px, 2.36fr);
        }

        .gp-card {
          min-width: 0;
          min-height: 0;
          overflow: hidden;
          border: 1px solid var(--gp-border);
          border-radius: 17px;
          background: rgba(255, 255, 255, 0.38);
        }

        .gp-inbox {
          display: flex;
          flex-direction: column;
          padding: 21px 4px 15px;
        }

        .gp-panel-heading {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 12px;
          padding: 0 15px 15px 17px;
        }

        .gp-panel-heading h2 {
          font-size: 21px;
          line-height: 1.3;
          letter-spacing: -0.015em;
        }

        .gp-icon {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
          width: 35px;
          height: 35px;
          padding: 0;
          border: 1px solid var(--gp-border);
          border-radius: 12px;
          background: transparent;
        }

        .gp-icon:hover:not(:disabled) {
          background: #f4f0e5;
        }

        .gp-search {
          display: flex;
          align-items: center;
          gap: 12px;
          min-height: 46px;
          margin: 0 13px;
          padding: 0 14px;
          border: 1px solid #e1dbce;
          border-radius: 12px;
          background: rgba(255, 255, 255, 0.56);
          color: #656b73;
        }

        .gp-search input {
          width: 100%;
          min-width: 0;
          border: 0;
          outline: none;
          background: transparent;
          font-size: 15px;
        }

        .gp-search > button {
          display: flex;
          padding: 0;
          border: 0;
          background: transparent;
        }

        .gp-tabs {
          display: flex;
          gap: 7px;
          padding: 15px 13px 16px;
        }

        .gp-tabs button {
          flex: 1;
          min-width: 0;
          height: 35px;
          padding: 0 10px;
          border: 1px solid #e3ded3;
          border-radius: 999px;
          background: transparent;
          color: #54575d;
          font-size: 13px;
          white-space: nowrap;
        }

        .gp-tabs button.is-active {
          border-color: #242524;
          background: linear-gradient(145deg, #363735, #1e1f1e);
          color: #fff;
        }

        .gp-group-list {
          flex: 1;
          min-height: 0;
          overflow-y: auto;
          scrollbar-width: thin;
          scrollbar-color: #d9d2c3 transparent;
        }

        .gp-group-row {
          display: flex;
          align-items: center;
          gap: 15px;
          position: relative;
          width: 100%;
          min-height: 96px;
          padding: 14px 16px;
          border: 0;
          border-radius: 14px;
          background: transparent;
          text-align: left;
        }

        .gp-group-row:not(:last-child)::after {
          content: "";
          position: absolute;
          right: 17px;
          bottom: 0;
          left: 17px;
          height: 1px;
          background: #eeeae2;
        }

        .gp-group-row.is-selected {
          background: linear-gradient(105deg, #fff5d4, #fff2c5);
        }

        .gp-group-row.is-selected::after {
          display: none;
        }

        .gp-group-row:hover:not(.is-selected) {
          background: #f7f4ec;
        }

        .gp-avatar {
          position: relative;
          display: inline-flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
          width: 58px;
          height: 58px;
          overflow: visible;
          border-radius: 50%;
          background: #e9e4da;
          color: #514b42;
          font-size: 18px;
          font-weight: 600;
        }

        .gp-avatar.is-group {
          background: linear-gradient(145deg, #ffe59a, #fff2c3);
          color: #22251f;
        }

        .gp-avatar img {
          position: absolute;
          inset: 0;
          width: 100%;
          height: 100%;
          border-radius: inherit;
          object-fit: cover;
        }

        .gp-online-badge {
          position: absolute;
          right: -1px;
          bottom: 1px;
          width: 16px;
          height: 16px;
          border: 2px solid #fffdf6;
          border-radius: 50%;
          background: var(--gp-green);
        }

        .gp-group-copy {
          display: flex;
          flex: 1;
          flex-direction: column;
          gap: 5px;
          min-width: 0;
        }

        .gp-group-copy strong {
          overflow: hidden;
          color: #171b26;
          font-size: 16px;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .gp-group-copy > span {
          overflow: hidden;
          color: #777b81;
          font-size: 13px;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .gp-row-trailing {
          display: flex;
          align-items: flex-end;
          flex-shrink: 0;
          flex-direction: column;
          gap: 9px;
          min-width: 35px;
          align-self: stretch;
          justify-content: center;
        }

        .gp-row-trailing time {
          color: #737981;
          font-size: 12px;
          font-variant-numeric: tabular-nums;
        }

        .gp-row-indicators {
          display: flex;
          align-items: center;
          gap: 8px;
          min-height: 24px;
          color: #545d67;
        }

        .gp-unread {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          min-width: 24px;
          height: 24px;
          padding: 0 5px;
          border: 1px solid #f0c900;
          border-radius: 50%;
          background: #ffd000;
          color: #242416;
          font-size: 13px;
          font-weight: 500;
        }

        .gp-archive-link {
          display: flex;
          align-items: center;
          gap: 12px;
          width: calc(100% - 26px);
          margin: 12px 13px 0;
          padding: 14px 5px 0;
          border: 0;
          border-top: 1px solid var(--gp-border);
          background: transparent;
          text-align: left;
          color: #545c68;
          font-size: 14px;
        }

        .gp-archive-link svg:last-child {
          margin-left: auto;
        }

        .gp-conversation {
          display: flex;
          flex-direction: column;
          position: relative;
        }

        .gp-conversation-header {
          display: flex;
          align-items: center;
          flex-shrink: 0;
          gap: 17px;
          min-height: 81px;
          padding: 12px 20px;
          border-bottom: 1px solid var(--gp-border);
        }

        .gp-conversation-header > .gp-avatar {
          width: 55px;
          height: 55px;
        }

        .gp-conversation-title {
          display: flex;
          flex: 1;
          flex-direction: column;
          align-items: flex-start;
          gap: 2px;
          min-width: 0;
          padding: 0;
          border: 0;
          background: transparent;
          text-align: left;
        }

        .gp-conversation-title strong {
          max-width: 100%;
          overflow: hidden;
          font-size: 19px;
          line-height: 1.35;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .gp-conversation-title > span {
          color: #676c74;
          font-size: 14px;
        }

        .gp-header-actions {
          display: flex;
          align-items: center;
          flex-shrink: 0;
          gap: 9px;
          position: relative;
        }

        .gp-header-actions > .gp-icon:not(:last-of-type) {
          border-color: transparent;
        }

        .gp-back {
          display: none;
        }

        .gp-message-search {
          display: flex;
          align-items: center;
          gap: 10px;
          padding: 9px 15px;
          border-bottom: 1px solid var(--gp-border);
          background: #fffdf7;
        }

        .gp-message-search input {
          flex: 1;
          min-width: 0;
          border: 0;
          outline: 0;
          background: transparent;
          font-size: 14px;
        }

        .gp-messages {
          flex: 1;
          min-height: 0;
          overflow-x: hidden;
          overflow-y: auto;
          padding: 0 23px 8px;
          scrollbar-width: thin;
          scrollbar-color: #d7d0c2 transparent;
          overflow-anchor: auto;
        }

        .gp-day {
          display: flex;
          justify-content: center;
          padding: 14px 0 13px;
        }

        .gp-day > span {
          padding: 4px 17px;
          border: 1px solid #e8e1d3;
          border-radius: 999px;
          background: #faf8f1;
          color: #515963;
          font-size: 13px;
        }

        .gp-message {
          display: flex;
          flex-direction: column;
          align-items: flex-start;
          width: fit-content;
          max-width: 79%;
          margin-bottom: 13px;
        }

        .gp-message.is-own {
          align-items: flex-end;
          margin-left: auto;
        }

        .gp-message-author {
          padding: 0 2px 4px;
          color: #505864;
          font-size: 12px;
          font-weight: 500;
        }

        .gp-bubble {
          position: relative;
          min-width: 75px;
          max-width: 100%;
          padding: 10px 16px 8px;
          border: 1px solid #eeebe4;
          border-radius: 16px;
          background: rgba(255, 255, 255, 0.93);
        }

        .gp-message.is-own .gp-bubble {
          border-color: #fff0bd;
          background: linear-gradient(120deg, #fff0b9, #fff3c6);
          border-bottom-right-radius: 5px;
        }

        .gp-message:not(.is-own) .gp-bubble {
          border-bottom-left-radius: 5px;
        }

        .gp-message-text {
          white-space: pre-wrap;
          overflow-wrap: anywhere;
          color: #252934;
          font-size: 15px;
          line-height: 1.55;
        }

        .gp-message-time {
          display: flex;
          align-items: center;
          justify-content: flex-end;
          gap: 6px;
          min-height: 17px;
          margin-top: 2px;
          color: #8b8c8d;
          font-size: 11px;
          font-variant-numeric: tabular-nums;
        }

        .gp-message.is-own .gp-message-time {
          color: #827344;
        }

        .gp-message.is-own .gp-message-time > svg {
          color: #dca500;
        }

        .gp-message.is-own .gp-message-time > .gp-read {
          color: #009bd5;
        }

        .gp-message-more {
          position: absolute;
          top: -9px;
          right: -7px;
          display: flex;
          align-items: center;
          justify-content: center;
          width: 26px;
          height: 24px;
          padding: 0;
          border: 1px solid #e8e2d5;
          border-radius: 8px;
          background: #fffef9;
          opacity: 0;
        }

        .gp-message:hover .gp-message-more,
        .gp-message:focus-within .gp-message-more {
          opacity: 1;
        }

        .gp-quoted {
          display: flex;
          flex-direction: column;
          gap: 2px;
          margin-bottom: 7px;
          padding: 7px 9px;
          border-radius: 8px;
          background: #f4efe2;
          color: #666050;
          font-size: 12px;
        }

        .gp-quoted > span {
          display: -webkit-box;
          overflow: hidden;
          -webkit-line-clamp: 2;
          -webkit-box-orient: vertical;
        }

        .gp-file {
          display: flex;
          align-items: center;
          gap: 10px;
          width: 100%;
          min-width: 0;
          margin-top: 7px;
          padding: 12px 14px;
          border: 1px solid #eee9df;
          border-radius: 15px;
          background: rgba(255, 255, 255, 0.83);
          text-align: left;
        }

        .gp-file:hover:not(:disabled) {
          background: #fff8e2;
        }

        .gp-file-icon {
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
          width: 45px;
          height: 49px;
          border-radius: 10px;
          background: #fff0e8;
          color: #e24638;
        }

        .gp-file-copy {
          display: flex;
          flex: 1;
          flex-direction: column;
          gap: 3px;
          min-width: 0;
        }

        .gp-file-copy strong {
          overflow-wrap: anywhere;
          font-size: 14px;
        }

        .gp-file-copy small {
          color: #868686;
          font-size: 12px;
        }

        .gp-reactions {
          display: flex;
          flex-wrap: wrap;
          gap: 5px;
          margin-top: 4px;
        }

        .gp-reactions button {
          padding: 2px 9px;
          border: 1px solid #ece6d9;
          border-radius: 999px;
          background: #fffef8;
          font-size: 12px;
        }

        .gp-composer-section {
          flex-shrink: 0;
          padding: 0 10px 11px;
        }

        .gp-typing {
          display: flex;
          align-items: center;
          gap: 9px;
          min-height: 38px;
          padding: 3px 13px 8px;
          color: #898986;
          font-size: 12px;
        }

        .gp-typing-dots {
          display: inline-flex;
          align-items: center;
          gap: 4px;
          height: 30px;
          padding: 0 12px;
          border: 1px solid #ece5d9;
          border-radius: 999px;
          background: #fcfaf3;
        }

        .gp-typing-dots i {
          width: 6px;
          height: 6px;
          border-radius: 50%;
          background: #a6a39b;
        }

        .gp-composer {
          display: flex;
          align-items: center;
          gap: 6px;
          position: relative;
          min-height: 66px;
          padding: 8px 9px;
          border: 1px solid #e4decf;
          border-radius: 19px;
          background: rgba(255, 255, 255, 0.94);
        }

        .gp-composer .gp-icon {
          width: 37px;
          height: 39px;
          border-color: transparent;
          border-radius: 9px;
        }

        .gp-composer textarea {
          flex: 1;
          min-width: 0;
          min-height: 25px;
          max-height: 105px;
          padding: 2px 5px;
          resize: none;
          border: 0;
          outline: 0;
          background: transparent;
          font-size: 15px;
          line-height: 1.6;
        }

        .gp-composer-divider {
          width: 1px;
          height: 34px;
          margin: 0 4px;
          background: #e6e0d4;
        }

        .gp-send {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
          width: 49px;
          height: 49px;
          padding: 0;
          border: 1px solid #151515;
          border-radius: 14px;
          background: linear-gradient(140deg, #363734, #1c1d1c);
          color: #fff;
        }

        .gp-hidden-input {
          display: none;
        }

        .gp-emoji-wrap {
          position: relative;
        }

        .gp-emoji {
          position: absolute;
          bottom: 48px;
          left: 0;
          z-index: 20;
          display: grid;
          grid-template-columns: repeat(4, 37px);
          gap: 5px;
          padding: 9px;
          border: 1px solid #e3dac9;
          border-radius: 13px;
          background: #fffdf7;
          box-shadow: 0 10px 25px rgba(55, 43, 19, 0.13);
        }

        .gp-emoji button {
          width: 37px;
          height: 35px;
          padding: 0;
          border: 0;
          border-radius: 8px;
          background: transparent;
          font-size: 22px;
        }

        .gp-emoji button:hover {
          background: #fff0b7;
        }

        .gp-reply-banner {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 10px;
          margin-bottom: 7px;
          padding: 8px 12px;
          border: 1px solid #eadfc6;
          border-radius: 12px;
          background: #fff8e4;
        }

        .gp-reply-banner > div {
          display: flex;
          flex-direction: column;
          gap: 2px;
          min-width: 0;
          font-size: 12px;
        }

        .gp-reply-banner span {
          overflow: hidden;
          color: #7b725d;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .gp-recording {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 5px 8px 10px;
          color: #b33e35;
          font-size: 12px;
        }

        .gp-recording > span {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background: #d4483e;
        }

        .gp-details {
          overflow-y: auto;
          padding: 22px 21px;
          scrollbar-width: thin;
          scrollbar-color: #d9d2c3 transparent;
        }

        .gp-details-heading {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 10px;
          padding: 0 5px 20px;
          border-bottom: 1px solid #eeebe4;
        }

        .gp-details-heading h2 {
          font-size: 18px;
          letter-spacing: -0.015em;
        }

        .gp-details-heading .gp-icon {
          width: 24px;
          height: 24px;
          border: 0;
        }

        .gp-details-person {
          display: flex;
          align-items: center;
          gap: 18px;
          padding: 13px 5px 19px;
        }

        .gp-details-person > .gp-avatar {
          width: 79px;
          height: 79px;
          font-size: 24px;
        }

        .gp-details-person > div {
          min-width: 0;
        }

        .gp-details-person h3 {
          overflow-wrap: anywhere;
          font-size: 18px;
          line-height: 1.4;
        }

        .gp-details-person p {
          margin-top: 3px;
          color: #73777d;
          font-size: 14px;
          line-height: 1.45;
        }

        .gp-description {
          padding: 0 5px 15px;
          color: #73777d;
          font-size: 14px;
          white-space: pre-wrap;
          overflow-wrap: anywhere;
        }

        .gp-detail-actions {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 13px;
          padding: 0 5px 21px;
          border-bottom: 1px solid #eeebe4;
        }

        .gp-detail-actions button {
          display: flex;
          align-items: center;
          justify-content: center;
          flex-direction: column;
          gap: 6px;
          min-height: 76px;
          padding: 10px 4px;
          border: 1px solid #e9e3d7;
          border-radius: 14px;
          background: rgba(255, 255, 255, 0.32);
          font-size: 14px;
        }

        .gp-detail-actions button:hover:not(:disabled) {
          background: #fff5d6;
        }

        .gp-details-links {
          display: flex;
          flex-direction: column;
          gap: 7px;
          padding: 18px 0 26px;
        }

        .gp-detail-link {
          display: flex;
          align-items: center;
          gap: 13px;
          min-height: 55px;
          padding: 0 16px;
          border: 1px solid #e9e3d7;
          border-radius: 13px;
          background: transparent;
          text-align: left;
          font-size: 15px;
        }

        .gp-detail-link svg:last-child {
          margin-left: auto;
          color: #737981;
        }

        .gp-detail-link:hover {
          background: #fff7df;
        }

        .gp-switches {
          padding: 0 13px;
          border: 1px solid #e9e3d7;
          border-radius: 15px;
          background: rgba(255, 255, 255, 0.22);
        }

        .gp-switch-row {
          display: flex;
          align-items: center;
          gap: 12px;
          min-height: 60px;
          font-size: 15px;
        }

        .gp-switch-row + .gp-switch-row {
          border-top: 1px solid #ece6da;
        }

        .gp-switch-row > span {
          flex: 1;
        }

        .gp-switch {
          position: relative;
          flex-shrink: 0;
          width: 47px;
          height: 28px;
          padding: 0;
          border: 0;
          border-radius: 999px;
          background: #c5c5c5;
        }

        .gp-switch > span {
          position: absolute;
          top: 3px;
          left: 3px;
          width: 22px;
          height: 22px;
          border-radius: 50%;
          background: #fff;
          transition: transform 150ms ease-out;
        }

        .gp-switch.is-on {
          background: #ffc500;
        }

        .gp-switch.is-on > span {
          transform: translateX(19px);
        }

        .gp-group-controls {
          margin-top: 20px;
          padding-top: 17px;
          border-top: 1px solid #e9e3d7;
        }

        .gp-controls-heading {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 10px;
          margin-bottom: 9px;
        }

        .gp-controls-heading h3 {
          font-size: 15px;
        }

        .gp-controls-heading > button {
          padding: 5px 9px;
          border: 1px solid #e4ddcf;
          border-radius: 9px;
          background: transparent;
          font-size: 12px;
        }

        .gp-control {
          display: flex;
          align-items: center;
          gap: 12px;
          width: 100%;
          min-height: 40px;
          padding: 8px 3px;
          border: 0;
          background: transparent;
          text-align: left;
          font-size: 14px;
        }

        .gp-control > span {
          margin-left: auto;
          color: #81858a;
          font-size: 12px;
        }

        .gp-control > svg:last-child {
          margin-left: auto;
          color: #858a91;
        }

        .gp-control > span + svg:last-child {
          margin-left: 0;
        }

        .gp-danger {
          color: #e33b32 !important;
        }

        .gp-control.gp-danger {
          margin-top: 8px;
          border-top: 1px solid #ece6db;
        }

        .gp-empty {
          display: flex;
          align-items: center;
          justify-content: center;
          flex-direction: column;
          gap: 9px;
          padding: 35px 18px;
          color: #747a82;
          text-align: center;
          font-size: 14px;
        }

        .gp-empty strong {
          color: #3f4650;
        }

        .gp-conversation-empty {
          flex: 1;
        }

        .gp-feedback {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 15px;
          margin: -4px 0 12px;
          padding: 9px 13px;
          border: 1px solid #e8ddb8;
          border-radius: 12px;
          background: #fff8e1;
          color: #655632;
          font-size: 13px;
        }

        .gp-feedback > span {
          overflow-wrap: anywhere;
        }

        .gp-feedback .gp-icon {
          width: 27px;
          height: 27px;
          border: 0;
        }

        .gp-error {
          border-color: #ecc6bd;
          background: #fff1eb;
          color: #9b3f32;
        }

        .gp-account,
        .gp-route-loading {
          padding: 35px;
          color: #626b77;
          font-size: 15px;
        }

        .gp-account a {
          color: #886000;
          text-decoration: underline;
          text-underline-offset: 3px;
        }

        .gp-menu {
          position: absolute;
          z-index: 40;
          display: flex;
          flex-direction: column;
          min-width: 195px;
          padding: 5px;
          border: 1px solid #e2d9c7;
          border-radius: 12px;
          background: #fffdf7;
          box-shadow: 0 12px 28px rgba(45, 37, 20, 0.13);
        }

        .gp-conversation-menu {
          top: 44px;
          right: 0;
        }

        .gp-message-menu {
          top: 25px;
          right: 0;
          min-width: 150px;
        }

        .gp-menu > button {
          display: flex;
          align-items: center;
          gap: 9px;
          min-height: 35px;
          padding: 7px 10px;
          border: 0;
          border-radius: 7px;
          background: transparent;
          text-align: left;
          font-size: 13px;
        }

        .gp-menu > button:hover:not(:disabled) {
          background: #fff0bd;
        }

        .gp-modal-backdrop {
          position: fixed;
          inset: 0;
          z-index: 1000;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 22px;
          background: rgba(26, 29, 34, 0.37);
        }

        .gp-modal {
          width: min(540px, 100%);
          max-height: calc(100dvh - 44px);
          overflow-y: auto;
          padding: 23px;
          border: 1px solid #e6ddcc;
          border-radius: 18px;
          background: #fffdf7;
          color: #202630;
          box-shadow: 0 20px 65px rgba(20, 20, 20, 0.2);
        }

        .gp-modal-heading {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 15px;
          margin-bottom: 20px;
        }

        .gp-modal-heading h2 {
          font-size: 21px;
        }

        .gp-field {
          display: flex;
          flex-direction: column;
          gap: 8px;
          margin-top: 14px;
          font-size: 14px;
          font-weight: 500;
        }

        .gp-field input,
        .gp-field textarea {
          width: 100%;
          padding: 11px 13px;
          border: 1px solid #dfd6c5;
          border-radius: 10px;
          background: #fff;
          color: #202630;
          font-weight: 400;
        }

        .gp-field textarea {
          resize: vertical;
        }

        .gp-friend-list {
          max-height: 300px;
          overflow-y: auto;
          margin-top: 17px;
          border: 1px solid #e8e0d2;
          border-radius: 12px;
        }

        .gp-friend {
          display: flex;
          align-items: center;
          gap: 12px;
          min-height: 64px;
          padding: 9px 13px;
          font-size: 14px;
          cursor: pointer;
        }

        .gp-friend + .gp-friend {
          border-top: 1px solid #eee7db;
        }

        .gp-friend input {
          accent-color: #b98b00;
        }

        .gp-friend .gp-avatar,
        .gp-member .gp-avatar {
          width: 39px;
          height: 39px;
          font-size: 13px;
        }

        .gp-modal-submit {
          width: 100%;
          margin-top: 20px;
          font-size: 15px;
        }

        .gp-modal-note {
          padding: 12px 0;
          color: #707780;
          font-size: 14px;
          line-height: 1.6;
        }

        .gp-modal-error {
          margin-bottom: 12px;
          padding: 10px 12px;
          border: 1px solid #ecc6bd;
          border-radius: 9px;
          background: #fff1eb;
          color: #9b3f32;
          font-size: 13px;
          overflow-wrap: anywhere;
        }

        .gp-member {
          display: flex;
          align-items: center;
          gap: 11px;
          padding: 11px 0;
          border-bottom: 1px solid #eee7db;
        }

        .gp-member > div:not(.gp-member-actions) {
          display: flex;
          flex: 1;
          flex-direction: column;
          min-width: 0;
        }

        .gp-member strong {
          overflow-wrap: anywhere;
          font-size: 14px;
        }

        .gp-member small {
          color: #7a818b;
          font-size: 12px;
          text-transform: capitalize;
        }

        .gp-member-actions {
          display: flex;
          flex-wrap: wrap;
          justify-content: flex-end;
          gap: 5px;
        }

        .gp-member-actions button {
          padding: 5px 7px;
          border: 1px solid #e3d9c7;
          border-radius: 7px;
          background: #fffdf6;
          font-size: 11px;
        }

        .gp-pinned-message {
          margin-bottom: 10px;
          padding: 12px;
          border: 1px solid #e8ddc5;
          border-radius: 11px;
          background: #fff9e8;
        }

        .gp-pinned-message strong {
          font-size: 13px;
        }

        .gp-pinned-message p {
          margin: 5px 0;
          white-space: pre-wrap;
          overflow-wrap: anywhere;
          font-size: 14px;
        }

        .gp-pinned-message small {
          color: #89806c;
        }

        .gp-leave-button {
          background: #bf3e35;
          border-color: #bf3e35;
          font-size: 15px;
        }

        @media (min-width: 1500px) {
          .gp-grid {
            grid-template-columns:
              minmax(310px, 0.98fr)
              minmax(480px, 1.51fr)
              minmax(295px, 0.85fr);
          }
        }

        @media (max-width: 1190px) {
          .gp-grid {
            grid-template-columns: 280px minmax(340px, 1fr);
          }

          .gp-details-hidden .gp-grid {
            grid-template-columns: 280px minmax(340px, 1fr);
          }

          .gp-details {
            position: fixed;
            top: 80px;
            right: 15px;
            bottom: 15px;
            z-index: 60;
            width: 320px;
            background: #fdfbf4;
            box-shadow: 0 14px 35px rgba(45, 37, 20, 0.15);
          }

          .gp-conversation-header {
            gap: 12px;
            padding-right: 12px;
            padding-left: 14px;
          }

          .gp-header-actions {
            gap: 3px;
          }

          .gp-page-header {
            padding-right: 8px;
            padding-left: 8px;
          }
        }

        @media (max-width: 760px) {
          .gp {
            padding: 17px 9px 12px;
          }

          .gp-page-header {
            min-height: 83px;
            gap: 12px;
            padding: 0 3px 17px;
          }

          .gp-page-header h1 {
            font-size: 30px;
          }

          .gp-page-header p {
            max-width: 240px;
            font-size: 12px;
          }

          .gp-page-header > .gp-primary {
            min-height: 40px;
            padding: 0 12px;
            gap: 6px;
            font-size: 12px;
          }

          .gp-page-header > .gp-primary svg {
            width: 17px;
          }

          .gp-grid,
          .gp-details-hidden .gp-grid {
            grid-template-columns: minmax(0, 1fr);
            height: calc(100dvh - 120px);
            min-height: 460px;
          }

          .gp-conversation {
            display: none;
          }

          .gp-mobile-chat .gp-inbox {
            display: none;
          }

          .gp-mobile-chat .gp-conversation {
            display: flex;
          }

          .gp-back {
            display: inline-flex;
            width: 27px;
            border: 0;
          }

          .gp-conversation-header {
            gap: 8px;
            min-height: 73px;
            padding: 10px;
          }

          .gp-conversation-header > .gp-avatar {
            width: 39px;
            height: 39px;
          }

          .gp-conversation-title strong {
            font-size: 15px;
          }

          .gp-conversation-title > span {
            font-size: 11px;
          }

          .gp-header-actions .gp-icon {
            width: 29px;
            height: 32px;
          }

          .gp-header-actions svg {
            width: 18px;
          }

          .gp-messages {
            padding-right: 14px;
            padding-left: 14px;
          }

          .gp-message {
            max-width: 88%;
          }

          .gp-message-text {
            font-size: 14px;
          }

          .gp-message-more {
            opacity: 1;
          }

          .gp-details {
            top: 12px;
            right: 10px;
            bottom: 12px;
            width: min(340px, calc(100vw - 20px));
          }

          .gp-composer-section {
            padding: 0 7px 8px;
          }

          .gp-composer {
            gap: 1px;
            min-height: 58px;
            padding: 6px;
            border-radius: 15px;
          }

          .gp-composer .gp-icon {
            width: 31px;
          }

          .gp-composer textarea {
            font-size: 14px;
          }

          .gp-composer-divider {
            margin: 0 1px;
          }

          .gp-send {
            width: 41px;
            height: 41px;
            border-radius: 12px;
          }

          .gp-member {
            align-items: flex-start;
            flex-wrap: wrap;
          }

          .gp-member-actions {
            width: 100%;
          }

          .gp-modal-backdrop {
            padding: 12px;
          }

          .gp-modal {
            max-height: calc(100dvh - 24px);
            padding: 18px;
          }
        }

        @media (prefers-reduced-motion: reduce) {
          .gp-switch > span {
            transition: none;
          }
        }
        /* Compact Groups interface */

        .gp {
          padding: 12px 10px;
          font-size: 13px;
        }

        .gp-page-header {
          min-height: 68px;
          gap: 14px;
          padding: 0 8px 12px;
        }

        .gp-page-header h1 {
          font-size: 27px;
          font-weight: 600;
        }

        .gp-page-header p {
          margin-top: 4px;
          font-size: 13px;
        }

        .gp-primary {
          min-height: 38px;
          gap: 8px;
          padding: 0 14px;
          border-radius: 9px;
          font-size: 13px;
        }

        .gp-grid {
          grid-template-columns: 240px minmax(0, 1fr) 260px;
          height: calc(100dvh - 230px);
          min-height: 0;
          gap: 8px;
        }

        .gp-details-hidden .gp-grid {
          grid-template-columns: 240px minmax(0, 1fr);
        }

        .gp-card {
          min-width: 0;
          min-height: 0;
          border-radius: 12px;
        }

        .gp svg {
          width: 18px;
          height: 18px;
        }

        .gp-icon,
        .gp-composer .gp-icon {
          width: 32px;
          height: 32px;
          border-radius: 8px;
        }

        .gp-panel-heading {
          padding: 12px;
        }

        .gp-panel-heading h2 {
          font-size: 17px;
        }

        .gp-search {
          min-height: 36px;
          gap: 8px;
          margin: 0 10px;
          padding: 0 10px;
          border-radius: 9px;
        }

        .gp-search input,
        .gp-message-search input {
          font-size: 13px;
        }

        .gp-tabs {
          gap: 4px;
          padding: 10px;
        }

        .gp-tabs button {
          height: 29px;
          padding: 0 8px;
          font-size: 11px;
        }

        .gp-group-row {
          min-height: 70px;
          gap: 9px;
          padding: 11px 10px;
        }

        .gp-avatar,
        .gp-conversation-header > .gp-avatar {
          width: 40px;
          height: 40px;
          font-size: 14px;
        }

        .gp-online-badge {
          width: 12px;
          height: 12px;
        }

        .gp-group-copy strong {
          font-size: 13px;
        }

        .gp-group-copy > span {
          font-size: 11px;
        }

        .gp-row-trailing time {
          font-size: 10px;
        }

        .gp-unread {
          min-width: 20px;
          height: 20px;
          font-size: 11px;
        }

        .gp-archive-link {
          padding: 12px;
          font-size: 12px;
        }

        .gp-conversation-header {
          min-height: 61px;
          gap: 9px;
          padding: 9px 11px;
        }

        .gp-conversation-title strong {
          font-size: 15px;
        }

        .gp-conversation-title > span {
          font-size: 11px;
        }

        .gp-header-actions {
          gap: 4px;
        }

        .gp-messages {
          padding: 14px;
          scrollbar-width: thin;
        }

        .gp-day > span {
          font-size: 11px;
        }

        .gp-message {
          position: relative;
          margin-bottom: 10px;
        }

        .gp-message.is-menu-open {
          z-index: 45;
        }

        .gp-bubble {
          padding: 8px 11px 6px;
          border-radius: 12px;
        }

        .gp-message-text {
          font-size: 13px;
          line-height: 1.5;
          overflow-wrap: anywhere;
        }

        .gp-message-author {
          font-size: 11px;
        }

        .gp-message-time {
          font-size: 10px;
        }

        .gp-message-time svg {
          width: 13px;
          height: 13px;
        }

        .gp-message-more {
          z-index: 2;
          width: 28px;
          height: 26px;
          opacity: 0;
          pointer-events: none;
        }

        .gp-message:hover .gp-message-more,
        .gp-message:focus-within .gp-message-more,
        .gp-message-more[aria-expanded="true"] {
          opacity: 1;
          pointer-events: auto;
        }

        .gp-message-menu {
          z-index: 50;
          min-width: 150px;
        }

        .gp-menu > button {
          min-height: 34px;
          font-size: 12px;
        }

        .gp-file-icon {
          width: 36px;
          height: 36px;
        }

        .gp-file-copy strong {
          font-size: 12px;
          overflow-wrap: anywhere;
        }

        .gp-file-copy small {
          font-size: 11px;
        }

        .gp-composer-section {
          padding: 9px;
        }

        .gp-typing {
          min-height: 25px;
          font-size: 11px;
        }

        .gp-composer {
          min-height: 49px;
          gap: 3px;
          padding: 6px;
          border-radius: 12px;
        }

        .gp-composer textarea {
          min-height: 22px;
          max-height: 84px;
          font-size: 13px;
          line-height: 1.5;
        }

        .gp-composer-divider {
          height: 25px;
          margin: 0 2px;
        }

        .gp-send {
          width: 36px;
          height: 36px;
          border-radius: 9px;
        }

        .gp-details {
          padding: 14px 12px;
          overflow-y: auto;
        }

        .gp-details-heading {
          padding: 0 0 11px;
        }

        .gp-details-heading h2 {
          font-size: 15px;
        }

        .gp-details-person {
          gap: 10px;
          padding: 13px 0;
        }

        .gp-details-person > .gp-avatar {
          width: 52px;
          height: 52px;
          font-size: 18px;
        }

        .gp-details-person h3 {
          font-size: 14px;
        }

        .gp-details-person p,
        .gp-description {
          font-size: 12px;
        }

        .gp-detail-actions {
          gap: 6px;
        }

        .gp-detail-actions button {
          min-height: 54px;
          gap: 6px;
          font-size: 12px;
        }

        .gp-details-links {
          gap: 6px;
          padding: 12px 0;
        }

        .gp-detail-link {
          min-height: 41px;
          gap: 9px;
          padding: 8px 10px;
          font-size: 12px;
        }

        .gp-switches {
          padding: 4px 10px;
        }

        .gp-switch-row {
          min-height: 43px;
          font-size: 12px;
        }

        .gp-group-controls {
          padding-top: 12px;
        }

        .gp-controls-heading {
          margin-bottom: 8px;
        }

        .gp-controls-heading h3,
        .gp-control {
          font-size: 12px;
        }

        .gp-control {
          min-height: 34px;
          gap: 8px;
        }

        .gp-modal {
          width: min(460px, calc(100vw - 24px));
          padding: 20px;
        }

        .gp-modal-heading h2 {
          font-size: 18px;
        }

        .gp-field,
        .gp-field input,
        .gp-field textarea {
          font-size: 13px;
        }

        .gp-friend {
          min-height: 52px;
        }

        .gp-feedback {
          padding: 9px 12px;
          font-size: 12px;
        }

        .gp-feedback > span {
          min-width: 0;
          overflow-wrap: anywhere;
        }

        .gp-error > span {
          max-height: 66px;
          overflow-y: auto;
        }

        @media (max-width: 1190px) {
          .gp-grid,
          .gp-details-hidden .gp-grid {
            grid-template-columns: 220px minmax(0, 1fr);
          }

          .gp-details {
            width: min(285px, calc(100vw - 24px));
          }
        }

        @media (max-width: 760px) {
          .gp {
            padding: 9px 6px;
          }

          .gp-page-header {
            min-height: 60px;
            padding: 0 4px 10px;
          }

          .gp-page-header h1 {
            font-size: 24px;
          }

          .gp-page-header p {
            font-size: 12px;
          }

          .gp-grid,
          .gp-details-hidden .gp-grid {
            grid-template-columns: minmax(0, 1fr);
            height: calc(100dvh - 210px);
            min-height: 0;
          }

          .gp-conversation-header {
            min-height: 58px;
            padding: 8px;
          }

          .gp-header-actions {
            gap: 2px;
          }

          .gp-messages {
            padding: 10px;
          }

          .gp-message {
            max-width: 88%;
          }

          .gp-composer textarea,
          .gp-search input,
          .gp-field input,
          .gp-field textarea {
            font-size: 16px;
          }
        }

        @media (pointer: coarse) {
          .gp-icon,
          .gp-composer .gp-icon,
          .gp-send {
            min-width: 44px;
            min-height: 44px;
          }

          .gp-message-more {
            width: 32px;
            height: 32px;
            opacity: 1;
            pointer-events: auto;
          }
        }
        /* Message actions stay inside the bubble. */

        .gp .gp-bubble {
          position: relative;
          min-height: 54px;
          padding: 9px 40px 7px 12px;
          overflow: visible;
        }

        .gp .gp-message-more {
          position: absolute;
          top: 5px;
          right: 5px;
          bottom: auto;
          left: auto;
          transform: none;
          display: inline-flex;
          align-items: center;
          justify-content: center;
          width: 24px;
          height: 24px;
          min-width: 24px;
          margin: 0;
          padding: 0;
          border: 0;
          border-radius: 6px;
          background: transparent;
          color: #616773;
          opacity: 0;
          pointer-events: none;
          cursor: pointer;
          z-index: 3;
        }

        .gp .gp-message-more svg {
          width: 17px;
          height: 17px;
          stroke: currentColor;
          pointer-events: none;
        }

        .gp .gp-message:hover .gp-message-more,
        .gp .gp-message:focus-within .gp-message-more,
        .gp .gp-message-more[aria-expanded="true"] {
          opacity: 1;
          pointer-events: auto;
        }

        .gp .gp-message-more:hover,
        .gp .gp-message-more[aria-expanded="true"] {
          background: rgba(23, 26, 35, 0.08);
        }

        /* Incoming menus open toward the conversation. */

        .gp .gp-message-menu {
          top: 34px;
          right: auto;
          bottom: auto;
          left: 0;
          width: 170px;
          min-width: 0;
          max-width: calc(100vw - 48px);
          max-height: min(240px, 45dvh);
          overflow-y: auto;
          z-index: 60;
        }

        /* Outgoing menus remain aligned to the right. */

        .gp .gp-message.is-own .gp-message-menu {
          right: 0;
          left: auto;
        }

        .gp .gp-message.is-menu-open {
          position: relative;
          z-index: 65;
        }

        .gp .gp-message-entry:not(:first-child):last-child
          .gp-message-menu {
          top: auto;
          bottom: calc(100% + 5px);
        }

        .gp .gp-message-text {
          min-width: 0;
          font-size: 13px;
          line-height: 1.5;
          white-space: pre-wrap;
          overflow-wrap: anywhere;
        }

        .gp .gp-message-time {
          justify-content: flex-end;
          gap: 4px;
          margin-top: 4px;
          font-size: 10px;
          line-height: 1.3;
        }

        /* Prevent the general button rule overriding Send. */

        .gp .gp-send {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          flex: 0 0 36px;
          width: 36px;
          height: 36px;
          min-width: 36px;
          padding: 0;
          border: 0;
          border-radius: 9px;
          background: #202220;
          color: #ffffff;
          opacity: 1;
        }

        .gp .gp-send svg {
          width: 18px;
          height: 18px;
          flex-shrink: 0;
          stroke: currentColor;
          stroke-width: 2;
          pointer-events: none;
        }

        .gp .gp-send:hover:not(:disabled) {
          background: #080a08;
          color: #ffffff;
        }

        .gp .gp-send:disabled {
          background: #e3e5e8;
          color: #858c96;
          opacity: 1;
          cursor: not-allowed;
        }

        /* Keep all four filters inside the sidebar. */

        .gp .gp-tabs {
          display: grid;
          grid-template-columns: repeat(4, minmax(0, 1fr));
          gap: 4px;
        }

        .gp .gp-tabs button {
          min-width: 0;
          padding: 0 3px;
          font-size: 11px;
        }

        @media (pointer: coarse) {
          .gp .gp-bubble {
            min-height: 60px;
            padding-right: 45px;
          }

          .gp .gp-message-more {
            width: 32px;
            height: 32px;
            min-width: 32px;
            opacity: 1;
            pointer-events: auto;
          }

          .gp .gp-send {
            flex-basis: 44px;
            width: 44px;
            height: 44px;
            min-width: 44px;
          }
        }

        /* Reserve room for smiley and three-dot controls. */

        .gp .gp-bubble {
          padding-right: 70px;
        }

        .gp .gp-message-reaction {
          position: absolute;
          top: 5px;
          right: 33px;
          display: inline-flex;
          align-items: center;
          justify-content: center;
          width: 24px;
          height: 24px;
          margin: 0;
          padding: 0;
          border: 0;
          border-radius: 6px;
          background: transparent;
          color: #727780;
          opacity: 0;
          pointer-events: none;
          cursor: pointer;
          z-index: 3;
        }

        .gp .gp-message-reaction svg {
          width: 16px;
          height: 16px;
          pointer-events: none;
        }

        .gp .gp-message:hover .gp-message-reaction,
        .gp .gp-message:focus-within .gp-message-reaction,
        .gp .gp-message-reaction[aria-expanded="true"] {
          opacity: 1;
          pointer-events: auto;
        }

        .gp .gp-message-reaction:hover,
        .gp .gp-message-reaction[aria-expanded="true"] {
          background: rgba(23, 26, 35, 0.07);
        }

        .gp .gp-reaction-picker {
          position: absolute;
          top: 35px;
          left: 0;
          display: flex;
          flex-wrap: wrap;
          gap: 3px;
          width: max-content;
          max-width: min(240px, calc(100vw - 40px));
          padding: 7px;
          border: 1px solid #e8e2d5;
          border-radius: 12px;
          background: #fffdf7;
          box-shadow: 0 8px 24px rgba(30, 25, 15, 0.14);
          z-index: 70;
        }

        .gp .gp-message.is-own .gp-reaction-picker {
          right: 0;
          left: auto;
        }

        .gp .gp-reaction-picker > button {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          width: 31px;
          height: 32px;
          margin: 0;
          padding: 0;
          border: 0;
          border-radius: 7px;
          background: transparent;
          font-size: 21px;
          line-height: 1;
          cursor: pointer;
        }

        .gp .gp-reaction-picker > button:hover {
          background: #fff0bc;
        }

        .gp .gp-reactions {
          gap: 5px;
          margin-top: 5px;
        }

        .gp .gp-reactions > button {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          gap: 4px;
          min-height: 24px;
          padding: 2px 8px;
          border: 1px solid #e8e2d5;
          border-radius: 999px;
          background: #fffef9;
          font-size: 12px;
          line-height: 1.2;
          cursor: pointer;
        }

        .gp .gp-reactions > button:hover:not(:disabled) {
          background: #fff0bc;
          border-color: #dfc572;
        }

        @media (pointer: coarse) {
          .gp .gp-bubble {
            padding-right: 82px;
          }

          .gp .gp-message-reaction {
            right: 41px;
            width: 32px;
            height: 32px;
            opacity: 1;
            pointer-events: auto;
          }

          .gp .gp-reaction-picker > button {
            width: 36px;
            height: 36px;
          }
        }         

        /* Compact Chat-style controls and responsive message layout. */
        .gp .gp-tabs {
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
          padding: 12px 10px;
        }
        .gp .gp-tabs > button {
          flex: 0 0 auto;
          width: auto;
          min-width: 44px;
          min-height: 32px;
          height: auto;
          padding: 7px 12px;
          font-size: 11px;
          line-height: 1.25;
          white-space: nowrap;
        }
        .gp .gp-message { position: relative; min-width: 0; max-width: min(82%, 520px); margin-bottom: 12px; }
        .gp .gp-message-body { position: relative; width: fit-content; max-width: 100%; min-width: 0; }
        .gp .gp-bubble { position: relative; min-width: 100px; min-height: 0; max-width: 100%; padding: 9px 12px 7px; border-radius: 13px; overflow: visible; }
        .gp .gp-message.is-own .gp-bubble { background: #fff0bc; border-color: #fff0bc; border-bottom-right-radius: 5px; }
        .gp .gp-message.is-own .gp-bubble::after { content: ""; position: absolute; right: -7px; bottom: 9px; width: 8px; height: 13px; background: #fff0bc; clip-path: polygon(0 0, 100% 50%, 0 100%); pointer-events: none; }
        .gp .gp-bubble-author { margin: 0 25px 4px 0; color: #514931; font-size: 12px; font-weight: 500; line-height: 1.4; overflow-wrap: anywhere; }
        .gp .gp-message:not(.is-own) .gp-bubble-author { color: #454c57; }
        .gp .gp-message-text { min-width: 0; font-size: 13px; line-height: 1.45; overflow-wrap: anywhere; white-space: pre-wrap; }
        .gp .gp-message-time { justify-content: flex-end; gap: 4px; margin-top: 5px; font-size: 10px; white-space: nowrap; }
        .gp .gp-message-more { position: absolute; inset: 4px 4px auto auto; display: inline-flex; align-items: center; justify-content: center; width: 24px; height: 24px; min-width: 24px; margin: 0; padding: 0; border: 0; border-radius: 6px; background: #fffdf8; color: #494438; cursor: pointer; opacity: 1; }
        .gp .gp-quoted { margin: 5px 0 7px; padding: 7px 9px; border: 1px solid #e8dbac; border-radius: 7px; background: #fff8df; color: #59523f; font-size: 12px; overflow-wrap: anywhere; }
        .gp .gp-message-footer { position: relative; display: flex; align-items: center; justify-content: flex-start; flex-wrap: wrap; gap: 4px; width: 100%; min-height: 26px; margin-top: 2px; }
        .gp .gp-message-reaction { appearance: none; position: static; inset: auto; display: inline-flex; flex: 0 0 26px; align-items: center; justify-content: center; width: 26px; height: 26px; min-width: 0; min-height: 0; margin: 0; padding: 3px; border: 0; border-radius: 6px; background: transparent; box-shadow: none; color: #68665f; cursor: pointer; opacity: 1; transform: none; }
        .gp .gp-message-reaction svg { width: 15px; height: 15px; }
        .gp .gp-message-reaction:hover { background: #f3eee2; }
        .gp .gp-reactions { display: flex; flex-wrap: wrap; gap: 4px; margin: 0; }
        .gp .gp-reactions > button { min-height: 26px; padding: 2px 9px; border: 1px solid #e8e1d2; border-radius: 999px; background: #fffdf7; color: #403a30; font-size: 12px; cursor: pointer; }
        .gp .gp-reaction-picker { position: absolute; z-index: 40; top: auto; bottom: 30px; left: 0; right: auto; display: grid; grid-template-columns: repeat(5, 32px); gap: 4px; width: max-content; max-width: calc(100vw - 40px); padding: 8px; border: 1px solid #e8e0d0; border-radius: 10px; background: #fffdf8; box-shadow: 0 8px 24px rgba(40, 32, 12, .12); }
        .gp .gp-message.is-own .gp-reaction-picker { left: auto; right: 0; }
        .gp .gp-reaction-picker > button { display: grid; place-items: center; width: 32px; height: 32px; margin: 0; padding: 3px; border: 0; border-radius: 6px; background: transparent; font-size: 20px; cursor: pointer; }
        .gp .gp-reaction-picker > button:hover, .gp .gp-emoji > button:hover { background: #fff0bd; }
        .gp .gp-message-entry:not(:first-child):last-child .gp-reaction-picker { top: auto; bottom: 30px; }
        .gp .gp-message-menu { top: 32px; right: auto; left: 0; min-width: 170px; max-width: calc(100vw - 48px); }
        .gp .gp-message.is-own .gp-message-menu { left: auto; right: 0; }
        .gp .gp-menu > button { display: flex; align-items: center; gap: 8px; }
        .gp .gp-emoji { display: grid; grid-template-columns: repeat(5, 32px); gap: 4px; width: max-content; max-width: calc(100vw - 32px); padding: 8px; }
        .gp .gp-emoji > button { width: 32px; height: 32px; padding: 3px; font-size: 20px; }
        .gp .gp-message-info { min-width: 0; }
        .gp .gp-info-preview { padding: 12px; border-radius: 10px; background: #fff0bc; overflow-wrap: anywhere; }
        .gp .gp-info-preview strong { font-size: 12px; }
        .gp .gp-info-preview p { margin: 5px 0 8px; white-space: pre-wrap; }
        .gp .gp-info-preview time, .gp .gp-viewers time { display: block; color: #625d50; font-size: 11px; }
        .gp .gp-info-heading { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-top: 20px; }
        .gp .gp-info-heading h3 { display: flex; align-items: center; gap: 6px; margin: 0; font-size: 14px; }
        .gp .gp-info-heading button { padding: 7px 10px; border: 1px solid #e8e1d2; border-radius: 7px; background: #fffdf7; cursor: pointer; }
        .gp .gp-viewers { list-style: none; margin: 8px 0 0; padding: 0; }
        .gp .gp-viewers li { display: flex; align-items: center; gap: 10px; padding: 12px 0; border-bottom: 1px solid #eee7d9; }
        .gp .gp-viewers li > div { flex: 1; min-width: 0; overflow-wrap: anywhere; }
        .gp .gp-viewers strong { display: block; font-size: 13px; margin-bottom: 4px; }
        .gp .gp-read { color: #16739a; }
        .gp button:focus-visible { outline: 2px solid #866409; outline-offset: 3px; }
        .gp button:disabled { cursor: default; opacity: .55; }
        @media (max-width: 640px) {
          .gp .gp-tabs { gap: 8px; padding: 12px; }
          .gp .gp-tabs > button { min-height: 40px; padding: 8px 13px; font-size: 12px; }
          .gp .gp-message { max-width: calc(100% - 24px); margin-bottom: 12px; }
          .gp .gp-message-more { width: 30px; height: 30px; }
          .gp .gp-bubble-author { margin-right: 28px; min-height: 24px; }
          .gp .gp-message-footer { min-height: 40px; }
          .gp .gp-message-reaction { flex-basis: 40px; width: 40px; height: 40px; justify-content: flex-start; padding-left: 3px; }
          .gp .gp-reactions > button { min-height: 36px; }
          .gp .gp-reaction-picker { grid-template-columns: repeat(5, 40px); bottom: 44px; }
          .gp .gp-reaction-picker > button { width: 40px; height: 40px; }
          .gp .gp-message-entry:not(:first-child):last-child .gp-reaction-picker { bottom: 44px; }
          .gp .gp-message-menu { top: 37px; }
          .gp .gp-menu > button { min-height: 40px; }
          .gp .gp-emoji { grid-template-columns: repeat(5, 40px); }
          .gp .gp-emoji > button { width: 40px; height: 40px; }
          .gp .gp-modal { width: min(100%, 460px); max-height: calc(100dvh - 32px); overflow-y: auto; }
        }

        /* Four filters always share one line, including the compact inbox. */
        .gp .gp-tabs {
          display: grid;
          grid-template-columns: minmax(36px, .65fr) minmax(0, 1fr) minmax(0, 1fr) minmax(0, 1.2fr);
          flex-wrap: nowrap;
          gap: 5px;
          padding: 12px 9px;
          overflow: visible;
        }
        .gp .gp-tabs > button {
          width: 100%;
          min-width: 0;
          height: 32px;
          min-height: 32px;
          padding: 6px 4px;
          font-size: 11px;
          line-height: 1.2;
          letter-spacing: 0;
          white-space: nowrap;
          overflow: visible;
        }
        .gp .gp-inbox { min-width: 0; }
        .gp .gp-selection-bar { margin: 0 9px 8px; padding: 9px; border-radius: 8px; background: #f6f1e4; font-size: 12px; }
        .gp .gp-selection-bar > div:first-child { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
        .gp .gp-selection-bar p { margin: 7px 0; color: #625d50; line-height: 1.4; }
        .gp .gp-selection-bar button { border: 0; padding: 5px 6px; border-radius: 6px; background: #fffdf8; color: #34312a; font-size: 11px; cursor: pointer; }
        .gp .gp-selection-actions { display: flex; flex-wrap: wrap; gap: 5px; }
        .gp .gp-selection-actions button { display: flex; align-items: center; gap: 4px; }
        .gp .gp-select-check { display: grid; place-items: center; flex: 0 0 18px; width: 18px; height: 18px; border: 1px solid #b9b09c; border-radius: 5px; background: #fffdf8; }
        .gp .gp-select-check.is-checked { background: #f8c600; border-color: #ba9200; color: #27251c; }
        .gp .gp-group-row.is-checked { background: #fff3c8; }
        .gp .gp-group-row:has(.gp-select-check) { gap: 7px; }
        .gp .gp-group-row:has(.gp-select-check) .gp-avatar { width: 32px; height: 32px; }
        .gp .gp-group-row:has(.gp-select-check) .gp-row-trailing { max-width: 54px; font-size: 9px; }
        .gp .gp-bulk-confirm p { margin: 0 0 12px; font-size: 13px; line-height: 1.6; }
        .gp .gp-bulk-confirm-actions { display: flex; justify-content: flex-end; align-items: center; gap: 8px; margin-top: 18px; }
        .gp .gp-bulk-confirm-actions > button { min-height: 36px; padding: 8px 14px; border: 1px solid #e5ddcb; border-radius: 8px; cursor: pointer; }

        /* Portaled menus cannot inherit the old timeline max-height/scrollbar. */
        .gp-floating-menu {
          position: fixed;
          z-index: 1000;
          display: flex;
          flex-direction: column;
          width: 190px;
          max-width: calc(100vw - 16px);
          height: auto;
          max-height: none;
          overflow: visible;
          box-sizing: border-box;
          padding: 6px;
          border: 1px solid #e8dfcf;
          border-radius: 11px;
          background: #fffdf8;
          color: #252b36;
          box-shadow: 0 12px 28px rgba(45, 37, 20, .14);
          font-family: inherit;
        }
        .gp-floating-menu > button {
          display: flex;
          align-items: center;
          gap: 8px;
          flex: 0 0 auto;
          width: 100%;
          min-height: 32px;
          padding: 7px 9px;
          border: 0;
          border-radius: 6px;
          background: transparent;
          color: inherit;
          font: inherit;
          font-size: 12px;
          line-height: 1.35;
          text-align: left;
          cursor: pointer;
        }
        .gp-floating-menu > button svg { flex-shrink: 0; width: 15px; height: 15px; }
        .gp-floating-menu > button:hover:not(:disabled), .gp-floating-menu > button:focus-visible { background: #fff0bd; outline: none; }
        .gp-floating-menu > button:disabled { opacity: .45; cursor: default; }
        .gp-floating-menu > button.gp-danger { color: #b32c21; }
        @media (max-height: 360px) {
          .gp-floating-menu { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); width: 340px; }
          .gp-floating-menu > button { min-height: 29px; padding: 5px 7px; font-size: 11px; }
        }
        @media (max-width: 640px) {
          .gp .gp-tabs { gap: 6px; padding: 12px 10px; }
          .gp .gp-tabs > button { min-height: 38px; height: 38px; padding: 7px 5px; font-size: 12px; }
          .gp .gp-selection-bar button { min-height: 36px; }
          .gp-floating-menu > button { min-height: 36px; }
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
                .gp .gp-message .gp-message-more {
          opacity: 0;
          pointer-events: none;
          background: transparent;
          border: 0;
          box-shadow: none;
        }

        .gp .gp-message:hover .gp-message-more,
        .gp .gp-message:focus-within .gp-message-more,
        .gp .gp-message .gp-message-more[aria-expanded="true"] {
          opacity: 1;
          pointer-events: auto;
          background: transparent;
        }

        @media (hover: none) {
          .gp .gp-message .gp-message-more {
            opacity: 1;
            pointer-events: auto;
            background: transparent;
          }
        }
        .gp .gp-clear-notice {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 4px;
          margin: 18px auto;
          padding: 8px 12px;
          color: #686458;
          font-size: 12px;
          line-height: 1.5;
          text-align: center;
        }

        .gp .gp-clear-notice small {
          font-size: 11px;
          color: #777267;
        }

        .gp .gp-unread {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          min-width: 20px;
          height: 20px;
          padding: 0 5px;
          border: 0;
          border-radius: 999px;
          background: #ffd000;
          color: #242416;
          font-size: 11px;
          font-weight: 600;
          line-height: 1;
        }

        .gp .gp-group-avatar-stack { position: relative; background: transparent; isolation: isolate; overflow: visible; }
        .gp .gp-avatar-part { position: absolute; display: grid; place-items: center; width: 70%; height: 70%; overflow: hidden; border: 2px solid #fffdf7; border-radius: 50%; background: #ebe5d6; color: #514b42; font-size: .65em; font-weight: 600; }
        .gp .gp-avatar-part-0 { left: 0; top: 0; z-index: 1; }
        .gp .gp-avatar-part-1 { right: 0; bottom: 0; z-index: 2; }
        .gp .gp-avatar-part-2 { left: 0; bottom: 0; z-index: 3; width: 58%; height: 58%; }
        .gp .gp-avatar-part img { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }
        .gp .gp-avatar-settings { margin: 0 0 18px; padding: 12px; border: 1px solid #e8e0cf; border-radius: 10px; }
        .gp .gp-avatar-settings legend { padding: 0 5px; font-size: 13px; font-weight: 600; }
        .gp .gp-avatar-preview { display: flex; align-items: center; gap: 14px; }
        .gp .gp-avatar-preview > .gp-avatar { flex: 0 0 64px; width: 64px; height: 64px; }
        .gp .gp-avatar-preview > div { display: flex; flex-wrap: wrap; gap: 7px; }
        .gp .gp-avatar-preview button { min-height: 34px; padding: 6px 10px; border: 1px solid #e3d9c4; border-radius: 7px; background: #fffdf8; color: #342f25; cursor: pointer; }
        .gp .gp-avatar-preview small { flex: 0 0 100%; color: #686258; font-size: 11px; }
        .gp .gp-avatar-modes { display: flex; flex-direction: column; gap: 9px; margin-top: 16px; }
        .gp .gp-avatar-modes label { display: flex; align-items: center; gap: 7px; font-size: 12px; line-height: 1.4; }
        .gp .gp-avatar-modes input { accent-color: #a57900; }
        .gp .gp-avatar-help { margin: 12px 0 0; color: #686258; font-size: 11px; line-height: 1.5; }
        .gp .gp-reaction-tabs { display: flex; flex-wrap: wrap; gap: 6px; padding-bottom: 12px; border-bottom: 1px solid #e9e2d4; }
        .gp .gp-reaction-tabs button { min-height: 34px; padding: 5px 12px; border: 1px solid #e5dcc8; border-radius: 999px; background: transparent; color: #403a30; font-size: 13px; cursor: pointer; }
        .gp .gp-reaction-tabs button[aria-pressed="true"] { background: #fff0bc; border-color: #d7b647; }
        .gp .gp-reaction-people { padding-top: 4px; }
        .gp .gp-reaction-person { display: flex; align-items: center; gap: 12px; width: 100%; padding: 12px 0; border: 0; border-bottom: 1px solid #eee7d9; border-radius: 0; background: transparent; color: #292b2e; text-align: left; }
        .gp button.gp-reaction-person { cursor: pointer; }
        .gp button.gp-reaction-person:hover { background: #faf4e6; }
        .gp .gp-reaction-person > .gp-avatar { flex: 0 0 40px; width: 40px; height: 40px; }
        .gp .gp-reaction-person-copy { flex: 1; min-width: 0; overflow-wrap: anywhere; }
        .gp .gp-reaction-person-copy strong { display: block; margin-bottom: 3px; font-size: 13px; font-weight: 600; }
        .gp .gp-reaction-person-copy small { color: #686258; font-size: 11px; }
        .gp .gp-reaction-person-emoji { flex-shrink: 0; font-size: 25px; }
        @media (max-width: 640px) {
          .gp .gp-avatar-preview { gap: 10px; }
          .gp .gp-avatar-preview button { min-height: 40px; }
          .gp .gp-reaction-tabs button { min-height: 40px; }
          .gp .gp-reaction-person { min-height: 64px; }
        }
        .gp .gp-message-body {
          min-width: 0;
          max-width: 100%;
        }

        .gp .gp-bubble .gp-message-file {
          display: flex;
          align-items: center;
          gap: 10px;
          width: 280px;
          max-width: 100%;
          min-width: 0;
          margin: 8px 0 4px;
          padding: 11px 12px;
          border: 1px solid rgba(95, 103, 119, 0.18);
          border-radius: 9px;
          background: rgba(255, 255, 255, 0.7);
          color: #172033;
          text-align: left;
          box-sizing: border-box;
        }

        .gp .gp-message-file .gp-file-icon {
          display: flex;
          align-items: center;
          justify-content: center;
          flex: 0 0 28px;
          width: 28px;
          height: 32px;
          padding: 0;
          border-radius: 0;
          background: transparent;
          color: #26334b;
        }

        .gp .gp-message-file .gp-file-copy {
          display: flex;
          flex: 1 1 0%;
          flex-direction: column;
          gap: 3px;
          min-width: 0;
          overflow: hidden;
        }

        .gp .gp-message-file .gp-file-copy strong {
          display: block;
          max-width: 100%;
          overflow: hidden;
          color: #172033;
          font-size: 12px;
          font-weight: 600;
          line-height: 1.4;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .gp .gp-message-file .gp-file-copy small {
          color: #7d8796;
          font-size: 11px;
          line-height: 1.4;
        }

        .gp .gp-message-file-download {
          flex: 0 0 auto;
        }

        @media (max-width: 640px) {
          .gp .gp-bubble .gp-message-file {
            width: 240px;
            gap: 8px;
            padding: 10px;
          }
        }
        .gp .gp-message .gp-bubble.gp-bubble--singleEmoji {
          min-width: 0;
          padding: 4px 8px;
          border-color: transparent;
          background: transparent;
          box-shadow: none;
        }

        .gp .gp-bubble.gp-bubble--singleEmoji::before,
        .gp .gp-bubble.gp-bubble--singleEmoji::after {
          display: none;
        }

        .gp .gp-bubble.gp-bubble--singleEmoji .gp-message-text {
          margin: 0;
          padding: 4px 0;
          font-family: "Segoe UI Emoji", "Apple Color Emoji", sans-serif;
          font-size: 56px;
          line-height: 1.2;
          overflow: visible;
        }

        .gp .gp-message.is-own .gp-bubble--singleEmoji .gp-bubble-author {
          display: none;
        }
        .gp .gp-message .gp-bubble .gp-bubble-author {
          display: block;
          visibility: visible;
          opacity: 1;
          max-width: 160px;
          margin: 0 24px 5px 0;
          overflow: hidden;
          color: #686258;
          font-size: 11px;
          font-weight: 600;
          line-height: 1.4;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .gp .gp-bubble > button.gp-quoted {
          display: block;
          width: 100%;
          margin: 5px 0 7px;
          padding: 7px 9px;
          border: 0;
          border-left: 3px solid #c7a52f;
          border-radius: 6px;
          background: rgba(170, 145, 65, 0.1);
          color: #59523f;
          text-align: left;
          cursor: pointer;
        }

        .gp button.gp-quoted strong,
        .gp button.gp-quoted span {
          display: block;
          font-size: 11px;
        }

        .gp button.gp-quoted strong {
          margin-bottom: 3px;
        }
      `}</style>
    </main>
  );
}

