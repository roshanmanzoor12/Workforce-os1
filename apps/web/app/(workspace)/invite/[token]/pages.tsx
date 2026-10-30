"use client";

import {
  Check,
  Loader2,
  Mail,
  ShieldCheck,
  X,
} from "lucide-react";

import {
  useEffect,
  useState,
} from "react";

import {
  useParams,
  useRouter,
} from "next/navigation";

import {
  workspaceInvitationsService,
} from "@/services/workspace-invitations.service";

import type {
  WorkspaceInvitationTokenPublic,
} from "@/types/workspace-invitations";


type ViewState =
  | "loading"
  | "ready"
  | "accepted"
  | "declined"
  | "error";


export default function InvitationTokenPage() {
  const params =
    useParams<{
      token:
        string;
    }>();


  const router =
    useRouter();


  const token =
    Array.isArray(
      params?.token,
    )
      ? params.token[0]
      : params?.token;


  const [
    invitation,
    setInvitation,
  ] =
    useState<
      WorkspaceInvitationTokenPublic |
      null
    >(null);


  const [
    state,
    setState,
  ] =
    useState<ViewState>(
      "loading",
    );


  const [
    message,
    setMessage,
  ] =
    useState(
      "",
    );


  const [
    actionLoading,
    setActionLoading,
  ] =
    useState<
      "accept" |
      "decline" |
      null
    >(null);


  useEffect(() => {
    if (
      !token
    ) {
      setState(
        "error",
      );

      setMessage(
        "Invitation token is missing.",
      );

      return;
    }


    let cancelled =
      false;


    async function load() {
      try {
        const response =
          await workspaceInvitationsService.getByToken(
            token,
          );


        if (
          cancelled
        ) {
          return;
        }


        setInvitation(
          response,
        );

        setState(
          "ready",
        );
      } catch (
        cause
      ) {
        if (
          cancelled
        ) {
          return;
        }


        setState(
          "error",
        );


        setMessage(
          cause instanceof Error
            ? cause.message
            : "Unable to load this invitation.",
        );
      }
    }


    void load();


    return () => {
      cancelled =
        true;
    };
  }, [
    token,
  ]);


  async function accept() {
    if (
      !token
    ) {
      return;
    }


    try {
      setActionLoading(
        "accept",
      );

      setMessage(
        "",
      );


      const response =
        await workspaceInvitationsService.accept(
          token,
        );


      setState(
        "accepted",
      );


      setMessage(
        response.message ||
          "Invitation accepted successfully.",
      );
    } catch (
      cause
    ) {
      setMessage(
        cause instanceof Error
          ? cause.message
          : "Unable to accept this invitation.",
      );
    } finally {
      setActionLoading(
        null,
      );
    }
  }


  async function decline() {
    if (
      !token
    ) {
      return;
    }


    try {
      setActionLoading(
        "decline",
      );

      setMessage(
        "",
      );


      const response =
        await workspaceInvitationsService.decline(
          token,
        );


      setState(
        "declined",
      );


      setMessage(
        response.message ||
          "Invitation declined.",
      );
    } catch (
      cause
    ) {
      setMessage(
        cause instanceof Error
          ? cause.message
          : "Unable to decline this invitation.",
      );
    } finally {
      setActionLoading(
        null,
      );
    }
  }


  function goToLogin() {
    router.push(
      "/login",
    );
  }


  return (
    <main
      style={{
        minHeight:
          "100vh",

        display:
          "grid",

        placeItems:
          "center",

        padding:
          24,

        background:
          "#f7f4eb",
      }}
    >
      <section
        className="panel"
        style={{
          width:
            "100%",

          maxWidth:
            520,
        }}
      >
        <div
          className="panel-body"
          style={{
            padding:
              26,
          }}
        >
          {state ===
          "loading" ? (
            <StateBlock
              icon={
                <Loader2
                  size={
                    24
                  }
                />
              }
              title="Loading invitation"
              description="Checking the invitation details..."
            />
          ) : null}


          {state ===
          "error" ? (
            <>
              <StateBlock
                icon={
                  <X
                    size={
                      24
                    }
                  />
                }
                title="Invitation unavailable"
                description={
                  message ||
                  "This invitation could not be loaded."
                }
              />

              <button
                type="button"
                onClick={
                  goToLogin
                }
                style={
                  primaryButtonStyle
                }
              >
                Sign In
              </button>
            </>
          ) : null}


          {state ===
            "ready" &&
          invitation ? (
            <>
              <div
                style={{
                  display:
                    "grid",

                  placeItems:
                    "center",

                  width:
                    48,

                  height:
                    48,

                  margin:
                    "0 auto 14px",

                  borderRadius:
                    12,

                  background:
                    "#faf7ed",

                  border:
                    "1px solid var(--color-border)",
                }}
              >
                <Mail
                  size={
                    22
                  }
                />
              </div>


              <div
                style={{
                  textAlign:
                    "center",
                }}
              >
                <div className="text-label">
                  Workspace Invitation
                </div>

                <h1
                  style={{
                    marginTop:
                      4,
                  }}
                >
                  You're invited
                </h1>

                <p
                  className="text-label"
                  style={{
                    marginTop:
                      7,
                  }}
                >
                  Join{" "}
                  <strong>
                    {
                      invitation.workspace_name ||
                      "this workspace"
                    }
                  </strong>{" "}
                  as{" "}
                  <strong>
                    {
                      invitation.role_key
                    }
                  </strong>
                  .
                </p>
              </div>


              <div
                style={{
                  marginTop:
                    20,

                  display:
                    "grid",

                  gap:
                    8,
                }}
              >
                <InfoRow
                  label="Email"
                  value={
                    invitation.email
                  }
                />

                <InfoRow
                  label="Role"
                  value={
                    invitation.role_key
                  }
                />

                <InfoRow
                  label="Expires"
                  value={formatDate(
                    invitation.expires_at,
                  )}
                />

                <InfoRow
                  label="Status"
                  value={
                    invitation.status
                  }
                />
              </div>


              <div
                style={{
                  display:
                    "grid",

                  gridTemplateColumns:
                    "1fr 1fr",

                  gap:
                    8,

                  marginTop:
                    18,
                }}
              >
                <button
                  type="button"
                  disabled={
                    actionLoading !==
                    null
                  }
                  onClick={() =>
                    void decline()
                  }
                  style={
                    secondaryButtonStyle
                  }
                >
                  {actionLoading ===
                  "decline" ? (
                    <Loader2
                      size={
                        14
                      }
                    />
                  ) : (
                    <X
                      size={
                        14
                      }
                    />
                  )}

                  Decline
                </button>


                <button
                  type="button"
                  disabled={
                    actionLoading !==
                    null
                  }
                  onClick={() =>
                    void accept()
                  }
                  style={
                    primaryButtonStyle
                  }
                >
                  {actionLoading ===
                  "accept" ? (
                    <Loader2
                      size={
                        14
                      }
                    />
                  ) : (
                    <Check
                      size={
                        14
                      }
                    />
                  )}

                  Accept Invitation
                </button>
              </div>


              <p
                className="text-label"
                style={{
                  marginTop:
                    12,

                  textAlign:
                    "center",
                }}
              >
                You must be signed in to the account that should receive this workspace access.
              </p>
            </>
          ) : null}


          {state ===
          "accepted" ? (
            <>
              <StateBlock
                icon={
                  <Check
                    size={
                      24
                    }
                  />
                }
                title="Invitation accepted"
                description={
                  message ||
                  "Your workspace membership has been created."
                }
              />

              <button
                type="button"
                onClick={() =>
                  router.push(
                    "/dashboard",
                  )
                }
                style={
                  primaryButtonStyle
                }
              >
                Open Workspace
              </button>
            </>
          ) : null}


          {state ===
          "declined" ? (
            <>
              <StateBlock
                icon={
                  <X
                    size={
                      24
                    }
                  />
                }
                title="Invitation declined"
                description={
                  message ||
                  "The workspace invitation was declined."
                }
              />

              <button
                type="button"
                onClick={
                  goToLogin
                }
                style={
                  secondaryButtonStyle
                }
              >
                Return to Sign In
              </button>
            </>
          ) : null}
        </div>
      </section>
    </main>
  );
}


function StateBlock({
  icon,

  title,

  description,
}: {
  icon:
    React.ReactNode;

  title:
    string;

  description:
    string;
}) {
  return (
    <div
      style={{
        textAlign:
          "center",

        marginBottom:
          18,
      }}
    >
      <div
        style={{
          display:
            "grid",

          placeItems:
            "center",

          width:
            50,

          height:
            50,

          margin:
            "0 auto 13px",

          borderRadius:
            12,

          border:
            "1px solid var(--color-border)",

          background:
            "#faf7ed",
        }}
      >
        {icon}
      </div>

      <h1>
        {title}
      </h1>

      <p
        className="text-label"
        style={{
          marginTop:
            7,

          lineHeight:
            1.6,
        }}
      >
        {description}
      </p>
    </div>
  );
}


function InfoRow({
  label,

  value,
}: {
  label:
    string;

  value:
    string;
}) {
  return (
    <div
      style={{
        display:
          "flex",

        justifyContent:
          "space-between",

        gap:
          15,

        padding:
          "9px 10px",

        border:
          "1px solid var(--color-border)",

        borderRadius:
          7,

        background:
          "#fff",
      }}
    >
      <span className="text-label">
        {label}
      </span>

      <strong
        style={{
          fontSize:
            10,

          textAlign:
            "right",
        }}
      >
        {value}
      </strong>
    </div>
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


const primaryButtonStyle:
  React.CSSProperties = {
    width:
      "100%",

    minHeight:
      38,

    display:
      "inline-flex",

    alignItems:
      "center",

    justifyContent:
      "center",

    gap:
      7,

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
    width:
      "100%",

    minHeight:
      38,

    display:
      "inline-flex",

    alignItems:
      "center",

    justifyContent:
      "center",

    gap:
      7,

    border:
      "1px solid var(--color-border)",

    borderRadius:
      7,

    background:
      "#fff",

    color:
      "#303235",

    cursor:
      "pointer",

    fontSize:
      10,
  };