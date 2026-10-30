"use client";

import {
  useEffect,
  useId,
  useMemo,
  useRef,
  useState,
} from "react";

import type {
  LucideIcon,
} from "lucide-react";

import Link from "next/link";

import {
  Activity,
  BriefcaseBusiness,
  Building2,
  CalendarDays,
  Check,
  ChevronDown,
  CircleHelp,
  CreditCard,
  Home,
  MessageSquareMore,
  Monitor,
  NotebookPen,
  Phone,
  Plus,
  Search,
  Settings,
  ShieldCheck,
  Sparkles,
  Target,
  UserRound,
  UserRoundCog,
  Users,
  UsersRound,
} from "lucide-react";

import {
  usePathname,
  useRouter,
} from "next/navigation";

import {
  UserAvatar,
} from "@/components/account/user-avatar";

import {
  useChatInbox,
} from "@/components/chat/chat-live-sync";

import {
  useWorkspace,
} from "@/contexts/workspace-context";

import {
  getWorkspaceNavigation,
} from "@/lib/workspace/navigation";
import { hasAnyPermission } from "@/lib/workspace/access";

import {
  getWorkspaceTemplate,
} from "@/lib/workspace/templates";

import {
  socialChatService,
} from "@/services/social-chat.service";

import type {
  WorkspaceNavigationGroup,
  WorkspaceNavigationItem,
} from "@/lib/workspace/navigation";

import { workspaceLogoSrc } from "@/lib/workspace/logo-url";

import styles from "./app-sidebar.module.css";


interface AppSidebarProps {
  workspaceName?: string | null;
}


interface AppSidebarProps {
  workspaceName?: string | null;
}


interface PersonalNavigationItem {
  key: string;
  label: string;
  href: string;
  icon: LucideIcon;
}


const personalNavigation: PersonalNavigationItem[] = [
  {
    key: "home",
    label: "Home",
    href: "/home",
    icon: Home,
  },
  {
    key: "profile",
    label: "Profile",
    href: "/settings",
    icon: UserRound,
  },
  {
    key: "friends",
    label: "Friends",
    href: "/friends",
    icon: Users,
  },
  {
    key: "messages",
    label: "Messages",
    href: "/messages",
    icon: MessageSquareMore,
  },
  {
    key: "groups",
    label: "Groups",
    href: "/groups",
    icon: UsersRound,
  },
  {
    key: "calls",
    label: "Personal Calls",
    href: "/calls",
    icon: Phone,
  },
  {
    key: "notes",
    label: "Notes",
    href: "/notes",
    icon: NotebookPen,
  },
  {
    key: "goals",
    label: "Goals",
    href: "/goals",
    icon: Target,
  },
  {
    key: "ai",
    label: "Personal AI",
    href: "/ai",
    icon: Sparkles,
  },
  {
    key: "billing",
    label: "Billing",
    href: "/billing",
    icon: CreditCard,
  },
  {
    key: "activities",
    label: "Activities",
    href: "/activities",
    icon: Activity,
  },
  {
    key: "settings",
    label: "Settings",
    href: "/settings/account",
    icon: Settings,
  },
];


const groupOrder: WorkspaceNavigationGroup[] = [
  "organization",
  "people",
  "communication",
  "work",
  "finance",
  "monitoring",
  "administration",
];


const groupIcons: Record<
  WorkspaceNavigationGroup,
  LucideIcon
> = {
  organization: ShieldCheck,
  people: UserRoundCog,
  communication: MessageSquareMore,
  work: BriefcaseBusiness,
  finance: CreditCard,
  monitoring: Monitor,
  administration: Settings,
};


function isActiveRoute(
  pathname: string,
  href: string,
): boolean {
  return (
    pathname === href ||
    pathname.startsWith(`${href}/`)
  );
}


function getInitials(
  value: string,
): string {
  const parts = value
    .trim()
    .split(/\s+/)
    .filter(Boolean);

  const first =
    parts[0] ?? "";

  const second =
    parts[1] ?? "";

  if (!first) {
    return "W";
  }

  if (!second) {
    return first
      .slice(0, 2)
      .toUpperCase();
  }

  return (
    first.charAt(0) +
    second.charAt(0)
  ).toUpperCase();
}


export function AppSidebar({
  workspaceName,
}: AppSidebarProps) {
  const pathname = usePathname();
  const router = useRouter();

  const searchId = useId();
  const navigationId = useId();

  const searchRef =
    useRef<HTMLInputElement>(null);

  const [
    search,
    setSearch,
  ] = useState("");

  const [
    openGroups,
    setOpenGroups,
  ] = useState<
    Partial<
      Record<
        WorkspaceNavigationGroup,
        boolean
      >
    >
  >({
    organization: true,
    people: true,
  });

  const {
    user,
    mode,
    effectiveNavigationView,
    effectivePermissions,
    workspace,
    membership,
    subscription,
    workspaces,
    workspaceEntitlements,
    canCreateWorkspace,
    switchWorkspace,
    enterPersonalMode,
  } = useWorkspace();

  const template =
    getWorkspaceTemplate(
      workspace?.workspace_type,
    );

  const liveInbox = useChatInbox(
    mode === "personal"
      ? user?.id
      : undefined,
  );

  const inboxKey = (
    liveInbox ?? []
  )
    .map(
      (item) =>
        item.conversation_id,
    )
    .sort()
    .join(",");

  const [
    conversationTypes,
    setConversationTypes,
  ] = useState<{
    owner: string;
    types: Record<string, string>;
  } | null>(null);

  useEffect(() => {
    const owner = user?.id;

    if (
      mode !== "personal" ||
      !owner ||
      !inboxKey
    ) {
      setConversationTypes(null);
      return;
    }

const ownerId: string = owner;

    let stopped = false;

    async function loadTypes() {
      try {
        const conversations =
          await socialChatService
            .listConversations();

        if (stopped) {
          return;
        }

        setConversationTypes({
          owner: ownerId,
          types: Object.fromEntries(
            conversations.map(
              (conversation) => [
                conversation.id,
                conversation.conversation_type,
              ],
            ),
          ),
        });
      } catch {
        // The next focus or inbox change retries the request.
      }
    }

    void loadTypes();

    function refresh() {
      void loadTypes();
    }

    window.addEventListener(
      "focus",
      refresh,
    );

    return () => {
      stopped = true;

      window.removeEventListener(
        "focus",
        refresh,
      );
    };
  }, [
    mode,
    user?.id,
    inboxKey,
  ]);

  const unreadMessages =
    mode === "personal" &&
    conversationTypes?.owner === user?.id &&
    Boolean(
      liveInbox?.some(
        (item) =>
          item.unread_count > 0 &&
          !item.muted &&
          conversationTypes?.types[
            item.conversation_id
          ] === "direct",
      ),
    );

  const unreadGroups =
    mode === "personal" &&
    conversationTypes?.owner === user?.id &&
    Boolean(
      liveInbox?.some(
        (item) =>
          item.unread_count > 0 &&
          !item.muted &&
          conversationTypes?.types[
            item.conversation_id
          ] === "group",
      ),
    );

  const workspaceNavigation =
    useMemo(
      () =>
        getWorkspaceNavigation(
          effectiveNavigationView,
          workspace?.workspace_type,
        ).filter((item) => {
          const roleAllows = !item.anyPermissions || hasAnyPermission(
            effectivePermissions,
            item.anyPermissions,
            effectiveNavigationView,
          );
          const planAllows = item.entitlement === "monitoring"
            ? workspaceEntitlements?.monitoring === true
            : item.entitlement === "live_screen"
              ? workspaceEntitlements?.live_screen === true
              : item.entitlement === "advanced_analytics"
                ? workspaceEntitlements?.advanced_analytics === true
                : true;
          return roleAllows && planAllows;
        }),
      [effectiveNavigationView, effectivePermissions, workspace?.workspace_type, workspaceEntitlements],
    );

  const activeWorkspaceItem =
    useMemo(
      () =>
        [
          ...workspaceNavigation,
        ]
          .sort(
            (a, b) =>
              b.href.length -
              a.href.length,
          )
          .find((item) =>
            isActiveRoute(
              pathname,
              item.href,
            ),
          ),
      [
        pathname,
        workspaceNavigation,
      ],
    );

  useEffect(() => {
    const activeGroup =
      activeWorkspaceItem?.group;

    if (!activeGroup) {
      return;
    }

    setOpenGroups(
      (current) => ({
        ...current,
        [activeGroup]: true,
      }),
    );
  }, [
    activeWorkspaceItem?.group,
  ]);

  const normalizedSearch =
    search.trim().toLowerCase();

  const workspaceItems =
    workspaceNavigation.filter(
      (item) =>
        !normalizedSearch ||
        item.label
          .toLowerCase()
          .includes(
            normalizedSearch,
          ),
    );

  const personalItems =
    personalNavigation.filter(
      (item) =>
        !normalizedSearch ||
        item.label
          .toLowerCase()
          .includes(
            normalizedSearch,
          ),
    );

  const workspaceRecord =
    workspace ??
    workspaces.find(
      (item) =>
        item.membership.status ===
        "active",
    )?.workspace ??
    null;

  const currentWorkspaceName =
    workspaceRecord?.name ??
    workspaceName ??
    "Workspace";

  const currentRole =
    membership?.role_key ??
    "—";

  const planCode =
    workspaceEntitlements?.plan_code ??
    subscription?.plan_code ??
    "FREE";

  const userName =
    [
      user?.first_name,
      user?.last_name,
    ]
      .filter(Boolean)
      .join(" ")
      .trim() ||
    user?.username ||
    "Account";

  const groupLabels: Record<
    WorkspaceNavigationGroup,
    string
  > = {
    organization:
      template.organization,
    people:
      template.people,
    communication:
      "Communication",
    work:
      template.work,
    finance:
      template.finance,
    monitoring:
      template.monitoring,
    administration:
      "Administration",
  };

  function renderItem(
    item: WorkspaceNavigationItem,
    nested = false,
  ) {
    const Icon = item.icon;

    const active =
      activeWorkspaceItem?.key ===
      item.key;

    return (
      <li
        key={item.key}
      >
        <Link
          href={item.href}
          className={[
            styles.link,
            nested
              ? styles.childLink
              : "",
            active
              ? styles.active
              : "",
          ]
            .filter(Boolean)
            .join(" ")}
          aria-current={
            active
              ? "page"
              : undefined
          }
        >
          <Icon
            size={nested ? 17 : 20}
            strokeWidth={1.75}
            aria-hidden="true"
          />

          <span>
            {item.label}
          </span>
        </Link>
      </li>
    );
  }

  function renderGroup(
    group: WorkspaceNavigationGroup,
  ) {
    const items =
      workspaceItems.filter(
        (item) =>
          item.group === group,
      );

    if (items.length === 0) {
      return null;
    }

    const Icon =
      groupIcons[group];

    const panelId =
      `${navigationId}-${group}`;

    const isOpen =
      Boolean(
        openGroups[group],
      ) ||
      items.some(
        (item) =>
          item.key ===
          activeWorkspaceItem?.key,
      );

    return (
      <li
        key={group}
        className={styles.group}
      >
        <button
          type="button"
          className={styles.groupButton}
          aria-expanded={isOpen}
          aria-controls={panelId}
          onClick={() =>
            setOpenGroups(
              (current) => ({
                ...current,
                [group]:
                  !current[group],
              }),
            )
          }
        >
          <Icon
            size={20}
            strokeWidth={1.75}
            aria-hidden="true"
          />

          <span>
            {groupLabels[group]}
          </span>

          <ChevronDown
            size={15}
            className={
              isOpen
                ? styles.chevronOpen
                : styles.chevron
            }
            aria-hidden="true"
          />
        </button>

        <ul
          id={panelId}
          className={styles.children}
          hidden={!isOpen}
        >
          {items.map((item) =>
            renderItem(
              item,
              true,
            ),
          )}
        </ul>
      </li>
    );
  }

  return (
    <aside
      className={styles.sidebar}
      aria-label={
        mode === "workspace"
          ? "Workspace navigation"
          : "Personal navigation"
      }
    >
      <div className={styles.brand}>
        <Link
          href={
            mode === "workspace"
              ? "/dashboard"
              : "/home"
          }
          className={styles.brandLink}
        >
          <span
            className={styles.brandMark}
            aria-hidden="true"
          >
            W
          </span>

          <span>
            Workforce OS
          </span>
        </Link>
      </div>

      {mode === "workspace" ? (
        <WorkspacePicker
          name={currentWorkspaceName}
          logoUrl={workspaceRecord?.logo_url ?? null}
          primaryColor={workspaceRecord?.primary_color ?? "#334155"}
          workspaces={workspaces}
          activeWorkspaceId={
            workspaceRecord?.id ??
            null
          }
          onPersonal={() =>
            enterPersonalMode()
          }
          onWorkspace={(id) =>
            switchWorkspace(id)
          }
          onCreate={() =>
            router.push(
              "/workspaces/new",
            )
          }
          canCreate={
            canCreateWorkspace
          }
        />
      ) : null}

      <div className={styles.search}>
        <Search
          size={16}
          strokeWidth={1.7}
          aria-hidden="true"
        />

        <input
          ref={searchRef}
          id={searchId}
          type="search"
          value={search}
          placeholder="Search menu..."
          autoComplete="off"
          onChange={(event) =>
            setSearch(
              event.target.value,
            )
          }
          onKeyDown={(event) => {
            if (
              event.key === "Escape"
            ) {
              setSearch("");
            }
          }}
        />

        <kbd>
          Ctrl K
        </kbd>
      </div>

      <nav
        className={styles.navigation}
        aria-label="Primary navigation"
      >
        {mode === "workspace" ? (
          <ul className={styles.list}>
            {workspaceItems
              .filter(
                (item) =>
                  !item.group,
              )
              .map((item) =>
                renderItem(item),
              )}

            {groupOrder.map(
              (group) =>
                renderGroup(group),
            )}
          </ul>
        ) : (
          <ul className={styles.list}>
            {personalItems.map(
              (item) => {
                const Icon =
                  item.icon;

                const active =
                  isActiveRoute(
                    pathname,
                    item.href,
                  );

                const unread =
                  (
                    item.key ===
                      "messages" &&
                    unreadMessages
                  ) ||
                  (
                    item.key ===
                      "groups" &&
                    unreadGroups
                  );

                return (
                  <li
                    key={item.key}
                  >
                    <Link
                      href={item.href}
                      className={[
                        styles.link,
                        active
                          ? styles.active
                          : "",
                      ]
                        .filter(Boolean)
                        .join(" ")}
                      aria-current={
                        active
                          ? "page"
                          : undefined
                      }
                    >
                      {item.key ===
                        "profile" &&
                      user ? (
                        <span
                          className={
                            styles.profileAvatar
                          }
                        >
                          <UserAvatar
                            userId={user.id}
                            name={userName}
                            size={20}
                          />
                        </span>
                      ) : (
                        <Icon
                          size={20}
                          strokeWidth={1.75}
                          aria-hidden="true"
                        />
                      )}

                      <span>
                        {item.label}
                      </span>

                      {unread ? (
                        <span
                          className={
                            styles.unread
                          }
                          aria-label="Unread messages"
                        />
                      ) : null}
                    </Link>
                  </li>
                );
              },
            )}
          </ul>
        )}
      </nav>

      <footer className={styles.footer}>
        <div className={styles.accountRow}>
          {user ? (
            <UserAvatar
              userId={user.id}
              name={userName}
              size={35}
            />
          ) : (
            <span
              className={styles.accountFallback}
            >
              <UserRound size={18} />
            </span>
          )}

          <div className={styles.accountCopy}>
            <strong title={userName}>
              {userName}
            </strong>

            {mode === "workspace" ? (
              <span>
                {currentRole}
              </span>
            ) : (
              <span>
                Personal account
              </span>
            )}
          </div>

          <Link
            href="/settings"
            className={styles.helpButton}
            aria-label="Account settings"
          >
            <CircleHelp
              size={17}
            />
          </Link>
        </div>

        {mode === "workspace" ? (
          <button
            type="button"
            className={styles.modeButton}
            onClick={() =>
              enterPersonalMode()
            }
          >
            <UserRound
              size={17}
            />

            Switch to Personal
          </button>
        ) : workspaceRecord ? (
          <button
            type="button"
            className={styles.modeButton}
            onClick={() =>
              switchWorkspace(
                workspaceRecord.id,
              )
            }
          >
            <Building2
              size={17}
            />

            Open Workspace
          </button>
        ) : null}

        {mode === "personal" &&
        canCreateWorkspace ? (
          <button
            type="button"
            className={styles.modeButton}
            onClick={() =>
              router.push(
                "/workspaces/new",
              )
            }
          >
            <Plus size={17} />

            Create Workspace
          </button>
        ) : null}
      </footer>
    </aside>
  );
}


function WorkspacePicker({
  name,
  logoUrl,
  primaryColor,
  workspaces,
  activeWorkspaceId,
  onPersonal,
  onWorkspace,
  onCreate,
  canCreate,
}: {
  name: string;
  logoUrl: string | null;
  primaryColor: string;
  workspaces: Array<{
    workspace: {
      id: string;
      name: string;
    };
    membership: {
      status: string;
    };
  }>;
  activeWorkspaceId: string | null;
  onPersonal: () => void;
  onWorkspace: (id: string) => void;
  onCreate: () => void;
  canCreate: boolean;
}) {
  const pickerId = useId();
  const wrapperRef =
    useRef<HTMLDivElement>(null);

  const [
    open,
    setOpen,
  ] = useState(false);

  useEffect(() => {
    if (!open) {
      return;
    }

    function closeOnOutside(
      event: PointerEvent,
    ) {
      if (
        event.target instanceof Node &&
        !wrapperRef.current?.contains(
          event.target,
        )
      ) {
        setOpen(false);
      }
    }

    document.addEventListener(
      "pointerdown",
      closeOnOutside,
    );

    return () =>
      document.removeEventListener(
        "pointerdown",
        closeOnOutside,
      );
  }, [open]);

  return (
    <div
      ref={wrapperRef}
      className={styles.picker}
    >
      <button
        type="button"
        className={styles.pickerTrigger}
        aria-expanded={open}
        aria-controls={pickerId}
        onClick={() =>
          setOpen(
            (value) => !value,
          )
        }
      >
        <span
          className={styles.workspaceMark}
          style={{ backgroundColor: primaryColor, color: "#FFFFFF", overflow: "hidden" }}
        >
          {logoUrl ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={workspaceLogoSrc(logoUrl)} alt="" style={{ width: "100%", height: "100%", objectFit: "cover" }} />
          ) : getInitials(name)}
        </span>

        <span
          className={styles.workspaceCopy}
        >
          <strong title={name}>
            {name}
          </strong>

          <small>
            Workspace
          </small>
        </span>

        <ChevronDown
          size={16}
          className={
            open
              ? styles.chevronOpen
              : styles.chevron
          }
        />
      </button>

      {open ? (
        <div
          id={pickerId}
          className={styles.pickerPanel}
        >
          <button
            type="button"
            className={styles.pickerOption}
            onClick={() => {
              setOpen(false);
              onPersonal();
            }}
          >
            <UserRound size={17} />

            <span>
              Personal
            </span>
          </button>

          <div className={styles.pickerLabel}>
            Workspaces
          </div>

          {workspaces
            .filter(
              (item) =>
                item.membership.status ===
                "active",
            )
            .map((item) => (
              <button
                key={item.workspace.id}
                type="button"
                className={[
                  styles.pickerOption,
                  item.workspace.id ===
                    activeWorkspaceId
                    ? styles.pickerSelected
                    : "",
                ]
                  .filter(Boolean)
                  .join(" ")}
                onClick={() => {
                  setOpen(false);
                  onWorkspace(
                    item.workspace.id,
                  );
                }}
              >
                <Building2 size={17} />

                <span>
                  {item.workspace.name}
                </span>

                {item.workspace.id ===
                activeWorkspaceId ? (
                  <Check size={15} />
                ) : null}
              </button>
            ))}

          {canCreate ? (
            <button
              type="button"
              className={styles.pickerCreate}
              onClick={() => {
                setOpen(false);
                onCreate();
              }}
            >
              <Plus size={17} />

              Create workspace
            </button>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
