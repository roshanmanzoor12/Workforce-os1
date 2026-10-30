"use client";

import {
  Check,
  Copy,
  Loader2,
  MailPlus,
} from "lucide-react";

import {
  useMemo,
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
  WorkspaceInvitationSecretResponse,
} from "@/types/workspace-invitations";

import type {
  WorkspaceRolePublic,
} from "@/types/workspace-roles";


interface InvitationCreateFormProps {
  roles:
    WorkspaceRolePublic[];

  onCreated?:
    (
      response:
        WorkspaceInvitationSecretResponse,
    ) => void;
}


export function InvitationCreateForm({
  roles,

  onCreated,
}: InvitationCreateFormProps) {
  const {
    workspaceId,

    effectivePermissions,

    effectiveNavigationView,
  } =
    useWorkspace();


  const [
    email,
    setEmail,
  ] =
    useState(
      "",
    );


  const [
    roleKey,
    setRoleKey,
  ] =
    useState(
      "",
    );


  const [
    expiresAt,
    setExpiresAt,
  ] =
    useState(
      "",
    );


  const [
    submitting,
    setSubmitting,
  ] =
    useState(
      false,
    );


  const [
    error,
    setError,
  ] =
    useState<
      string | null
    >(null);


  const [
    created,
    setCreated,
  ] =
    useState<
      WorkspaceInvitationSecretResponse |
      null
    >(null);


  const canInvite =
    hasPermission(
      effectivePermissions,
      "members.invite",
      effectiveNavigationView,
    );


  const activeRoles =
    useMemo(
      () =>
        roles.filter(
          (
            role,
          ) =>
            role.is_active,
        ),
      [
        roles,
      ],
    );


  async function submit(
    event:
      React.FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();


    if (
      !workspaceId
    ) {
      setError(
        "No workspace is selected.",
      );

      return;
    }


    if (
      !canInvite
    ) {
      setError(
        "You do not have permission to invite workspace members.",
      );

      return;
    }


    const normalizedEmail =
      email
        .trim()
        .toLowerCase();


    if (
      !normalizedEmail
    ) {
      setError(
        "Email address is required.",
      );

      return;
    }


    if (
      !normalizedEmail.includes(
        "@",
      )
    ) {
      setError(
        "Enter a valid email address.",
      );

      return;
    }


    if (
      !roleKey
    ) {
      setError(
        "Select a role.",
      );

      return;
    }


    try {
      setSubmitting(
        true,
      );

      setError(
        null,
      );


      const response =
        await workspaceInvitationsService.create(
          workspaceId,
          {
            email:
              normalizedEmail,

            role_key:
              roleKey,

            expires_at:
              expiresAt
                ? new Date(
                    expiresAt,
                  ).toISOString()
                : null,
          },
        );


      setCreated(
        response,
      );

      setEmail(
        "",
      );

      setExpiresAt(
        "",
      );


      onCreated?.(
        response,
      );
    } catch (
      cause
    ) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Unable to create invitation.",
      );
    } finally {
      setSubmitting(
        false,
      );
    }
  }


  const invitationLink =
    created
      ? buildWorkspaceInvitationLink(
          created.invitation_token,
        )
      : "";


  async function copyLink() {
    if (
      !invitationLink
    ) {
      return;
    }


    await navigator.clipboard.writeText(
      invitationLink,
    );
  }


  return (
    <section className="panel">
      <div
        className="panel-body"
        style={{
          padding:
            18,
        }}
      >
        <div
          style={{
            display:
              "flex",

            alignItems:
              "center",

            gap:
              9,

            marginBottom:
              14,
          }}
        >
          <MailPlus
            size={
              18
            }
          />

          <div>
            <h2>
              Invite Member
            </h2>

            <p className="text-label">
              Send a workspace invitation and assign the initial role.
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


        {!canInvite ? (
          <div
            className="text-label"
            style={{
              padding:
                12,

              border:
                "1px solid var(--color-border)",

              borderRadius:
                7,
            }}
          >
            You do not have permission to create workspace invitations.
          </div>
        ) : (
          <form
            onSubmit={
              submit
            }
          >
            <div
              style={{
                display:
                  "grid",

                gridTemplateColumns:
                  "2fr 1fr 1fr",

                gap:
                  10,
              }}
            >
              <label>
                <span className="text-label">
                  Email
                </span>

                <input
                  type="email"
                  value={
                    email
                  }
                  onChange={(
                    event,
                  ) =>
                    setEmail(
                      event.target.value,
                    )
                  }
                  placeholder="employee@company.com"
                  style={
                    inputStyle
                  }
                />
              </label>


              <label>
                <span className="text-label">
                  Role
                </span>

                <select
                  value={
                    roleKey
                  }
                  onChange={(
                    event,
                  ) =>
                    setRoleKey(
                      event.target.value,
                    )
                  }
                  style={
                    inputStyle
                  }
                >
                  <option value="">
                    Select role
                  </option>

                  {activeRoles.map(
                    (
                      role,
                    ) => (
                      <option
                        key={
                          role.role_key
                        }
                        value={
                          role.role_key
                        }
                      >
                        {
                          role.display_name
                        }
                      </option>
                    ),
                  )}
                </select>
              </label>


              <label>
                <span className="text-label">
                  Expires
                </span>

                <input
                  type="datetime-local"
                  value={
                    expiresAt
                  }
                  onChange={(
                    event,
                  ) =>
                    setExpiresAt(
                      event.target.value,
                    )
                  }
                  style={
                    inputStyle
                  }
                />
              </label>
            </div>


            <div
              style={{
                display:
                  "flex",

                justifyContent:
                  "flex-end",

                marginTop:
                  12,
              }}
            >
              <button
                type="submit"
                disabled={
                  submitting
                }
                style={
                  primaryButtonStyle
                }
              >
                {submitting ? (
                  <Loader2
                    size={
                      14
                    }
                  />
                ) : (
                  <MailPlus
                    size={
                      14
                    }
                  />
                )}

                Create Invitation
              </button>
            </div>
          </form>
        )}


        {created ? (
          <div
            style={{
              marginTop:
                16,

              padding:
                13,

              border:
                "1px solid #cfe5cf",

              borderRadius:
                8,

              background:
                "#f6fbf5",
            }}
          >
            <div
              style={{
                display:
                  "flex",

                alignItems:
                  "center",

                gap:
                  7,

                fontSize:
                  11,

                fontWeight:
                  600,
              }}
            >
              <Check
                size={
                  14
                }
              />

              Invitation created
            </div>


            <div
              className="text-label"
              style={{
                marginTop:
                  5,
              }}
            >
              Send this invitation link to the recipient.
            </div>


            <div
              style={{
                display:
                  "flex",

                gap:
                  7,

                marginTop:
                  9,
              }}
            >
              <input
                readOnly
                value={
                  invitationLink
                }
                style={{
                  ...inputStyle,

                  flex:
                    1,
                }}
              />

              <button
                type="button"
                onClick={() =>
                  void copyLink()
                }
                style={
                  secondaryButtonStyle
                }
              >
                <Copy
                  size={
                    14
                  }
                />

                Copy
              </button>
            </div>
          </div>
        ) : null}
      </div>
    </section>
  );
}


const inputStyle:
  React.CSSProperties = {
    width:
      "100%",

    minHeight:
      35,

    marginTop:
      5,

    padding:
      "7px 9px",

    border:
      "1px solid var(--color-border)",

    borderRadius:
      7,

    background:
      "#fffefa",

    fontSize:
      10,
  };


const primaryButtonStyle:
  React.CSSProperties = {
    display:
      "inline-flex",

    alignItems:
      "center",

    gap:
      6,

    padding:
      "8px 12px",

    border:
      "1px solid var(--color-black)",

    borderRadius:
      7,

    background:
      "var(--color-black)",

    color:
      "#fff",

    cursor:
      "pointer",

    fontSize:
      10,
  };


const secondaryButtonStyle:
  React.CSSProperties = {
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

    fontSize:
      10,
  };