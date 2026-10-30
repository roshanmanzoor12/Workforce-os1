"use client";

import {
  Hash,
  Megaphone,
  Volume2,
  X,
} from "lucide-react";

import {
  useState,
} from "react";

import {
  channelsService,
} from "@/services/channels.service";

import type {
  WorkspaceChannel,
  WorkspaceChannelType,
} from "@/types/channels";


interface ChannelCreateModalProps {
  workspaceId: string;

  onClose: () => void;

  onCreated: (
    channel: WorkspaceChannel,
  ) => Promise<void> | void;
}


export function ChannelCreateModal({
  workspaceId,

  onClose,

  onCreated,
}: ChannelCreateModalProps) {
  const [
    name,
    setName,
  ] =
    useState(
      "",
    );


  const [
    channelType,
    setChannelType,
  ] =
    useState<WorkspaceChannelType>(
      "text",
    );


  const [
    saving,
    setSaving,
  ] =
    useState(
      false,
    );


  const [
    error,
    setError,
  ] =
    useState<string | null>(
      null,
    );


  async function create() {
    const normalized =
      name.trim();


    if (
      !normalized ||
      saving
    ) {
      return;
    }


    try {
      setSaving(
        true,
      );


      setError(
        null,
      );


      const channel =
        await channelsService.create({
          workspace_id:
            workspaceId,

          name:
            normalized,

          channel_type:
            channelType,
        });


      await onCreated(
        channel,
      );


      onClose();

    } catch (
      cause
    ) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Unable to create channel.",
      );

    } finally {
      setSaving(
        false,
      );
    }
  }


  return (
    <div
      style={{
        position:
          "fixed",

        inset:
          0,

        zIndex:
          160,

        display:
          "grid",

        placeItems:
          "center",

        padding:
          20,

        background:
          "rgba(30, 30, 28, .44)",
      }}
    >
      <section
        style={{
          width:
            "min(480px, 100%)",

          overflow:
            "hidden",

          border:
            "1px solid var(--color-border)",

          borderRadius:
            12,

          background:
            "#fffefa",

          boxShadow:
            "0 22px 70px rgba(0,0,0,.2)",
        }}
      >
        <header
          style={{
            display:
              "flex",

            justifyContent:
              "space-between",

            alignItems:
              "center",

            padding:
              "13px 14px",

            borderBottom:
              "1px solid var(--color-border)",
          }}
        >
          <div>
            <strong>
              Create Channel
            </strong>


            <div
              className="text-label"
              style={{
                marginTop:
                  3,
              }}
            >
              Add a text, announcement or voice channel.
            </div>
          </div>


          <button
            type="button"
            className="button button--outline"
            onClick={
              onClose
            }
          >
            <X
              size={
                13
              }
            />
          </button>
        </header>


        <div
          style={{
            display:
              "grid",

            gap:
              14,

            padding:
              14,
          }}
        >
          {error ? (
            <div
              style={{
                padding:
                  "9px 10px",

                border:
                  "1px solid #efc6c6",

                borderRadius:
                  7,

                background:
                  "#fff1f1",

                color:
                  "#b52b2b",

                fontSize:
                  9,
              }}
            >
              {error}
            </div>
          ) : null}


          <div
            style={{
              display:
                "grid",

              gap:
                7,
            }}
          >
            <span
              style={{
                fontSize:
                  9,

                fontWeight:
                  700,
              }}
            >
              Channel Type
            </span>


            <ChannelTypeButton
              active={
                channelType ===
                "text"
              }
              title="Text"
              description="Messages, files and discussions."
              icon={
                <Hash
                  size={
                    16
                  }
                />
              }
              onClick={() =>
                setChannelType(
                  "text",
                )
              }
            />


            <ChannelTypeButton
              active={
                channelType ===
                "announcement"
              }
              title="Announcement"
              description="Workspace notices and broadcast posts."
              icon={
                <Megaphone
                  size={
                    16
                  }
                />
              }
              onClick={() =>
                setChannelType(
                  "announcement",
                )
              }
            />


            <ChannelTypeButton
              active={
                channelType ===
                "voice"
              }
              title="Voice"
              description="Persistent Discord-style voice room."
              icon={
                <Volume2
                  size={
                    16
                  }
                />
              }
              onClick={() =>
                setChannelType(
                  "voice",
                )
              }
            />
          </div>


          <label
            style={{
              display:
                "grid",

              gap:
                5,

              fontSize:
                9,

              fontWeight:
                700,
            }}
          >
            Channel Name

            <input
              value={
                name
              }
              maxLength={
                120
              }
              autoFocus
              placeholder={
                channelType ===
                "voice"
                  ? "General Voice"
                  : channelType ===
                      "announcement"
                    ? "Announcements"
                    : "General"
              }
              disabled={
                saving
              }
              onChange={(
                event,
              ) =>
                setName(
                  event.target.value,
                )
              }
              onKeyDown={(
                event,
              ) => {
                if (
                  event.key ===
                  "Enter"
                ) {
                  event.preventDefault();


                  void create();
                }
              }}
              style={{
                height:
                  38,

                padding:
                  "0 10px",

                border:
                  "1px solid var(--color-border)",

                borderRadius:
                  7,

                background:
                  "#fff",

                outline:
                  "none",

                fontSize:
                  10,
              }}
            />
          </label>


          <div
            style={{
              display:
                "flex",

              justifyContent:
                "flex-end",

              gap:
                8,

              paddingTop:
                3,
            }}
          >
            <button
              type="button"
              className="button button--outline"
              disabled={
                saving
              }
              onClick={
                onClose
              }
            >
              Cancel
            </button>


            <button
              type="button"
              className="button button--primary"
              disabled={
                saving ||
                !name.trim()
              }
              onClick={() => {
                void create();
              }}
            >
              {saving
                ? "Creating..."
                : "Create Channel"}
            </button>
          </div>
        </div>
      </section>
    </div>
  );
}


function ChannelTypeButton({
  active,

  title,

  description,

  icon,

  onClick,
}: {
  active: boolean;

  title: string;

  description: string;

  icon: React.ReactNode;

  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={
        onClick
      }
      style={{
        display:
          "grid",

        gridTemplateColumns:
          "38px minmax(0,1fr) 18px",

        alignItems:
          "center",

        gap:
          9,

        padding:
          9,

        border:
          active
            ? "1px solid #b28b2e"
            : "1px solid var(--color-border)",

        borderRadius:
          8,

        background:
          active
            ? "#fff7df"
            : "#fffefa",

        color:
          "#3c3d3f",

        textAlign:
          "left",

        cursor:
          "pointer",
      }}
    >
      <span
        style={{
          display:
            "grid",

          width:
            36,

          height:
            36,

          placeItems:
            "center",

          borderRadius:
            7,

          background:
            active
              ? "#2f3032"
              : "#ece7dc",

          color:
            active
              ? "#fff"
              : "#555",
        }}
      >
        {icon}
      </span>


      <span>
        <strong
          style={{
            display:
              "block",

            fontSize:
              9,
          }}
        >
          {title}
        </strong>


        <span
          style={{
            display:
              "block",

            marginTop:
              2,

            color:
              "#818386",

            fontSize:
              8,
          }}
        >
          {description}
        </span>
      </span>


      <span
        style={{
          width:
            13,

          height:
            13,

          border:
            active
              ? "4px solid #2f3032"
              : "1px solid #aaa",

          borderRadius:
            999,
        }}
      />
    </button>
  );
}