import type {
  VoiceSignalEnvelope,
} from "@/types/channels";


export interface VoiceWebRtcCallbacks {
  sendSignal(
    targetUserId: string,
    signalType:
      | "offer"
      | "answer"
      | "ice_candidate",
    payload: Record<
      string,
      unknown
    >,
  ): Promise<void>;

  onRemoteStream(
    userId: string,
    stream: MediaStream,
  ): void;

  onRemoteStreamRemoved(
    userId: string,
  ): void;
}


export class VoiceWebRtcClient {
  private readonly callbacks:
    VoiceWebRtcCallbacks;

  private readonly peers =
    new Map<
      string,
      RTCPeerConnection
    >();

  private localStream:
    | MediaStream
    | null = null;

  private screenStream:
    | MediaStream
    | null = null;


  constructor(
    callbacks:
      VoiceWebRtcCallbacks,
  ) {
    this.callbacks =
      callbacks;
  }


  getLocalStream():
    | MediaStream
    | null {
    return this.localStream;
  }


  async startMicrophone():
    Promise<MediaStream> {
    if (
      this.localStream
    ) {
      return this.localStream;
    }

    this.localStream =
      await navigator
        .mediaDevices
        .getUserMedia({
          audio: {
            echoCancellation:
              true,

            noiseSuppression:
              true,

            autoGainControl:
              true,
          },

          video: false,
        });

    return this.localStream;
  }


  setMicrophoneEnabled(
    enabled: boolean,
  ) {
    if (
      !this.localStream
    ) {
      return;
    }

    for (
      const track
      of this.localStream
        .getAudioTracks()
    ) {
      track.enabled =
        enabled;
    }
  }


  private createPeer(
    remoteUserId: string,
  ): RTCPeerConnection {
    const existing =
      this.peers.get(
        remoteUserId,
      );

    if (existing) {
      return existing;
    }

    const stunUrl =
      process.env
        .NEXT_PUBLIC_STUN_URL ??
      "stun:stun.l.google.com:19302";

    const peer =
      new RTCPeerConnection(
        {
          iceServers: [
            {
              urls:
                stunUrl,
            },
          ],
        },
      );


    if (
      this.localStream
    ) {
      for (
        const track
        of this.localStream
          .getTracks()
      ) {
        peer.addTrack(
          track,
          this.localStream,
        );
      }
    }


    peer.onicecandidate =
      (event) => {
        if (
          !event.candidate
        ) {
          return;
        }

        void this.callbacks
          .sendSignal(
            remoteUserId,
            "ice_candidate",
            {
              candidate:
                event.candidate
                  .toJSON(),
            },
          );
      };


    peer.ontrack =
      (event) => {
        const stream =
          event.streams[0];

        if (!stream) {
          return;
        }

        this.callbacks
          .onRemoteStream(
            remoteUserId,
            stream,
          );
      };


    peer.onconnectionstatechange =
      () => {
        if (
          peer.connectionState ===
            "failed" ||
          peer.connectionState ===
            "closed" ||
          peer.connectionState ===
            "disconnected"
        ) {
          this.removePeer(
            remoteUserId,
          );
        }
      };


    this.peers.set(
      remoteUserId,
      peer,
    );

    return peer;
  }


  async ensurePeer(
    remoteUserId: string,
    initiator: boolean,
  ): Promise<void> {
    const peer =
      this.createPeer(
        remoteUserId,
      );

    if (
      !initiator ||
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

    await this.callbacks
      .sendSignal(
        remoteUserId,
        "offer",
        {
          sdp:
            offer.sdp,
          type:
            offer.type,
        },
      );
  }


  async handleSignal(
    event:
      VoiceSignalEnvelope,
  ): Promise<void> {
    const remoteUserId =
      event.sender_user_id;

    const peer =
      this.createPeer(
        remoteUserId,
      );


    if (
      event.signal_type ===
      "offer"
    ) {
      const sdp =
        event.payload
          .sdp;

      if (
        typeof sdp !==
        "string"
      ) {
        return;
      }

      await peer
        .setRemoteDescription(
          {
            type: "offer",
            sdp,
          },
        );

      const answer =
        await peer
          .createAnswer();

      await peer
        .setLocalDescription(
          answer,
        );

      await this.callbacks
        .sendSignal(
          remoteUserId,
          "answer",
          {
            type:
              answer.type,

            sdp:
              answer.sdp,
          },
        );

      return;
    }


    if (
      event.signal_type ===
      "answer"
    ) {
      const sdp =
        event.payload
          .sdp;

      if (
        typeof sdp !==
        "string"
      ) {
        return;
      }

      await peer
        .setRemoteDescription(
          {
            type:
              "answer",
            sdp,
          },
        );

      return;
    }


    if (
      event.signal_type ===
      "ice_candidate"
    ) {
      const candidate =
        event.payload
          .candidate;

      if (
        !candidate ||
        typeof candidate !==
          "object"
      ) {
        return;
      }

      await peer
        .addIceCandidate(
          candidate as RTCIceCandidateInit,
        );
    }
  }


  async startScreenShare():
    Promise<MediaStream> {
    if (
      this.screenStream
    ) {
      return this.screenStream;
    }

    const stream =
      await navigator
        .mediaDevices
        .getDisplayMedia({
          video: true,
          audio: false,
        });

    const screenTrack =
      stream
        .getVideoTracks()[0];

    if (!screenTrack) {
      throw new Error(
        "No screen video track was provided.",
      );
    }

    this.screenStream =
      stream;


    for (
      const peer
      of this.peers.values()
    ) {
      const sender =
        peer
          .getSenders()
          .find(
            (item) =>
              item.track
                ?.kind ===
              "video",
          );

      if (sender) {
        await sender
          .replaceTrack(
            screenTrack,
          );
      } else {
        peer.addTrack(
          screenTrack,
          stream,
        );
      }
    }


    screenTrack.onended =
      () => {
        void this
          .stopScreenShare();
      };

    return stream;
  }


  async stopScreenShare():
    Promise<void> {
    if (
      !this.screenStream
    ) {
      return;
    }

    for (
      const track
      of this.screenStream
        .getTracks()
    ) {
      track.stop();
    }

    this.screenStream =
      null;


    for (
      const peer
      of this.peers.values()
    ) {
      for (
        const sender
        of peer.getSenders()
      ) {
        if (
          sender.track
            ?.kind ===
          "video"
        ) {
          try {
            await sender
              .replaceTrack(
                null,
              );
          } catch {
            // Peer may already be closed.
          }
        }
      }
    }
  }


  removePeer(
    remoteUserId: string,
  ) {
    const peer =
      this.peers.get(
        remoteUserId,
      );

    if (!peer) {
      return;
    }

    peer.close();

    this.peers.delete(
      remoteUserId,
    );

    this.callbacks
      .onRemoteStreamRemoved(
        remoteUserId,
      );
  }


  syncUsers(
    userIds: string[],
  ) {
    const allowed =
      new Set(
        userIds,
      );

    for (
      const userId
      of this.peers.keys()
    ) {
      if (
        !allowed.has(
          userId,
        )
      ) {
        this.removePeer(
          userId,
        );
      }
    }
  }


  async destroy() {
    await this
      .stopScreenShare();

    for (
      const peer
      of this.peers.values()
    ) {
      peer.close();
    }

    this.peers.clear();


    if (
      this.localStream
    ) {
      for (
        const track
        of this.localStream
          .getTracks()
      ) {
        track.stop();
      }
    }

    this.localStream =
      null;
  }
}