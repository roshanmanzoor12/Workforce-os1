"use client";

import {
  Archive,
  Ban,
  Hash,
  Headphones,
  HeadphoneOff,
  Megaphone,
  Mic,
  MicOff,
  MonitorUp,
  Pencil,
  PhoneOff,
  Plus,
  RefreshCcw,
  Search,
  Settings2,
  UserMinus,
  Volume2,
  VolumeX,
  X,
} from "lucide-react";

import {
  useCallback,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import {
  ChannelRealtimeRoom,
} from "@/components/channels/channel-realtime-room";

import {
  ChannelUnreadSidebarSection,
} from "@/components/channels/channel-unread-sidebar-section";

import {
  ChannelUnreadWorkspaceProvider,
} from "@/components/channels/channel-unread-provider";

import {
  VoiceConnectionBar,
} from "@/components/channels/voice-connection-bar";

import {
  WorkspaceRequired,
} from "@/components/workspace/workspace-required";

import {
  useWorkspace,
} from "@/contexts/workspace-context";

import {
  useVoiceChannel,
} from "@/hooks/use-voice-channel";

import {
  employeesService,
  type Employee,
} from "@/services/employees.service";

import {
  workspaceChannelsService,
  type VoiceParticipantPublic,
  type WorkspaceChannelPublic,
  type WorkspaceChannelType,
} from "@/services/workspace-channels.service";


export default function ChannelsPage() {
  return (
    <WorkspaceRequired>
      <ChannelsContent />
    </WorkspaceRequired>
  );
}


function ChannelsContent() {
  const {
    workspaceId,
    workspace,
    user,
  } =
    useWorkspace();


  const [
    channels,
    setChannels,
  ] =
    useState<WorkspaceChannelPublic[]>(
      [],
    );


  const [
    employees,
    setEmployees,
  ] =
    useState<Employee[]>(
      [],
    );


  /*
   * selectedChannelId controls what the user is viewing.
   *
   * connectedVoiceChannelId controls the active voice connection.
   *
   * Keeping them separate gives Discord-style behavior:
   * user can remain connected to voice while browsing text channels.
   */
  const [
    selectedChannelId,
    setSelectedChannelId,
  ] =
    useState<string | null>(
      null,
    );


  const [
    connectedVoiceChannelId,
    setConnectedVoiceChannelId,
  ] =
    useState<string | null>(
      null,
    );


  const [
    search,
    setSearch,
  ] =
    useState(
      "",
    );


  const [
    loading,
    setLoading,
  ] =
    useState(
      true,
    );


  const [
    showCreate,
    setShowCreate,
  ] =
    useState(
      false,
    );


  const [
    showSettings,
    setShowSettings,
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


  const selectedChannel =
    useMemo(
      () =>
        channels.find(
          (
            channel,
          ) =>
            channel.id ===
            selectedChannelId,
        ) ??
        null,
      [
        channels,
        selectedChannelId,
      ],
    );


  const connectedVoiceChannel =
    useMemo(
      () =>
        channels.find(
          (
            channel,
          ) =>
            channel.id ===
            connectedVoiceChannelId &&
            channel.channel_type ===
            "voice",
        ) ??
        null,
      [
        channels,
        connectedVoiceChannelId,
      ],
    );


  const voice =
    useVoiceChannel({
      workspaceId,

      channelId:
        connectedVoiceChannelId,

      currentUserId:
        user?.id ??
        null,
    });


  const employeeByUserId =
    useMemo(
      () => {
        const map =
          new Map<
            string,
            Employee
          >();


        for (
          const employee
          of employees
        ) {
          if (
            employee.user_id
          ) {
            map.set(
              employee.user_id,
              employee,
            );
          }
        }


        return map;
      },
      [
        employees,
      ],
    );


  const load =
    useCallback(
      async () => {
        if (
          !workspaceId
        ) {
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
            await workspaceChannelsService.list(
              workspaceId,
            );


          const active =
            response.filter(
              (
                channel,
              ) =>
                channel.is_active,
            );


          setChannels(
            active,
          );


          setSelectedChannelId(
            (
              current,
            ) => {
              if (
                current &&
                active.some(
                  (
                    channel,
                  ) =>
                    channel.id ===
                    current,
                )
              ) {
                return current;
              }


              return (
                active[0]?.id ??
                null
              );
            },
          );


          setConnectedVoiceChannelId(
            (
              current,
            ) => {
              if (
                current &&
                active.some(
                  (
                    channel,
                  ) =>
                    channel.id ===
                      current &&
                    channel.channel_type ===
                      "voice",
                )
              ) {
                return current;
              }


              return null;
            },
          );


          try {
            const employeeResponse =
              await employeesService.list(
                workspaceId,
              );


            setEmployees(
              employeeResponse.employees,
            );

          } catch {
            /*
             * Channel usage should not completely fail if
             * the current role cannot list employee records.
             */
            setEmployees(
              [],
            );
          }

        } catch (
          cause
        ) {
          setError(
            cause instanceof Error
              ? cause.message
              : "Unable to load channels.",
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


  useEffect(
    () => {
      void load();
    },
    [
      load,
    ],
  );


  /*
   * If hook loses the call unexpectedly, remove the
   * connected channel marker too.
   */
  useEffect(
    () => {
      if (
        connectedVoiceChannelId &&
        !voice.joined &&
        !voice.joining &&
        voice.call ===
          null
      ) {
        /*
         * Do not immediately clear while initial connection
         * is being prepared. Only clean stale state after
         * actual hook lifecycle settles.
         */
      }
    },
    [
      connectedVoiceChannelId,
      voice.joined,
      voice.joining,
      voice.call,
    ],
  );


  const filteredChannels =
    useMemo(
      () => {
        const query =
          search
            .trim()
            .toLowerCase();


        if (
          !query
        ) {
          return channels;
        }


        return channels.filter(
          (
            channel,
          ) =>
            `${channel.name} ${channel.slug} ${channel.channel_type}`
              .toLowerCase()
              .includes(
                query,
              ),
        );
      },
      [
        channels,
        search,
      ],
    );


  const textChannels =
    filteredChannels.filter(
      (
        channel,
      ) =>
        channel.channel_type ===
          "text" ||
        channel.channel_type ===
          "announcement",
    );


  const voiceChannels =
    filteredChannels.filter(
      (
        channel,
      ) =>
        channel.channel_type ===
        "voice",
    );


  function selectChannel(
    channel:
      WorkspaceChannelPublic,
  ) {
    setSelectedChannelId(
      channel.id,
    );
  }


  async function joinSelectedVoiceChannel() {
    if (
      !selectedChannel ||
      selectedChannel.channel_type !==
        "voice"
    ) {
      return;
    }


    /*
     * Already connected to this exact voice room.
     */
    if (
      connectedVoiceChannelId ===
        selectedChannel.id &&
      voice.joined
    ) {
      return;
    }


    /*
     * Discord-style single current voice room:
     * disconnect old room first.
     */
    if (
      voice.joined &&
      connectedVoiceChannelId &&
      connectedVoiceChannelId !==
        selectedChannel.id
    ) {
      await voice.leave();
    }


    setConnectedVoiceChannelId(
      selectedChannel.id,
    );
  }


  /*
   * The hook receives the channel id after state update,
   * therefore join on the following render.
   */
  useEffect(
    () => {
      if (
        !connectedVoiceChannelId ||
        voice.joined ||
        voice.joining
      ) {
        return;
      }


      void voice.join();
    },
    [
      connectedVoiceChannelId,
      voice.joined,
      voice.joining,
      voice.join,
    ],
  );


  async function disconnectVoice() {
    await voice.leave();


    setConnectedVoiceChannelId(
      null,
    );
  }


  async function archiveSelectedChannel() {
    if (
      !selectedChannel
    ) {
      return;
    }


    if (
      !window.confirm(
        `Archive "${selectedChannel.name}"?`,
      )
    ) {
      return;
    }


    try {
      if (
        connectedVoiceChannelId ===
        selectedChannel.id
      ) {
        await disconnectVoice();
      }


      await workspaceChannelsService.archive(
        selectedChannel.id,
      );


      setShowSettings(
        false,
      );


      await load();

    } catch (
      cause
    ) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Unable to archive channel.",
      );
    }
  }


  return (
    <ChannelUnreadWorkspaceProvider
      workspaceId={
        workspaceId
      }
    >
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

          justifyContent:
            "space-between",

          alignItems:
            "flex-start",

          gap:
            12,
        }}
      >
        <div>
          <h1>
            Channels
          </h1>


          <p
            className="text-label"
            style={{
              marginTop:
                4,
            }}
          >
            Text, announcement and voice channels for{" "}
            {workspace?.name ??
              "this workspace"}.
          </p>
        </div>


        <div
          style={{
            display:
              "flex",

            gap:
              8,
          }}
        >
          <button
            type="button"
            className="button button--outline"
            onClick={() => {
              void load();
            }}
          >
            <RefreshCcw
              size={
                14
              }
            />

            Refresh
          </button>


          <button
            type="button"
            className="button button--primary"
            onClick={() =>
              setShowCreate(
                true,
              )
            }
          >
            <Plus
              size={
                14
              }
            />

            New Channel
          </button>
        </div>
      </header>


      {error ? (
        <div
          style={errorStyle}
        >
          {error}
        </div>
      ) : null}


      {voice.error ? (
        <div
          style={errorStyle}
        >
          {voice.error}
        </div>
      ) : null}


      <section
        style={{
          display:
            "grid",

          gridTemplateColumns:
            "250px minmax(0,1fr)",

          minHeight:
            680,

          overflow:
            "hidden",

          border:
            "1px solid var(--color-border)",

          borderRadius:
            9,

          background:
            "#fffefa",
        }}
      >
        <aside
          style={{
            display:
              "grid",

            gridTemplateRows:
              "auto minmax(0,1fr) auto",

            minHeight:
              680,

            borderRight:
              "1px solid var(--color-border)",

            background:
              "#f7f4ee",
          }}
        >
          <div
            style={{
              padding:
                9,

              borderBottom:
                "1px solid var(--color-border)",
            }}
          >
            <div
              style={{
                position:
                  "relative",
              }}
            >
              <Search
                size={
                  13
                }
                style={{
                  position:
                    "absolute",

                  left:
                    10,

                  top:
                    10,

                  color:
                    "#888",
                }}
              />


              <input
                value={
                  search
                }
                placeholder="Find channel"
                onChange={(
                  event,
                ) =>
                  setSearch(
                    event.target.value,
                  )
                }
                style={{
                  ...inputStyle,

                  paddingLeft:
                    31,
                }}
              />
            </div>
          </div>


          <div
            style={{
              overflowY:
                "auto",

              padding:
                7,
            }}
          >
            {loading ? (
              <div
                className="skeleton"
                style={{
                  height:
                    300,
                }}
              />
            ) : (
              <>
                <SectionLabel>
                  TEXT CHANNELS
                </SectionLabel>


                <ChannelUnreadSidebarSection
                  channels={
                    textChannels
                  }
                  selectedChannelId={
                    selectedChannelId
                  }
                  connectedVoiceChannelId={
                    connectedVoiceChannelId
                  }
                  onSelect={(
                    channelId,
                  ) => {
                    setSelectedChannelId(
                      channelId,
                    );
                  }}
                />


                <div
                  style={{
                    height:
                      12,
                  }}
                />


                <SectionLabel>
                  VOICE CHANNELS
                </SectionLabel>


                {voiceChannels.map(
                  (
                    channel,
                  ) => {
                    const connected =
                      channel.id ===
                      connectedVoiceChannelId;


                    return (
                      <div
                        key={
                          channel.id
                        }
                      >
                        <ChannelButton
                          channel={
                            channel
                          }
                          selected={
                            channel.id ===
                            selectedChannelId
                          }
                          connected={
                            connected &&
                            voice.joined
                          }
                          onClick={() =>
                            selectChannel(
                              channel,
                            )
                          }
                        />


                        {connected &&
                        voice.participants.length >
                          0 ? (
                          <div
                            style={{
                              padding:
                                "3px 4px 6px 29px",
                            }}
                          >
                            {voice.participants
                              .filter(
                                (
                                  participant,
                                ) =>
                                  !participant.left_at,
                              )
                              .map(
                                (
                                  participant,
                                ) => (
                                  <div
                                    key={
                                      participant.user_id
                                    }
                                    style={{
                                      display:
                                        "flex",

                                      alignItems:
                                        "center",

                                      gap:
                                        5,

                                      padding:
                                        "4px 5px",

                                      color:
                                        participant.speaking
                                          ? "#347c2d"
                                          : "#717375",

                                      fontSize:
                                        8,
                                    }}
                                  >
                                    {participant.effective_muted ? (
                                      <MicOff
                                        size={
                                          9
                                        }
                                      />
                                    ) : (
                                      <Mic
                                        size={
                                          9
                                        }
                                      />
                                    )}


                                    <span
                                      style={{
                                        overflow:
                                          "hidden",

                                        textOverflow:
                                          "ellipsis",

                                        whiteSpace:
                                          "nowrap",
                                      }}
                                    >
                                      {displayUserName(
                                        participant.user_id,
                                        user?.id ??
                                          null,
                                        employeeByUserId,
                                      )}
                                    </span>
                                  </div>
                                ),
                              )}
                          </div>
                        ) : null}
                      </div>
                    );
                  },
                )}
              </>
            )}
          </div>


          {connectedVoiceChannel &&
          voice.joined ? (
            <VoiceConnectionBar
              channelName={
                connectedVoiceChannel.name
              }
              muted={
                voice.selfParticipant
                  ?.self_muted ??
                false
              }
              deafened={
                voice.selfParticipant
                  ?.self_deafened ??
                false
              }
              screenSharing={
                Boolean(
                  voice.localScreenStream,
                )
              }
              busy={
                voice.busy
              }
              onOpen={() =>
                setSelectedChannelId(
                  connectedVoiceChannel.id,
                )
              }
              onToggleMute={() => {
                void voice.toggleSelfMute();
              }}
              onToggleDeafen={() => {
                void voice.toggleSelfDeafen();
              }}
              onToggleScreenShare={() => {
                void voice.toggleScreenShare();
              }}
              onDisconnect={() => {
                void disconnectVoice();
              }}
            />
          ) : null}
        </aside>


        <main
          style={{
            minWidth:
              0,
          }}
        >
          {!selectedChannel ? (
            <EmptyRoom />
          ) : selectedChannel.channel_type ===
            "voice" ? (
            <VoiceRoom
              channel={
                selectedChannel
              }
              isConnected={
                connectedVoiceChannelId ===
                  selectedChannel.id &&
                voice.joined
              }
              isConnecting={
                connectedVoiceChannelId ===
                  selectedChannel.id &&
                voice.joining
              }
              currentUserId={
                user?.id ??
                null
              }
              employeeByUserId={
                employeeByUserId
              }
              voice={
                voice
              }
              onJoin={() => {
                void joinSelectedVoiceChannel();
              }}
              onDisconnect={() => {
                void disconnectVoice();
              }}
              onSettings={() =>
                setShowSettings(
                  true,
                )
              }
            />
          ) : workspaceId ? (
            <ChannelRealtimeRoom
              workspaceId={
                workspaceId
              }
              channelId={
                selectedChannel.id
              }
              channelName={
                selectedChannel.name
              }
              currentUserId={
                user?.id ??
                null
              }
            />
          ) : (
            <EmptyRoom />
          )}
        </main>
      </section>


      {showCreate &&
      workspaceId ? (
        <CreateChannelModal
          workspaceId={
            workspaceId
          }
          onClose={() =>
            setShowCreate(
              false,
            )
          }
          onCreated={async (
            channel,
          ) => {
            setShowCreate(
              false,
            );


            await load();


            setSelectedChannelId(
              channel.id,
            );
          }}
        />
      ) : null}


      {showSettings &&
      selectedChannel ? (
        <ChannelSettingsModal
          channel={
            selectedChannel
          }
          onClose={() =>
            setShowSettings(
              false,
            )
          }
          onRenamed={(
            updated,
          ) => {
            setChannels(
              (
                current,
              ) =>
                current.map(
                  (
                    channel,
                  ) =>
                    channel.id ===
                    updated.id
                      ? updated
                      : channel,
                ),
            );


            setShowSettings(
              false,
            );
          }}
          onArchive={() => {
            void archiveSelectedChannel();
          }}
        />
      ) : null}
      </div>
    </ChannelUnreadWorkspaceProvider>
  );
}


/* -------------------------------------------------------------------------- */
/* Voice room                                                                  */
/* -------------------------------------------------------------------------- */

function VoiceRoom({
  channel,

  isConnected,

  isConnecting,

  currentUserId,

  employeeByUserId,

  voice,

  onJoin,

  onDisconnect,

  onSettings,
}: {
  channel:
    WorkspaceChannelPublic;

  isConnected:
    boolean;

  isConnecting:
    boolean;

  currentUserId:
    string | null;

  employeeByUserId:
    Map<string, Employee>;

  voice:
    ReturnType<
      typeof useVoiceChannel
    >;

  onJoin:
    () => void;

  onDisconnect:
    () => void;

  onSettings:
    () => void;
}) {
  return (
    <div
      style={{
        display:
          "grid",

        gridTemplateRows:
          "auto minmax(0,1fr) auto",

        minHeight:
          680,
      }}
    >
      <RoomHeader
        icon={
          <Volume2
            size={
              14
            }
          />
        }
        title={
          channel.name
        }
        subtitle={
          isConnected
            ? "Voice connected"
            : "Voice channel"
        }
        onSettings={
          onSettings
        }
      />


      <div
        style={{
          padding:
            14,

          overflowY:
            "auto",
        }}
      >
        {!isConnected ? (
          <div
            style={{
              display:
                "grid",

              minHeight:
                500,

              placeItems:
                "center",

              textAlign:
                "center",
            }}
          >
            <div>
              <div
                style={{
                  display:
                    "grid",

                  width:
                    64,

                  height:
                    64,

                  margin:
                    "0 auto 12px",

                  placeItems:
                    "center",

                  borderRadius:
                    18,

                  background:
                    "#f1ede2",

                  color:
                    "#846813",
                }}
              >
                <Volume2
                  size={
                    28
                  }
                />
              </div>


              <h2>
                {channel.name}
              </h2>


              <p
                className="text-label"
                style={{
                  maxWidth:
                    390,

                  margin:
                    "6px auto 14px",
                }}
              >
                Join this room to talk with workspace members.
              </p>


              <button
                type="button"
                className="button button--primary"
                disabled={
                  isConnecting
                }
                onClick={
                  onJoin
                }
              >
                <Mic
                  size={
                    14
                  }
                />

                {isConnecting
                  ? "Joining..."
                  : "Join Voice"}
              </button>
            </div>
          </div>
        ) : (
          <div
            style={{
              display:
                "grid",

              gap:
                10,
            }}
          >
            {voice.localScreenStream ? (
              <ScreenVideo
                title="Your screen"
                stream={
                  voice.localScreenStream
                }
                muted
              />
            ) : null}


            {voice.participants
              .filter(
                (
                  participant,
                ) =>
                  participant.screen_sharing &&
                  participant.user_id !==
                    currentUserId,
              )
              .map(
                (
                  participant,
                ) => {
                  const stream =
                    voice.remoteStreams[
                      participant.user_id
                    ];


                  if (
                    !stream
                  ) {
                    return null;
                  }


                  return (
                    <ScreenVideo
                      key={
                        participant.user_id
                      }
                      title={`${displayUserName(
                        participant.user_id,
                        currentUserId,
                        employeeByUserId,
                      )} is sharing`}
                      stream={
                        stream
                      }
                      muted={
                        voice.selfParticipant
                          ?.effective_deafened ??
                        false
                      }
                    />
                  );
                },
              )}


            {Object.entries(
              voice.remoteStreams,
            ).map(
              ([
                userId,
                stream,
              ]) => (
                <audio
                  key={
                    userId
                  }
                  autoPlay
                  muted={
                    voice.selfParticipant
                      ?.effective_deafened ??
                    false
                  }
                  ref={(
                    element,
                  ) => {
                    if (
                      element &&
                      element.srcObject !==
                        stream
                    ) {
                      element.srcObject =
                        stream;
                    }
                  }}
                />
              ),
            )}


            <section
              className="panel"
            >
              <div
                style={{
                  padding:
                    "10px 12px",

                  borderBottom:
                    "1px solid var(--color-border)",
                }}
              >
                <strong>
                  Connected members
                </strong>
              </div>


              <div
                style={{
                  display:
                    "grid",

                  gap:
                    7,

                  padding:
                    10,
                }}
              >
                {voice.participants
                  .filter(
                    (
                      participant,
                    ) =>
                      !participant.left_at,
                  )
                  .map(
                    (
                      participant,
                    ) => (
                      <VoiceParticipantRow
                        key={
                          participant.user_id
                        }
                        participant={
                          participant
                        }
                        currentUserId={
                          currentUserId
                        }
                        employeeByUserId={
                          employeeByUserId
                        }
                        busy={
                          voice.busy
                        }
                        onMute={() => {
                          void voice.moderate(
                            participant,
                            "server_muted",
                          );
                        }}
                        onDeafen={() => {
                          void voice.moderate(
                            participant,
                            "server_deafened",
                          );
                        }}
                        onKick={() => {
                          if (
                            window.confirm(
                              "Kick this user from the voice channel?",
                            )
                          ) {
                            void voice.kick(
                              participant.user_id,
                            );
                          }
                        }}
                        onBan={() => {
                          const reason =
                            window.prompt(
                              "Optional ban reason:",
                              "",
                            );


                          if (
                            reason ===
                            null
                          ) {
                            return;
                          }


                          void voice.ban(
                            participant.user_id,
                            reason.trim() ||
                              null,
                          );
                        }}
                      />
                    ),
                  )}
              </div>
            </section>
          </div>
        )}
      </div>


      {isConnected ? (
        <div
          style={{
            display:
              "flex",

            justifyContent:
              "space-between",

            alignItems:
              "center",

            gap:
              8,

            padding:
              10,

            borderTop:
              "1px solid var(--color-border)",

            background:
              "#f7f4ee",
          }}
        >
          <div
            style={{
              display:
                "flex",

              gap:
                7,
            }}
          >
            <button
              type="button"
              className="button button--outline"
              disabled={
                voice.busy
              }
              onClick={() => {
                void voice.toggleSelfMute();
              }}
            >
              {voice.selfParticipant
                ?.self_muted ? (
                <MicOff
                  size={
                    14
                  }
                />
              ) : (
                <Mic
                  size={
                    14
                  }
                />
              )}

              {voice.selfParticipant
                ?.self_muted
                ? "Unmute"
                : "Mute"}
            </button>


            <button
              type="button"
              className="button button--outline"
              disabled={
                voice.busy
              }
              onClick={() => {
                void voice.toggleSelfDeafen();
              }}
            >
              {voice.selfParticipant
                ?.self_deafened ? (
                <HeadphoneOff
                  size={
                    14
                  }
                />
              ) : (
                <Headphones
                  size={
                    14
                  }
                />
              )}

              {voice.selfParticipant
                ?.self_deafened
                ? "Undeafen"
                : "Deafen"}
            </button>


            <button
              type="button"
              className="button button--outline"
              disabled={
                voice.busy ||
                voice.capabilities
                  ?.screen_share ===
                  false
              }
              onClick={() => {
                void voice.toggleScreenShare();
              }}
            >
              <MonitorUp
                size={
                  14
                }
              />

              {voice.localScreenStream
                ? "Stop Share"
                : "Share Screen"}
            </button>
          </div>


          <button
            type="button"
            className="button button--outline"
            style={{
              color:
                "#b52b2b",
            }}
            onClick={
              onDisconnect
            }
          >
            <PhoneOff
              size={
                14
              }
            />

            Disconnect
          </button>
        </div>
      ) : null}
    </div>
  );
}


function VoiceParticipantRow({
  participant,

  currentUserId,

  employeeByUserId,

  busy,

  onMute,

  onDeafen,

  onKick,

  onBan,
}: {
  participant:
    VoiceParticipantPublic;

  currentUserId:
    string | null;

  employeeByUserId:
    Map<string, Employee>;

  busy:
    boolean;

  onMute:
    () => void;

  onDeafen:
    () => void;

  onKick:
    () => void;

  onBan:
    () => void;
}) {
  const mine =
    participant.user_id ===
    currentUserId;


  return (
    <div
      style={{
        display:
          "grid",

        gridTemplateColumns:
          "34px minmax(0,1fr) auto",

        alignItems:
          "center",

        gap:
          8,

        padding:
          9,

        border:
          participant.speaking
            ? "1px solid #84bc79"
            : "1px solid var(--color-border)",

        borderRadius:
          8,

        background:
          participant.speaking
            ? "#f2faef"
            : "#fffefa",
      }}
    >
      <div
        style={{
          display:
            "grid",

          width:
            32,

          height:
            32,

          placeItems:
            "center",

          borderRadius:
            999,

          background:
            "#ede8dc",

          fontSize:
            8,

          fontWeight:
            700,
        }}
      >
        {mine
          ? "YOU"
          : "U"}
      </div>


      <div
        style={{
          minWidth:
            0,
        }}
      >
        <strong
          style={{
            display:
              "block",

            overflow:
              "hidden",

            textOverflow:
              "ellipsis",

            whiteSpace:
              "nowrap",

            fontSize:
              9,
          }}
        >
          {displayUserName(
            participant.user_id,
            currentUserId,
            employeeByUserId,
          )}
        </strong>


        <div
          className="text-label"
          style={{
            display:
              "flex",

            alignItems:
              "center",

            gap:
              5,

            marginTop:
              3,

            fontSize:
              7,
          }}
        >
          {participant.presence}

          {participant.effective_muted ? (
            <MicOff
              size={
                9
              }
            />
          ) : null}

          {participant.effective_deafened ? (
            <HeadphoneOff
              size={
                9
              }
            />
          ) : null}

          {participant.screen_sharing ? (
            <MonitorUp
              size={
                9
              }
            />
          ) : null}
        </div>
      </div>


      {!mine ? (
        <div
          style={{
            display:
              "flex",

            gap:
              5,
          }}
        >
          <button
            type="button"
            className="button button--outline"
            disabled={
              busy
            }
            title={
              participant.server_muted
                ? "Server unmute"
                : "Server mute"
            }
            onClick={
              onMute
            }
          >
            {participant.server_muted ? (
              <Mic
                size={
                  12
                }
              />
            ) : (
              <MicOff
                size={
                  12
                }
              />
            )}
          </button>


          <button
            type="button"
            className="button button--outline"
            disabled={
              busy
            }
            title={
              participant.server_deafened
                ? "Server undeafen"
                : "Server deafen"
            }
            onClick={
              onDeafen
            }
          >
            {participant.server_deafened ? (
              <Headphones
                size={
                  12
                }
              />
            ) : (
              <VolumeX
                size={
                  12
                }
              />
            )}
          </button>


          <button
            type="button"
            className="button button--outline"
            disabled={
              busy
            }
            title="Kick from voice"
            onClick={
              onKick
            }
          >
            <UserMinus
              size={
                12
              }
            />
          </button>


          <button
            type="button"
            className="button button--outline"
            disabled={
              busy
            }
            title="Ban from voice"
            style={{
              color:
                "#b52b2b",
            }}
            onClick={
              onBan
            }
          >
            <Ban
              size={
                12
              }
            />
          </button>
        </div>
      ) : null}
    </div>
  );
}


/* -------------------------------------------------------------------------- */
/* Shared room header                                                          */
/* -------------------------------------------------------------------------- */

function RoomHeader({
  icon,

  title,

  subtitle,

  onSettings,
}: {
  icon:
    ReactNode;

  title:
    string;

  subtitle:
    string;

  onSettings:
    () => void;
}) {
  return (
    <div
      style={{
        display:
          "flex",

        justifyContent:
          "space-between",

        alignItems:
          "center",

        gap:
          10,

        padding:
          "10px 13px",

        borderBottom:
          "1px solid var(--color-border)",
      }}
    >
      <div>
        <strong
          style={{
            display:
              "flex",

            alignItems:
              "center",

            gap:
              6,
          }}
        >
          {icon}

          {title}
        </strong>


        <div
          className="text-label"
          style={{
            marginTop:
              3,
          }}
        >
          {subtitle}
        </div>
      </div>


      <button
        type="button"
        className="button button--outline"
        onClick={
          onSettings
        }
      >
        <Settings2
          size={
            13
          }
        />

        Channel
      </button>
    </div>
  );
}


/* -------------------------------------------------------------------------- */
/* Channel button                                                              */
/* -------------------------------------------------------------------------- */
function ChannelButton({
  channel,

  selected,

  connected,

  onClick,
}: {
  channel:
    WorkspaceChannelPublic;

  selected:
    boolean;

  connected:
    boolean;

  onClick:
    () => void;
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
          "22px minmax(0,1fr) auto",

        gap:
          6,

        alignItems:
          "center",

        width:
          "100%",

        padding:
          "7px 8px",

        border:
          0,

        borderRadius:
          6,

        background:
          selected
            ? "#2e3032"
            : "transparent",

        color:
          selected
            ? "#fff"
            : "#505254",

        textAlign:
          "left",

        cursor:
          "pointer",
      }}
    >
      {channel.channel_type ===
      "voice" ? (
        <Volume2
          size={
            13
          }
        />
      ) : channel.channel_type ===
        "announcement" ? (
        <Megaphone
          size={
            13
          }
        />
      ) : (
        <Hash
          size={
            13
          }
        />
      )}


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
            600,
        }}
      >
        {channel.name}
      </span>


      {connected ? (
        <span
          title="Connected"
          style={{
            width:
              7,

            height:
              7,

            borderRadius:
              999,

            background:
              "#65b85a",
          }}
        />
      ) : null}
    </button>
  );
}


function SectionLabel({
  children,
}: {
  children:
    ReactNode;
}) {
  return (
    <div
      style={{
        padding:
          "7px 8px 4px",

        color:
          "#888",

        fontSize:
          7,

        fontWeight:
          700,

        letterSpacing:
          ".08em",
      }}
    >
      {children}
    </div>
  );
}


function ScreenVideo({
  title,

  stream,

  muted,
}: {
  title:
    string;

  stream:
    MediaStream;

  muted:
    boolean;
}) {
  return (
    <section
      className="panel"
      style={{
        overflow:
          "hidden",
      }}
    >
      <div
        style={{
          padding:
            "8px 11px",

          borderBottom:
            "1px solid var(--color-border)",
        }}
      >
        <strong>
          {title}
        </strong>
      </div>


      <video
        autoPlay
        playsInline
        muted={
          muted
        }
        ref={(
          element,
        ) => {
          if (
            element &&
            element.srcObject !==
              stream
          ) {
            element.srcObject =
              stream;
          }
        }}
        style={{
          display:
            "block",

          width:
            "100%",

          maxHeight:
            480,

          background:
            "#17181a",

          objectFit:
            "contain",
        }}
      />
    </section>
  );
}


/* -------------------------------------------------------------------------- */
/* Create/settings                                                             */
/* -------------------------------------------------------------------------- */

function CreateChannelModal({
  workspaceId,

  onClose,

  onCreated,
}: {
  workspaceId:
    string;

  onClose:
    () => void;

  onCreated:
    (
      channel:
        WorkspaceChannelPublic,
    ) => Promise<void>;
}) {
  const [
    name,
    setName,
  ] =
    useState(
      "",
    );


  const [
    type,
    setType,
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
    modalError,
    setModalError,
  ] =
    useState<string | null>(
      null,
    );


  async function create() {
    if (
      !name.trim() ||
      saving
    ) {
      return;
    }


    try {
      setSaving(
        true,
      );

      setModalError(
        null,
      );


      const channel =
        await workspaceChannelsService.create(
          {
            workspace_id:
              workspaceId,

            name:
              name.trim(),

            channel_type:
              type,
          },
        );


      await onCreated(
        channel,
      );

    } catch (
      cause
    ) {
      setModalError(
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
    <ModalShell
      title="Create Channel"
      onClose={
        onClose
      }
    >
      {modalError ? (
        <div
          style={errorStyle}
        >
          {modalError}
        </div>
      ) : null}


      <label
        style={labelStyle}
      >
        Name

        <input
          autoFocus
          value={
            name
          }
          maxLength={
            120
          }
          onChange={(
            event,
          ) =>
            setName(
              event.target.value,
            )
          }
          style={inputStyle}
        />
      </label>


      <label
        style={labelStyle}
      >
        Type

        <select
          value={
            type
          }
          onChange={(
            event,
          ) =>
            setType(
              event.target.value as
                WorkspaceChannelType,
            )
          }
          style={inputStyle}
        >
          <option value="text">
            Text
          </option>

          <option value="announcement">
            Announcement
          </option>

          <option value="voice">
            Voice
          </option>
        </select>
      </label>


      <div
        style={{
          display:
            "flex",

          justifyContent:
            "flex-end",

          gap:
            8,
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
          <Plus
            size={
              13
            }
          />

          {saving
            ? "Creating..."
            : "Create Channel"}
        </button>
      </div>
    </ModalShell>
  );
}


function ChannelSettingsModal({
  channel,

  onClose,

  onRenamed,

  onArchive,
}: {
  channel:
    WorkspaceChannelPublic;

  onClose:
    () => void;

  onRenamed:
    (
      channel:
        WorkspaceChannelPublic,
    ) => void;

  onArchive:
    () => void;
}) {
  const [
    name,
    setName,
  ] =
    useState(
      channel.name,
    );


  const [
    saving,
    setSaving,
  ] =
    useState(
      false,
    );


  const [
    modalError,
    setModalError,
  ] =
    useState<string | null>(
      null,
    );


  async function rename() {
    if (
      !name.trim() ||
      name.trim() ===
        channel.name
    ) {
      return;
    }


    try {
      setSaving(
        true,
      );

      setModalError(
        null,
      );


      const updated =
        await workspaceChannelsService.rename(
          channel.id,
          {
            name:
              name.trim(),
          },
        );


      onRenamed(
        updated,
      );

    } catch (
      cause
    ) {
      setModalError(
        cause instanceof Error
          ? cause.message
          : "Unable to rename channel.",
      );

    } finally {
      setSaving(
        false,
      );
    }
  }


  return (
    <ModalShell
      title="Channel Settings"
      onClose={
        onClose
      }
    >
      {modalError ? (
        <div
          style={errorStyle}
        >
          {modalError}
        </div>
      ) : null}


      <label
        style={labelStyle}
      >
        Name

        <input
          value={
            name
          }
          maxLength={
            120
          }
          onChange={(
            event,
          ) =>
            setName(
              event.target.value,
            )
          }
          style={inputStyle}
        />
      </label>


      <div
        style={{
          display:
            "flex",

          gap:
            8,
        }}
      >
        <button
          type="button"
          className="button button--primary"
          disabled={
            saving ||
            !name.trim() ||
            name.trim() ===
              channel.name
          }
          onClick={() => {
            void rename();
          }}
        >
          <Pencil
            size={
              13
            }
          />

          Rename
        </button>


        <button
          type="button"
          className="button button--outline"
          style={{
            color:
              "#b52b2b",
          }}
          onClick={
            onArchive
          }
        >
          <Archive
            size={
              13
            }
          />

          Archive
        </button>
      </div>
    </ModalShell>
  );
}


function ModalShell({
  title,

  onClose,

  children,
}: {
  title:
    string;

  onClose:
    () => void;

  children:
    ReactNode;
}) {
  return (
    <div
      style={{
        position:
          "fixed",

        inset:
          0,

        zIndex:
          110,

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
        className="panel"
        style={{
          width:
            "100%",

          maxWidth:
            500,
        }}
      >
        <div
          style={{
            display:
              "flex",

            justifyContent:
              "space-between",

            alignItems:
              "center",

            padding:
              "12px 14px",

            borderBottom:
              "1px solid var(--color-border)",
          }}
        >
          <strong>
            {title}
          </strong>


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
        </div>


        <div
          style={{
            display:
              "grid",

            gap:
              12,

            padding:
              14,
          }}
        >
          {children}
        </div>
      </section>
    </div>
  );
}


function EmptyRoom() {
  return (
    <div
      style={{
        display:
          "grid",

        minHeight:
          680,

        placeItems:
          "center",

        color:
          "#777",
      }}
    >
      Select a channel.
    </div>
  );
}


function displayUserName(
  userId:
    string,

  currentUserId:
    string | null,

  employeeByUserId:
    Map<string, Employee>,
): string {
  if (
    currentUserId &&
    userId ===
      currentUserId
  ) {
    return "You";
  }


  const employee =
    employeeByUserId.get(
      userId,
    );


  return (
    employee?.full_name ??
    `User ${userId.slice(
      0,
      8,
    )}`
  );
}


function formatDate(
  value:
    string,
): string {
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


const labelStyle = {
  display:
    "grid",

  gap:
    5,

  fontSize:
    9,
} as const;


const inputStyle = {
  width:
    "100%",

  height:
    36,

  padding:
    "0 10px",

  border:
    "1px solid var(--color-border)",

  borderRadius:
    7,

  background:
    "#fffefa",

  outline:
    "none",

  fontSize:
    10,
} as const;


const errorStyle = {
  padding:
    "10px 12px",

  border:
    "1px solid #efc6c6",

  borderRadius:
    7,

  background:
    "#fff0f0",

  color:
    "#b52b2b",

  fontSize:
    10,
} as const;