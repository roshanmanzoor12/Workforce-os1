"use client";
import { mediaSlots, roleFor, type MediaRole } from "@/lib/call-media-slots";
import { DirectCallInvite } from "@/components/chat/direct-call-invite";
import { CallRingtone } from "@/components/chat/call-ringtone";

import {
  SpeakingIndicator,
} from "@/components/chat/speaking-indicator";

import { UserAvatar } from "@/components/account/user-avatar";

import {
  ArrowDownLeft,
  ArrowUpRight,
  Camera,
  ChevronLeft,
  ChevronRight,
  Loader2,
  Mic,
  MicOff,
  Monitor,
  MoreHorizontal,
  Phone,
  PhoneMissed,
  PhoneOff,
  Plus,
  RefreshCw,
  Search,
  Star,
  UserPlus,
  Users,
  Video,
  VideoOff,
  Volume2,
  VolumeX,
  X,
} from "lucide-react";
import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import type { FormEvent } from "react";
import { api as authenticatedApi } from "@/lib/api/client";

const PAGE_SIZE = 5;

type Kind = "VOICE" | "VIDEO";
type CallStatus = "RINGING" | "ACTIVE" | "ENDED" | "CANCELLED";
type Direction = "Incoming" | "Outgoing" | "Missed";

type Participant = {
  user_id: string;
  state: "INVITED" | "JOINED" | "LEFT" | "DECLINED";
  microphone_enabled: boolean;
  camera_enabled: boolean;
  screen_share_state: "STOPPED" | "ACTIVE";
  joined_at: string | null;
  left_at: string | null;
};

type PersonalCall = {
  id: string;
  scope: "CONVERSATION" | "CHANNEL";
  conversation_id: string | null;
  channel_id: string | null;
  started_by_user_id: string;
  kind: Kind;
  status: CallStatus;
  created_at: string;
  started_at: string | null;
  ended_at: string | null;
  participants?: Participant[];
  invitation_expires_at?: string;
  caller_avatar_url?: string | null;
  contact_avatar_url?: string | null;
  conversation_name?: string;
  conversation_type?: "direct" | "group";
  caller_name?: string;
  contact_number?: string | null;
  direction?: Direction;
  duration_seconds?: number;
  outcome?: string;
};

type Friend = {
  user_id: string;
  name: string;
  online?: boolean;
  calling_number?: string;
  username?: string;
  avatar_url?: string | null;
};

type Conversation = {
  id: string;
  conversation_type: "direct" | "group";
  name: string | null;
  is_active: boolean;
};

type User = {
  id: string;
  username: string;
};

type CallHistory = {
  items: PersonalCall[];
  total: number;
  totals: {
    total: number;
    missed: number;
    voice: number;
    video: number;
  };
};

type CallContext = {
  id?: string;
  name: string;
  conversation_type: "direct" | "group";
  members: Friend[];
};

type RemoteMedia = {
  key: string;
  userId: string;
  stream: MediaStream;
  source: "microphone" | "camera" | "screen";
};

type SignalEnvelope = {
  call_id: string;
  from_user_id: string;
  target_user_id?: string | null;
  signal_type: "OFFER" | "ANSWER" | "ICE_CANDIDATE";
  payload: {
    media_slots?: Record<string, MediaRole>;
    description?: RTCSessionDescriptionInit;
    type?: RTCSdpType;
    sdp?: string;
    candidate?: RTCIceCandidateInit | null;
  };
};

type Peer = {
  pc: RTCPeerConnection;
  microphone: RTCRtpSender;
  camera: RTCRtpSender;
  screen: RTCRtpSender;
  makingOffer: boolean;
  ignoreOffer: boolean;
  settingAnswer: boolean;
  offer: () => Promise<void>;
  remoteSlots: Record<string, MediaRole>;
  needsNegotiation: boolean;
  candidates: RTCIceCandidateInit[];
  received: Promise<void>;
};

function messageOf(error: unknown): string {
  return error instanceof Error ? error.message : "The request failed.";
}

function isClosedCallError(error: unknown): boolean {
  return Boolean(
    error &&
      typeof error === "object" &&
      "status" in error &&
      [404, 409].includes(Number(error.status)),
  );
}

function api<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  return authenticatedApi.request<T>(path, options);
}

function post<T>(path: string, body?: unknown): Promise<T> {
  return api<T>(path, {
    method: "POST",
    ...(body === undefined ? {} : { body: JSON.stringify(body) }),
  });
}

function initials(name: string): string {
  return (
    name
      .trim()
      .split(/\s+/)
      .slice(0, 2)
      .map((part) => part[0]?.toUpperCase())
      .join("") || "?"
  );
}

function duration(seconds: number): string {
  const value = Math.max(0, Math.floor(seconds));
  const minutes = Math.floor(value / 60);
  const remainder = value % 60;

  return `${String(minutes).padStart(2, "0")}:${String(remainder).padStart(2, "0")}`;
}

function callDuration(call: PersonalCall): string {
  if (call.duration_seconds !== undefined) {
    return call.started_at ? duration(call.duration_seconds) : "—";
  }

  if (!call.started_at || !call.ended_at) return "—";

  return duration(
    (new Date(call.ended_at).getTime() -
      new Date(call.started_at).getTime()) /
      1000,
  );
}

function callDirection(
  call: PersonalCall,
  userId: string,
): Direction {
  if (call.direction) return call.direction;
  if (call.started_by_user_id === userId) return "Outgoing";

  const participant = call.participants?.find(
    (item) => item.user_id === userId,
  );

  const completed =
    call.status === "ENDED" || call.status === "CANCELLED";

  if (
    completed &&
    participant?.state === "INVITED" &&
    !participant.joined_at
  ) {
    return "Missed";
  }

  return "Incoming";
}

function dateLabel(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";

  const today = new Date();
  const yesterday = new Date();
  yesterday.setDate(yesterday.getDate() - 1);

  const time = date.toLocaleTimeString([], {
    hour: "numeric",
    minute: "2-digit",
  });

  if (date.toDateString() === today.toDateString()) {
    return `Today, ${time}`;
  }

  if (date.toDateString() === yesterday.toDateString()) {
    return `Yesterday, ${time}`;
  }

  return `${date.toLocaleDateString([], {
    day: "numeric",
    month: "short",
  })}, ${time}`;
}

function StreamVideo({
  stream,
  muted,
  className,
}: {
  stream: MediaStream;
  muted: boolean;
  className?: string;
}) {
  const ref = useRef<HTMLMediaElement | null>(null);
  const [blocked, setBlocked] = useState(false);
  const [videoReady, setVideoReady] = useState(false);
  const hasVideo = stream.getVideoTracks().length > 0;

  useEffect(() => {
    const element = ref.current;
    if (!element) return;

    element.srcObject = stream;
    setBlocked(false);
    setVideoReady(false);

    let disposed = false;

    void element.play().catch((cause) => {
      if (!disposed && cause?.name === "NotAllowedError") {
        setBlocked(true);
      }
    });

    return () => {
      disposed = true;
      element.srcObject = null;
    };
  }, [stream]);

  return (
    <div
      className={className}
      aria-busy={hasVideo && !videoReady}
      style={
        !hasVideo
          ? {
              display: blocked ? "block" : "none",
              gridColumn: "1 / -1",
            }
          : undefined
      }
    >
      {hasVideo ? (
        <video
          ref={(element) => {
            ref.current = element;
          }}
          onLoadedData={() => setVideoReady(true)}
          autoPlay
          playsInline
          muted={muted}
        />
      ) : (
        <audio
          ref={(element) => {
            ref.current = element;
          }}
          autoPlay
          muted={muted}
        />
      )}

      {blocked ? (
        <button
          type="button"
          className="pc-enable-audio"
          onClick={() => {
            void ref.current
              ?.play()
              .then(() => setBlocked(false))
              .catch(() => setBlocked(true));
          }}
        >
          Enable playback
        </button>
      ) : null}
    </div>
  );
}

function VoiceWaveform({ stream }: { stream: MediaStream }) {
  const canvas = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const element = canvas.current;
    if (!element) return;

    const context = element.getContext("2d");
    if (!context) return;

    const audio = new AudioContext();
    const source = audio.createMediaStreamSource(stream);
    const analyser = audio.createAnalyser();

    analyser.fftSize = 256;
    source.connect(analyser);

    const levels = new Uint8Array(analyser.frequencyBinCount);
    const waveform = new Float32Array(analyser.fftSize);
    let frame = 0;

    const draw = () => {
      analyser.getByteFrequencyData(levels);
      context.clearRect(0, 0, element.width, element.height);
      analyser.getFloatTimeDomainData(waveform);

      let power = 0;

      for (const sample of waveform) {
        power += sample * sample;
      }

      const enabled = stream.getAudioTracks().some(
        track => track.enabled && !track.muted,
      );

      context.fillStyle =
        enabled
        && Math.sqrt(power / waveform.length) > 0.025
          ? "#e7ac12"
          : "#d5d0c5";

      for (let index = 0; index < 48; index++) {
        const height = Math.max(
          3,
          ((levels[index * 2] || 0) / 255) * 72,
        );

        context.fillRect(
          index * 14 + 2,
          (86 - height) / 2,
          4,
          height,
        );
      }

      frame = requestAnimationFrame(draw);
    };

    void audio.resume().catch(() => undefined);
    draw();

    return () => {
      cancelAnimationFrame(frame);
      source.disconnect();
      void audio.close();
    };
  }, [stream]);

  return (
    <canvas
      className="pc-waveform"
      ref={canvas}
      width={680}
      height={86}
      role="img"
      aria-label="Microphone audio activity"
    />
  );
}

function useCallMedia(onError: (message: string) => void) {
  const iceConfiguration = useRef<RTCIceServer[]>([]);
  const localRef = useRef<MediaStream | null>(null);
  const screenRef = useRef<MediaStream | null>(null);
  const callRef = useRef<PersonalCall | null>(null);
  const userRef = useRef("");
  const peers = useRef(new Map<string, Peer>());
  const outgoing = useRef(Promise.resolve());

  const [local, setLocal] = useState<MediaStream | null>(null);
  const [remotes, setRemotes] = useState<RemoteMedia[]>([]);
  const [connectedIds, setConnectedIds] = useState<string[]>([]);
  const [ready, setReady] = useState(false);

  const send = useCallback(
    (
      targetUserId: string,
      signalType: SignalEnvelope["signal_type"],
      payload: Record<string, unknown>,
    ) => {
      const callId = callRef.current?.id;
      if (!callId) return Promise.resolve();

      const task = outgoing.current
        .catch(() => undefined)
        .then(async () => {
          if (callRef.current?.id !== callId) return;

          const compatiblePayload =
            typeof payload.sdp === "string"
              ? {
                  ...payload,
                  description: {
                    type:
                      signalType === "OFFER" ? "offer" : "answer",
                    sdp: payload.sdp,
                  },
                }
              : payload;

          await post(`/calls/${callId}/signal`, {
            target_user_id: targetUserId,
            signal_type: signalType,
            payload: compatiblePayload,
          });
        });

      outgoing.current = task;
      return task;
    },
    [],
  );

  const clear = useCallback(() => {
    callRef.current = null;
    userRef.current = "";

    peers.current.forEach(({ pc }) => {
      pc.ontrack = null;
      pc.onicecandidate = null;
      pc.onnegotiationneeded = null;
      pc.onconnectionstatechange = null;
      pc.close();
    });

    peers.current.clear();
    localRef.current?.getTracks().forEach((track) => track.stop());
    screenRef.current?.getTracks().forEach((track) => track.stop());

    localRef.current = null;
    screenRef.current = null;

    setLocal(null);
    setRemotes([]);
    setConnectedIds([]);
    setReady(false);
  }, []);

  const ensurePeer = useCallback(
    (remoteUserId: string): Peer => {
      const existing = peers.current.get(remoteUserId);
      if (existing) return existing;

      const pc = new RTCPeerConnection({
        iceServers: iceConfiguration.current,
      });

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
        makingOffer: false,
        ignoreOffer: false,
        settingAnswer: false,
        offer: async () => undefined,
        remoteSlots: {},
        needsNegotiation: false,
        candidates: [],
        received: Promise.resolve(),
      };

      peers.current.set(remoteUserId, peer);

      pc.onicecandidate = ({ candidate }) => {
        if (!candidate) return;

        void send(remoteUserId, "ICE_CANDIDATE", {
          candidate: candidate.toJSON(),
        }).catch((cause) => onError(messageOf(cause)));
      };

      pc.ontrack = (event) => {
        const key = `${remoteUserId}:${event.track.id}`;
        const stream = new MediaStream([event.track]);

        const source: RemoteMedia["source"] = roleFor(event, peer.remoteSlots, screen);

        const show = () => {
          setRemotes((current) => [
            ...current.filter((item) => item.key !== key),
            { key, userId: remoteUserId, stream, source },
          ]);
        };

        const hide = () => {
          setRemotes((current) =>
            current.filter((item) => item.key !== key),
          );
        };

        show();

        event.track.onunmute = show;

        event.track.onmute = () => {};

        event.track.onended = hide;
      };

      pc.onconnectionstatechange = () => {
        setConnectedIds((current) => {
          const without = current.filter(
            (id) => id !== remoteUserId,
          );

          return pc.connectionState === "connected"
            ? [...without, remoteUserId]
            : without;
        });

        if (pc.connectionState === "failed") {
          onError(
            "Media connection failed. Check signal delivery and TURN configuration.",
          );
        }
      };

      peer.offer = async () => {
        if (pc.signalingState === "closed") return;

        if (
          peer.makingOffer
          || pc.signalingState !== "stable"
        ) {
          peer.needsNegotiation = true;
          return;
        }

        peer.needsNegotiation = false;
        peer.makingOffer = true;

        try {
          await pc.setLocalDescription(
            await pc.createOffer(),
          );

          await send(remoteUserId, "OFFER", {
            description: pc.localDescription!.toJSON(),
            media_slots: mediaSlots(
              pc,
              microphone,
              camera,
              screen,
            ),
          });
        } finally {
          peer.makingOffer = false;
        }
      };

      pc.onnegotiationneeded = () => {
        if (
          !pc.remoteDescription
          && userRef.current > remoteUserId
        ) {
          return;
        }

        void peer.offer().catch(
          cause => onError(messageOf(cause)),
        );
      };

      pc.onsignalingstatechange = () => {
        if (
          pc.signalingState === "stable"
          && peer.needsNegotiation
        ) {
          void peer.offer().catch(
            cause => onError(messageOf(cause)),
          );
        }
      };

      const stream = localRef.current;

      void Promise.all([
        microphone.replaceTrack(
          stream?.getAudioTracks()[0] || null,
        ),
        camera.replaceTrack(
          stream?.getVideoTracks()[0] || null,
        ),
        screen.replaceTrack(
          screenRef.current?.getVideoTracks()[0] || null,
        ),
      ]).catch((cause) => onError(messageOf(cause)));

      return peer;
    },
    [onError, send],
  );

  const attach = useCallback(
    (
      call: PersonalCall,
      userId: string,
      stream: MediaStream,
    ) => {
      clear();

      callRef.current = call;
      userRef.current = userId;
      localRef.current = stream;

      setLocal(stream);
      setReady(true);
    },
    [clear],
  );

  const syncParticipants = useCallback(
    (participants: Participant[]) => {
      if (!callRef.current || !localRef.current) return;

      const remoteJoined = participants
        .filter(
          (participant) =>
            participant.state === "JOINED" &&
            participant.user_id !== userRef.current,
        )
        .map((participant) => participant.user_id);

      remoteJoined.forEach((userId) => ensurePeer(userId));

      peers.current.forEach(({ pc }, userId) => {
        if (remoteJoined.includes(userId)) return;

        pc.close();
        peers.current.delete(userId);

        setRemotes((current) =>
          current.filter((item) => item.userId !== userId),
        );

        setConnectedIds((current) =>
          current.filter((id) => id !== userId),
        );
      });
    },
    [ensurePeer],
  );

  useEffect(() => {
    const receive = (event: Event) => {
      const signal = (
        event as CustomEvent<SignalEnvelope>
      ).detail;

      if (
        !signal ||
        signal.call_id !== callRef.current?.id ||
        !signal.from_user_id ||
        signal.from_user_id === userRef.current ||
        (signal.target_user_id &&
          signal.target_user_id !== userRef.current) ||
        !localRef.current
      ) {
        return;
      }

      const peer = ensurePeer(signal.from_user_id);
      const pc = peer.pc;

      peer.received = peer.received
        .catch(() => undefined)
        .then(async () => {
          if (pc.signalingState === "closed") return;

          if (signal.signal_type === "ICE_CANDIDATE") {
            const candidate = signal.payload.candidate;
            if (!candidate || peer.ignoreOffer) return;

            if (!pc.remoteDescription) {
              peer.candidates.push(candidate);
            } else {
              await pc.addIceCandidate(candidate);
            }

            return;
          }

          const description: RTCSessionDescriptionInit = {
            type:
              signal.signal_type === "OFFER"
                ? "offer"
                : "answer",
            sdp:
              signal.payload.sdp ||
              signal.payload.description?.sdp,
          };

          if (!description.sdp) {
            throw new Error(
              "The received call signal has no SDP.",
            );
          }

          const polite =
            userRef.current.localeCompare(
              signal.from_user_id,
            ) > 0;

          const readyForOffer =
            !peer.makingOffer &&
            (pc.signalingState === "stable" ||
              peer.settingAnswer);

          const collision =
            description.type === "offer" && !readyForOffer;

          peer.ignoreOffer = !polite && collision;
          if (peer.ignoreOffer) return;

          peer.remoteSlots =
            signal.payload.media_slots
            ?? peer.remoteSlots;

          peer.settingAnswer = description.type === "answer";

          try {
            await pc.setRemoteDescription(description);
          } finally {
            peer.settingAnswer = false;
          }

          for (const candidate of peer.candidates.splice(0)) {
            await pc.addIceCandidate(candidate);
          }

          if (description.type === "offer") {
            await pc.setLocalDescription();

            await send(signal.from_user_id, "ANSWER", {
              type: pc.localDescription?.type,
              sdp: pc.localDescription?.sdp,
              media_slots: mediaSlots(
                pc,
                peer.microphone,
                peer.camera,
                peer.screen,
              ),
            });
          }
        })
        .catch((cause) => onError(messageOf(cause)));
    };

    window.addEventListener("workforce:call-signal", receive);

    return () => {
      window.removeEventListener(
        "workforce:call-signal",
        receive,
      );
    };
  }, [ensurePeer, onError, send]);

  useEffect(() => clear, [clear]);

  async function microphone(enabled: boolean) {
    const stream = localRef.current;

    if (!stream) {
      throw new Error("Join the media session first.");
    }

    stream.getAudioTracks().forEach((track) => {
      track.enabled = enabled;
    });
  }

  async function replaceVideo(
    track: MediaStreamTrack | null,
    screen = false,
  ) {
    await Promise.all(
      Array.from(peers.current.values()).map((peer) =>
        (screen ? peer.screen : peer.camera).replaceTrack(track),
      ),
    );
  }

  async function camera(enabled: boolean) {
    const stream = localRef.current;

    if (!stream) {
      throw new Error("Join the media session first.");
    }

    let track = stream.getVideoTracks()[0];

    if (enabled && (!track || track.readyState === "ended")) {
      const acquired =
        await navigator.mediaDevices.getUserMedia({
          video: true,
          audio: false,
        });

      const acquiredTrack = acquired.getVideoTracks()[0];

      if (!acquiredTrack) {
        acquired.getTracks().forEach((item) => item.stop());

        throw new Error(
          "The camera did not provide a video track.",
        );
      }

      track = acquiredTrack;

      stream.getVideoTracks().forEach((oldTrack) => {
        stream.removeTrack(oldTrack);
      });

      stream.addTrack(track);
    }

    if (track) track.enabled = enabled;

    await replaceVideo(enabled ? track || null : null);
    setLocal(new MediaStream(stream.getTracks()));
  }

  async function startScreen(onEnded: () => void) {
    if (!navigator.mediaDevices?.getDisplayMedia) {
      throw new Error(
        "Screen sharing is unavailable in this browser.",
      );
    }

    const stream =
      await navigator.mediaDevices.getDisplayMedia({
        video: true,
        audio: false,
      });

    const track = stream.getVideoTracks()[0];

    if (!track) {
      stream.getTracks().forEach((item) => item.stop());

      throw new Error(
        "Screen sharing did not provide a video track.",
      );
    }

    try {
      await replaceVideo(track, true);
      screenRef.current = stream;

      await Promise.all(
        [...peers.current.values()].map(
          peer => peer.offer(),
        ),
      );
      track.onended = onEnded;
    } catch (cause) {
      stream.getTracks().forEach((item) => item.stop());
      throw cause;
    }
  }

  async function stopScreen() {
    const screen = screenRef.current;
    screenRef.current = null;

    screen?.getTracks().forEach((track) => {
      track.onended = null;
      track.stop();
    });

    await replaceVideo(null, true);
  }

  async function prepare() {
    const configuration = await api<{
      ice_servers: RTCIceServer[];
    }>("/calls/ice-config");

    iceConfiguration.current = configuration.ice_servers;
  }

  return {
    local,
    remotes,
    connectedIds,
    ready,
    attach,
    prepare,
    clear,
    syncParticipants,
    microphone,
    camera,
    startScreen,
    stopScreen,
  };
}

export default function PersonalCallsPage() {
  const [me, setMe] = useState<User | null>(null);
  const [history, setHistory] =
    useState<CallHistory | null>(null);
  const [recentGroups, setRecentGroups] =
    useState<PersonalCall[]>([]);
  const [callingNumber, setCallingNumber] = useState("");
  const [historyKind, setHistoryKind] =
    useState<"" | Kind>("");
  const [dialNumber, setDialNumber] = useState("");
  const [dialContact, setDialContact] =
    useState<Friend | null>(null);
  const [dialLookup, setDialLookup] = useState(false);
  const [dialError, setDialError] = useState("");
  const [inviteCandidates, setInviteCandidates] =
    useState<Friend[]>([]);
  const [dismissedIncoming, setDismissedIncoming] =
    useState("");
  const [friends, setFriends] = useState<Friend[]>([]);
  const [conversations, setConversations] =
    useState<Conversation[]>([]);
  const [calls, setCalls] = useState<PersonalCall[]>([]);
  const [active, setActive] =
    useState<PersonalCall | null>(null);
  const [incoming, setIncoming] =
    useState<PersonalCall | null>(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [filter, setFilter] =
    useState<"All" | "Missed" | "Incoming" | "Outgoing">(
      "All",
    );
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [favorites, setFavorites] = useState<string[]>([]);
  const [showAllFavorites, setShowAllFavorites] =
    useState(false);
  const [showAllGroups, setShowAllGroups] =
    useState(false);
  const [menu, setMenu] = useState(false);
  const [speaker, setSpeaker] = useState(true);
  const [microphoneEnabled, setMicrophoneEnabled] =
    useState(true);
  const [cameraEnabled, setCameraEnabled] =
    useState(false);
  const [sharing, setSharing] = useState(false);
  const [now, setNow] = useState(Date.now());

  const [picker, setPicker] =
    useState<"direct" | "group" | "invite" | null>(null);
  const [pickerSearch, setPickerSearch] = useState("");
  const [selectedFriends, setSelectedFriends] =
    useState<string[]>([]);
  const [selectedGroup, setSelectedGroup] = useState("");
  const [groupName, setGroupName] = useState("");
  const [kind, setKind] = useState<Kind>("VOICE");

  const busyRef = useRef(false);
  const historyGeneration = useRef(0);
  const activeRef = useRef<PersonalCall | null>(null);
  const mounted = useRef(true);
  const connectionId = useRef("");
  const [contactNames, setContactNames] =
    useState<Record<string, string>>({});

  const showError = useCallback((message: string) => {
    if (mounted.current) setError(message);
  }, []);

  const media = useCallMedia(showError);

  useEffect(() => {
    if (!picker) return;

    const previous =
      document.activeElement as HTMLElement | null;

    const handler = (event: KeyboardEvent) => {
      if (
        event.key === "Escape" &&
        !busyRef.current
      ) {
        event.preventDefault();
        setPicker(null);
      }

      if (event.key !== "Tab") return;

      const dialog =
        document.querySelector<HTMLDialogElement>(
          ".pc-dialog",
        );

      const controls = dialog
        ? Array.from(
            dialog.querySelectorAll<HTMLElement>(
              'button:not(:disabled), input:not(:disabled), select:not(:disabled), [tabindex="0"]',
            ),
          )
        : [];

      const first = controls[0];
      const last = controls[controls.length - 1];

      if (
        event.shiftKey &&
        document.activeElement === first
      ) {
        event.preventDefault();
        last?.focus();
      } else if (
        !event.shiftKey &&
        document.activeElement === last
      ) {
        event.preventDefault();
        first?.focus();
      }
    };

    document.addEventListener("keydown", handler);

    return () => {
      document.removeEventListener("keydown", handler);
      previous?.focus();
    };
  }, [picker]);

  useEffect(() => {
    activeRef.current = active;
  }, [active]);

  const localCallKey = me
    ? `workforce:personal-call:${me.id}`
    : "";

  useEffect(() => {
    mounted.current = true;
    connectionId.current = crypto.randomUUID();

    const controller = new AbortController();

    void api<{ user: User }>("/auth/me", {
      signal: controller.signal,
    })
      .then(({ user }) => {
        if (!controller.signal.aborted) setMe(user);
      })
      .catch((cause) => {
        if (!controller.signal.aborted) {
          showError(messageOf(cause));
          setLoading(false);
        }
      });

    return () => {
      mounted.current = false;
      controller.abort();
    };
  }, [showError]);

  useEffect(() => {
    const timer = window.setInterval(
      () => setNow(Date.now()),
      1000,
    );

    return () => window.clearInterval(timer);
  }, []);

  const forgetActive = useCallback(() => {
    activeRef.current = null;

    setActive(null);
    setSharing(false);
    setMenu(false);
    media.clear();

    if (localCallKey) {
      try {
        localStorage.removeItem(localCallKey);
      } catch {
        // Calling continues to work when browser storage is unavailable.
      }
    }
  }, [localCallKey, media.clear]);

  const rememberActive = useCallback(
    (call: PersonalCall) => {
      activeRef.current = call;
      setActive(call);

      if (localCallKey) {
        try {
          localStorage.setItem(localCallKey, call.id);
        } catch {
          // Local recovery is optional.
        }
      }
    },
    [localCallKey],
  );

  const reload = useCallback(async () => {
    if (!me) return;

    const generation = ++historyGeneration.current;

    const params = new URLSearchParams({
      direction: filter.toLowerCase(),
      search,
      limit: String(PAGE_SIZE),
      offset: String((page - 1) * PAGE_SIZE),
    });

    if (historyKind) params.set("kind", historyKind);

    const results = await Promise.allSettled([
      api<CallHistory>(`/calls/history?${params}`),
      api<{ items: Friend[] }>("/calls/contacts"),
      api<Conversation[]>("/chat/conversations"),
      api<{ user_ids: string[] }>("/calls/favorites"),
      api<CallHistory>(
        `/calls/history?group_only=true&limit=${showAllGroups ? 100 : 3}`,
      ),
    ]);

    if (
      !mounted.current ||
      generation !== historyGeneration.current
    ) {
      return;
    }

    const [
      records,
      directory,
      groups,
      starred,
      groupHistory,
    ] = results;

    if (records.status === "fulfilled") {
      setHistory(records.value);
      setCalls(records.value.items);

      const lastPage = Math.max(
        1,
        Math.ceil(records.value.total / PAGE_SIZE),
      );

      if (page > lastPage) setPage(lastPage);
    }

    if (directory.status === "fulfilled") {
      setFriends(directory.value.items);
    }

    if (groups.status === "fulfilled") {
      setConversations(
        groups.value.filter((item) => item.is_active),
      );
    }

    if (starred.status === "fulfilled") {
      setFavorites(starred.value.user_ids);
    }

    if (groupHistory.status === "fulfilled") {
      setRecentGroups(groupHistory.value.items);
    }

    const failures = results.filter(
      (result): result is PromiseRejectedResult =>
        result.status === "rejected",
    );

    if (failures.length) {
      showError(
        failures
          .map((item) => messageOf(item.reason))
          .join(" "),
      );
    }

    setLoading(false);
  }, [
    me,
    filter,
    search,
    page,
    historyKind,
    showAllGroups,
    showError,
  ]);

  useEffect(() => {
    if (!me) return;

    const delay = window.setTimeout(
      () => void reload(),
      200,
    );

    const timer = window.setInterval(
      () => void reload(),
      10000,
    );

    return () => {
      window.clearTimeout(delay);
      window.clearInterval(timer);
      historyGeneration.current++;
    };
  }, [me, reload]);

  useEffect(() => {
    if (!me) return;

    let disposed = false;

    void api<Friend>("/calls/numbers/me")
      .then((result) => {
        if (!disposed) {
          setCallingNumber(result.calling_number || "");
        }
      })
      .catch((cause) => {
        if (!disposed) showError(messageOf(cause));
      });

    return () => {
      disposed = true;
    };
  }, [me, showError]);

  useEffect(() => {
    if (!me) return;

    let stopped = false;
    let timer: ReturnType<typeof setTimeout>;

    async function check() {
      try {
        const result = await api<{
          items: PersonalCall[];
        }>("/calls/active");

        if (stopped) return;

        const next = result.items.find(
          (call) =>
            call.started_by_user_id !== me!.id &&
            call.participants?.some(
              (participant) =>
                participant.user_id === me!.id &&
                participant.state === "INVITED",
            ),
        );

        setIncoming(
          !activeRef.current &&
            next?.id !== dismissedIncoming
            ? next || null
            : null,
        );
      } catch (cause) {
        if (!stopped) showError(messageOf(cause));
      } finally {
        if (!stopped) {
          timer = setTimeout(() => void check(), 1500);
        }
      }
    }

    void check();

    return () => {
      stopped = true;
      clearTimeout(timer);
    };
  }, [me, dismissedIncoming, showError]);

  useEffect(() => {
    setDialContact(null);
    setDialError("");

    if (
      picker !== "direct" ||
      dialNumber.length !== 10
    ) {
      setDialLookup(false);
      return;
    }

    let cancelled = false;
    setDialLookup(true);

    const timer = setTimeout(() => {
      void api<Friend>(
        `/calls/numbers/lookup?number=${encodeURIComponent(dialNumber)}`,
      )
        .then((person) => {
          if (!cancelled) setDialContact(person);
        })
        .catch((cause) => {
          if (!cancelled) {
            setDialError(messageOf(cause));
          }
        })
        .finally(() => {
          if (!cancelled) setDialLookup(false);
        });
    }, 250);

    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [dialNumber, picker]);

  useEffect(() => {
    if (!me || !localCallKey) return;

    let stopped = false;

    async function restore() {
      try {
        const id = localStorage.getItem(localCallKey);
        if (!id) return;

        const call = await api<PersonalCall>(
          `/calls/${id}`,
        );

        if (stopped) return;

        const participant = call.participants?.find(
          (item) => item.user_id === me!.id,
        );

        if (
          call.scope === "CONVERSATION" &&
          (call.status === "ACTIVE" ||
            call.status === "RINGING") &&
          participant?.state === "JOINED"
        ) {
          rememberActive(call);
        } else {
          localStorage.removeItem(localCallKey);
        }
      } catch (cause) {
        if (!stopped) showError(messageOf(cause));
      }
    }

    void restore();

    return () => {
      stopped = true;
    };
  }, [
    me,
    localCallKey,
    rememberActive,
    showError,
  ]);

  useEffect(() => {
    if (!active?.id || !media.ready) return;

    const callId = active.id;
    let cursor = "0-0";
    let stopped = false;
    let timer: ReturnType<typeof setTimeout>;

    async function receive() {
      try {
        const response = await api<{
          items: (
            Omit<SignalEnvelope, "from_user_id"> & {
              sender_user_id: string;
            }
          )[];
          next_cursor: string;
        }>(
          `/calls/${callId}/signals?cursor=${encodeURIComponent(cursor)}`,
        );

        if (stopped) return;

        for (const event of response.items) {
          window.dispatchEvent(
            new CustomEvent<SignalEnvelope>(
              "workforce:call-signal",
              {
                detail: {
                  ...event,
                  call_id: callId,
                  from_user_id: event.sender_user_id,
                },
              },
            ),
          );
        }

        cursor = response.next_cursor;
      } catch (cause) {
        if (!stopped && !isClosedCallError(cause)) {
          showError(messageOf(cause));
        }
      } finally {
        if (!stopped) {
          timer = setTimeout(
            () => void receive(),
            500,
          );
        }
      }
    }

    void receive();

    return () => {
      stopped = true;
      clearTimeout(timer);
    };
  }, [active?.id, media.ready, showError]);

  useEffect(() => {
    if (!active?.id) return;

    const callId = active.id;
    let stopped = false;
    let polling = false;

    async function poll() {
      if (polling) return;
      polling = true;

      try {
        const [call, participantData] =
          await Promise.all([
            api<PersonalCall>(`/calls/${callId}`),
            api<{ participants: Participant[] }>(
              `/calls/${callId}/participants`,
            ),
          ]);

        if (
          stopped ||
          activeRef.current?.id !== callId
        ) {
          return;
        }

        const stillJoined =
          participantData.participants.some(
            (participant) =>
              participant.user_id === me?.id &&
              participant.state === "JOINED",
          );

        if (
          call.status === "ENDED" ||
          call.status === "CANCELLED" ||
          !stillJoined
        ) {
          forgetActive();
          void reload();
          return;
        }

        const context = await api<CallContext>(
          `/calls/${callId}/context`,
        );

        if (stopped) return;

        setFriends(current => [
          ...current.filter(
            person =>
              !context.members.some(
                member => member.user_id === person.user_id,
              ),
          ),
          ...context.members,
        ]);

        const combined: PersonalCall = {
          ...call,
          conversation_name: context.name,
          conversation_type: context.conversation_type,
          participants: participantData.participants,
        };

        activeRef.current = combined;
        setActive(combined);

        media.syncParticipants(
          participantData.participants,
        );
      } catch (cause) {
        if (!stopped && !isClosedCallError(cause)) {
          showError(messageOf(cause));
        }
      } finally {
        polling = false;
      }
    }

    void poll();

    const timer = window.setInterval(
      () => void poll(),
      3000,
    );

    return () => {
      stopped = true;
      window.clearInterval(timer);
    };
  }, [
    active?.id,
    me?.id,
    media.syncParticipants,
    forgetActive,
    reload,
    showError,
  ]);

  useEffect(() => {
    if (!active?.id || !media.ready) return;

    let stopped = false;
    let pending = false;
    const callId = active.id;

    async function heartbeat() {
      if (pending) return;
      pending = true;

      try {
        await post(`/calls/${callId}/heartbeat`, {
          connection_id: connectionId.current,
        });
      } catch (cause) {
        if (!stopped && !isClosedCallError(cause)) {
          showError(messageOf(cause));
        }
      } finally {
        pending = false;
      }
    }

    void heartbeat();

    const timer = window.setInterval(
      () => void heartbeat(),
      15000,
    );

    return () => {
      stopped = true;
      window.clearInterval(timer);
    };
  }, [active?.id, media.ready, showError]);

  async function run(task: () => Promise<void>) {
    if (busyRef.current) return;

    busyRef.current = true;
    setBusy(true);
    setError("");

    try {
      await task();
    } catch (cause) {
      showError(messageOf(cause));
    } finally {
      busyRef.current = false;

      if (mounted.current) {
        setBusy(false);
      }
    }
  }

  function avatarForCall(call: PersonalCall) {
    const conversation = conversations.find(
      item => item.id === call.conversation_id,
    );

    const groupCall = (
      call.conversation_type ?? conversation?.conversation_type
    ) === "group";

    const peerId = call.started_by_user_id !== me?.id
      ? call.started_by_user_id
      : call.participants?.find(
          item => item.user_id !== me?.id,
        )?.user_id;

    const person = friends.find(item =>
      item.user_id === peerId || (
        Boolean(call.contact_number) &&
        item.calling_number === call.contact_number
      ),
    );

    return (
      <UserAvatar
        userId={groupCall ? undefined : peerId}
        src={groupCall ? null : person?.avatar_url ?? call.contact_avatar_url ?? (peerId === call.started_by_user_id ? call.caller_avatar_url : null)}
        name={nameOf(call)}
        fallback={
          groupCall
            ? <Users size={22} />
            : initials(nameOf(call))
        }
      />
    );
  }

  function nameOf(call: PersonalCall): string {
    if (call.conversation_name) {
      return call.conversation_name;
    }

    const conversationId = call.conversation_id || "";

    const known =
      contactNames[conversationId] ||
      conversations.find(
        (item) => item.id === conversationId,
      )?.name;

    if (known) return known;

    const peerId = call.participants?.find(
      (participant) =>
        participant.user_id !== me?.id,
    )?.user_id;

    return (
      friends.find(
        (friend) => friend.user_id === peerId,
      )?.name || "Personal conversation"
    );
  }

  function openPicker(
    mode: "direct" | "group" | "invite",
    callKind: Kind = "VOICE",
  ) {
    setPicker(mode);
    setDialNumber("");
    setDialContact(null);
    setDialError("");
    setKind(callKind);
    setSelectedFriends([]);
    setSelectedGroup("");
    setGroupName("");
    setPickerSearch("");
    setMenu(false);
  }

  async function acquire(callKind: Kind) {
    if (!navigator.mediaDevices?.getUserMedia) {
      throw new Error(
        "Microphone and camera access require a supported browser and HTTPS.",
      );
    }

    await media.prepare();

    return navigator.mediaDevices.getUserMedia({
      audio: true,
      video: callKind === "VIDEO",
    });
  }

  async function launch(
    conversationId: string,
    callKind: Kind,
    invitedUserIds: string[] = [],
  ) {
    if (!me) {
      throw new Error(
        "Your account is still loading.",
      );
    }

    if (activeRef.current) {
      throw new Error(
        "Leave your current call before starting another.",
      );
    }

    const stream = await acquire(callKind);
    let created: PersonalCall | null = null;

    try {
      created = await post<PersonalCall>("/calls", {
        scope: "CONVERSATION",
        kind: callKind,
        conversation_id: conversationId,
        invited_user_ids: invitedUserIds,
      });

      if (created.scope !== "CONVERSATION") {
        throw new Error(
          "The server returned a non-personal call.",
        );
      }

      await post(`/calls/${created.id}/join`);

      media.attach(created, me.id, stream);
      rememberActive(created);

      setMicrophoneEnabled(true);
      setCameraEnabled(callKind === "VIDEO");
      setSpeaker(true);
      setSharing(false);
      setPicker(null);

      void reload();
    } catch (cause) {
      stream.getTracks().forEach((track) => {
        track.stop();
      });

      if (created) {
        try {
          await post(
            `/calls/${created.id}/${created.started_by_user_id === me.id ? "end" : "leave"}`,
          );
        } catch (cleanupError) {
          throw new Error(
            `${messageOf(cause)} Call cleanup also failed: ${messageOf(cleanupError)}`,
          );
        }
      }

      throw cause;
    }
  }

  async function submitPicker(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    await run(async () => {
      if (picker === "direct") {
        if (
          !dialContact ||
          dialContact.calling_number !== dialNumber
        ) {
          throw new Error(
            "Enter a valid 10-digit account calling number.",
          );
        }

        await dialAccount(dialNumber, kind);
        return;
      }

      if (picker === "invite") {
        const call = activeRef.current;

        if (!call) {
          throw new Error(
            "The call ended. Start another call.",
          );
        }

        await post(
          `/calls/${call.id}/participants/invite`,
          {
            user_ids: selectedFriends,
          },
        );

        setPicker(null);
        setMenu(false);

        const current = await api<PersonalCall>(
          `/calls/${call.id}`,
        );

        rememberActive(current);
        return;
      }

      if (selectedGroup) {
        await launch(selectedGroup, kind);
        return;
      }

      if (!groupName.trim()) {
        throw new Error("Enter a group name.");
      }

      if (selectedFriends.length < 2) {
        throw new Error(
          "Choose at least two friends for a group call.",
        );
      }

      const conversation =
        await post<Conversation>("/chat/groups", {
          name: groupName.trim(),
          member_user_ids: selectedFriends,
        });

      setContactNames((current) => ({
        ...current,
        [conversation.id]: groupName.trim(),
      }));

      await launch(
        conversation.id,
        kind,
        selectedFriends,
      );
    });
  }

  async function dialAccount(
    number: string,
    callKind: Kind,
  ) {
    if (!me || activeRef.current) {
      throw new Error(
        "Leave the current call before dialing.",
      );
    }

    const stream = await acquire(callKind);
    let created: PersonalCall | null = null;

    try {
      created = await post<PersonalCall>(
        "/calls/dial",
        {
          number,
          kind: callKind,
        },
      );

      media.attach(created, me.id, stream);
      rememberActive(created);

      setMicrophoneEnabled(true);
      setCameraEnabled(callKind === "VIDEO");
      setSpeaker(true);
      setSharing(false);
      setPicker(null);

      void reload();
    } catch (cause) {
      stream.getTracks().forEach((track) => {
        track.stop();
      });

      if (created) {
        await post(`/calls/${created.id}/end`).catch(
          () => undefined,
        );
      }

      throw cause;
    }
  }

  async function openInvite() {
    const call = activeRef.current;

    if (!call) {
      throw new Error("Join a call first.");
    }

    const context = await api<CallContext>(
      `/calls/${call.id}/context`,
    );

    if (context.conversation_type !== "direct") {
      throw new Error(
        "Additional people can be invited from a direct call.",
      );
    }

    window.dispatchEvent(
      new CustomEvent(
        "workforce:open-call-invite",
        {
          detail: call.id,
        },
      ),
    );

    setMenu(false);
  }

  async function join(call: PersonalCall) {
    if (!me) {
      throw new Error(
        "Your account is still loading.",
      );
    }

    if (
      activeRef.current &&
      activeRef.current.id !== call.id
    ) {
      throw new Error(
        "Leave your current call before accepting another.",
      );
    }

    const stream = await acquire(call.kind);
    let joined = false;

    try {
      let current = await api<PersonalCall>(
        `/calls/${call.id}`,
      );

      if (
        current.scope !== "CONVERSATION" ||
        !["RINGING", "ACTIVE"].includes(
          current.status,
        )
      ) {
        throw new Error(
          "This call is no longer available.",
        );
      }

      await post(`/calls/${current.id}/join`);
      joined = true;

      const context = await api<CallContext>(
        `/calls/context/${current.conversation_id}`,
      );

      current = {
        ...(await api<PersonalCall>(
          `/calls/${current.id}`,
        )),
        conversation_name: context.name,
        conversation_type:
          context.conversation_type,
      };

      media.attach(current, me.id, stream);
      rememberActive(current);

      setIncoming(null);
      setMicrophoneEnabled(true);
      setCameraEnabled(
        current.kind === "VIDEO",
      );
      setSpeaker(true);
      setSharing(false);

      media.syncParticipants(
        current.participants || [],
      );
    } catch (cause) {
      stream.getTracks().forEach((track) => {
        track.stop();
      });

      if (joined) {
        try {
          await post(`/calls/${call.id}/leave`);
        } catch (cleanupError) {
          showError(
            `Call cleanup failed: ${messageOf(cleanupError)}`,
          );
        }
      }

      throw cause;
    }
  }

  async function finish(
    action: "leave" | "end",
  ) {
    const call = activeRef.current;
    if (!call) return;

    await post(`/calls/${call.id}/${action}`);
    forgetActive();
    void reload();
  }

  async function toggleMicrophone() {
    const call = activeRef.current;
    if (!call || !media.ready) return;

    const enabled = !microphoneEnabled;

    await api(
      `/calls/${call.id}/media-state`,
      {
        method: "PATCH",
        body: JSON.stringify({
          microphone_enabled: enabled,
        }),
      },
    );

    await media.microphone(enabled);
    setMicrophoneEnabled(enabled);
  }

  async function toggleCamera() {
    const call = activeRef.current;
    if (!call || !media.ready) return;

    const enabled = !cameraEnabled;
    await media.camera(enabled);

    try {
      await api(
        `/calls/${call.id}/media-state`,
        {
          method: "PATCH",
          body: JSON.stringify({
            camera_enabled: enabled,
          }),
        },
      );

      setCameraEnabled(enabled);
    } catch (cause) {
      await media.camera(!enabled);
      throw cause;
    }
  }

  async function stopSharing() {
    const call = activeRef.current;
    if (!call) return;

    await media.stopScreen();
    setSharing(false);

    await post(
      `/calls/${call.id}/screen-share/stop`,
    );
  }

  async function toggleSharing() {
    const call = activeRef.current;

    if (!call || !media.ready) {
      openPicker("direct", "VIDEO");
      return;
    }

    if (sharing) {
      await stopSharing();
      return;
    }

    await media.startScreen(() => {
      void stopSharing().catch((cause) => {
        showError(messageOf(cause));
      });
    });

    try {
      await post(
        `/calls/${call.id}/screen-share/start`,
      );

      setSharing(true);
    } catch (cause) {
      await media.stopScreen();
      throw cause;
    }
  }

  function toggleFavorite(userId: string) {
    void run(async () => {
      await api(
        `/calls/favorites/${userId}`,
        {
          method: favorites.includes(userId)
            ? "DELETE"
            : "PUT",
        },
      );

      await reload();
    });
  }

  const namedCalls = useMemo(
    () =>
      calls.map((call) => ({
        call,
        name: nameOf(call),
        direction: callDirection(
          call,
          me?.id || "",
        ),
      })),
    [
      calls,
      conversations,
      friends,
      contactNames,
      me,
    ],
  );

  const pages = Math.max(
    1,
    Math.ceil(
      (history?.total || 0) / PAGE_SIZE,
    ),
  );

  const safePage = Math.min(page, pages);
  const pageCalls = namedCalls;

  const groupCalls = recentGroups.map(
    (call) => ({
      call,
      name: nameOf(call),
    }),
  );

  const favoriteFriends = friends.filter(
    (friend) =>
      favorites.includes(friend.user_id),
  );

  const filteredFriends = (
    picker === "invite"
      ? inviteCandidates
      : friends
  ).filter((friend) =>
    `${friend.name} ${friend.calling_number || ""} ${friend.username || ""}`
      .toLowerCase()
      .includes(pickerSearch.toLowerCase()),
  );

  const currentCallName = active
    ? nameOf(active)
    : "";

  const elapsed = active?.started_at
    ? duration(
        (now -
          new Date(
            active.started_at,
          ).getTime()) /
          1000,
      )
    : "00:00";

  const metricItems = [
    {
      label: "Total calls",
      value: history?.totals.total ?? "—",
      icon: Phone,
      color: "gold",
    },
    {
      label: "Missed calls",
      value: history?.totals.missed ?? "—",
      icon: PhoneMissed,
      color: "red",
    },
    {
      label: "Voice calls",
      value: history?.totals.voice ?? "—",
      icon: Phone,
      color: "gold",
    },
    {
      label: "Video calls",
      value: history?.totals.video ?? "—",
      icon: Video,
      color: "gold",
    },
  ];

  function callback(call: PersonalCall) {
    void run(async () => {
      if (!call.conversation_id) {
        throw new Error(
          "This call has no personal conversation.",
        );
      }

      await launch(
        call.conversation_id,
        call.kind,
        (call.participants || [])
          .filter(
            (participant) =>
              participant.user_id !== me?.id,
          )
          .map(
            (participant) =>
              participant.user_id,
          ),
      );
    });
  }

  return (
    <main className="pc-page">
      <div className="pc-breadcrumb">
        <span>Personal</span>
        <span>/</span>
        <span>Personal Calls</span>
      </div>

      <header className="pc-header">
        <div>
          <h1>Personal Calls</h1>
          <p>
            Voice, video and group calls, all in one place.
          </p>

          {callingNumber ? (
            <p className="pc-own-number">
              Your calling number
              <strong>{callingNumber}</strong>
            </p>
          ) : null}
        </div>

        <div className="pc-header-actions">
          <button
            type="button"
            className="pc-button pc-dark"
            disabled={busy || !me || Boolean(active)}
            onClick={() => openPicker("direct")}
          >
            <Plus size={20} />
            New call
          </button>

          <button
            type="button"
            className="pc-button"
            disabled={busy || !me || Boolean(active)}
            onClick={() => openPicker("group")}
          >
            <Users size={20} />
            Start group call
          </button>
        </div>
      </header>

      {error ? (
        <div className="pc-error" role="alert">
          <span>{error}</span>
          <button
            type="button"
            aria-label="Dismiss error"
            onClick={() => setError("")}
          >
            <X size={17} />
          </button>
        </div>
      ) : null}

      <div className="pc-metrics">
        {metricItems.map(
          ({
            label,
            value,
            icon: Icon,
            color,
          }) => (
            <section
              className="pc-metric"
              key={label}
            >
              <div
                className={`pc-metric-icon pc-${color}`}
              >
                <Icon
                  size={26}
                  strokeWidth={1.6}
                />
              </div>
              <div>
                <span>{label}</span>
                <strong>{value}</strong>
              </div>
            </section>
          ),
        )}
      </div>

      <div className="pc-main-grid">
        <section className="pc-card pc-history">
          <div className="pc-card-heading">
            <h2>Call history</h2>

            <div className="pc-history-actions">
              <button
                type="button"
                className="pc-icon-button"
                aria-label="Refresh calls"
                disabled={busy || loading || !me}
                onClick={() => void reload()}
              >
                <RefreshCw size={16} />
              </button>

              <label className="pc-search">
                <Search size={18} />
                <input
                  aria-label="Search calls"
                  placeholder="Search calls"
                  value={search}
                  onChange={(event) => {
                    setSearch(event.target.value);
                    setPage(1);
                  }}
                />
              </label>
            </div>
          </div>

          <div
            className="pc-tabs"
            aria-label="Call history filters"
          >
            {(
              [
                "All",
                "Missed",
                "Incoming",
                "Outgoing",
              ] as const
            ).map((tab) => (
              <button
                type="button"
                key={tab}
                aria-pressed={filter === tab}
                className={
                  filter === tab
                    ? "pc-selected-tab"
                    : ""
                }
                onClick={() => {
                  setFilter(tab);
                  setPage(1);
                }}
              >
                {tab}
              </button>
            ))}
          </div>

          <label className="pc-kind-filter">
            Call type
            <select
              value={historyKind}
              onChange={(event) => {
                setHistoryKind(
                  event.target.value as "" | Kind,
                );
                setPage(1);
              }}
            >
              <option value="">All calls</option>
              <option value="VOICE">Voice</option>
              <option value="VIDEO">Video</option>
            </select>
          </label>

          <div className="pc-table-scroll">
            <table className="pc-table">
              <thead>
                <tr>
                  <th>Contact</th>
                  <th>Type</th>
                  <th>Call type</th>
                  <th>Date &amp; time</th>
                  <th>Duration</th>
                  <th>Action</th>
                </tr>
              </thead>

              <tbody>
                {loading ? (
                  <tr>
                    <td
                      colSpan={6}
                      className="pc-empty"
                    >
                      Loading personal calls…
                    </td>
                  </tr>
                ) : pageCalls.length === 0 ? (
                  <tr>
                    <td
                      colSpan={6}
                      className="pc-empty"
                    >
                      {search ||
                      filter !== "All" ||
                      historyKind
                        ? "No calls match your filters."
                        : "No personal calls yet."}
                    </td>
                  </tr>
                ) : (
                  pageCalls.map(
                    (
                      {
                        call,
                        name,
                        direction,
                      },
                      index,
                    ) => (
                      <tr key={call.id}>
                        <td>
                          <div className="pc-person">
                            <span
                              className={`pc-avatar pc-avatar-${index % 5}`}
                            >
                              {avatarForCall(call)}
                            </span>
                            <span>
                              <strong>
                                {name}
                              </strong>

                              {call.contact_number ? (
                                <small className="pc-contact-number">
                                  {call.contact_number}
                                </small>
                              ) : null}
                            </span>
                          </div>
                        </td>

                        <td>
                          <span
                            className={`pc-direction pc-direction-${direction.toLowerCase()}`}
                          >
                            {direction ===
                            "Missed" ? (
                              <PhoneMissed
                                size={18}
                              />
                            ) : direction ===
                              "Incoming" ? (
                              <ArrowDownLeft
                                size={18}
                              />
                            ) : (
                              <ArrowUpRight
                                size={18}
                              />
                            )}

                            {direction}

                            {call.outcome ===
                            "Declined" ? (
                              <small>
                                {" "}
                                · Declined
                              </small>
                            ) : null}
                          </span>
                        </td>

                        <td>
                          <span className="pc-inline-icon">
                            {call.kind ===
                            "VIDEO" ? (
                              <Video
                                size={19}
                              />
                            ) : (
                              <Phone
                                size={19}
                              />
                            )}
                            {call.kind ===
                            "VIDEO"
                              ? "Video"
                              : "Voice"}
                          </span>
                        </td>

                        <td
                          title={new Date(
                            call.created_at,
                          ).toLocaleString()}
                        >
                          {dateLabel(
                            call.created_at,
                          )}
                        </td>

                        <td>
                          {callDuration(call)}
                        </td>

                        <td>
                          <button
                            type="button"
                            className="pc-round-button"
                            aria-label={`Call ${name} again`}
                            disabled={
                              busy ||
                              Boolean(active)
                            }
                            onClick={() =>
                              callback(call)
                            }
                          >
                            <Phone size={19} />
                          </button>
                        </td>
                      </tr>
                    ),
                  )
                )}
              </tbody>
            </table>
          </div>

          <footer className="pc-table-footer">
            <span>
              {pageCalls.length
                ? `Showing ${(safePage - 1) * PAGE_SIZE + 1}–${Math.min(
                    safePage * PAGE_SIZE,
                    history?.total || 0,
                  )} of ${history?.total || 0} calls`
                : "Showing 0 calls"}
            </span>

            <div className="pc-pagination">
              <button
                type="button"
                className="pc-page-arrow"
                aria-label="Previous page"
                disabled={safePage === 1}
                onClick={() =>
                  setPage(safePage - 1)
                }
              >
                <ChevronLeft size={16} />
              </button>

              {Array.from(
                { length: pages },
                (_, index) => index + 1,
              )
                .filter(
                  (number) =>
                    number === 1 ||
                    number === pages ||
                    Math.abs(
                      number - safePage,
                    ) <= 1,
                )
                .map((number) => (
                  <button
                    type="button"
                    key={number}
                    aria-label={`Page ${number}`}
                    aria-current={
                      safePage === number
                        ? "page"
                        : undefined
                    }
                    className={
                      safePage === number
                        ? "pc-current-page"
                        : ""
                    }
                    onClick={() =>
                      setPage(number)
                    }
                  >
                    {number}
                  </button>
                ))}

              <button
                type="button"
                className="pc-page-arrow"
                aria-label="Next page"
                disabled={safePage === pages}
                onClick={() =>
                  setPage(safePage + 1)
                }
              >
                <ChevronRight size={16} />
              </button>
            </div>
          </footer>
        </section>

        <div className="pc-right-column">
          <section className="pc-card pc-active">
            <div className="pc-card-heading">
              <h2>
                {active
                  ? `Active ${active.kind === "VIDEO" ? "video" : "voice"} call`
                  : "Active voice call"}
              </h2>

              {active ? (
                <div className="pc-menu-anchor">
                  <button
                    type="button"
                    className="pc-icon-button"
                    aria-label="Call options"
                    aria-expanded={menu}
                    onClick={() =>
                      setMenu(!menu)
                    }
                  >
                    <MoreHorizontal
                      size={19}
                    />
                  </button>

                  {menu ? (
                    <div className="pc-menu">
                      <button
                        type="button"
                        disabled={busy}
                        onClick={() =>
                          void run(() =>
                            finish("leave"),
                          )
                        }
                      >
                        Leave call
                      </button>

                      <button
                        type="button"
                        disabled={
                          busy ||
                          !media.ready
                        }
                        onClick={() =>
                          void run(
                            toggleCamera,
                          )
                        }
                      >
                        {cameraEnabled
                          ? "Turn camera off"
                          : "Turn camera on"}
                      </button>

                      <button style={{ display:(active?.conversation_type ?? conversations.find(item => item.id === active?.conversation_id)?.conversation_type) === "group" ? "none" : undefined }}
                        type="button"
                        disabled={
                          busy ||
                          !media.ready
                        }
                        onClick={() =>
                          void run(
                            openInvite,
                          )
                        }
                      >
                        Add person
                      </button>
                    </div>
                  ) : null}
                </div>
              ) : null}
            </div>

            {active ? (
              <>
                <div className="pc-active-person">
                  <span className="pc-avatar pc-large-avatar">
                    {avatarForCall(active)}
                  </span>

                  <div>
                    <h3>
                      {currentCallName}
                      <SpeakingIndicator stream={media.local} />
                    </h3>

                    <p
                      className={
                        media.connectedIds.length
                          ? "pc-connected"
                          : "pc-waiting"
                      }
                    >
                      <span />

                      {media.connectedIds.length
                        ? "Connected"
                        : !media.ready
                          ? "Ready to rejoin"
                          : active.status ===
                              "RINGING"
                            ? "Calling…"
                            : "Waiting for media"}
                    </p>

                    <strong className="pc-timer">
                      {elapsed}
                    </strong>
                  </div>
                </div>

                {media.local &&
                media.ready ? (
                  <VoiceWaveform
                    stream={media.local}
                  />
                ) : (
                  <div className="pc-call-divider">
                    <span />
                    <Phone size={16} />
                    <span />
                  </div>
                )}

                {!media.ready ? (
                  <button
                    type="button"
                    className="pc-button pc-dark pc-full-button"
                    disabled={busy}
                    onClick={() =>
                      void run(() =>
                        join(active),
                      )
                    }
                  >
                    <Phone size={17} />
                    Rejoin media
                  </button>
                ) : (
                  <div className="pc-call-controls">
                    <button
                      type="button"
                      className={
                        microphoneEnabled
                          ? "pc-control-on"
                          : ""
                      }
                      disabled={busy}
                      aria-pressed={
                        microphoneEnabled
                      }
                      onClick={() =>
                        void run(
                          toggleMicrophone,
                        )
                      }
                    >
                      {microphoneEnabled ? (
                        <Mic size={23} />
                      ) : (
                        <MicOff size={23} />
                      )}
                      <span>
                        Microphone
                      </span>
                    </button>

                    <button
                      type="button"
                      disabled={busy}
                      aria-pressed={speaker}
                      onClick={() =>
                        setSpeaker(
                          !speaker,
                        )
                      }
                    >
                      {speaker ? (
                        <Volume2
                          size={23}
                        />
                      ) : (
                        <VolumeX
                          size={23}
                        />
                      )}
                      <span>Speaker</span>
                    </button>

                    {active.kind ===
                    "VIDEO" ? (
                      <button
                        type="button"
                        disabled={busy}
                        aria-pressed={
                          cameraEnabled
                        }
                        onClick={() =>
                          void run(
                            toggleCamera,
                          )
                        }
                      >
                        {cameraEnabled ? (
                          <Video
                            size={23}
                          />
                        ) : (
                          <VideoOff
                            size={23}
                          />
                        )}
                        <span>
                          Camera
                        </span>
                      </button>
                    ) : (
                      <button style={{ display:(active?.conversation_type ?? conversations.find(item => item.id === active?.conversation_id)?.conversation_type) === "group" ? "none" : undefined }}
                        type="button"
                        disabled={
                          busy ||
                          !media.ready
                        }
                        onClick={() =>
                          void run(
                            openInvite,
                          )
                        }
                      >
                        <UserPlus
                          size={23}
                        />
                        <span>
                          Add person
                        </span>
                      </button>
                    )}

                    <button
                      type="button"
                      className="pc-control-end"
                      disabled={busy}
                      onClick={() =>
                        void run(() =>
                          finish(
                            active.started_by_user_id ===
                              me?.id
                              ? "end"
                              : "leave",
                          ),
                        )
                      }
                    >
                      <PhoneOff
                        size={23}
                      />
                      <span>
                        {active.started_by_user_id ===
                        me?.id
                          ? "End call"
                          : "Leave call"}
                      </span>
                    </button>
                  </div>
                )}

                {/* call-status-visible-v2 */}

                <div
                  style={{
                    display: "flex",
                    flexWrap: "wrap",
                    justifyContent: "center",
                    gap: 6,
                    margin: "8px 0",
                  }}
                >
                  {(active.participants ?? [])
                    .filter(
                      participant =>
                        participant.user_id !== me?.id,
                    )
                    .map(participant => {
                      const member = friends.find(
                        item =>
                          item.user_id === participant.user_id,
                      );

                      const status =
                        participant.state === "JOINED"
                          ? media.connectedIds.includes(
                              participant.user_id,
                            )
                            ? "Connected"
                            : "Joined · connecting media"
                          : participant.state === "INVITED"
                            ? "Invited · ringing"
                            : participant.state
                                .toLowerCase()
                                .replaceAll("_", " ");

                      return (
                        <span
                          key={participant.user_id}
                          style={{
                            padding: "4px 8px",
                            borderRadius: 12,
                            background: "#fff5d4",
                            color: "#594b28",
                            fontSize: 11,
                          }}
                        >
                          {member?.name
                            || member?.username
                            || "Participant"}

                          {" · "}

                          {status}
                        </span>
                      );
                    })}
                </div>

                <p className="pc-mic-status">
                  <span
                    className={
                      microphoneEnabled
                        ? "pc-green-dot"
                        : ""
                    }
                  />
                  {media.ready
                    ? `Microphone ${microphoneEnabled ? "on" : "off"}`
                    : "Join to enable microphone"}
                </p>

                {active
                  && active.started_by_user_id === me?.id
                  && active.participants?.some(
                    person => person.state === "INVITED",
                  )
                  && !active.participants?.some(
                    person =>
                      person.user_id !== me?.id
                      && person.state === "JOINED",
                  )
                  && (
                    <CallRingtone
                      key={active.id}
                      callId={active.id}
                      mode="outgoing"
                    />
                  )}

                {me && (
                  <DirectCallInvite hideTrigger
                    callId={active.id}
                    userId={me.id}
                  />
                )}

                <div className="pc-remote-media">
                  {media.remotes
                    .filter(remote => remote.source === "microphone")
                    .map(remote => (
                      <StreamVideo
                        key={remote.key}
                        stream={remote.stream}
                        muted={!speaker}
                        className="pc-audio-stream"
                      />
                    ))}

                  {(active.participants ?? [])
                    .filter(participant =>
                      participant.user_id !== me?.id &&
                      participant.state === "JOINED",
                    )
                    .map(participant => {
                      const person = friends.find(
                        item => item.user_id === participant.user_id,
                      );

                      const camera = media.remotes.find(
                        remote =>
                          remote.userId === participant.user_id &&
                          remote.source === "camera",
                      );

                      const screen = media.remotes.find(
                        remote =>
                          remote.userId === participant.user_id &&
                          remote.source === "screen",
                      );

                      return (
                        <div
                          key={participant.user_id}
                          className="pc-remote-person"
                        >
                          <section className="pc-person-tile">
                            <strong>
                              {person?.name || person?.username || "Participant"}

                              <SpeakingIndicator
                                stream={
                                  media.remotes.find(
                                    remote =>
                                      remote.userId === participant.user_id
                                      && remote.source === "microphone",
                                  )?.stream
                                }
                              />
                            </strong>

                            {person?.username && (
                              <small>@{person.username}</small>
                            )}

                            {participant.camera_enabled && camera ? (
                              <StreamVideo
                                stream={camera.stream}
                                muted
                                className="pc-remote-video"
                              />
                            ) : (
                              <div className="pc-remote-identity">
                                <UserAvatar
                                  userId={participant.user_id}
                                  src={person?.avatar_url}
                                  name={person?.name || person?.username}
                                  size={54}
                                />
                                <span>
                                  {participant.camera_enabled
                                    ? "Connecting camera…"
                                    : "Camera off"}
                                </span>
                              </div>
                            )}
                          </section>

                          {participant.screen_share_state === "ACTIVE" && (
                            <section className="pc-person-tile pc-screen-tile">
                              <strong>
                                {person?.name ||
                                  person?.username ||
                                  "Participant"} · Screen
                              </strong>

                              {screen ? (
                                <StreamVideo
                                  stream={screen.stream}
                                  muted
                                  className="pc-remote-video pc-screen-video"
                                />
                              ) : (
                                <p role="status">
                                  Waiting for shared screen…
                                </p>
                              )}
                            </section>
                          )}
                        </div>
                      );
                    })}
                </div>
              </>
            ) : (
              <div className="pc-no-active">
                <span className="pc-avatar pc-large-avatar">
                  <Phone
                    size={30}
                    strokeWidth={1.5}
                  />
                </span>
                <h3>No active call</h3>
                <p>
                  Start a voice or video call
                  with a friend or group.
                </p>
              </div>
            )}
          </section>

          <section className="pc-card pc-favorites">
            <div className="pc-card-heading">
              <h2>Favorites</h2>

              <button
                type="button"
                className="pc-text-button"
                onClick={() =>
                  setShowAllFavorites(
                    !showAllFavorites,
                  )
                }
              >
                {showAllFavorites
                  ? "Show less"
                  : "View all"}
              </button>
            </div>

            {favoriteFriends.length === 0 ? (
              <div className="pc-empty-small">
                Star an account in New call
                to add a favorite.
              </div>
            ) : (
              (
                showAllFavorites
                  ? favoriteFriends
                  : favoriteFriends.slice(
                      0,
                      3,
                    )
              ).map(
                (friend, index) => (
                  <div
                    className="pc-favorite-row"
                    key={friend.user_id}
                  >
                    <div className="pc-person">
                      <span
                        className={`pc-avatar pc-avatar-${index % 5}`}
                      >
                        {<UserAvatar userId={friend.user_id} name={friend.name} src={friend.avatar_url} />}
                      </span>
                      <strong>
                        {friend.name}
                      </strong>
                    </div>

                    <div className="pc-favorite-actions">
                      {(
                        [
                          "VOICE",
                          "VIDEO",
                        ] as const
                      ).map((callKind) => (
                        <button
                          type="button"
                          key={callKind}
                          className="pc-round-button"
                          disabled={
                            busy ||
                            Boolean(active)
                          }
                          aria-label={`${callKind === "VIDEO" ? "Video" : "Voice"} call ${friend.name}`}
                          onClick={() => {
                            void run(
                              async () => {
                                if (
                                  !friend.calling_number
                                ) {
                                  throw new Error(
                                    "This contact has no calling number.",
                                  );
                                }

                                await dialAccount(
                                  friend.calling_number,
                                  callKind,
                                );
                              },
                            );
                          }}
                        >
                          {callKind ===
                          "VIDEO" ? (
                            <Video
                              size={18}
                            />
                          ) : (
                            <Phone
                              size={18}
                            />
                          )}
                        </button>
                      ))}
                    </div>
                  </div>
                ),
              )
            )}
          </section>
        </div>
      </div>

      <div className="pc-bottom-grid">
        <section className="pc-card pc-groups">
          <div className="pc-card-heading">
            <h2>Recent group calls</h2>

            <button
              type="button"
              className="pc-text-button"
              onClick={() =>
                setShowAllGroups(
                  !showAllGroups,
                )
              }
            >
              {showAllGroups
                ? "Show less"
                : "View all"}
            </button>
          </div>

          {groupCalls.length === 0 ? (
            <div className="pc-empty-small">
              No recent group calls.
            </div>
          ) : (
            (
              showAllGroups
                ? groupCalls
                : groupCalls.slice(0, 1)
            ).map(({ call, name }) => (
              <div
                className="pc-group-row"
                key={call.id}
              >
                <div className="pc-person">
                  <span className="pc-avatar pc-avatar-2">
                    {avatarForCall(call)}
                  </span>

                  <div>
                    <strong>{name}</strong>
                    <small>
                      {call.participants
                        ?.length ?? 0}{" "}
                      participants
                    </small>
                  </div>
                </div>

                <span className="pc-inline-icon">
                  {call.kind ===
                  "VIDEO" ? (
                    <Video size={18} />
                  ) : (
                    <Phone size={18} />
                  )}
                  {call.kind === "VIDEO"
                    ? "Video call"
                    : "Voice call"}
                </span>

                <div className="pc-group-time">
                  <span>
                    {dateLabel(
                      call.created_at,
                    )}
                  </span>
                  <small>
                    {callDuration(call)}
                  </small>
                </div>

                <button
                  type="button"
                  className="pc-round-button"
                  aria-label={`Call ${name} again`}
                  disabled={
                    busy ||
                    Boolean(active)
                  }
                  onClick={() =>
                    callback(call)
                  }
                >
                  <Phone size={18} />
                </button>
              </div>
            ))
          )}
        </section>

        <section className="pc-card pc-sharing">
          <h2>
            Video &amp; screen sharing
          </h2>

          <div className="pc-sharing-content">
            <div className="pc-preview-grid">
              {media.local
                ?.getVideoTracks()
                .length ? (
                <StreamVideo
                  stream={media.local}
                  muted
                  className="pc-local-video"
                />
              ) : (
                friends
                  .slice(0, 4)
                  .map(
                    (friend, index) => (
                      <div
                        key={
                          friend.user_id
                        }
                      >
                        <span
                          className={`pc-avatar pc-avatar-${index % 5}`}
                        >
                          {<UserAvatar userId={friend.user_id} name={friend.name} src={friend.avatar_url} />}
                        </span>
                      </div>
                    ),
                  )
              )}

              {!media.local &&
              friends.length === 0 ? (
                <div className="pc-preview-empty">
                  <Video
                    size={28}
                    strokeWidth={1.5}
                  />
                </div>
              ) : null}
            </div>

            <div className="pc-sharing-copy">
              <p>
                Start a video call or share your
                screen with contacts or groups.
              </p>

              <div className="pc-sharing-buttons">
                <button
                  type="button"
                  className="pc-button pc-dark"
                  disabled={
                    busy ||
                    !me ||
                    Boolean(active)
                  }
                  onClick={() =>
                    openPicker(
                      "direct",
                      "VIDEO",
                    )
                  }
                >
                  <Video size={15} />
                  Start video call
                </button>

                <button
                  type="button"
                  className={`pc-button ${sharing ? "pc-sharing-on" : ""}`}
                  disabled={busy || !me}
                  onClick={() => {
                    if (!active) {
                      openPicker(
                        "direct",
                        "VIDEO",
                      );
                    } else {
                      void run(
                        toggleSharing,
                      );
                    }
                  }}
                >
                  <Monitor size={15} />
                  {sharing
                    ? "Stop sharing"
                    : "Share screen"}
                </button>
              </div>
            </div>
          </div>
        </section>
      </div>

      {incoming ? (
        <section
          className="pc-incoming"
          aria-label="Incoming call"
        >
          <CallRingtone
            callId={incoming.id}
            mode="incoming"
            expiresAt={incoming.invitation_expires_at}
          />

          <div className="pc-incoming-heading">
            <span>
              <Phone size={16} />
              Incoming call
            </span>

            <button
              type="button"
              aria-label="Dismiss incoming call notification"
              onClick={() => {
                setDismissedIncoming(
                  incoming.id,
                );
                setIncoming(null);
              }}
            >
              <X size={16} />
            </button>
          </div>

          <div className="pc-incoming-person">
            <span className="pc-avatar pc-avatar-3">
              {avatarForCall(incoming)}
            </span>

            <div>
              <strong>
                {nameOf(incoming)}
              </strong>
              <small>
                {incoming.kind === "VIDEO"
                  ? "Video call"
                  : "Voice call"}
              </small>
            </div>
          </div>

          <div className="pc-incoming-actions">
            <button
              type="button"
              className="pc-accept"
              disabled={
                busy ||
                Boolean(active)
              }
              onClick={() =>
                void run(() =>
                  join(incoming),
                )
              }
            >
              <Phone size={18} />
              Accept
            </button>

            <button
              type="button"
              className="pc-decline"
              disabled={busy}
              onClick={() =>
                void run(async () => {
                  await post(
                    `/calls/${incoming.id}/decline`,
                  );

                  setIncoming(null);
                  void reload();
                })
              }
            >
              <PhoneOff size={18} />
              Decline
            </button>
          </div>
        </section>
      ) : null}

      {picker ? (
        <div
          className="pc-dialog-backdrop"
          onClick={(event) => {
            if (
              event.target ===
                event.currentTarget &&
              !busy
            ) {
              setPicker(null);
            }
          }}
        >
          <dialog
            open
            className="pc-dialog"
            aria-modal="true"
            aria-labelledby="pc-picker-title"
            onCancel={(event) => {
              event.preventDefault();

              if (!busy) {
                setPicker(null);
              }
            }}
          >
            <form
              onSubmit={(event) =>
                void submitPicker(event)
              }
            >
              <div className="pc-card-heading">
                <h2 id="pc-picker-title">
                  {picker === "group"
                    ? "Start group call"
                    : picker === "invite"
                      ? "Add person"
                      : "New call"}
                </h2>

                <button
                  type="button"
                  className="pc-icon-button"
                  aria-label="Close call picker"
                  disabled={busy}
                  onClick={() =>
                    setPicker(null)
                  }
                >
                  <X size={18} />
                </button>
              </div>

              <div className="pc-picker-body">
                {picker !== "invite" ? (
                  <div className="pc-kind-picker">
                    {(
                      [
                        "VOICE",
                        "VIDEO",
                      ] as const
                    ).map((value) => (
                      <button
                        type="button"
                        key={value}
                        disabled={busy}
                        aria-pressed={
                          kind === value
                        }
                        className={
                          kind === value
                            ? "pc-kind-selected"
                            : ""
                        }
                        onClick={() =>
                          setKind(value)
                        }
                      >
                        {value ===
                        "VOICE" ? (
                          <Phone
                            size={17}
                          />
                        ) : (
                          <Camera
                            size={17}
                          />
                        )}
                        {value === "VOICE"
                          ? "Voice call"
                          : "Video call"}
                      </button>
                    ))}
                  </div>
                ) : null}

                {picker === "direct" ? (
                  <div className="pc-dialpad">
                    <label className="pc-field">
                      <span>
                        Account calling number
                      </span>

                      <input
                        autoFocus
                        type="text"
                        inputMode="numeric"
                        autoComplete="off"
                        aria-describedby="pc-number-help"
                        value={dialNumber}
                        maxLength={10}
                        disabled={busy}
                        placeholder="Enter 10 digits"
                        onChange={(event) =>
                          setDialNumber(
                            event.target.value
                              .replace(
                                /[^0-9]/g,
                                "",
                              )
                              .slice(0, 10),
                          )
                        }
                      />
                    </label>

                    <p id="pc-number-help">
                      Use the 10-digit calling number
                      shown on their profile.
                    </p>

                    <div className="pc-dial-keys">
                      {[
                        "1",
                        "2",
                        "3",
                        "4",
                        "5",
                        "6",
                        "7",
                        "8",
                        "9",
                        "",
                        "0",
                        "delete",
                      ].map(
                        (digit, index) =>
                          digit ? (
                            <button
                              type="button"
                              key={digit}
                              disabled={busy}
                              aria-label={
                                digit ===
                                "delete"
                                  ? "Delete last digit"
                                  : `Dial ${digit}`
                              }
                              onClick={() =>
                                setDialNumber(
                                  (value) =>
                                    digit ===
                                    "delete"
                                      ? value.slice(
                                          0,
                                          -1,
                                        )
                                      : (
                                          value +
                                          digit
                                        ).slice(
                                          0,
                                          10,
                                        ),
                                )
                              }
                            >
                              {digit ===
                              "delete" ? (
                                <ChevronLeft
                                  size={22}
                                />
                              ) : (
                                digit
                              )}
                            </button>
                          ) : (
                            <span
                              key={`blank-${index}`}
                            />
                          ),
                      )}
                    </div>

                    <div
                      className="pc-dial-result"
                      aria-live="polite"
                    >
                      {dialLookup
                        ? "Finding account…"
                        : dialError ||
                          (dialContact
                            ? `${dialContact.name}${dialContact.username ? ` · @${dialContact.username}` : ""}`
                            : "Enter a number to find the account.")}
                    </div>

                    {dialContact ? (
                      <button
                        type="button"
                        className="pc-text-button"
                        disabled={busy}
                        onClick={() =>
                          toggleFavorite(
                            dialContact.user_id,
                          )
                        }
                      >
                        {favorites.includes(
                          dialContact.user_id,
                        )
                          ? "Remove favorite"
                          : "Add to favorites"}
                      </button>
                    ) : null}
                  </div>
                ) : null}

                {picker === "group" ? (
                  <>
                    <label className="pc-field">
                      <span>
                        Existing group
                      </span>

                      <select
                        value={selectedGroup}
                        disabled={busy}
                        onChange={(event) =>
                          setSelectedGroup(
                            event.target.value,
                          )
                        }
                      >
                        <option value="">
                          Create a new group
                        </option>

                        {conversations
                          .filter(
                            (
                              conversation,
                            ) =>
                              conversation.conversation_type ===
                              "group",
                          )
                          .map(
                            (
                              conversation,
                            ) => (
                              <option
                                key={
                                  conversation.id
                                }
                                value={
                                  conversation.id
                                }
                              >
                                {conversation.name ||
                                  "Personal group"}
                              </option>
                            ),
                          )}
                      </select>
                    </label>

                    {!selectedGroup ? (
                      <label className="pc-field">
                        <span>
                          New group name
                        </span>

                        <input
                          value={groupName}
                          maxLength={120}
                          disabled={busy}
                          placeholder="Enter a group name"
                          onChange={(
                            event,
                          ) =>
                            setGroupName(
                              event.target
                                .value,
                            )
                          }
                        />
                      </label>
                    ) : null}
                  </>
                ) : null}

                {picker !== "direct" &&
                !selectedGroup ? (
                  <>
                    <label className="pc-search pc-picker-search">
                      <Search size={17} />

                      <input
                        autoFocus
                        value={pickerSearch}
                        disabled={busy}
                        placeholder={
                          picker ===
                          "invite"
                            ? "Search people"
                            : "Search friends"
                        }
                        aria-label="Search call contacts"
                        onChange={(event) =>
                          setPickerSearch(
                            event.target.value,
                          )
                        }
                      />
                    </label>

                    <div className="pc-contact-list">
                      {filteredFriends.length ===
                      0 ? (
                        <p className="pc-empty-small">
                          No available people
                          match your search.
                        </p>
                      ) : (
                        filteredFriends.map(
                          (
                            friend,
                            index,
                          ) => (
                            <div
                              className="pc-contact-row"
                              key={
                                friend.user_id
                              }
                            >
                              <label>
                                <input
                                  type="checkbox"
                                  name="call-contact"
                                  checked={selectedFriends.includes(
                                    friend.user_id,
                                  )}
                                  disabled={
                                    busy
                                  }
                                  onChange={() =>
                                    setSelectedFriends(
                                      (
                                        current,
                                      ) =>
                                        current.includes(
                                          friend.user_id,
                                        )
                                          ? current.filter(
                                              (
                                                id,
                                              ) =>
                                                id !==
                                                friend.user_id,
                                            )
                                          : [
                                              ...current,
                                              friend.user_id,
                                            ],
                                    )
                                  }
                                />

                                <span
                                  className={`pc-avatar pc-avatar-${index % 5}`}
                                >
                                  {<UserAvatar userId={friend.user_id} name={friend.name} src={friend.avatar_url} />}
                                </span>

                                <span>
                                  <strong>
                                    {
                                      friend.name
                                    }
                                  </strong>

                                  {friend.calling_number ? (
                                    <small>
                                      {
                                        friend.calling_number
                                      }
                                    </small>
                                  ) : null}

                                  {friend.online !==
                                  undefined ? (
                                    <small>
                                      {friend.online
                                        ? "Online"
                                        : "Offline"}
                                    </small>
                                  ) : null}
                                </span>
                              </label>

                              <button
                                type="button"
                                disabled={busy}
                                className={`pc-star-button ${
                                  favorites.includes(
                                    friend.user_id,
                                  )
                                    ? "pc-star-active"
                                    : ""
                                }`}
                                aria-label={`${
                                  favorites.includes(
                                    friend.user_id,
                                  )
                                    ? "Remove"
                                    : "Add"
                                } ${friend.name} ${
                                  favorites.includes(
                                    friend.user_id,
                                  )
                                    ? "from"
                                    : "to"
                                } favorites`}
                                aria-pressed={favorites.includes(
                                  friend.user_id,
                                )}
                                onClick={() =>
                                  toggleFavorite(
                                    friend.user_id,
                                  )
                                }
                              >
                                <Star
                                  size={18}
                                />
                              </button>
                            </div>
                          ),
                        )
                      )}
                    </div>
                  </>
                ) : null}

                {error ? (
                  <p
                    className="pc-picker-error"
                    role="alert"
                  >
                    {error}
                  </p>
                ) : null}

                <button
                  type="submit"
                  className="pc-button pc-dark pc-full-button"
                  disabled={
                    busy ||
                    !me ||
                    (Boolean(active) &&
                      picker !==
                        "invite") ||
                    (picker === "direct"
                      ? !dialContact ||
                        dialLookup ||
                        dialContact.calling_number !==
                          dialNumber
                      : !selectedGroup &&
                        selectedFriends.length ===
                          0)
                  }
                >
                  {busy ? (
                    <Loader2
                      size={18}
                      className="pc-spin"
                    />
                  ) : (
                    <Phone size={18} />
                  )}

                  {busy
                    ? "Please wait…"
                    : picker === "invite"
                      ? "Invite to call"
                      : "Start call"}
                </button>
              </div>
            </form>
          </dialog>
        </div>
      ) : null}

      <style jsx global>{`
        .pc-waveform {
          display: block;
          width: calc(100% - 36px);
          height: 44px;
          margin: 12px 18px;
        }

        .pc-page .pc-own-number {
          margin-top: 6px;
          font-size: 12px;
        }

        .pc-own-number strong {
          margin-left: 8px;
          color: #493b18;
          letter-spacing: 0.06em;
        }

        .pc-contact-number {
          display: block;
          font-size: 11px;
          color: #686258;
        }

        .pc-kind-filter {
          display: flex;
          align-items: center;
          gap: 10px;
          margin: 0 18px 12px;
          color: #59534a;
          font-size: 12px;
        }

        .pc-kind-filter select {
          border: 1px solid #e5ddcd;
          border-radius: 8px;
          background: #fffdf8;
          padding: 5px 9px;
          color: #25282c;
        }

        .pc-dialpad {
          max-width: 300px;
          margin: 0 auto 18px;
        }

        .pc-page .pc-dialpad input {
          text-align: center;
          font-size: 25px;
          letter-spacing: 0.06em;
        }

        .pc-dialpad p {
          color: #655e52;
          font-size: 12px;
          margin: 8px 0 14px;
        }

        .pc-dial-keys {
          display: grid;
          grid-template-columns: repeat(3, minmax(0, 1fr));
          gap: 8px;
        }

        .pc-page .pc-dial-keys button {
          min-height: 48px;
          display: flex;
          align-items: center;
          justify-content: center;
          border: 1px solid #e5ddcd;
          background: #fbf7ed;
          border-radius: 10px;
          color: #171d2a;
          font-size: 21px;
        }

        .pc-page .pc-dial-keys button:hover {
          background: #fff0bd;
        }

        .pc-dial-result {
          min-height: 44px;
          margin-top: 12px;
          color: #4b4335;
          font-size: 13px;
        }

        .pc-page {
          --pc-ink: #10182b;
          --pc-muted: #77818f;
          --pc-border: #e9e3d8;
          --pc-gold: #eed8a2;
          --pc-surface: #fffdf8;
          width: 100%;
          max-width: 1400px;
          margin: 0 auto;
          padding: 10px 10px 24px;
          color: var(--pc-ink);
          font-family: inherit;
          font-size: 14px;
          line-height: 1.5;
          font-variant-numeric: tabular-nums;
          color-scheme: light;
          border-radius: 14px;
        }

        .pc-page *,
        .pc-dialog * {
          box-sizing: border-box;
        }

        .pc-page button,
        .pc-page input,
        .pc-page select {
          font: inherit;
        }

        .pc-page button {
          cursor: pointer;
        }

        .pc-page button:disabled {
          cursor: not-allowed;
          opacity: 0.45;
        }

        .pc-page button:focus-visible,
        .pc-page input:focus-visible,
        .pc-page select:focus-visible {
          outline: 2px solid #b87920;
          outline-offset: 3px;
        }

        .pc-page ::selection {
          background: #ffdf8c;
          color: #182031;
        }

        .pc-breadcrumb {
          display: flex;
          align-items: center;
          gap: 9px;
          margin-bottom: 15px;
          color: #343a45;
          font-size: 12px;
        }

        .pc-breadcrumb > span:nth-child(2) {
          color: #9098a2;
        }

        .pc-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 22px;
          margin-bottom: 22px;
        }

        .pc-header h1 {
          margin: 0;
          font-size: clamp(30px, 3.4vw, 43px);
          font-weight: 500;
          letter-spacing: -0.035em;
          line-height: 1.16;
        }

        .pc-header p {
          margin: 6px 0 0;
          font-size: 16px;
          color: var(--pc-muted);
        }

        .pc-header-actions {
          display: flex;
          align-items: center;
          gap: 11px;
          flex-shrink: 0;
        }

        .pc-button {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          gap: 10px;
          min-height: 49px;
          padding: 11px 22px;
          border: 1px solid var(--pc-gold);
          border-radius: 11px;
          background: #fcf7e9;
          color: var(--pc-ink);
          font-weight: 500;
          font-size: 13px;
          white-space: nowrap;
        }

        .pc-button:hover:not(:disabled) {
          background: #f7efd9;
        }

        .pc-dark {
          border-color: #292a2d;
          background: #292a2d;
          color: #fff;
        }

        .pc-dark:hover:not(:disabled) {
          background: #17181b;
        }

        .pc-error {
          display: flex;
          align-items: flex-start;
          justify-content: space-between;
          gap: 16px;
          margin-bottom: 15px;
          padding: 12px 15px;
          border: 1px solid #eac2b8;
          border-radius: 10px;
          background: #fff1ec;
          color: #92362a;
          font-size: 12px;
          overflow-wrap: anywhere;
        }

        .pc-error button {
          display: flex;
          padding: 2px;
          border: 0;
          background: transparent;
          color: inherit;
        }

        .pc-metrics {
          display: grid;
          grid-template-columns: repeat(4, minmax(0, 1fr));
          gap: 9px;
          margin-bottom: 14px;
        }

        .pc-metric {
          display: flex;
          align-items: center;
          gap: 23px;
          min-height: 91px;
          padding: 15px 18px;
          border: 1px solid var(--pc-gold);
          border-radius: 10px;
          background: #fffdf6;
        }

        .pc-metric-icon {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 52px;
          height: 52px;
          flex: 0 0 52px;
          border-radius: 15px;
        }

        .pc-gold {
          background: #fbf1d0;
          color: #665919;
        }

        .pc-red {
          background: #fde8dd;
          color: #f32f29;
        }

        .pc-metric span {
          display: block;
          font-size: 13px;
        }

        .pc-metric strong {
          display: block;
          margin-top: 2px;
          font-size: 29px;
          font-weight: 600;
          line-height: 1.15;
        }

        .pc-main-grid {
          display: grid;
          grid-template-columns:
            minmax(0, 1.93fr)
            minmax(325px, 1fr);
          gap: 14px;
          align-items: start;
        }

        .pc-card {
          min-width: 0;
          border: 1px solid var(--pc-border);
          border-radius: 11px;
          background: var(--pc-surface);
          overflow: hidden;
        }

        .pc-card-heading {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 12px;
          padding: 16px 18px 12px;
        }

        .pc-card h2,
        .pc-dialog h2 {
          margin: 0;
          font-size: 18px;
          font-weight: 600;
          line-height: 1.35;
          letter-spacing: -0.02em;
        }

        .pc-history-actions {
          display: flex;
          align-items: center;
          gap: 7px;
        }

        .pc-search {
          display: flex;
          align-items: center;
          gap: 10px;
          width: 245px;
          min-height: 36px;
          padding: 0 11px;
          border: 1px solid #e0d9ce;
          border-radius: 10px;
          background: #fffdfa;
          color: #82858b;
        }

        .pc-search:focus-within {
          border-color: #b87920;
        }

        .pc-search input {
          width: 100%;
          min-width: 0;
          height: 35px;
          padding: 0;
          border: 0;
          background: transparent;
          outline: 0;
          color: var(--pc-ink);
          font-size: 12px;
        }

        .pc-search input:focus-visible {
          outline: 0;
        }

        .pc-search input::placeholder {
          color: #827d74;
          opacity: 1;
        }

        .pc-tabs {
          display: flex;
          gap: 9px;
          padding: 0 18px 16px;
        }

        .pc-tabs button {
          min-height: 33px;
          padding: 5px 19px;
          border: 1px solid var(--pc-border);
          border-radius: 999px;
          background: #fcf9f3;
          color: #455068;
          font-size: 12px;
        }

        .pc-tabs .pc-selected-tab {
          background: #292a2d;
          border-color: #292a2d;
          color: #fff;
        }

        .pc-table-scroll {
          overflow-x: auto;
          padding: 0 16px;
          scrollbar-width: thin;
          scrollbar-color: #cfc5b5 #f4efe6;
        }

        .pc-table {
          width: 100%;
          border-collapse: separate;
          border-spacing: 0;
          text-align: left;
          font-size: 12px;
          white-space: nowrap;
        }

        .pc-table th {
          padding: 10px 10px;
          background: #f2eee6;
          color: #626770;
          text-transform: uppercase;
          font-size: 10px;
          font-weight: 500;
        }

        .pc-table th:first-child {
          border-radius: 8px 0 0 8px;
          padding-left: 14px;
        }

        .pc-table th:last-child {
          border-radius: 0 8px 8px 0;
          text-align: center;
        }

        .pc-table td {
          height: 56px;
          padding: 7px 10px;
          border-bottom: 1px solid #eee9e1;
          color: #3c4961;
        }

        .pc-table td:first-child {
          padding-left: 7px;
        }

        .pc-table td:last-child {
          text-align: center;
        }

        .pc-table tbody tr:last-child td {
          border-bottom: 0;
        }

        .pc-table tbody tr:hover {
          background: #fcf8ed;
        }

        .pc-person {
          display: flex;
          align-items: center;
          gap: 12px;
          min-width: 0;
        }

        .pc-person strong {
          font-size: 12px;
          font-weight: 500;
          color: var(--pc-ink);
          overflow-wrap: anywhere;
        }

        .pc-person small {
          display: block;
          margin-top: 3px;
          color: var(--pc-muted);
          font-size: 11px;
        }

        .pc-avatar {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          width: 40px;
          height: 40px;
          flex: 0 0 40px;
          border-radius: 50%;
          background: #ffedb3;
          color: #162038;
          font-size: 13px;
          font-weight: 500;
        }

        .pc-avatar-0 {
          background: #ffedb3;
        }

        .pc-avatar-1 {
          background: #cfe7ff;
        }

        .pc-avatar-2 {
          background: #e3d7fb;
        }

        .pc-avatar-3 {
          background: #ffd1df;
        }

        .pc-avatar-4 {
          background: #d0eddb;
        }

        .pc-inline-icon,
        .pc-direction {
          display: inline-flex;
          align-items: center;
          gap: 10px;
        }

        .pc-direction-incoming svg {
          color: #17a753;
        }

        .pc-direction-outgoing svg {
          color: #1a73b8;
        }

        .pc-direction-missed svg {
          color: #f53635;
        }

        .pc-inline-icon svg {
          color: var(--pc-ink);
        }

        .pc-round-button {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          width: 40px;
          height: 40px;
          padding: 0;
          border: 1px solid var(--pc-border);
          border-radius: 50%;
          background: #fffcf6;
          color: var(--pc-ink);
        }

        .pc-round-button:hover:not(:disabled) {
          background: #f8ecd0;
        }

        .pc-icon-button {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          width: 31px;
          height: 31px;
          padding: 0;
          border: 1px solid var(--pc-border);
          border-radius: 10px;
          background: #fcf9f2;
          color: var(--pc-ink);
          flex: 0 0 31px;
        }

        .pc-table-footer {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 12px;
          padding: 14px 18px;
          min-height: 57px;
          color: var(--pc-muted);
          font-size: 11px;
        }

        .pc-pagination {
          display: flex;
          align-items: center;
          gap: 3px;
        }

        .pc-pagination button {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 29px;
          height: 32px;
          padding: 0;
          border: 0;
          border-radius: 8px;
          background: transparent;
          color: #38465e;
          font-size: 12px;
        }

        .pc-pagination .pc-current-page {
          color: #fff;
          background: #292a2d;
        }

        .pc-pagination .pc-page-arrow {
          border: 1px solid var(--pc-border);
          background: #fffcf6;
        }

        .pc-right-column {
          display: grid;
          gap: 9px;
        }

        .pc-active {
          padding-bottom: 9px;
        }

        .pc-active-person {
          display: flex;
          align-items: center;
          gap: 23px;
          padding: 3px 34px 9px;
        }

        .pc-large-avatar {
          width: 80px;
          height: 80px;
          flex-basis: 80px;
          font-size: 24px;
        }

        .pc-active-person h3,
        .pc-no-active h3 {
          margin: 0;
          font-size: 16px;
          font-weight: 600;
        }

        .pc-active-person p {
          display: flex;
          align-items: center;
          gap: 7px;
          margin: 3px 0;
          font-size: 12px;
        }

        .pc-active-person p > span,
        .pc-mic-status > span {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background: currentColor;
          flex: 0 0 8px;
        }

        .pc-connected {
          color: #189943;
        }

        .pc-waiting {
          color: #876b27;
        }

        .pc-timer {
          font-size: 19px;
          font-weight: 400;
        }

        .pc-call-divider {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 12px;
          margin: 8px 28px 16px;
          color: #c79922;
          height: 30px;
        }

        .pc-call-divider > span {
          width: 40%;
          height: 1px;
          background: #ead494;
        }

        .pc-call-controls {
          display: grid;
          grid-template-columns: repeat(4, minmax(0, 1fr));
          gap: 10px;
          margin: 0 17px;
        }

        .pc-call-controls button {
          display: flex;
          align-items: center;
          justify-content: center;
          flex-direction: column;
          gap: 8px;
          min-height: 65px;
          padding: 9px 3px 6px;
          border: 1px solid var(--pc-border);
          border-radius: 10px;
          background: #faf7ef;
          color: var(--pc-ink);
        }

        .pc-call-controls button > span {
          font-size: 10px;
          white-space: nowrap;
        }

        .pc-call-controls .pc-control-on {
          background: #fbedbe;
          border-color: #eee1b8;
        }

        .pc-call-controls .pc-control-end {
          background: #f3363b;
          border-color: #f3363b;
          color: #fff;
        }

        .pc-mic-status {
          display: flex;
          align-items: center;
          gap: 7px;
          margin: 8px 18px 0;
          color: #7b8490;
          font-size: 10px;
        }

        .pc-mic-status .pc-green-dot {
          background: #23a74c;
        }

        .pc-no-active {
          text-align: center;
          padding: 14px 22px 28px;
        }

        .pc-no-active h3 {
          margin-top: 14px;
        }

        .pc-no-active p {
          margin: 6px auto 0;
          max-width: 28ch;
          font-size: 12px;
          color: var(--pc-muted);
        }

        .pc-favorites {
          padding-bottom: 5px;
        }

        .pc-text-button {
          padding: 0;
          border: 0;
          background: transparent;
          color: #59667d;
          font-size: 11px;
          text-decoration: underline;
          text-underline-offset: 3px;
          white-space: nowrap;
        }

        .pc-favorite-row {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 8px;
          padding: 5px 18px;
        }

        .pc-favorite-row + .pc-favorite-row {
          border-top: 1px solid #f0ebe2;
        }

        .pc-favorite-row .pc-avatar {
          width: 35px;
          height: 35px;
          flex-basis: 35px;
          font-size: 11px;
        }

        .pc-favorite-actions {
          display: flex;
          gap: 9px;
        }

        .pc-favorite-actions .pc-round-button {
          width: 35px;
          height: 35px;
        }

        .pc-bottom-grid {
          display: grid;
          grid-template-columns:
            minmax(0, 1.18fr)
            minmax(0, 1fr);
          gap: 9px;
          margin-top: 12px;
        }

        .pc-group-row {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 12px;
          padding: 11px 16px 22px;
          font-size: 11px;
        }

        .pc-group-row .pc-avatar {
          width: 45px;
          height: 45px;
          flex-basis: 45px;
        }

        .pc-group-time small {
          display: block;
          color: var(--pc-muted);
          margin-top: 4px;
        }

        .pc-sharing {
          padding: 12px 15px;
        }

        .pc-sharing h2 {
          font-size: 14px;
        }

        .pc-sharing-content {
          display: flex;
          align-items: center;
          gap: 18px;
          margin-top: 8px;
        }

        .pc-preview-grid {
          display: grid;
          grid-template-columns: repeat(2, minmax(0, 1fr));
          gap: 4px;
          width: 192px;
          min-height: 104px;
          flex: 0 0 192px;
          padding: 5px;
          border: 1px solid var(--pc-border);
          border-radius: 10px;
          background: #f5f2eb;
          overflow: hidden;
        }

        .pc-preview-grid > div {
          display: flex;
          align-items: center;
          justify-content: center;
          min-height: 45px;
          background: #ece9e1;
          border-radius: 6px;
        }

        .pc-preview-grid .pc-avatar {
          width: 32px;
          height: 32px;
          flex-basis: 32px;
          font-size: 10px;
        }

        .pc-preview-grid .pc-preview-empty {
          grid-column: 1 / -1;
          color: #7b755f;
        }

        .pc-sharing-copy {
          min-width: 0;
        }

        .pc-sharing-copy p {
          margin: 0 0 12px;
          max-width: 27ch;
          color: var(--pc-muted);
          font-size: 12px;
          line-height: 1.4;
        }

        .pc-sharing-buttons {
          display: flex;
          flex-wrap: wrap;
          gap: 7px;
        }

        .pc-sharing-buttons .pc-button {
          min-height: 35px;
          padding: 7px 8px;
          gap: 5px;
          border-radius: 7px;
          font-size: 9px;
        }

        .pc-sharing-on {
          background: #fbe8b6;
        }

        .pc-empty {
          padding: 44px 12px !important;
          text-align: center;
          color: var(--pc-muted) !important;
        }

        .pc-empty-small {
          padding: 14px 18px 22px;
          font-size: 12px;
          color: var(--pc-muted);
        }

        .pc-incoming {
          position: fixed;
          right: 25px;
          bottom: 25px;
          z-index: 60;
          width: 280px;
          padding: 12px 15px 14px;
          border-radius: 13px;
          background: #fffefa;
          color: var(--pc-ink);
          box-shadow:
            0 10px 38px
            rgba(31, 37, 49, 0.18);
        }

        .pc-incoming-heading {
          display: flex;
          align-items: center;
          justify-content: space-between;
        }

        .pc-incoming-heading > span {
          display: inline-flex;
          align-items: center;
          gap: 10px;
          color: #485670;
          font-size: 11px;
        }

        .pc-incoming-heading > button {
          display: flex;
          padding: 0;
          border: 0;
          background: transparent;
          color: #7e8793;
        }

        .pc-incoming-person {
          display: flex;
          align-items: center;
          gap: 13px;
          padding: 13px 5px;
        }

        .pc-incoming-person .pc-avatar {
          width: 49px;
          height: 49px;
          flex-basis: 49px;
          font-size: 18px;
        }

        .pc-incoming-person strong {
          display: block;
          font-weight: 500;
          font-size: 13px;
        }

        .pc-incoming-person small {
          display: block;
          color: var(--pc-muted);
          font-size: 11px;
          margin-top: 2px;
        }

        .pc-incoming-actions {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 10px;
        }

        .pc-incoming-actions button {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 10px;
          min-height: 39px;
          border: 0;
          border-radius: 8px;
          color: #fff;
          font-size: 12px;
        }

        .pc-accept {
          background: #168b43;
        }

        .pc-decline {
          background: #ef3438;
        }

        .pc-menu-anchor {
          position: relative;
        }

        .pc-menu {
          position: absolute;
          top: 38px;
          right: 0;
          z-index: 10;
          min-width: 175px;
          padding: 5px;
          border-radius: 10px;
          background: #fffdf8;
          box-shadow:
            0 7px 22px
            rgba(30, 35, 45, 0.16);
        }

        .pc-menu button {
          display: block;
          width: 100%;
          padding: 9px 10px;
          border: 0;
          border-radius: 6px;
          background: transparent;
          color: var(--pc-ink);
          text-align: left;
          font-size: 12px;
        }

        .pc-menu button:hover:not(:disabled) {
          background: #f7edda;
        }

        .pc-dialog-backdrop {
          position: fixed;
          inset: 0;
          z-index: 80;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 20px;
          background: rgba(21, 27, 39, 0.36);
        }

        .pc-dialog {
          position: relative;
          inset: auto;
          width: min(470px, 100%);
          max-height: 88vh;
          margin: 0;
          padding: 0;
          overflow-y: auto;
          border: 1px solid var(--pc-border);
          border-radius: 14px;
          background: #fffdf7;
          color: var(--pc-ink);
          box-shadow:
            0 18px 55px
            rgba(20, 27, 40, 0.22);
        }

        .pc-picker-body {
          padding: 0 18px 18px;
        }

        .pc-kind-picker {
          display: flex;
          gap: 8px;
          margin-bottom: 15px;
        }

        .pc-kind-picker button {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
          flex: 1;
          min-height: 39px;
          border: 1px solid var(--pc-border);
          border-radius: 8px;
          background: #faf7ef;
          color: var(--pc-ink);
          font-size: 12px;
        }

        .pc-kind-picker .pc-kind-selected {
          background: #292a2d;
          border-color: #292a2d;
          color: #fff;
        }

        .pc-field {
          display: block;
          margin: 0 0 13px;
          font-size: 12px;
        }

        .pc-field > span {
          display: block;
          margin-bottom: 5px;
          font-weight: 500;
        }

        .pc-field input,
        .pc-field select {
          width: 100%;
          min-height: 39px;
          padding: 8px 10px;
          border: 1px solid #ddd5c7;
          border-radius: 8px;
          background: #fffefb;
          color: var(--pc-ink);
          font-size: 12px;
        }

        .pc-picker-search {
          width: 100%;
        }

        .pc-contact-list {
          max-height: 290px;
          overflow-y: auto;
          margin: 8px 0 16px;
          scrollbar-width: thin;
          scrollbar-color: #cfc5b5 #f4efe6;
        }

        .pc-contact-row {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 10px;
          padding: 10px 0;
          border-bottom: 1px solid #eee7da;
        }

        .pc-contact-row label {
          display: flex;
          align-items: center;
          gap: 10px;
          min-width: 0;
          flex: 1;
          cursor: pointer;
        }

        .pc-contact-row input {
          width: 15px;
          height: 15px;
          margin: 0;
          accent-color: #292a2d;
        }

        .pc-contact-row strong {
          display: block;
          font-size: 12px;
          font-weight: 500;
        }

        .pc-contact-row small {
          display: block;
          color: var(--pc-muted);
          font-size: 10px;
        }

        .pc-star-button {
          display: flex;
          padding: 7px;
          border: 0;
          background: transparent;
          color: #8a8170;
        }

        .pc-star-active {
          color: #b58411;
        }

        .pc-star-active svg {
          fill: #ffe49b;
        }

        .pc-full-button {
          width: 100%;
        }

        .pc-active > .pc-full-button {
          width: calc(100% - 36px);
          margin: 0 18px;
        }

        .pc-picker-error {
          font-size: 12px;
          color: #a03b2b;
          overflow-wrap: anywhere;
        }

        .pc-remote-person {
          display: contents;
        }
        .pc-person-tile {
          min-width: 0;
          padding: 9px;
          background: #fff9e8;
          color: #252627;
          border-radius: 10px;
        }
        .pc-person-tile > strong {
          display: block;
          font-size: 12px;
          margin-bottom: 5px;
        }
        .pc-person-tile > small {
          display: block;
          font-size: 10px;
          margin-bottom: 6px;
          color: #655b40;
        }
        .pc-remote-identity {
          display: flex;
          min-height: 110px;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          gap: 8px;
          font-size: 11px;
        }
        .pc-screen-tile {
          grid-column: 1 / -1;
        }
        .pc-screen-video video {
          height: auto !important;
          max-height: 340px;
          object-fit: contain !important;
        }
        .pc-remote-media {
          display: grid;
          grid-template-columns: repeat(2, minmax(0, 1fr));
          gap: 6px;
          margin: 10px 17px 0;
        }

        .pc-remote-video {
          position: relative;
          overflow: hidden;
          border-radius: 8px;
          background: #252a35;
        }

        .pc-remote-video video {
          display: block;
          width: 100%;
          height: 120px;
          object-fit: cover;
        }

        .pc-audio-stream {
          display: contents;
          position: relative;
        }

        .pc-audio-stream video {
          width: 1px;
          height: 1px;
          position: absolute;
          overflow: hidden;
          opacity: 0;
        }

        .pc-enable-audio {
          padding: 5px 7px;
          border: 1px solid #ddd2bc;
          border-radius: 6px;
          background: #fcf3df;
          font-size: 10px !important;
        }

        .pc-preview-grid .pc-local-video {
          grid-column: 1 / -1;
          min-height: 92px;
          overflow: hidden;
          background: #252a35;
        }

        .pc-local-video video {
          display: block;
          width: 100%;
          height: 92px;
          object-fit: cover;
          transform: scaleX(-1);
        }

        .pc-spin {
          animation: pc-spin 900ms linear infinite;
        }

        @keyframes pc-spin {
          to {
            transform: rotate(360deg);
          }
        }

        @media (max-width: 1250px) {
          .pc-page {
            padding: 24px 20px;
          }

          .pc-main-grid {
            grid-template-columns:
              minmax(0, 1.75fr)
              minmax(300px, 1fr);
          }

          .pc-metric {
            gap: 14px;
            padding: 13px 14px;
          }

          .pc-search {
            width: 195px;
          }

          .pc-table {
            min-width: 700px;
          }

          .pc-sharing-content {
            gap: 10px;
          }

          .pc-preview-grid {
            width: 145px;
            flex-basis: 145px;
          }

          .pc-group-row {
            flex-wrap: wrap;
          }
        }

        @media (max-width: 1000px) {
          .pc-main-grid {
            grid-template-columns: minmax(0, 1fr);
          }

          .pc-right-column {
            grid-template-columns: repeat(2, minmax(0, 1fr));
            align-items: start;
          }

          .pc-bottom-grid {
            grid-template-columns: minmax(0, 1fr);
          }

          .pc-sharing-content {
            gap: 20px;
          }

          .pc-preview-grid {
            width: 192px;
            flex-basis: 192px;
          }

          .pc-header h1 {
            font-size: 35px;
          }

          .pc-header p {
            font-size: 13px;
          }

          .pc-header-actions .pc-button {
            padding: 10px 14px;
            min-height: 43px;
            font-size: 12px;
          }
        }

        @media (max-width: 720px) {
          .pc-page {
            padding: 20px 14px;
          }

          .pc-header {
            align-items: flex-start;
            flex-direction: column;
            gap: 16px;
          }

          .pc-metrics {
            grid-template-columns: repeat(2, minmax(0, 1fr));
          }

          .pc-right-column {
            grid-template-columns: minmax(0, 1fr);
          }

          .pc-history .pc-card-heading {
            flex-wrap: wrap;
          }

          .pc-history-actions {
            width: 100%;
          }

          .pc-history-actions .pc-search {
            width: 100%;
          }

          .pc-table-footer {
            align-items: flex-start;
            flex-direction: column;
          }

          .pc-tabs {
            gap: 6px;
            flex-wrap: wrap;
          }

          .pc-tabs button {
            padding: 5px 14px;
          }

          .pc-group-row {
            justify-content: flex-start;
            gap: 15px;
          }
        }

        @media (max-width: 460px) {
          .pc-page {
            padding: 17px 10px;
          }

          .pc-header h1 {
            font-size: 31px;
          }

          .pc-header-actions {
            width: 100%;
            gap: 8px;
          }

          .pc-header-actions .pc-button {
            flex: 1;
            padding: 10px 8px;
            gap: 7px;
            font-size: 11px;
          }

          .pc-metric {
            gap: 10px;
            min-height: 82px;
            padding: 11px;
          }

          .pc-metric-icon {
            width: 41px;
            height: 44px;
            flex-basis: 41px;
            border-radius: 12px;
          }

          .pc-metric span {
            font-size: 11px;
          }

          .pc-metric strong {
            font-size: 25px;
          }

          .pc-card-heading {
            padding-right: 14px;
            padding-left: 14px;
          }

          .pc-sharing-content {
            align-items: stretch;
            flex-direction: column;
          }

          .pc-preview-grid {
            width: 100%;
            flex-basis: auto;
          }

          .pc-sharing-copy p {
            max-width: none;
          }

          .pc-incoming {
            right: 12px;
            bottom: 12px;
            width: min(280px, calc(100vw - 24px));
          }
        }

        @media (prefers-reduced-motion: reduce) {
          .pc-spin {
            animation-duration: 1800ms;
          }
        }
      
        .pc-audio-stream {
          width: fit-content;
          max-width: 100%;
        }

        .pc-enable-audio {
          width: auto;
          padding: 7px 12px;
          border-radius: 7px;
          background: #ffda55;
          color: #292722;
        }
`}</style>
    </main>
  );
}