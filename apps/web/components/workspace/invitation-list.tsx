"use client";

import {
  Check,
  Copy,
  Loader2,
  RefreshCcw,
  RotateCcw,
  XCircle,
} from "lucide-react";

import {
  useState,
} from "react";

import {
  useWorkspace,
} from "@/contexts/workspace-context";

import {
  hasPermission,
} from "@/lib/workspace/access";

import {
  buildWorkspaceInvitationLink,
} from "@/lib/workspace/invitation-link";

import {
  workspaceInvitationsService,
} from "@/services/workspace-invitations.service";

import type {
  WorkspaceInvitationPublic,
  WorkspaceInvitationSecretResponse,
} from "@/types/workspace-invitations";

import type {
  WorkspaceRolePublic,
} from "@/types/workspace-roles";


interface InvitationListProps {
  invitations:
    WorkspaceInvitationPublic[];

  roles:
    WorkspaceRolePublic[];

  onChanged?:
    () => void;
}


export function InvitationList({
  invitations,

  roles,

  onChanged,
}: InvitationListProps) {
  const {
    workspaceId,

    effectivePermissions,

    effectiveNavigationView,
  } =
    useWorkspace();


  const [
    actionKey,
    setActionKey,
  ] =
    useState<
      string | null
    >(null);


  const [
    error,
    setError,
  ] =
    useState<
      string | null
    >(null);


  const [
    latestLink,
    setLatestLink,
  ] =
    useState<
      string | null
    >(null);


  const canInvite =
    hasPermission(
      effectivePermissions,
      "members.invite",
      effectiveNavigationView,
    );


  const canManage =
    hasPermission(
      effectivePermissions,
      "members.update",
      effectiveNavigationView,
    ) ||
    hasPermission(
      effectivePermissions,
      "members.invite",
      effectiveNavigationView,
    );


  function roleName(
    roleKey:
      string,
  ) {
    return (
      roles.find(
        (
          role,
        ) =>
          role.role_key ===
          roleKey,
      )?.display_name ??
      roleKey
    );
  }


  async function resend(
    invitation:
      WorkspaceInvitationPublic,
  ) {
    if (
      !workspaceId ||
      !canInvite
    ) {
      return;
    }


    const key =
      `resend:${invitation.id}`;


    try {
      setActionKey(
        key,
      );

      setError(
        null,
      );


      const response =
        await workspaceInvitationsService.resend(
          workspaceId,
          invitation.id,
        );


      setLatestLink(
        buildWorkspaceInvitationLink(
          response.invitation_token,
        ),
      );


      onChanged?.();
    } catch (
      cause
    ) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Unable to resend invitation.",
      );
    } finally {
      setActionKey(
        null,
      );
    }
  }


  async function revoke(
    invitation:
      WorkspaceInvitationPublic,
  ) {
    if (
      !workspaceId ||
      !canManage
    ) {
      return;
    }


    const confirmed =
      window.confirm(
        `Revoke the invitation for ${invitation.email}?`,
      );


    if (
      !confirmed
    ) {
      return;
    }


    const key =
      `revoke:${invitation.id}`;


    try {
      setActionKey(
        key,
      );

      setError(
        null,
      );


      await workspaceInvitationsService.revoke(
        workspaceId,
        invitation.id,
      );


      onChanged?.();
    } catch (
      cause
    ) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Unable to revoke invitation.",
      );
    } finally {
      setActionKey(
        null,
      );
    }
  }


  async function copy(
    value:
      string,
  ) {
    await navigator.clipboard.writeText(
      value,
    );

    setLatestLink(
      value,
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

            marginBottom:
              12,
          }}
        >
          <div>
            <h2>
              Invitations
            </h2>

            <p className="text-label">
              Pending and historical workspace access invitations.
            </p>
          </div>
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


        {latestLink ? (
          <div
            style={{
              marginBottom:
                12,

              display:
                "flex",

              alignItems:
                "center",

              gap:
                8,

              padding:
                10,

              border:
                "1px solid #d9e5d7",

              borderRadius:
                7,

              background:
                "#f7fbf5",

              fontSize:
                10,
            }}
          >
            <Check
              size={
                14
              }
            />

            <input
              readOnly
              value={
                latestLink
              }
              style={{
                flex:
                  1,

                minWidth:
                  0,

                border:
                  "none",

                background:
                  "transparent",

                fontSize:
                  10,
              }}
            />

            <button
              type="button"
              onClick={() =>
                void copy(
                  latestLink,
                )
              }
              style={
                smallButtonStyle
              }
            >
              <Copy
                size={
                  13
                }
              />

              Copy
            </button>
          </div>
        ) : null}


        {invitations.length ===
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
            No invitations found.
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
                    Email
                  </th>

                  <th style={headStyle}>
                    Role
                  </th>

                  <th style={headStyle}>
                    Status
                  </th>

                  <th style={headStyle}>
                    Expires
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
                {invitations.map(
                  (
                    invitation,
                  ) => (
                    <tr
                      key={
                        invitation.id
                      }
                    >
                      <td style={cellStyle}>
                        <strong
                          style={{
                            fontSize:
                              11,
                          }}
                        >
                          {
                            invitation.email
                          }
                        </strong>
                      </td>


                      <td style={cellStyle}>
                        {
                          roleName(
                            invitation.role_key,
                          )
                        }
                      </td>


                      <td style={cellStyle}>
                        <StatusBadge
                          status={
                            invitation.status
                          }
                        />
                      </td>


                      <td style={cellStyle}>
                        <span className="text-label">
                          {formatDate(
                            invitation.expires_at,
                          )}
                        </span>
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

                            gap:
                              5,
                          }}
                        >
                          {canInvite &&
                          (
                            invitation.status ===
                              "pending" ||
                            invitation.status ===
                              "expired"
                          ) ? (
                            <ActionButton
                              title="Resend"
                              disabled={
                                actionKey ===
                                `resend:${invitation.id}`
                              }
                              onClick={() =>
                                void resend(
                                  invitation,
                                )
                              }
                            >
                              {actionKey ===
                              `resend:${invitation.id}` ? (
                                <Loader2
                                  size={
                                    13
                                  }
                                />
                              ) : (
                                <RefreshCcw
                                  size={
                                    13
                                  }
                                />
                              )}
                            </ActionButton>
                          ) : null}


                          {canManage &&
                          invitation.status ===
                            "pending" ? (
                            <ActionButton
                              title="Revoke"
                              disabled={
                                actionKey ===
                                `revoke:${invitation.id}`
                              }
                              onClick={() =>
                                void revoke(
                                  invitation,
                                )
                              }
                            >
                              {actionKey ===
                              `revoke:${invitation.id}` ? (
                                <Loader2
                                  size={
                                    13
                                  }
                                />
                              ) : (
                                <XCircle
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


function StatusBadge({
  status,
}: {
  status:
    string;
}) {
  return (
    <span
      style={{
        display:
          "inline-flex",

        alignItems:
          "center",

        gap:
          5,

        padding:
          "4px 7px",

        borderRadius:
          5,

        border:
          "1px solid var(--color-border)",

        background:
          status ===
          "accepted"
            ? "#f0f8ed"
            : status ===
                "pending"
              ? "#fffaf0"
              : "#faf8f1",

        fontSize:
          9,
      }}
    >
      {status}
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

  disabled:
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
      style={
        smallButtonStyle
      }
    >
      {children}
    </button>
  );
}


function formatDate(
  value:
    string,
) {
  const date =
    new Date(
      value,
    );


  if (
    Number.isNaN(
      date.getTime(),
    )
  ) {
    return value;
  }


  return date.toLocaleString();
}


const smallButtonStyle:
  React.CSSProperties = {
    display:
      "inline-flex",

    alignItems:
      "center",

    justifyContent:
      "center",

    gap:
      5,

    minHeight:
      29,

    padding:
      "5px 8px",

    border:
      "1px solid var(--color-border)",

    borderRadius:
      6,

    background:
      "#fff",

    cursor:
      "pointer",

    fontSize:
      9,
  };


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