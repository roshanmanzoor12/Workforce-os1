"use client";

import {
  RefreshCcw,
} from "lucide-react";

import {
  useCallback,
  useEffect,
  useState,
} from "react";

import {
  InvitationCreateForm,
} from "@/components/workspace/invitation-create-form";

import {
  InvitationList,
} from "@/components/workspace/invitation-list";

import {
  WorkspaceRequired,
} from "@/components/workspace/workspace-required";

import {
  useWorkspace,
} from "@/contexts/workspace-context";

import {
  workspaceInvitationsService,
} from "@/services/workspace-invitations.service";

import {
  workspaceRolesService,
} from "@/services/workspace-roles.service";

import type {
  WorkspaceInvitationPublic,
} from "@/types/workspace-invitations";

import type {
  WorkspaceRolePublic,
} from "@/types/workspace-roles";


export default function InvitationsPage() {
  return (
    <WorkspaceRequired>
      <InvitationsContent />
    </WorkspaceRequired>
  );
}


function InvitationsContent() {
  const {
    workspaceId,
  } =
    useWorkspace();


  const [
    invitations,
    setInvitations,
  ] =
    useState<
      WorkspaceInvitationPublic[]
    >([]);


  const [
    roles,
    setRoles,
  ] =
    useState<
      WorkspaceRolePublic[]
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


  const load =
    useCallback(
      async () => {
        if (
          !workspaceId
        ) {
          return;
        }


        try {
          setLoading(
            true,
          );

          setError(
            null,
          );


          const [
            invitationResponse,

            roleResponse,
          ] =
            await Promise.all([
              workspaceInvitationsService.list(
                workspaceId,
              ),

              workspaceRolesService.list(
                workspaceId,
              ),
            ]);


          setInvitations(
            invitationResponse.items ??
              [],
          );


          setRoles(
            roleResponse.roles ??
              [],
          );
        } catch (
          cause
        ) {
          setError(
            cause instanceof Error
              ? cause.message
              : "Unable to load workspace invitations.",
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


  if (
    loading
  ) {
    return (
      <section className="panel">
        <div
          className="panel-body"
          style={{
            padding:
              24,

            textAlign:
              "center",
          }}
        >
          <span className="text-label">
            Loading invitations...
          </span>
        </div>
      </section>
    );
  }


  return (
    <div
      style={{
        display:
          "grid",

        gap:
          14,
      }}
    >
      <header
        style={{
          display:
            "flex",

          alignItems:
            "flex-start",

          justifyContent:
            "space-between",

          gap:
            15,
        }}
      >
        <div>
          <div className="text-label">
            Workspace / Access
          </div>

          <h1
            style={{
              marginTop:
                3,
            }}
          >
            Invitations
          </h1>

          <p
            className="text-label"
            style={{
              marginTop:
                5,

              maxWidth:
                680,
            }}
          >
            Invite employees and collaborators into this workspace and manage their pending access.
          </p>
        </div>


        <button
          type="button"
          onClick={() =>
            void load()
          }
          style={
            refreshButtonStyle
          }
        >
          <RefreshCcw
            size={
              13
            }
          />

          Refresh
        </button>
      </header>


      {error ? (
        <div
          style={{
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


      <InvitationCreateForm
        roles={
          roles
        }
        onCreated={() =>
          void load()
        }
      />


      <InvitationList
        invitations={
          invitations
        }
        roles={
          roles
        }
        onChanged={() =>
          void load()
        }
      />
    </div>
  );
}


const refreshButtonStyle:
  React.CSSProperties = {
    display:
      "inline-flex",

    alignItems:
      "center",

    gap:
      6,

    padding:
      "8px 11px",

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