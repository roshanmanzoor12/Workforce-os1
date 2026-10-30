"use client";

import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import {
  workspaceChannelsService,
  type VoiceCallPublic,
  type VoiceCapabilitiesResponse,
  type VoiceParticipantPublic,
  type VoiceSignalEnvelope,
  type VoiceSignalType,
} from "@/services/workspace-channels.service";


interface UseVoiceChannelOptions {
  workspaceId: string | null;

  channelId: string | null;

  currentUserId: string | null;
}


function makeConnectionId(): string {
  if (
    typeof crypto !==
      "undefined" &&
    typeof crypto.randomUUID ===
      "function"
  ) {
    return crypto.randomUUID();
  }


  return `${Date.now()}-${Math.random()
    .toString(16)
    .slice(2)}`;
}


export function useVoiceChannel({
  workspaceId,
  channelId,
  currentUserId,
}: UseVoiceChannelOptions) {
  const [
    call,
    setCall,
  ] =
    useState<VoiceCallPublic | null>(
      null,
    );


  const [
    participants,
    setParticipants,
  ] =
    useState<VoiceParticipantPublic[]>(
      [],
    );


  const [
    capabilities,
    setCapabilities,
  ] =
    useState<VoiceCapabilitiesResponse | null>(
      null,
    );


  const [
    joined,
    setJoined,
  ] =
    useState(
      false,
    );


  const [
    joining,
    setJoining,
  ] =
    useState(
      false,
    );


  const [
    busy,
    setBusy,
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


  const [
    remoteStreams,
    setRemoteStreams,
  ] =
    useState<Record<string, MediaStream>>(
      {},
    );


  const [
    localScreenStream,
    setLocalScreenStream,
  ] =
    useState<MediaStream | null>(
      null,
    );


  const [
    bannedUserIds,
    setBannedUserIds,
  ] =
    useState<string[]>(
      [],
    );


  const microphoneRef =
    useRef<MediaStream | null>(
      null,
    );


  const screenRef =
    useRef<MediaStream | null>(
      null,
    );


  const peersRef =
    useRef<Map<string, RTCPeerConnection>>(
      new Map(),
    );


  const processedSignalsRef =
    useRef<Set<string>>(
      new Set(),
    );


  const joinedRef =
    useRef(
      false,
    );


  const participantTimerRef =
    useRef<number | null>(
      null,
    );


  const signalTimerRef =
    useRef<number | null>(
      null,
    );


  const heartbeatTimerRef =
    useRef<number | null>(
      null,
    );


  const speakingTimerRef =
    useRef<number | null>(
      null,
    );


  const audioContextRef =
    useRef<AudioContext | null>(
      null,
    );


  const speakingRef =
    useRef(
      false,
    );


  const connectionIdRef =
    useRef(
      makeConnectionId(),
    );


  const selfParticipant =
    useMemo(
      () =>
        participants.find(
          (
            participant,
          ) =>
            participant.user_id ===
            currentUserId,
        ) ??
        null,
      [
        participants,
        currentUserId,
      ],
    );


  const updateParticipant =
    useCallback(
      (
        participant:
          VoiceParticipantPublic,
      ) => {
        setParticipants(
          (
            current,
          ) => {
            const exists =
              current.some(
                (
                  item,
                ) =>
                  item.user_id ===
                  participant.user_id,
              );


            if (
              !exists
            ) {
              return [
                ...current,
                participant,
              ];
            }


            return current.map(
              (
                item,
              ) =>
                item.user_id ===
                participant.user_id
                  ? participant
                  : item,
            );
          },
        );
      },
      [],
    );


  const sendSignal =
    useCallback(
      async (
        targetUserId:
          string,

        signalType:
          VoiceSignalType,

        payload:
          Record<string, unknown>,
      ) => {
        if (
          !workspaceId ||
          !channelId
        ) {
          return;
        }


        await workspaceChannelsService.sendVoiceSignal(
          workspaceId,
          channelId,
          {
            signal_type:
              signalType,

            target_user_id:
              targetUserId,

            payload,
          },
        );
      },
      [
        workspaceId,
        channelId,
      ],
    );


  const closePeer =
    useCallback(
      (
        userId:
          string,
      ) => {
        const peer =
          peersRef.current.get(
            userId,
          );


        if (
          peer
        ) {
          peer.close();

          peersRef.current.delete(
            userId,
          );
        }


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
      [],
    );


  const ensurePeer =
    useCallback(
      (
        remoteUserId:
          string,
      ): RTCPeerConnection => {
        const existing =
          peersRef.current.get(
            remoteUserId,
          );


        if (
          existing
        ) {
          return existing;
        }


        const peer =
          new RTCPeerConnection({
            iceServers: [
              {
                urls:
                  "stun:stun.l.google.com:19302",
              },
            ],
          });


        const microphone =
          microphoneRef.current;


        if (
          microphone
        ) {
          for (
            const track
            of microphone.getTracks()
          ) {
            peer.addTrack(
              track,
              microphone,
            );
          }
        }


        const screen =
          screenRef.current;


        if (
          screen
        ) {
          for (
            const track
            of screen.getTracks()
          ) {
            peer.addTrack(
              track,
              screen,
            );
          }
        }


        peer.onicecandidate =
          (
            event,
          ) => {
            if (
              !event.candidate
            ) {
              return;
            }


            void sendSignal(
              remoteUserId,
              "ice_candidate",
              {
                candidate:
                  event.candidate.toJSON(),
              },
            );
          };


        peer.ontrack =
          (
            event,
          ) => {
            const stream =
              event.streams[0] ??
              new MediaStream([
                event.track,
              ]);


            setRemoteStreams(
              (
                current,
              ) => ({
                ...current,

                [remoteUserId]:
                  stream,
              }),
            );
          };


        peer.onconnectionstatechange =
          () => {
            if (
              peer.connectionState ===
                "closed" ||
              peer.connectionState ===
                "failed"
            ) {
              closePeer(
                remoteUserId,
              );
            }
          };


        peersRef.current.set(
          remoteUserId,
          peer,
        );


        return peer;
      },
      [
        closePeer,
        sendSignal,
      ],
    );


  const sendOffer =
    useCallback(
      async (
        userId:
          string,

        peer:
          RTCPeerConnection,
      ) => {
        if (
          peer.signalingState !==
          "stable"
        ) {
          return;
        }


        const offer =
          await peer.createOffer();


        await peer.setLocalDescription(
          offer,
        );


        await sendSignal(
          userId,
          "offer",
          {
            sdp:
              offer.sdp ??
              "",
          },
        );
      },
      [
        sendSignal,
      ],
    );


  const handleSignal =
    useCallback(
      async (
        signal:
          VoiceSignalEnvelope,
      ) => {
        if (
          !currentUserId ||
          signal.sender_user_id ===
            currentUserId
        ) {
          return;
        }


        if (
          signal.target_user_id &&
          signal.target_user_id !==
            currentUserId
        ) {
          return;
        }


        if (
          processedSignalsRef.current.has(
            signal.event_id,
          )
        ) {
          return;
        }


        processedSignalsRef.current.add(
          signal.event_id,
        );


        const remoteUserId =
          signal.sender_user_id;


        const peer =
          ensurePeer(
            remoteUserId,
          );


        if (
          signal.signal_type ===
          "offer"
        ) {
          const sdp =
            typeof signal.payload.sdp ===
            "string"
              ? signal.payload.sdp
              : "";


          if (
            !sdp
          ) {
            return;
          }


          await peer.setRemoteDescription(
            {
              type:
                "offer",

              sdp,
            },
          );


          const answer =
            await peer.createAnswer();


          await peer.setLocalDescription(
            answer,
          );


          await sendSignal(
            remoteUserId,
            "answer",
            {
              sdp:
                answer.sdp ??
                "",
            },
          );


          return;
        }


        if (
          signal.signal_type ===
          "answer"
        ) {
          const sdp =
            typeof signal.payload.sdp ===
            "string"
              ? signal.payload.sdp
              : "";


          if (
            !sdp ||
            peer.signalingState !==
              "have-local-offer"
          ) {
            return;
          }


          await peer.setRemoteDescription(
            {
              type:
                "answer",

              sdp,
            },
          );


          return;
        }


        if (
          signal.signal_type ===
          "ice_candidate"
        ) {
          const candidate =
            signal.payload.candidate;


          if (
            candidate &&
            typeof candidate ===
              "object"
          ) {
            try {
              await peer.addIceCandidate(
                candidate as RTCIceCandidateInit,
              );
            } catch {
              // Candidate can arrive before matching SDP.
            }
          }


          return;
        }


        if (
          signal.signal_type ===
          "renegotiate"
        ) {
          await sendOffer(
            remoteUserId,
            peer,
          );
        }
      },
      [
        currentUserId,
        ensurePeer,
        sendOffer,
        sendSignal,
      ],
    );


  const refreshParticipants =
    useCallback(
      async () => {
        if (
          !workspaceId ||
          !channelId ||
          !joinedRef.current
        ) {
          return;
        }


        try {
          const response =
            await workspaceChannelsService.listVoiceParticipants(
              workspaceId,
              channelId,
            );


          const next =
            response.participants ??
            [];


          setParticipants(
            next,
          );


          const activeUserIds =
            new Set<string>(
              next
                .filter(
                  (
                    participant:
                      VoiceParticipantPublic,
                  ) =>
                    !participant.left_at &&
                    participant.state !==
                      "LEFT",
                )
                .map(
                  (
                    participant:
                      VoiceParticipantPublic,
                  ) =>
                    participant.user_id,
                ),
            );


          for (
            const userId
            of Array.from(
              peersRef.current.keys(),
            )
          ) {
            if (
              !activeUserIds.has(
                userId,
              )
            ) {
              closePeer(
                userId,
              );
            }
          }


          for (
            const participant
            of next
          ) {
            if (
              participant.user_id ===
                currentUserId ||
              participant.left_at
            ) {
              continue;
            }


            const peer =
              ensurePeer(
                participant.user_id,
              );


            /*
             * Deterministic offer initiator prevents
             * both peers from sending offers together.
             */
            if (
              currentUserId &&
              currentUserId <
                participant.user_id &&
              peer.signalingState ===
                "stable" &&
              peer.connectionState ===
                "new"
            ) {
              void sendOffer(
                participant.user_id,
                peer,
              );
            }
          }


          const me =
            next.find(
              (
                participant,
              ) =>
                participant.user_id ===
                currentUserId,
            );


          if (
            me
          ) {
            const microphone =
              microphoneRef.current;


            for (
              const track
              of microphone?.getAudioTracks() ??
                []
            ) {
              track.enabled =
                !me.effective_muted;
            }
          }

        } catch (
          cause
        ) {
          setError(
            cause instanceof Error
              ? cause.message
              : "Unable to refresh voice participants.",
          );
        }
      },
      [
        workspaceId,
        channelId,
        currentUserId,
        closePeer,
        ensurePeer,
        sendOffer,
      ],
    );


  const pollSignals =
    useCallback(
      async () => {
        if (
          !workspaceId ||
          !channelId ||
          !joinedRef.current
        ) {
          return;
        }


        try {
          const response =
            await workspaceChannelsService.pollVoiceSignals(
              workspaceId,
              channelId,
            );


          for (
            const signal
            of response.events ??
              []
          ) {
            await handleSignal(
              signal,
            );
          }
        } catch {
          // Polling retries automatically.
        }
      },
      [
        workspaceId,
        channelId,
        handleSignal,
      ],
    );


  const heartbeat =
    useCallback(
      async () => {
        if (
          !workspaceId ||
          !channelId ||
          !joinedRef.current
        ) {
          return;
        }


        try {
          await workspaceChannelsService.voicePresenceHeartbeat(
            workspaceId,
            channelId,
            {
              connection_id:
                connectionIdRef.current,
            },
          );
        } catch {
          // Next heartbeat retries.
        }
      },
      [
        workspaceId,
        channelId,
      ],
    );


  const stopTimers =
    useCallback(
      () => {
        const timers = [
          participantTimerRef,
          signalTimerRef,
          heartbeatTimerRef,
          speakingTimerRef,
        ];


        for (
          const timer
          of timers
        ) {
          if (
            timer.current !==
            null
          ) {
            window.clearInterval(
              timer.current,
            );

            timer.current =
              null;
          }
        }


        if (
          audioContextRef.current
        ) {
          void audioContextRef.current.close();

          audioContextRef.current =
            null;
        }


        speakingRef.current =
          false;
      },
      [],
    );


  const stopMedia =
    useCallback(
      () => {
        for (
          const track
          of microphoneRef.current?.getTracks() ??
            []
        ) {
          track.stop();
        }


        microphoneRef.current =
          null;


        for (
          const track
          of screenRef.current?.getTracks() ??
            []
        ) {
          track.stop();
        }


        screenRef.current =
          null;


        setLocalScreenStream(
          null,
        );


        for (
          const peer
          of peersRef.current.values()
        ) {
          peer.close();
        }


        peersRef.current.clear();


        setRemoteStreams(
          {},
        );
      },
      [],
    );


  const startSpeakingDetector =
    useCallback(
      (
        stream:
          MediaStream,
      ) => {
        if (
          typeof window ===
          "undefined"
        ) {
          return;
        }


        const context =
          new AudioContext();


        audioContextRef.current =
          context;


        const analyser =
          context.createAnalyser();


        analyser.fftSize =
          256;


        const source =
          context.createMediaStreamSource(
            stream,
          );


        source.connect(
          analyser,
        );


        const values =
          new Uint8Array(
            analyser.fftSize,
          );


        speakingTimerRef.current =
          window.setInterval(
            () => {
              if (
                !workspaceId ||
                !channelId ||
                !joinedRef.current
              ) {
                return;
              }


              analyser.getByteTimeDomainData(
                values,
              );


              let sum =
                0;


              for (
                const value
                of values
              ) {
                const normalized =
                  (
                    value -
                    128
                  ) /
                  128;


                sum +=
                  normalized *
                  normalized;
              }


              const rms =
                Math.sqrt(
                  sum /
                    values.length,
                );


              const microphoneEnabled =
                stream
                  .getAudioTracks()
                  .some(
                    (
                      track,
                    ) =>
                      track.enabled,
                  );


              const speaking =
                microphoneEnabled &&
                rms >
                  0.035;


              if (
                speaking ===
                speakingRef.current
              ) {
                return;
              }


              speakingRef.current =
                speaking;


              void workspaceChannelsService.setVoiceSpeaking(
                workspaceId,
                channelId,
                {
                  speaking,
                },
              );
            },
            350,
          );
      },
      [
        workspaceId,
        channelId,
      ],
    );


  const startTimers =
    useCallback(
      (
        microphone:
          MediaStream,
      ) => {
        stopTimers();


        void heartbeat();

        void pollSignals();

        void refreshParticipants();


        signalTimerRef.current =
          window.setInterval(
            () => {
              void pollSignals();
            },
            750,
          );


        participantTimerRef.current =
          window.setInterval(
            () => {
              void refreshParticipants();
            },
            2000,
          );


        heartbeatTimerRef.current =
          window.setInterval(
            () => {
              void heartbeat();
            },
            10000,
          );


        startSpeakingDetector(
          microphone,
        );
      },
      [
        stopTimers,
        heartbeat,
        pollSignals,
        refreshParticipants,
        startSpeakingDetector,
      ],
    );


  const join =
    useCallback(
      async () => {
        if (
          !workspaceId ||
          !channelId ||
          !currentUserId ||
          joining ||
          joinedRef.current
        ) {
          return;
        }


        let microphone:
          MediaStream | null =
          null;


        try {
          setJoining(
            true,
          );

          setError(
            null,
          );


          microphone =
            await navigator.mediaDevices.getUserMedia(
              {
                audio: {
                  echoCancellation:
                    true,

                  noiseSuppression:
                    true,

                  autoGainControl:
                    true,
                },

                video:
                  false,
              },
            );


          microphoneRef.current =
            microphone;


          const [
            joinResponse,
            capabilityResponse,
          ] =
            await Promise.all([
              workspaceChannelsService.joinVoice(
                workspaceId,
                channelId,
              ),

              workspaceChannelsService.voiceCapabilities(
                workspaceId,
                channelId,
              ),
            ]);


          setCall(
            joinResponse.call,
          );


          setCapabilities(
            capabilityResponse,
          );


          const initialParticipants =
            joinResponse.call
              .participants?.length
              ? joinResponse.call.participants
              : [
                  joinResponse.participant,
                ];


          setParticipants(
            initialParticipants,
          );


          joinedRef.current =
            true;


          setJoined(
            true,
          );


          startTimers(
            microphone,
          );


          for (
            const participant
            of initialParticipants
          ) {
            if (
              participant.user_id ===
                currentUserId ||
              participant.left_at
            ) {
              continue;
            }


            const peer =
              ensurePeer(
                participant.user_id,
              );


            if (
              currentUserId <
              participant.user_id
            ) {
              void sendOffer(
                participant.user_id,
                peer,
              );
            }
          }

        } catch (
          cause
        ) {
          for (
            const track
            of microphone?.getTracks() ??
              []
          ) {
            track.stop();
          }


          microphoneRef.current =
            null;


          setError(
            cause instanceof Error
              ? cause.message
              : "Unable to join voice channel.",
          );

        } finally {
          setJoining(
            false,
          );
        }
      },
      [
        workspaceId,
        channelId,
        currentUserId,
        joining,
        ensurePeer,
        sendOffer,
        startTimers,
      ],
    );


  const leave =
    useCallback(
      async () => {
        try {
          if (
            workspaceId &&
            channelId &&
            joinedRef.current
          ) {
            try {
              await workspaceChannelsService.setVoiceSpeaking(
                workspaceId,
                channelId,
                {
                  speaking:
                    false,
                },
              );
            } catch {
              // Ignore final speaking update.
            }


            await workspaceChannelsService.leaveVoice(
              workspaceId,
              channelId,
            );
          }
        } finally {
          joinedRef.current =
            false;


          setJoined(
            false,
          );


          setCall(
            null,
          );


          setParticipants(
            [],
          );


          processedSignalsRef.current.clear();


          stopTimers();

          stopMedia();
        }
      },
      [
        workspaceId,
        channelId,
        stopTimers,
        stopMedia,
      ],
    );


  const toggleSelfMute =
    useCallback(
      async () => {
        if (
          !workspaceId ||
          !channelId ||
          !selfParticipant
        ) {
          return;
        }


        try {
          setBusy(
            true,
          );


          const updated =
            await workspaceChannelsService.updateSelfVoiceState(
              workspaceId,
              channelId,
              {
                self_muted:
                  !selfParticipant.self_muted,
              },
            );


          updateParticipant(
            updated,
          );


          for (
            const track
            of microphoneRef.current?.getAudioTracks() ??
              []
          ) {
            track.enabled =
              !updated.effective_muted;
          }

        } catch (
          cause
        ) {
          setError(
            cause instanceof Error
              ? cause.message
              : "Unable to change microphone state.",
          );

        } finally {
          setBusy(
            false,
          );
        }
      },
      [
        workspaceId,
        channelId,
        selfParticipant,
        updateParticipant,
      ],
    );


  const toggleSelfDeafen =
    useCallback(
      async () => {
        if (
          !workspaceId ||
          !channelId ||
          !selfParticipant
        ) {
          return;
        }


        try {
          setBusy(
            true,
          );


          const updated =
            await workspaceChannelsService.updateSelfVoiceState(
              workspaceId,
              channelId,
              {
                self_deafened:
                  !selfParticipant.self_deafened,
              },
            );


          updateParticipant(
            updated,
          );

        } catch (
          cause
        ) {
          setError(
            cause instanceof Error
              ? cause.message
              : "Unable to change deafen state.",
          );

        } finally {
          setBusy(
            false,
          );
        }
      },
      [
        workspaceId,
        channelId,
        selfParticipant,
        updateParticipant,
      ],
    );


  const moderate =
    useCallback(
      async (
        participant:
          VoiceParticipantPublic,

        field:
          | "server_muted"
          | "server_deafened",
      ) => {
        if (
          !workspaceId ||
          !channelId
        ) {
          return;
        }


        try {
          setBusy(
            true,
          );


          const updated =
            await workspaceChannelsService.moderateVoiceParticipant(
              workspaceId,
              channelId,
              participant.user_id,
              field ===
                "server_muted"
                ? {
                    server_muted:
                      !participant.server_muted,
                  }
                : {
                    server_deafened:
                      !participant.server_deafened,
                  },
            );


          updateParticipant(
            updated,
          );

        } catch (
          cause
        ) {
          setError(
            cause instanceof Error
              ? cause.message
              : "Unable to moderate participant.",
          );

        } finally {
          setBusy(
            false,
          );
        }
      },
      [
        workspaceId,
        channelId,
        updateParticipant,
      ],
    );


  const kick =
    useCallback(
      async (
        userId:
          string,
      ) => {
        if (
          !workspaceId ||
          !channelId
        ) {
          return;
        }


        try {
          setBusy(
            true,
          );


          await workspaceChannelsService.kickVoiceParticipant(
            workspaceId,
            channelId,
            userId,
          );


          closePeer(
            userId,
          );


          await refreshParticipants();

        } catch (
          cause
        ) {
          setError(
            cause instanceof Error
              ? cause.message
              : "Unable to kick participant.",
          );

        } finally {
          setBusy(
            false,
          );
        }
      },
      [
        workspaceId,
        channelId,
        closePeer,
        refreshParticipants,
      ],
    );


  const ban =
    useCallback(
      async (
        userId:
          string,

        reason:
          string | null =
          null,
      ) => {
        if (
          !workspaceId ||
          !channelId
        ) {
          return;
        }


        try {
          setBusy(
            true,
          );


          await workspaceChannelsService.banVoiceUser(
            workspaceId,
            channelId,
            userId,
            {
              reason,
            },
          );


          setBannedUserIds(
            (
              current,
            ) =>
              current.includes(
                userId,
              )
                ? current
                : [
                    ...current,
                    userId,
                  ],
          );


          closePeer(
            userId,
          );


          await refreshParticipants();

        } catch (
          cause
        ) {
          setError(
            cause instanceof Error
              ? cause.message
              : "Unable to ban user.",
          );

        } finally {
          setBusy(
            false,
          );
        }
      },
      [
        workspaceId,
        channelId,
        closePeer,
        refreshParticipants,
      ],
    );


  const unban =
    useCallback(
      async (
        userId:
          string,
      ) => {
        if (
          !workspaceId ||
          !channelId
        ) {
          return;
        }


        try {
          setBusy(
            true,
          );


          await workspaceChannelsService.unbanVoiceUser(
            workspaceId,
            channelId,
            userId,
          );


          setBannedUserIds(
            (
              current,
            ) =>
              current.filter(
                (
                  item,
                ) =>
                  item !==
                  userId,
              ),
          );

        } catch (
          cause
        ) {
          setError(
            cause instanceof Error
              ? cause.message
              : "Unable to unban user.",
          );

        } finally {
          setBusy(
            false,
          );
        }
      },
      [
        workspaceId,
        channelId,
      ],
    );


  const stopScreenShare =
    useCallback(
      async () => {
        if (
          !workspaceId ||
          !channelId
        ) {
          return;
        }


        try {
          await workspaceChannelsService.stopVoiceScreenShare(
            workspaceId,
            channelId,
          );
        } catch {
          // Continue local cleanup.
        }


        for (
          const track
          of screenRef.current?.getTracks() ??
            []
        ) {
          track.onended =
            null;

          track.stop();
        }


        screenRef.current =
          null;


        setLocalScreenStream(
          null,
        );


        for (
          const [
            userId,
            peer,
          ]
          of peersRef.current.entries()
        ) {
          const senders =
            peer
              .getSenders()
              .filter(
                (
                  sender,
                ) =>
                  sender.track?.kind ===
                  "video",
              );


          for (
            const sender
            of senders
          ) {
            peer.removeTrack(
              sender,
            );
          }


          void sendOffer(
            userId,
            peer,
          );
        }


        await refreshParticipants();
      },
      [
        workspaceId,
        channelId,
        refreshParticipants,
        sendOffer,
      ],
    );


  const toggleScreenShare =
    useCallback(
      async () => {
        if (
          !workspaceId ||
          !channelId ||
          !joinedRef.current
        ) {
          return;
        }


        if (
          screenRef.current
        ) {
          await stopScreenShare();

          return;
        }


        try {
          setBusy(
            true,
          );


          const stream =
            await navigator.mediaDevices.getDisplayMedia(
              {
                video:
                  true,

                audio:
                  false,
              },
            );


          await workspaceChannelsService.startVoiceScreenShare(
            workspaceId,
            channelId,
          );


          screenRef.current =
            stream;


          setLocalScreenStream(
            stream,
          );


          const track =
            stream.getVideoTracks()[0];


          if (
            track
          ) {
            track.onended =
              () => {
                void stopScreenShare();
              };
          }


          for (
            const [
              userId,
              peer,
            ]
            of peersRef.current.entries()
          ) {
            for (
              const mediaTrack
              of stream.getTracks()
            ) {
              peer.addTrack(
                mediaTrack,
                stream,
              );
            }


            void sendOffer(
              userId,
              peer,
            );
          }


          await refreshParticipants();

        } catch (
          cause
        ) {
          setError(
            cause instanceof Error
              ? cause.message
              : "Unable to start screen sharing.",
          );

        } finally {
          setBusy(
            false,
          );
        }
      },
      [
        workspaceId,
        channelId,
        stopScreenShare,
        refreshParticipants,
        sendOffer,
      ],
    );


  useEffect(
    () => {
      return () => {
        stopTimers();

        stopMedia();


        if (
          joinedRef.current &&
          workspaceId &&
          channelId
        ) {
          void workspaceChannelsService.leaveVoice(
            workspaceId,
            channelId,
          );
        }


        joinedRef.current =
          false;
      };
    },
    [
      workspaceId,
      channelId,
      stopTimers,
      stopMedia,
    ],
  );


  return {
    call,

    participants,

    capabilities,

    selfParticipant,

    joined,

    joining,

    busy,

    error,

    remoteStreams,

    localScreenStream,

    bannedUserIds,

    join,

    leave,

    toggleSelfMute,

    toggleSelfDeafen,

    moderate,

    kick,

    ban,

    unban,

    toggleScreenShare,

    refreshParticipants,
  };
}