"use client";

import {
  Radio,
  Volume2,
} from "lucide-react";

import {
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";

import {
  VoiceControls,
} from "@/components/channels/voice-controls";

import {
  VoiceParticipantList,
} from "@/components/channels/voice-participant-list";

import {
  VoiceWebRtcClient,
} from "@/lib/voice/webrtc-client";

import {
  voiceChannelsService,
} from "@/services/voice-channels.service";

import type {
  VoiceParticipant,
  WorkspaceChannel,
} from "@/types/channels";


interface VoiceChannelRoomProps {
  workspaceId: string;

  channel: WorkspaceChannel;

  canModerate: boolean;
}


export function VoiceChannelRoom({
  workspaceId,
  channel,
  canModerate,
}: VoiceChannelRoomProps) {
  const [
    participants,
    setParticipants,
  ] =
    useState<
      VoiceParticipant[]
    >([]);

  const [
    selfUserId,
    setSelfUserId,
  ] =
    useState<
      string | null
    >(null);

  const [
    joined,
    setJoined,
  ] = useState(false);

  const [
    muted,
    setMuted,
  ] = useState(false);

  const [
    deafened,
    setDeafened,
  ] = useState(false);

  const [
    screenSharing,
    setScreenSharing,
  ] = useState(false);

  const [
    busy,
    setBusy,
  ] = useState(false);

  const [
    error,
    setError,
  ] =
    useState<
      string | null
    >(null);

  const [
    remoteStreams,
    setRemoteStreams,
  ] =
    useState<
      Record<
        string,
        MediaStream
      >
    >({});


  const rtcRef =
    useRef<
      VoiceWebRtcClient | null
    >(null);

  const audioContextRef =
    useRef<
      AudioContext | null
    >(null);

  const speakingTimerRef =
    useRef<
      number | null
    >(null);

  const lastSpeakingRef =
    useRef(false);

  const connectionIdRef =
    useRef(
      crypto.randomUUID(),
    );


  const refreshParticipants =
    useCallback(
      async () => {
        try {
          const result =
            await voiceChannelsService
              .participants(
                workspaceId,
                channel.id,
              );

          setParticipants(
            result.participants,
          );


          if (
            selfUserId &&
            rtcRef.current
          ) {
            const remoteUsers =
              result
                .participants
                .filter(
                  (
                    participant,
                  ) =>
                    participant
                      .user_id !==
                    selfUserId,
                )
                .map(
                  (
                    participant,
                  ) =>
                    participant
                      .user_id,
                );

            rtcRef.current
              .syncUsers(
                remoteUsers,
              );


            for (
              const remoteUserId
              of remoteUsers
            ) {
              const initiator =
                selfUserId
                  .localeCompare(
                    remoteUserId,
                  ) < 0;

              await rtcRef.current
                .ensurePeer(
                  remoteUserId,
                  initiator,
                );
            }
          }
        } catch (
          refreshError
        ) {
          if (joined) {
            setError(
              refreshError
                instanceof Error
                ? refreshError.message
                : "Unable to refresh voice participants.",
            );
          }
        }
      },
      [
        workspaceId,
        channel.id,
        selfUserId,
        joined,
      ],
    );


  const createRtc =
    useCallback(
      () => {
        const rtc =
          new VoiceWebRtcClient(
            {
              sendSignal:
                async (
                  targetUserId,
                  signalType,
                  payload,
                ) => {
                  await voiceChannelsService
                    .signal(
                      workspaceId,
                      channel.id,
                      {
                        signal_type:
                          signalType,

                        target_user_id:
                          targetUserId,

                        payload,
                      },
                    );
                },

              onRemoteStream:
                (
                  userId,
                  stream,
                ) => {
                  setRemoteStreams(
                    (
                      current,
                    ) => ({
                      ...current,
                      [
                        userId
                      ]:
                        stream,
                    }),
                  );
                },

              onRemoteStreamRemoved:
                (
                  userId,
                ) => {
                  setRemoteStreams(
                    (
                      current,
                    ) => {
                      const next =
                        {
                          ...current,
                        };

                      delete next[
                        userId
                      ];

                      return next;
                    },
                  );
                },
            },
          );

        rtcRef.current =
          rtc;

        return rtc;
      },
      [
        workspaceId,
        channel.id,
      ],
    );


  async function startSpeakingDetector(
    stream: MediaStream,
  ) {
    const audioContext =
      new AudioContext();

    audioContextRef.current =
      audioContext;

    const source =
      audioContext
        .createMediaStreamSource(
          stream,
        );

    const analyser =
      audioContext
        .createAnalyser();

    analyser.fftSize =
      512;

    analyser.smoothingTimeConstant =
      0.5;

    source.connect(
      analyser,
    );

    const values =
      new Uint8Array(
        analyser
          .frequencyBinCount,
      );


    speakingTimerRef.current =
      window.setInterval(
        () => {
          if (
            muted ||
            deafened
          ) {
            if (
              lastSpeakingRef
                .current
            ) {
              lastSpeakingRef.current =
                false;

              void voiceChannelsService
                .speaking(
                  workspaceId,
                  channel.id,
                  false,
                );
            }

            return;
          }

          analyser
            .getByteFrequencyData(
              values,
            );

          let total = 0;

          for (
            const value
            of values
          ) {
            total += value;
          }

          const average =
            total /
            values.length;

          const speaking =
            average > 18;

          if (
            speaking !==
            lastSpeakingRef
              .current
          ) {
            lastSpeakingRef.current =
              speaking;

            void voiceChannelsService
              .speaking(
                workspaceId,
                channel.id,
                speaking,
              );
          }
        },
        350,
      );
  }


  function stopSpeakingDetector() {
    if (
      speakingTimerRef
        .current !==
      null
    ) {
      window.clearInterval(
        speakingTimerRef
          .current,
      );

      speakingTimerRef.current =
        null;
    }

    if (
      audioContextRef.current
    ) {
      void audioContextRef
        .current
        .close();

      audioContextRef.current =
        null;
    }

    lastSpeakingRef.current =
      false;
  }


  async function handleJoin() {
    try {
      setBusy(
        true,
      );

      setError(
        null,
      );

      const result =
        await voiceChannelsService
          .join(
            workspaceId,
            channel.id,
          );

      setSelfUserId(
        result
          .participant
          .user_id,
      );

      setParticipants(
        result
          .call
          .participants,
      );

      setMuted(
        result
          .participant
          .self_muted,
      );

      setDeafened(
        result
          .participant
          .self_deafened,
      );

      const rtc =
        createRtc();

      const stream =
        await rtc
          .startMicrophone();

      await startSpeakingDetector(
        stream,
      );

      setJoined(
        true,
      );
    } catch (
      joinError
    ) {
      setError(
        joinError
          instanceof Error
          ? joinError.message
          : "Unable to join voice channel.",
      );

      if (
        rtcRef.current
      ) {
        await rtcRef
          .current
          .destroy();

        rtcRef.current =
          null;
      }
    } finally {
      setBusy(
        false,
      );
    }
  }


  const handleLeave =
    useCallback(
      async () => {
        try {
          setBusy(
            true,
          );

          if (
            joined
          ) {
            await voiceChannelsService
              .leave(
                workspaceId,
                channel.id,
              );
          }
        } catch {
          // Local disconnect still proceeds.
        } finally {
          stopSpeakingDetector();

          if (
            rtcRef.current
          ) {
            await rtcRef
              .current
              .destroy();

            rtcRef.current =
              null;
          }

          setJoined(
            false,
          );

          setSelfUserId(
            null,
          );

          setParticipants(
            [],
          );

          setRemoteStreams(
            {},
          );

          setScreenSharing(
            false,
          );

          setBusy(
            false,
          );
        }
      },
      [
        joined,
        workspaceId,
        channel.id,
      ],
    );


  async function toggleMute() {
    const next =
      !muted;

    const result =
      await voiceChannelsService
        .updateSelf(
          workspaceId,
          channel.id,
          {
            self_muted:
              next,
          },
        );

    setMuted(
      result.self_muted,
    );

    setDeafened(
      result.self_deafened,
    );

    rtcRef.current
      ?.setMicrophoneEnabled(
        !result
          .effective_muted,
      );
  }


  async function toggleDeafen() {
    const next =
      !deafened;

    const result =
      await voiceChannelsService
        .updateSelf(
          workspaceId,
          channel.id,
          {
            self_deafened:
              next,
          },
        );

    setMuted(
      result.self_muted,
    );

    setDeafened(
      result.self_deafened,
    );

    rtcRef.current
      ?.setMicrophoneEnabled(
        !result
          .effective_muted,
      );
  }


  async function toggleScreenShare() {
    if (
      !rtcRef.current
    ) {
      return;
    }

    if (
      screenSharing
    ) {
      await rtcRef.current
        .stopScreenShare();

      await voiceChannelsService
        .stopScreenShare(
          workspaceId,
          channel.id,
        );

      setScreenSharing(
        false,
      );

      return;
    }

    await rtcRef.current
      .startScreenShare();

    try {
      await voiceChannelsService
        .startScreenShare(
          workspaceId,
          channel.id,
        );

      setScreenSharing(
        true,
      );
    } catch (
      shareError
    ) {
      await rtcRef.current
        .stopScreenShare();

      throw shareError;
    }
  }


  async function moderateMute(
    userId: string,
    value: boolean,
  ) {
    await voiceChannelsService
      .moderate(
        workspaceId,
        channel.id,
        userId,
        {
          server_muted:
            value,
        },
      );

    await refreshParticipants();
  }


  async function moderateDeafen(
    userId: string,
    value: boolean,
  ) {
    await voiceChannelsService
      .moderate(
        workspaceId,
        channel.id,
        userId,
        {
          server_deafened:
            value,
        },
      );

    await refreshParticipants();
  }


  async function kick(
    userId: string,
  ) {
    await voiceChannelsService
      .kick(
        workspaceId,
        channel.id,
        userId,
      );

    await refreshParticipants();
  }


  async function ban(
    userId: string,
  ) {
    await voiceChannelsService
      .ban(
        workspaceId,
        channel.id,
        userId,
        "Removed by voice moderator.",
      );

    await refreshParticipants();
  }


  useEffect(
    () => {
      if (!joined) {
        return;
      }

      const heartbeatTimer =
        window.setInterval(
          () => {
            void voiceChannelsService
              .heartbeat(
                workspaceId,
                channel.id,
                connectionIdRef
                  .current,
              );
          },
          15000,
        );


      const participantTimer =
        window.setInterval(
          () => {
            void refreshParticipants();
          },
          2000,
        );


      const signalTimer =
        window.setInterval(
          () => {
            void (
              async () => {
                try {
                  const result =
                    await voiceChannelsService
                      .pollSignals(
                        workspaceId,
                        channel.id,
                      );

                  for (
                    const event
                    of result.events
                  ) {
                    await rtcRef
                      .current
                      ?.handleSignal(
                        event,
                      );
                  }
                } catch {
                  // Poll retry will occur automatically.
                }
              }
            )();
          },
          800,
        );


      void voiceChannelsService
        .heartbeat(
          workspaceId,
          channel.id,
          connectionIdRef
            .current,
        );

      void refreshParticipants();


      return () => {
        window.clearInterval(
          heartbeatTimer,
        );

        window.clearInterval(
          participantTimer,
        );

        window.clearInterval(
          signalTimer,
        );
      };
    },
    [
      joined,
      workspaceId,
      channel.id,
      refreshParticipants,
    ],
  );


  useEffect(
    () => {
      return () => {
        stopSpeakingDetector();

        if (
          rtcRef.current
        ) {
          void rtcRef.current
            .destroy();

          rtcRef.current =
            null;
        }
      };
    },
    [],
  );


  return (
    <section
      style={{
        flex: 1,
        minWidth: 0,
        display: "flex",
        flexDirection:
          "column",
      }}
    >
      <header
        style={{
          minHeight: 58,

          padding:
            "10px 18px",

          display: "flex",

          alignItems:
            "center",

          justifyContent:
            "space-between",

          gap: 16,

          borderBottom:
            "1px solid var(--border, #e5e7eb)",
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems:
              "center",
            gap: 8,
            fontWeight: 800,
          }}
        >
          <Volume2
            size={18}
          />

          {channel.name}
        </div>

        <VoiceControls
          joined={joined}
          muted={muted}
          deafened={
            deafened
          }
          screenSharing={
            screenSharing
          }
          busy={busy}
          onJoin={
            handleJoin
          }
          onLeave={
            handleLeave
          }
          onMuteToggle={
            toggleMute
          }
          onDeafenToggle={
            toggleDeafen
          }
          onScreenShareToggle={
            toggleScreenShare
          }
        />
      </header>

      <div
        style={{
          flex: 1,

          overflowY:
            "auto",

          padding: 20,
        }}
      >
        {error ? (
          <div
            style={{
              marginBottom:
                16,

              padding: 12,

              border:
                "1px solid #ef4444",

              borderRadius:
                8,
            }}
          >
            {error}
          </div>
        ) : null}

        {!joined ? (
          <div
            style={{
              minHeight: 320,

              display: "grid",

              placeItems:
                "center",

              textAlign:
                "center",
            }}
          >
            <div>
              <Radio
                size={38}
                style={{
                  margin:
                    "0 auto 14px",
                }}
              />

              <h2>
                {channel.name}
              </h2>

              <p
                style={{
                  opacity:
                    0.65,

                  maxWidth:
                    460,
                }}
              >
                Join to connect your microphone,
                receive WebRTC audio, share your
                screen, and see speaking state.
              </p>
            </div>
          </div>
        ) : (
          <>
            <h3
              style={{
                marginBottom:
                  12,
              }}
            >
              Participants
            </h3>

            <VoiceParticipantList
              participants={
                participants
              }
              selfUserId={
                selfUserId
              }
              canModerate={
                canModerate
              }
              onServerMute={
                moderateMute
              }
              onServerDeafen={
                moderateDeafen
              }
              onKick={kick}
              onBan={ban}
            />

            {Object.entries(
              remoteStreams,
            ).length >
            0 ? (
              <div
                style={{
                  marginTop:
                    24,

                  display:
                    "grid",

                  gridTemplateColumns:
                    "repeat(auto-fit, minmax(240px, 1fr))",

                  gap: 12,
                }}
              >
                {Object.entries(
                  remoteStreams,
                ).map(
                  ([
                    userId,
                    stream,
                  ]) => (
                    <RemoteMedia
                      key={
                        userId
                      }
                      userId={
                        userId
                      }
                      stream={
                        stream
                      }
                    />
                  ),
                )}
              </div>
            ) : null}
          </>
        )}
      </div>
    </section>
  );
}


function RemoteMedia({
  userId,
  stream,
}: {
  userId: string;
  stream: MediaStream;
}) {
  const videoRef =
    useRef<
      HTMLVideoElement | null
    >(null);

  const audioRef =
    useRef<
      HTMLAudioElement | null
    >(null);

  const hasVideo =
    stream
      .getVideoTracks()
      .length > 0;


  useEffect(
    () => {
      if (
        videoRef.current
      ) {
        videoRef.current
          .srcObject =
          stream;
      }

      if (
        audioRef.current
      ) {
        audioRef.current
          .srcObject =
          stream;
      }
    },
    [
      stream,
    ],
  );


  return (
    <div
      style={{
        border:
          "1px solid var(--border, #e5e7eb)",

        borderRadius:
          10,

        overflow:
          "hidden",
      }}
    >
      {hasVideo ? (
        <video
          ref={
            videoRef
          }
          autoPlay
          playsInline
          style={{
            width: "100%",
            display:
              "block",
            background:
              "#111",
          }}
        />
      ) : null}

      <audio
        ref={
          audioRef
        }
        autoPlay
      />

      <div
        style={{
          padding:
            "8px 10px",

          fontSize:
            12,

          opacity:
            0.7,
        }}
      >
        User{" "}
        {userId.slice(
          0,
          8,
        )}
      </div>
    </div>
  );
}