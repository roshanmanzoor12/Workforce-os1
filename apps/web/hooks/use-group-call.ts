"use client";
import { mediaSlots, roleFor, type MediaRole } from "@/lib/call-media-slots";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  groupsService,
  type GroupCall,
  type GroupDetail,
  type CallSignal,
} from "@/services/groups.service";

export type RemoteMedia = {
  key: string;
  userId: string;
  stream: MediaStream;
  kind: "audio" | "video";
  source: "microphone" | "camera" | "screen";
};

type Peer = {
  pc: RTCPeerConnection;
  microphone: RTCRtpSender;
  camera: RTCRtpSender;
  screen: RTCRtpSender;
  remoteSlots: Record<string, MediaRole>;
  needsNegotiation: boolean;
  makingOffer: boolean;
  ignoreOffer: boolean;
  received: Promise<void>;
  candidates: RTCIceCandidateInit[];
};

function errorMessage(error: unknown) {
  return error instanceof Error ? error.message : "The call failed.";
}

export function useGroupCall(userId?: string) {
  const [call, setCall] = useState<GroupCall | null>(null);
  const [localStream, setLocalStream] = useState<MediaStream | null>(null);
  const [screenStream, setScreenStream] = useState<MediaStream | null>(null);
  const [remoteMedia, setRemoteMedia] = useState<RemoteMedia[]>([]);
  const [status, setStatus] = useState("Idle");
  const [busy, setBusy] = useState(false);
  const [microphoneEnabled, setMicrophoneEnabled] = useState(true);
  const [cameraEnabled, setCameraEnabled] = useState(false);
  const [error, setError] = useState("");

  const callRef = useRef<GroupCall | null>(null);
  const localRef = useRef<MediaStream | null>(null);
  const screenRef = useRef<MediaStream | null>(null);
  const peers = useRef(new Map<string, Peer>());
  const generation = useRef(0);
  const starting = useRef(false);
  const iceServers = useRef<RTCIceServer[]>([]);
  const signalCursor = useRef<string | undefined>(undefined);
  const connectionId = useRef("");
  const heartbeatAt = useRef(0);

  const cleanup = useCallback(() => {
    generation.current += 1;

    peers.current.forEach(({ pc }) => pc.close());
    peers.current.clear();

    localRef.current?.getTracks().forEach((track) => track.stop());
    screenRef.current?.getTracks().forEach((track) => track.stop());

    localRef.current = null;
    screenRef.current = null;
    callRef.current = null;

    setCall(null);
    setLocalStream(null);
    setScreenStream(null);
    setRemoteMedia([]);
    setStatus("Idle");
    setBusy(false);
  }, []);

  const updateConnectionStatus = useCallback(() => {
    const states = [...peers.current.values()].map(
      ({ pc }) => pc.connectionState,
    );

    if (states.some((state) => state === "connected")) {
      setStatus("Connected");
    } else if (states.some((state) => state === "failed")) {
      setStatus("Connection failed — leave and retry");
    } else if (states.some((state) => state === "disconnected")) {
      setStatus("Connection interrupted");
    } else if (states.length) {
      setStatus("Connecting");
    } else {
      setStatus("Waiting for participants");
    }
  }, []);

  const negotiate = useCallback(async (target: string, peer: Peer) => {
    const current = callRef.current;

    if (!current || peer.pc.signalingState === "closed") return;

    if (peer.makingOffer || peer.pc.signalingState !== "stable") {
      peer.needsNegotiation = true;
      return;
    }

    peer.needsNegotiation = false;
    peer.makingOffer = true;

    try {
      await peer.pc.setLocalDescription(
        await peer.pc.createOffer(),
      );

      await groupsService.signal(
        current.id,
        target,
        "OFFER",
        {
          description: peer.pc.localDescription!.toJSON(),
          media_slots: mediaSlots(
            peer.pc,
            peer.microphone,
            peer.camera,
            peer.screen,
          ),
        },
      );
    } finally {
      peer.makingOffer = false;
    }
  }, []);

  const getPeer = useCallback((targetUserId: string) => {
    const existing = peers.current.get(targetUserId);

    if (existing) return existing;

    const currentCall = callRef.current;

    if (!currentCall) {
      throw new Error("No active call.");
    }

    const pc = new RTCPeerConnection({
      iceServers: iceServers.current,
    });

    // Reserve independent microphone, camera and screen tracks.
    // Later screen sharing can replace a track without adding
    // an extra transceiver or relying on an undocumented signal.
    const microphone = pc.addTransceiver("audio", {
      direction: "sendrecv",
    }).sender;

    const camera = pc.addTransceiver("video", {
      direction: "sendrecv",
    }).sender;

    const screen = pc.addTransceiver("video", {
      direction: "sendrecv",
    }).sender;

    const peer: Peer = {
      pc,
      microphone,
      camera,
      screen,
      remoteSlots: {},
      needsNegotiation: false,
      makingOffer: false,
      ignoreOffer: false,
      received: Promise.resolve(),
      candidates: [],
    };

    peers.current.set(targetUserId, peer);

    pc.onicecandidate = (event) => {
      if (!event.candidate || !callRef.current) return;

      void groupsService.signal(
        currentCall.id,
        targetUserId,
        "ICE_CANDIDATE",
        { candidate: event.candidate.toJSON() },
      ).catch((cause) => setError(errorMessage(cause)));
    };

    pc.onconnectionstatechange = updateConnectionStatus;

    pc.onsignalingstatechange = () => {
      if (
        pc.signalingState === "stable"
        && peer.needsNegotiation
      ) {
        void negotiate(targetUserId, peer).catch(
          cause => setError(errorMessage(cause)),
        );
      }
    };

    pc.ontrack = (event) => {
      const stream = new MediaStream([event.track]);
      const key = `${targetUserId}:${event.track.id}`;

      const source: RemoteMedia["source"] = roleFor(event, peer.remoteSlots, screen);

      const show = () => setRemoteMedia(current => [
        ...current.filter(item => item.key !== key),
        {
          key,
          userId: targetUserId,
          stream,
          kind: event.track.kind === "audio" ? "audio" : "video",
          source,
        },
      ]);

      const hide = () => setRemoteMedia(current =>
        current.filter(item => item.key !== key),
      );

      show();

      event.track.onunmute = show;

      event.track.onmute = () => {};

      event.track.onended = hide;
    };

    return peer;
  }, [updateConnectionStatus, negotiate]);

  const installTracks = useCallback(async (peer: Peer) => {
    await Promise.all([
      peer.microphone.replaceTrack(
        localRef.current?.getAudioTracks()[0] ?? null,
      ),
      peer.camera.replaceTrack(
        localRef.current?.getVideoTracks()[0] ?? null,
      ),
      peer.screen.replaceTrack(
        screenRef.current?.getVideoTracks()[0] ?? null,
      ),
    ]);
  }, []);


  const receiveSignal = useCallback(async (signal: CallSignal) => {
    if (
      !callRef.current
      || signal.sender_user_id === userId
    ) {
      return;
    }

    const peer = getPeer(signal.sender_user_id);
    const pc = peer.pc;

    peer.received = peer.received
      .catch(() => undefined)
      .then(async () => {
        if (pc.signalingState === "closed") return;

        if (signal.signal_type === "ICE_CANDIDATE") {
          if (!signal.payload.candidate || peer.ignoreOffer) return;

          if (pc.remoteDescription) {
            await pc.addIceCandidate(signal.payload.candidate);
          } else {
            peer.candidates.push(signal.payload.candidate);
          }

          return;
        }

        const description = signal.payload.description;

        if (!description?.sdp) {
          throw new Error(
            "A call signal is missing its description.",
          );
        }

        const collision =
          description.type === "offer"
          && (
            peer.makingOffer
            || pc.signalingState !== "stable"
          );

        peer.ignoreOffer =
          collision
          && userId! < signal.sender_user_id;

        if (peer.ignoreOffer) return;

        peer.remoteSlots =
          signal.payload.media_slots
          ?? peer.remoteSlots;

        await pc.setRemoteDescription(description);

        for (const candidate of peer.candidates.splice(0)) {
          await pc.addIceCandidate(candidate);
        }

        if (description.type === "offer") {
          await installTracks(peer);

          await pc.setLocalDescription(
            await pc.createAnswer(),
          );

          await groupsService.signal(
            callRef.current!.id,
            signal.sender_user_id,
            "ANSWER",
            {
              description: pc.localDescription!.toJSON(),
              media_slots: mediaSlots(
                pc,
                peer.microphone,
                peer.camera,
                peer.screen,
              ),
            },
          );
        }
      });

    return peer.received;
  }, [getPeer, installTracks, userId]);

  const stopScreen = useCallback(async () => {
    const currentCall = callRef.current;

    screenRef.current?.getTracks().forEach((track) => track.stop());
    screenRef.current = null;
    setScreenStream(null);

    await Promise.all(
      [...peers.current.values()].map(({ screen }) =>
        screen.replaceTrack(null),
      ),
    );

    if (currentCall) {
      await groupsService.screenState(currentCall.id, false);
    }
  }, []);

  const startScreen = useCallback(async () => {
    if (!callRef.current) return;

    const captured = await navigator.mediaDevices.getDisplayMedia({
      video: true,
      audio: false,
    });

    try {
      await groupsService.screenState(callRef.current.id, true);

      screenRef.current = captured;
      setScreenStream(captured);

      await Promise.all(
        [...peers.current.values()].map(({ screen }) =>
          screen.replaceTrack(captured.getVideoTracks()[0] ?? null),
        ),
      );

      await Promise.all(
        [...peers.current].map(
          ([id, peer]) => negotiate(id, peer),
        ),
      );

      const track = captured.getVideoTracks()[0];

      if (track) {
        track.onended = () => {
          void stopScreen().catch((cause) =>
            setError(errorMessage(cause)),
          );
        };
      }
    } catch (cause) {
      captured.getTracks().forEach((track) => track.stop());
      throw cause;
    }
  }, [stopScreen, negotiate]);

  const start = useCallback(async (
    group: {
      id: string;
      members: {
        user_id: string;
      }[];
    },
    mode: "voice" | "video" | "screen",
    existing?: GroupCall,
  ) => {
    if (!userId || starting.current || callRef.current) return;

    starting.current = true;
    setBusy(true);
    setError("");
    setStatus("Requesting media permission");

    const run = ++generation.current;
    let captured: MediaStream | null = null;
    let display: MediaStream | null = null;
    let joined: GroupCall | null = null;

    try {
      if (!navigator.mediaDevices?.getUserMedia) {
        throw new Error(
          "Calling requires a secure browser context with media support.",
        );
      }

      // Screen capture stays directly connected to the click action.
      if (mode === "screen") {
        display = await navigator.mediaDevices.getDisplayMedia({
          video: true,
          audio: false,
        });
      }

      captured = await navigator.mediaDevices.getUserMedia({
        audio: true,
        video: mode === "video",
      });

      const configuration = await groupsService.iceConfig();

      if (!configuration.ice_servers.length) {
        throw new Error("The backend returned no ICE/TURN configuration.");
      }

      if (run !== generation.current) {
        throw new Error("Call start was cancelled.");
      }

      iceServers.current = configuration.ice_servers;

      joined = existing ?? await groupsService.createCall(
        group.id,
        mode === "video" ? "VIDEO" : "VOICE",
        group.members
          .filter((member) => member.user_id !== userId)
          .map((member) => member.user_id),
      );

      await groupsService.joinCall(joined.id);

      if (run !== generation.current) {
        throw new Error("Call start was cancelled.");
      }

      connectionId.current = crypto.randomUUID();
      signalCursor.current = undefined;
      heartbeatAt.current = 0;

      localRef.current = captured;
      screenRef.current = display;
      callRef.current = joined;

      setLocalStream(captured);
      setScreenStream(display);
      setCall(joined);
      setMicrophoneEnabled(true);
      setCameraEnabled(mode === "video");
      setStatus("Waiting for participants");

      await groupsService.mediaState(
        joined.id,
        true,
        mode === "video",
      );

      if (display) {
        await groupsService.screenState(joined.id, true);

        const track = display.getVideoTracks()[0];

        if (track) {
          track.onended = () => {
            void stopScreen().catch((cause) =>
              setError(errorMessage(cause)),
            );
          };
        }
      }
    } catch (cause) {
      captured?.getTracks().forEach((track) => track.stop());
      display?.getTracks().forEach((track) => track.stop());

      if (joined) {
        const closeRequest =
          !existing && joined.started_by_user_id === userId
            ? groupsService.endCall(joined.id)
            : groupsService.leaveCall(joined.id);

        void closeRequest.catch(() => undefined);
      }

      cleanup();
      setError(errorMessage(cause));
    } finally {
      starting.current = false;
      setBusy(false);
    }
  }, [cleanup, stopScreen, userId]);

  useEffect(() => {
    if (!call || !userId) return;

    let disposed = false;
    let timer: ReturnType<typeof setTimeout>;
    const controller = new AbortController();

    async function poll() {
      try {
        const current = await groupsService.getCall(call!.id);

        if (disposed) return;

        if (["ENDED", "CANCELLED", "FAILED"].includes(
          current.status.toUpperCase(),
        )) {
          cleanup();
          return;
        }

        callRef.current = current;
        setCall(current);

        const joinedIds = new Set(
          current.participants
            .filter((item) => item.state === "JOINED")
            .map((item) => item.user_id),
        );

        for (const [peerId, peer] of peers.current) {
          if (!joinedIds.has(peerId)) {
            peer.pc.close();
            peers.current.delete(peerId);

            setRemoteMedia((items) =>
              items.filter((item) => item.userId !== peerId),
            );
          }
        }

        /**
         * Deterministic offer ownership prevents simultaneous offers.
         * The lower user ID initiates each pair.
         */
        for (const peerId of joinedIds) {
          if (
            peerId === userId ||
            userId! > peerId ||
            peers.current.has(peerId)
          ) {
            continue;
          }

          const peer = getPeer(peerId);
          await installTracks(peer);
          await negotiate(peerId, peer);
        }

        const inbox = await groupsService.signals(
          current.id,
          signalCursor.current,
          controller.signal,
        );

        for (const signal of inbox.items) {
          if (disposed) return;
          await receiveSignal(signal);
        }

        signalCursor.current =
          inbox.next_cursor ?? signalCursor.current;

        if (Date.now() - heartbeatAt.current >= 15_000) {
          await groupsService.heartbeat(
            current.id,
            connectionId.current,
          );

          heartbeatAt.current = Date.now();
        }

        if (!disposed) updateConnectionStatus();
      } catch (cause) {
        if (!disposed) {
          setError(errorMessage(cause));
          setStatus("Connection interrupted — retrying");
        }
      } finally {
        if (!disposed) {
          timer = setTimeout(() => void poll(), 1_000);
        }
      }
    }

    void poll();

    return () => {
      disposed = true;
      controller.abort();
      clearTimeout(timer);
    };
  }, [
    call?.id,
    userId,
    cleanup,
    getPeer,
    installTracks,
    receiveSignal,
    updateConnectionStatus,
    negotiate,
  ]);

  const toggleMicrophone = useCallback(async () => {
    const current = callRef.current;

    if (!current) return;

    const next = !microphoneEnabled;

    await groupsService.mediaState(current.id, next, cameraEnabled);

    localRef.current?.getAudioTracks().forEach((track) => {
      track.enabled = next;
    });

    setMicrophoneEnabled(next);
  }, [cameraEnabled, microphoneEnabled]);

  const toggleCamera = useCallback(async () => {
    const current = callRef.current;
    const stream = localRef.current;

    if (!current || !stream) return;

    const next = !cameraEnabled;
    let addedTrack: MediaStreamTrack | null = null;

    try {
      if (next && !stream.getVideoTracks().length) {
        const captured = await navigator.mediaDevices.getUserMedia({
          audio: false,
          video: true,
        });

        addedTrack = captured.getVideoTracks()[0] ?? null;

        if (addedTrack) {
          stream.addTrack(addedTrack);
        }
      }

      await groupsService.mediaState(
        current.id,
        microphoneEnabled,
        next,
      );

      stream.getVideoTracks().forEach((track) => {
        track.enabled = next;
      });

      await Promise.all(
        [...peers.current.values()].map(({ camera }) =>
          camera.replaceTrack(stream.getVideoTracks()[0] ?? null),
        ),
      );

      setLocalStream(new MediaStream(stream.getTracks()));
      setCameraEnabled(next);
    } catch (cause) {
      if (addedTrack) {
        stream.removeTrack(addedTrack);
        addedTrack.stop();
      }

      throw cause;
    }
  }, [cameraEnabled, microphoneEnabled]);

  const leave = useCallback(async (endForEveryone = false) => {
    const current = callRef.current;

    if (!current) return;

    // Release browser media immediately.
    cleanup();

    try {
      if (endForEveryone) {
        await groupsService.endCall(current.id);
      } else {
        await groupsService.leaveCall(current.id);
      }
    } catch (cause) {
      setError(
        `Media was stopped, but the backend could not close your call session: ${
          errorMessage(cause)
        }`,
      );
    }
  }, [cleanup]);

  useEffect(() => {
    return () => {
      const current = callRef.current;

      generation.current += 1;
      peers.current.forEach(({ pc }) => pc.close());
      peers.current.clear();

      localRef.current?.getTracks().forEach((track) => track.stop());
      screenRef.current?.getTracks().forEach((track) => track.stop());

      if (current) {
        void groupsService.leaveCall(current.id).catch(() => undefined);
      }
    };
  }, []);

  return {
    call,
    localStream,
    screenStream,
    remoteMedia,
    status,
    busy,
    error,
    microphoneEnabled,
    cameraEnabled,
    start,
    leave,
    toggleMicrophone,
    toggleCamera,
    startScreen,
    stopScreen,
  };
}