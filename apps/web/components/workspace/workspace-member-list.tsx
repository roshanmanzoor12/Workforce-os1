"use client";

import {
  useCallback,
  useEffect,
  useState,
} from "react";

import {
  Eye,
  EyeOff,
  Loader2,
  RefreshCcw,
  ShieldBan,
  Volume2,
  VolumeX,
  UserMinus,
} from "lucide-react";

import {
  useWorkspace,
} from "@/contexts/workspace-context";

import {
  hasPermission,
} from "@/lib/workspace/access";

import {
  workspaceMembersService,
} from "@/services/workspace-members.service";

import type {
  WorkspaceMemberPublic,
} from "@/types/workspace-members";

import {
  MemberRoleSelect,
} from "@/components/workspace/member-role-select";


interface WorkspaceMemberListProps {
  workspaceId?:
    string;
}


export function WorkspaceMemberList({
  workspaceId: workspaceIdProp,
}: WorkspaceMemberListProps) {
  const {
    workspaceId:
      contextWorkspaceId,

    effectivePermissions,

    effectiveNavigationView,
  } =
    useWorkspace();


  const workspaceId =
    workspaceIdProp ??
    contextWorkspaceId;


  const [
    members,
    setMembers,
  ] =
    useState<
      WorkspaceMemberPublic[]
    >([]);


  const [
    loading,
    setLoading,
  ] =
    useState(
      true,
    );


  const [
    error,
    setError,
  ] =
    useState<
      string | null
    >(null);


  const [
    actionKey,
    setActionKey,
  ] =
    useState<
      string | null
    >(null);


  const canAssignRole =
    hasPermission(
      effectivePermissions,
      "roles.assign",
      effectiveNavigationView,
    );


  const canKick =
    hasPermission(
      effectivePermissions,
      "members.kick",
      effectiveNavigationView,
    );


  const canBan =
    hasPermission(
      effectivePermissions,
      "members.ban",
      effectiveNavigationView,
    );


  const canMute =
    hasPermission(
      effectivePermissions,
      "members.mute",
      effectiveNavigationView,
    );


  const canDeafen =
    hasPermission(
      effectivePermissions,
      "members.deafen",
      effectiveNavigationView,
    );


  const canHide =
    hasPermission(
      effectivePermissions,
      "members.hide",
      effectiveNavigationView,
    );


  const load =
    useCallback(
      async () => {
        if (
          !workspaceId
        ) {
          setMembers(
            [],
          );

          setLoading(
            false,
          );

          return;
        }


        try {
          setLoading(
            true,
          );

          setError(
            null,
          );


          const response =
            await workspaceMembersService.list(
              workspaceId,
            );


          setMembers(
            response.members ??
              [],
          );
        } catch (
          cause
        ) {
          setError(
            cause instanceof Error
              ? cause.message
              : "Unable to load workspace members.",
          );
        } finally {
          setLoading(
            false,
          );
        }
      },
      [
        workspaceId,
      ],
    );


  useEffect(() => {
    void load();
  }, [
    load,
  ]);


  function updateMember(
    updated:
      WorkspaceMemberPublic,
  ) {
    setMembers(
      (
        previous,
      ) =>
        previous.map(
          (
            member,
          ) =>
            member.membership_id ===
            updated.membership_id
              ? updated
              : member,
        ),
    );
  }


  async function moderate(
    member:
      WorkspaceMemberPublic,

    action:
      "kick" |
      "ban" |
      "mute" |
      "deafen",
  ) {
    if (
      !workspaceId
    ) {
      return;
    }


    const label =
      action
        .charAt(
          0,
        )
        .toUpperCase() +
      action.slice(
        1,
      );


    if (
      action ===
        "kick" ||
      action ===
        "ban"
    ) {
      const confirmed =
        window.confirm(
          `${label} ${member.username || member.email}?`,
        );


      if (
        !confirmed
      ) {
        return;
      }
    }


    const key =
      `${action}:${member.membership_id}`;


    try {
      setActionKey(
        key,
      );

      setError(
        null,
      );


      let response;


      if (
        action ===
        "kick"
      ) {
        response =
          await workspaceMembersService.kick(
            workspaceId,
            member.membership_id,
          );
      } else if (
        action ===
        "ban"
      ) {
        response =
          await workspaceMembersService.ban(
            workspaceId,
            member.membership_id,
          );
      } else if (
        action ===
        "mute"
      ) {
        response =
          await workspaceMembersService.mute(
            workspaceId,
            member.membership_id,
          );
      } else {
        response =
          await workspaceMembersService.deafen(
            workspaceId,
            member.membership_id,
          );
      }


      setMembers(
        (
          previous,
        ) =>
          previous.map(
            (
              item,
            ) =>
              item.membership_id ===
              member.membership_id
                ? {
                    ...item,

                    moderation:
                      response.moderation,
                  }
                : item,
          ),
      );


      if (
        action ===
          "kick" ||
        action ===
          "ban"
      ) {
        await load();
      }
    } catch (
      cause
    ) {
      setError(
        cause instanceof Error
          ? cause.message
          : `Unable to ${action} member.`,
      );
    } finally {
      setActionKey(
        null,
      );
    }
  }


  async function toggleHidden(
    member:
      WorkspaceMemberPublic,
  ) {
    if (
      !workspaceId
    ) {
      return;
    }


    const hidden =
      !member.moderation
        .is_hidden;


    const key =
      `hidden:${member.membership_id}`;


    try {
      setActionKey(
        key,
      );

      const response =
        await workspaceMembersService.updateVisibility(
          workspaceId,
          member.membership_id,
          hidden,
        );


      setMembers(
        (
          previous,
        ) =>
          previous.map(
            (
              item,
            ) =>
              item.membership_id ===
              member.membership_id
                ? {
                    ...item,

                    moderation:
                      response.moderation,
                  }
                : item,
          ),
      );
    } catch (
      cause
    ) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Unable to update member visibility.",
      );
    } finally {
      setActionKey(
        null,
      );
    }
  }


  if (
    loading
  ) {
    return (
      <section className="panel">
        <div
          className="panel-body"
          style={{
            padding:
              20,

            display:
              "flex",

            alignItems:
              "center",

            gap:
              8,
          }}
        >
          <Loader2
            size={
              15
            }
          />

          <span className="text-label">
            Loading members...
          </span>
        </div>
      </section>
    );
  }


  return (
    <section className="panel">
      <div
        className="panel-body"
        style={{
          padding:
            16,
        }}
      >
        <div
          style={{
            display:
              "flex",

            alignItems:
              "center",

            justifyContent:
              "space-between",

            gap:
              12,

            marginBottom:
              12,
          }}
        >
          <div>
            <h2>
              Workspace Members
            </h2>

            <p className="text-label">
              Manage workspace roles and member moderation.
            </p>
          </div>


          <button
            type="button"
            onClick={() =>
              void load()
            }
            style={{
              display:
                "inline-flex",

              alignItems:
                "center",

              gap:
                6,

              padding:
                "7px 10px",

              border:
                "1px solid var(--color-border)",

              borderRadius:
                7,

              background:
                "#fff",

              cursor:
                "pointer",
            }}
          >
            <RefreshCcw
              size={
                13
              }
            />

            Refresh
          </button>
        </div>


        {error ? (
          <div
            style={{
              marginBottom:
                12,

              padding:
                10,

              border:
                "1px solid #efc5c5",

              borderRadius:
                7,

              background:
                "#fff5f5",

              color:
                "#a32b2b",

              fontSize:
                10,
            }}
          >
            {error}
          </div>
        ) : null}


        {members.length ===
        0 ? (
          <div
            className="text-label"
            style={{
              padding:
                24,

              textAlign:
                "center",
            }}
          >
            No workspace members found.
          </div>
        ) : (
          <div
            style={{
              overflowX:
                "auto",
            }}
          >
            <table
              style={{
                width:
                  "100%",

                borderCollapse:
                  "collapse",
              }}
            >
              <thead>
                <tr>
                  <th style={headStyle}>
                    Member
                  </th>

                  <th style={headStyle}>
                    Role
                  </th>

                  <th style={headStyle}>
                    Status
                  </th>

                  <th style={headStyle}>
                    Moderation
                  </th>

                  <th
                    style={{
                      ...headStyle,

                      textAlign:
                        "right",
                    }}
                  >
                    Actions
                  </th>
                </tr>
              </thead>

              <tbody>
                {members.map(
                  (
                    member,
                  ) => (
                    <tr
                      key={
                        member.membership_id
                      }
                    >
                      <td style={cellStyle}>
                        <strong
                          style={{
                            display:
                              "block",

                            fontSize:
                              11,
                          }}
                        >
                          {member.username ||
                            member.email}
                        </strong>

                        <span className="text-label">
                          {
                            member.email
                          }
                        </span>
                      </td>


                      <td style={cellStyle}>
                        <MemberRoleSelect
                          membershipId={
                            member.membership_id
                          }
                          value={
                            member.role_key
                          }
                          disabled={
                            !canAssignRole
                          }
                          onSaved={(
                            nextRole,
                          ) => {
                            updateMember({
                              ...member,

                              role_key:
                                nextRole,
                            });
                          }}
                        />
                      </td>


                      <td style={cellStyle}>
                        <span
                          style={{
                            fontSize:
                              10,
                          }}
                        >
                          {
                            member.status
                          }
                        </span>
                      </td>


                      <td style={cellStyle}>
                        <div
                          style={{
                            display:
                              "flex",

                            flexWrap:
                              "wrap",

                            gap:
                              5,
                          }}
                        >
                          {member.moderation
                            .is_banned ? (
                            <Badge>
                              Banned
                            </Badge>
                          ) : null}

                          {member.moderation
                            .is_muted ? (
                            <Badge>
                              Muted
                            </Badge>
                          ) : null}

                          {member.moderation
                            .is_deafened ? (
                            <Badge>
                              Deafened
                            </Badge>
                          ) : null}

                          {member.moderation
                            .is_hidden ? (
                            <Badge>
                              Hidden
                            </Badge>
                          ) : null}

                          {!member.moderation
                            .is_banned &&
                          !member.moderation
                            .is_muted &&
                          !member.moderation
                            .is_deafened &&
                          !member.moderation
                            .is_hidden ? (
                            <span className="text-label">
                              Normal
                            </span>
                          ) : null}
                        </div>
                      </td>


                      <td
                        style={{
                          ...cellStyle,

                          textAlign:
                            "right",
                        }}
                      >
                        <div
                          style={{
                            display:
                              "inline-flex",

                            alignItems:
                              "center",

                            gap:
                              5,

                            flexWrap:
                              "wrap",

                            justifyContent:
                              "flex-end",
                          }}
                        >
                          {canKick ? (
                            <ActionButton
                              title="Kick"
                              disabled={
                                actionKey ===
                                `kick:${member.membership_id}`
                              }
                              onClick={() =>
                                void moderate(
                                  member,
                                  "kick",
                                )
                              }
                            >
                              <UserMinus
                                size={
                                  13
                                }
                              />
                            </ActionButton>
                          ) : null}


                          {canBan ? (
                            <ActionButton
                              title="Ban"
                              disabled={
                                actionKey ===
                                `ban:${member.membership_id}`
                              }
                              onClick={() =>
                                void moderate(
                                  member,
                                  "ban",
                                )
                              }
                            >
                              <ShieldBan
                                size={
                                  13
                                }
                              />
                            </ActionButton>
                          ) : null}


                          {canMute ? (
                            <ActionButton
                              title="Mute"
                              disabled={
                                actionKey ===
                                `mute:${member.membership_id}`
                              }
                              onClick={() =>
                                void moderate(
                                  member,
                                  "mute",
                                )
                              }
                            >
                              <VolumeX
                                size={
                                  13
                                }
                              />
                            </ActionButton>
                          ) : null}


                          {canDeafen ? (
                            <ActionButton
                              title="Deafen"
                              disabled={
                                actionKey ===
                                `deafen:${member.membership_id}`
                              }
                              onClick={() =>
                                void moderate(
                                  member,
                                  "deafen",
                                )
                              }
                            >
                              <Volume2
                                size={
                                  13
                                }
                              />
                            </ActionButton>
                          ) : null}


                          {canHide ? (
                            <ActionButton
                              title={
                                member
                                  .moderation
                                  .is_hidden
                                  ? "Show"
                                  : "Hide"
                              }
                              disabled={
                                actionKey ===
                                `hidden:${member.membership_id}`
                              }
                              onClick={() =>
                                void toggleHidden(
                                  member,
                                )
                              }
                            >
                              {member
                                .moderation
                                .is_hidden ? (
                                <Eye
                                  size={
                                    13
                                  }
                                />
                              ) : (
                                <EyeOff
                                  size={
                                    13
                                  }
                                />
                              )}
                            </ActionButton>
                          ) : null}
                        </div>
                      </td>
                    </tr>
                  ),
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </section>
  );
}


function Badge({
  children,
}: {
  children:
    React.ReactNode;
}) {
  return (
    <span
      style={{
        padding:
          "3px 6px",

        border:
          "1px solid var(--color-border)",

        borderRadius:
          5,

        fontSize:
          9,

        background:
          "#faf8f1",
      }}
    >
      {children}
    </span>
  );
}


function ActionButton({
  children,

  title,

  disabled,

  onClick,
}: {
  children:
    React.ReactNode;

  title:
    string;

  disabled?:
    boolean;

  onClick:
    () => void;
}) {
  return (
    <button
      type="button"
      title={
        title
      }
      disabled={
        disabled
      }
      onClick={
        onClick
      }
      style={{
        width:
          30,

        height:
          30,

        display:
          "inline-grid",

        placeItems:
          "center",

        border:
          "1px solid var(--color-border)",

        borderRadius:
          6,

        background:
          "#fff",

        cursor:
          disabled
            ? "not-allowed"
            : "pointer",

        opacity:
          disabled
            ? 0.55
            : 1,
      }}
    >
      {children}
    </button>
  );
}


const headStyle:
  React.CSSProperties = {
    padding:
      "9px 8px",

    borderBottom:
      "1px solid var(--color-border)",

    color:
      "#777b80",

    fontSize:
      9,

    fontWeight:
      600,

    textAlign:
      "left",
  };


const cellStyle:
  React.CSSProperties = {
    padding:
      "10px 8px",

    borderBottom:
      "1px solid var(--color-border)",

    verticalAlign:
      "middle",
  };