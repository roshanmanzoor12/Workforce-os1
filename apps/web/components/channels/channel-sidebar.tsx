"use client";

import {
  Hash,
  Megaphone,
  MoreHorizontal,
  Pencil,
  Plus,
  RefreshCcw,
  Trash2,
  Volume2,
  X,
} from "lucide-react";

import {
  useMemo,
  useState,
} from "react";

import {
  channelsService,
} from "@/services/channels.service";

import type {
  WorkspaceChannel,
} from "@/types/channels";


interface ChannelSidebarProps {
  channels:
    WorkspaceChannel[];

  selectedChannelId:
    string | null;

  loading:
    boolean;

  canManage:
    boolean;

  onSelect: (
    channelId:
      string,
  ) => void;

  onCreate:
    () => void;

  onRefresh:
    () => void;

  onChanged:
    () => Promise<void> | void;
}


export function ChannelSidebar({
  channels,

  selectedChannelId,

  loading,

  canManage,

  onSelect,

  onCreate,

  onRefresh,

  onChanged,
}: ChannelSidebarProps) {
  const [
    menuChannelId,
    setMenuChannelId,
  ] =
    useState<string | null>(
      null,
    );


  const [
    renameChannel,
    setRenameChannel,
  ] =
    useState<WorkspaceChannel | null>(
      null,
    );


  const [
    renameValue,
    setRenameValue,
  ] =
    useState(
      "",
    );


  const [
    busyId,
    setBusyId,
  ] =
    useState<string | null>(
      null,
    );


  const [
    error,
    setError,
  ] =
    useState<string | null>(
      null,
    );


  const activeChannels =
    useMemo(
      () =>
        channels.filter(
          (
            channel,
          ) =>
            channel.is_active,
        ),
      [
        channels,
      ],
    );


  const textChannels =
    activeChannels.filter(
      (
        channel,
      ) =>
        channel.channel_type ===
        "text",
    );


  const announcementChannels =
    activeChannels.filter(
      (
        channel,
      ) =>
        channel.channel_type ===
        "announcement",
    );


  const voiceChannels =
    activeChannels.filter(
      (
        channel,
      ) =>
        channel.channel_type ===
        "voice",
    );


  function beginRename(
    channel:
      WorkspaceChannel,
  ) {
    setMenuChannelId(
      null,
    );


    setRenameChannel(
      channel,
    );


    setRenameValue(
      channel.name,
    );


    setError(
      null,
    );
  }


  async function saveRename() {
    if (
      !renameChannel ||
      !renameValue.trim()
    ) {
      return;
    }


    try {
      setBusyId(
        renameChannel.id,
      );


      setError(
        null,
      );


      await channelsService.rename(
        renameChannel.id,
        {
          name:
            renameValue.trim(),
        },
      );


      setRenameChannel(
        null,
      );


      setRenameValue(
        "",
      );


      await onChanged();

    } catch (
      cause
    ) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Unable to rename channel.",
      );

    } finally {
      setBusyId(
        null,
      );
    }
  }


  async function archive(
    channel:
      WorkspaceChannel,
  ) {
    const confirmed =
      window.confirm(
        `Archive "${channel.name}"?`,
      );


    if (
      !confirmed
    ) {
      return;
    }


    try {
      setBusyId(
        channel.id,
      );


      setError(
        null,
      );


      setMenuChannelId(
        null,
      );


      await channelsService.archive(
        channel.id,
      );


      await onChanged();

    } catch (
      cause
    ) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Unable to archive channel.",
      );

    } finally {
      setBusyId(
        null,
      );
    }
  }


  return (
    <>
      <aside
        style={{
          width:
            260,

          minWidth:
            260,

          display:
            "flex",

          flexDirection:
            "column",

          borderRight:
            "1px solid var(--color-border)",

          background:
            "#f4f1ea",
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
              8,

            padding:
              "11px 10px",

            borderBottom:
              "1px solid var(--color-border)",
          }}
        >
          <strong
            style={{
              fontSize:
                10,
            }}
          >
            Channels
          </strong>


          <div
            style={{
              display:
                "flex",

              gap:
                4,
            }}
          >
            <button
              type="button"
              title="Refresh channels"
              onClick={
                onRefresh
              }
              style={iconButtonStyle}
            >
              <RefreshCcw
                size={
                  13
                }
              />
            </button>


            {canManage ? (
              <button
                type="button"
                title="Create channel"
                onClick={
                  onCreate
                }
                style={iconButtonStyle}
              >
                <Plus
                  size={
                    14
                  }
                />
              </button>
            ) : null}
          </div>
        </div>


        {error ? (
          <div
            style={{
              margin:
                8,

              padding:
                8,

              border:
                "1px solid #efc6c6",

              borderRadius:
                6,

              background:
                "#fff1f1",

              color:
                "#b52b2b",

              fontSize:
                8,
            }}
          >
            {error}
          </div>
        ) : null}


        <div
          style={{
            flex:
              1,

            overflowY:
              "auto",

            padding:
              "8px 6px 18px",
          }}
        >
          {loading ? (
            <div
              className="skeleton"
              style={{
                height:
                  280,

                margin:
                  4,
              }}
            />
          ) : (
            <>
              <ChannelGroup
                title="TEXT CHANNELS"
                channels={
                  textChannels
                }
                selectedChannelId={
                  selectedChannelId
                }
                canManage={
                  canManage
                }
                menuChannelId={
                  menuChannelId
                }
                busyId={
                  busyId
                }
                onSelect={
                  onSelect
                }
                onToggleMenu={(
                  channelId,
                ) =>
                  setMenuChannelId(
                    (
                      current,
                    ) =>
                      current ===
                      channelId
                        ? null
                        : channelId,
                  )
                }
                onRename={
                  beginRename
                }
                onArchive={(
                  channel,
                ) => {
                  void archive(
                    channel,
                  );
                }}
              />


              <ChannelGroup
                title="ANNOUNCEMENTS"
                channels={
                  announcementChannels
                }
                selectedChannelId={
                  selectedChannelId
                }
                canManage={
                  canManage
                }
                menuChannelId={
                  menuChannelId
                }
                busyId={
                  busyId
                }
                onSelect={
                  onSelect
                }
                onToggleMenu={(
                  channelId,
                ) =>
                  setMenuChannelId(
                    (
                      current,
                    ) =>
                      current ===
                      channelId
                        ? null
                        : channelId,
                  )
                }
                onRename={
                  beginRename
                }
                onArchive={(
                  channel,
                ) => {
                  void archive(
                    channel,
                  );
                }}
              />


              <ChannelGroup
                title="VOICE CHANNELS"
                channels={
                  voiceChannels
                }
                selectedChannelId={
                  selectedChannelId
                }
                canManage={
                  canManage
                }
                menuChannelId={
                  menuChannelId
                }
                busyId={
                  busyId
                }
                onSelect={
                  onSelect
                }
                onToggleMenu={(
                  channelId,
                ) =>
                  setMenuChannelId(
                    (
                      current,
                    ) =>
                      current ===
                      channelId
                        ? null
                        : channelId,
                  )
                }
                onRename={
                  beginRename
                }
                onArchive={(
                  channel,
                ) => {
                  void archive(
                    channel,
                  );
                }}
              />


              {activeChannels.length ===
              0 ? (
                <div
                  style={{
                    padding:
                      20,

                    textAlign:
                      "center",

                    color:
                      "#858585",

                    fontSize:
                      8,
                  }}
                >
                  No channels yet.
                </div>
              ) : null}
            </>
          )}
        </div>
      </aside>


      {renameChannel ? (
        <div
          style={{
            position:
              "fixed",

            inset:
              0,

            zIndex:
              170,

            display:
              "grid",

            placeItems:
              "center",

            padding:
              20,

            background:
              "rgba(30,30,28,.4)",
          }}
        >
          <section
            style={{
              width:
                "min(420px, 100%)",

              border:
                "1px solid var(--color-border)",

              borderRadius:
                10,

              background:
                "#fffefa",

              boxShadow:
                "0 18px 60px rgba(0,0,0,.2)",
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
                  "11px 12px",

                borderBottom:
                  "1px solid var(--color-border)",
              }}
            >
              <strong>
                Rename Channel
              </strong>


              <button
                type="button"
                className="button button--outline"
                onClick={() =>
                  setRenameChannel(
                    null,
                  )
                }
              >
                <X
                  size={
                    12
                  }
                />
              </button>
            </header>


            <div
              style={{
                display:
                  "grid",

                gap:
                  10,

                padding:
                  12,
              }}
            >
              <input
                value={
                  renameValue
                }
                maxLength={
                  120
                }
                autoFocus
                disabled={
                  busyId !==
                  null
                }
                onChange={(
                  event,
                ) =>
                  setRenameValue(
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


                    void saveRename();
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

                  outline:
                    "none",

                  background:
                    "#fff",

                  fontSize:
                    10,
                }}
              />


              <button
                type="button"
                className="button button--primary"
                disabled={
                  busyId !==
                    null ||
                  !renameValue.trim()
                }
                onClick={() => {
                  void saveRename();
                }}
              >
                Save
              </button>
            </div>
          </section>
        </div>
      ) : null}
    </>
  );
}


function ChannelGroup({
  title,

  channels,

  selectedChannelId,

  canManage,

  menuChannelId,

  busyId,

  onSelect,

  onToggleMenu,

  onRename,

  onArchive,
}: {
  title:
    string;

  channels:
    WorkspaceChannel[];

  selectedChannelId:
    string | null;

  canManage:
    boolean;

  menuChannelId:
    string | null;

  busyId:
    string | null;

  onSelect:
    (
      channelId:
        string,
    ) => void;

  onToggleMenu:
    (
      channelId:
        string,
    ) => void;

  onRename:
    (
      channel:
        WorkspaceChannel,
    ) => void;

  onArchive:
    (
      channel:
        WorkspaceChannel,
    ) => void;
}) {
  if (
    channels.length ===
    0
  ) {
    return null;
  }


  return (
    <div
      style={{
        marginBottom:
          14,
      }}
    >
      <div
        style={{
          padding:
            "5px 7px",

          color:
            "#858585",

          fontSize:
            7,

          fontWeight:
            700,

          letterSpacing:
            ".08em",
      }}
      >
        {title}
      </div>


      <div
        style={{
          display:
            "grid",

          gap:
            2,
        }}
      >
        {channels.map(
          (
            channel,
          ) => {
            const selected =
              selectedChannelId ===
              channel.id;


            return (
              <div
                key={
                  channel.id
                }
                style={{
                  position:
                    "relative",

                  display:
                    "grid",

                  gridTemplateColumns:
                    canManage
                      ? "minmax(0,1fr) 30px"
                      : "minmax(0,1fr)",

                  alignItems:
                    "center",

                  borderRadius:
                    6,

                  background:
                    selected
                      ? "#303133"
                      : "transparent",

                  color:
                    selected
                      ? "#fff"
                      : "#555",
                }}
              >
                <button
                  type="button"
                  disabled={
                    busyId ===
                    channel.id
                  }
                  onClick={() =>
                    onSelect(
                      channel.id,
                    )
                  }
                  style={{
                    display:
                      "grid",

                    gridTemplateColumns:
                      "20px minmax(0,1fr)",

                    alignItems:
                      "center",

                    gap:
                      5,

                    minWidth:
                      0,

                    padding:
                      "7px 8px",

                    border:
                      0,

                    background:
                      "transparent",

                    color:
                      "inherit",

                    textAlign:
                      "left",

                    cursor:
                      "pointer",
                  }}
                >
                  <ChannelIcon
                    channel={
                      channel
                    }
                  />


                  <span
                    style={{
                      overflow:
                        "hidden",

                      textOverflow:
                        "ellipsis",

                      whiteSpace:
                        "nowrap",

                      fontSize:
                        9,

                      fontWeight:
                        selected
                          ? 700
                          : 500,
                    }}
                  >
                    {channel.name}
                  </span>
                </button>


                {canManage ? (
                  <button
                    type="button"
                    title="Channel options"
                    disabled={
                      busyId ===
                      channel.id
                    }
                    onClick={() =>
                      onToggleMenu(
                        channel.id,
                      )
                    }
                    style={{
                      display:
                        "grid",

                      width:
                        26,

                      height:
                        26,

                      placeItems:
                        "center",

                      border:
                        0,

                      borderRadius:
                        5,

                      background:
                        "transparent",

                      color:
                        "inherit",

                      cursor:
                        "pointer",
                    }}
                  >
                    <MoreHorizontal
                      size={
                        13
                      }
                    />
                  </button>
                ) : null}


                {menuChannelId ===
                channel.id ? (
                  <div
                    style={{
                      position:
                        "absolute",

                      top:
                        32,

                      right:
                        2,

                      zIndex:
                        80,

                      width:
                        150,

                      padding:
                        4,

                      border:
                        "1px solid var(--color-border)",

                      borderRadius:
                        7,

                      background:
                        "#fffefa",

                      color:
                        "#404244",

                      boxShadow:
                        "0 10px 26px rgba(0,0,0,.16)",
                    }}
                  >
                    <button
                      type="button"
                      onClick={() =>
                        onRename(
                          channel,
                        )
                      }
                      style={menuButtonStyle}
                    >
                      <Pencil
                        size={
                          11
                        }
                      />

                      Rename
                    </button>


                    <button
                      type="button"
                      onClick={() =>
                        onArchive(
                          channel,
                        )
                      }
                      style={{
                        ...menuButtonStyle,

                        color:
                          "#b52b2b",
                      }}
                    >
                      <Trash2
                        size={
                          11
                        }
                      />

                      Archive
                    </button>
                  </div>
                ) : null}
              </div>
            );
          },
        )}
      </div>
    </div>
  );
}


function ChannelIcon({
  channel,
}: {
  channel:
    WorkspaceChannel;
}) {
  if (
    channel.channel_type ===
    "voice"
  ) {
    return (
      <Volume2
        size={
          13
        }
      />
    );
  }


  if (
    channel.channel_type ===
    "announcement"
  ) {
    return (
      <Megaphone
        size={
          13
        }
      />
    );
  }


  return (
    <Hash
      size={
        13
      }
    />
  );
}


const iconButtonStyle = {
  display:
    "grid",

  width:
    28,

  height:
    28,

  placeItems:
    "center",

  border:
    "1px solid var(--color-border)",

  borderRadius:
    6,

  background:
    "#fffefa",

  color:
    "#555",

  cursor:
    "pointer",
} as const;


const menuButtonStyle = {
  display:
    "flex",

  alignItems:
    "center",

  gap:
    7,

  width:
    "100%",

  padding:
    "7px 8px",

  border:
    0,

  borderRadius:
    5,

  background:
    "transparent",

  color:
    "#404244",

  textAlign:
    "left",

  fontSize:
    8,

  cursor:
    "pointer",
} as const;