"use client";
import { DirectCallInvite } from "@/components/chat/direct-call-invite";
import { CallRingtone } from "@/components/chat/call-ringtone";

import {
  SpeakingIndicator,
} from "@/components/chat/speaking-indicator";

import {
  useEffect,
  useRef,
  useState,
} from "react";
import {
  Camera,
  Mic,
  MonitorUp,
  PhoneOff,
  X,
} from "lucide-react";

import { UserAvatar } from "@/components/account/user-avatar";
import { api } from "@/lib/api/client";
import { useGroupCall } from "@/hooks/use-group-call";
import { groupsService } from "@/services/groups.service";
import type { GroupCall } from "@/services/groups.service";
import type { CallKind } from "@/types/conversation-call";

type Person = {
  user_id: string;
  name: string;
  username?: string | null;
  avatar_url?: string | null;
};

type CallContext = {
  id: string;
  name: string;
  members: Person[];
  conversation_type?: "direct" | "group";
};

interface Props {
  conversationId: string;
  conversationName: string;
  currentUserId: string | null;
  initialKind?: CallKind | null;
  invitedUserIds?: string[];
  existingCallId?: string;
  onClose: () => void;
}

// call-media-compact-v2
function Media({
  stream,
  kind,
  muted = false,
}: {
  stream: MediaStream;
  kind: "audio" | "video";
  muted?: boolean;
}) {
  const ref = useRef<HTMLMediaElement | null>(null);
  const [blocked, setBlocked] = useState(false);

  useEffect(() => {
    const element = ref.current;
    if (!element) return;

    let disposed = false;

    setBlocked(false);
    element.srcObject = stream;

    const play = () => {
      void element.play()
        .then(() => {
          if (!disposed) setBlocked(false);
        })
        .catch((cause: unknown) => {
          if (
            !disposed
            && cause instanceof DOMException
            && cause.name === "NotAllowedError"
          ) {
            setBlocked(true);
          }
        });
    };

    element.addEventListener(
      "loadedmetadata",
      play,
    );

    play();

    return () => {
      disposed = true;

      element.removeEventListener(
        "loadedmetadata",
        play,
      );

      element.srcObject = null;
    };
  }, [stream]);

  return (
    <div
      style={
        kind === "audio"
          ? {
              display: blocked ? "block" : "none",
              gridColumn: "1 / -1",
              justifySelf: "start",
            }
          : {
              width: "100%",
              minWidth: 0,
            }
      }
    >
      {kind === "audio" ? (
        <audio
          ref={element => {
            ref.current = element;
          }}
          autoPlay
          muted={muted}
          style={{ display: "none" }}
        />
      ) : (
        <video
          ref={element => {
            ref.current = element;
          }}
          autoPlay
          playsInline
          muted={muted}
          style={{
            display: "block",
            width: "100%",
            maxHeight: 360,
            borderRadius: 12,
            background: "#111",
          }}
        />
      )}

      {blocked && (
        <button
          type="button"
          style={{
            width: "auto",
            padding: "7px 12px",
            border: "1px solid #d4ad37",
            borderRadius: 7,
            background: "#ffda55",
            color: "#292722",
            fontSize: 12,
          }}
          onClick={() => {
            void ref.current?.play()
              .then(() => setBlocked(false))
              .catch(() => setBlocked(true));
          }}
        >
          Enable {kind}
        </button>
      )}
    </div>
  );
}

export function ConversationCallPanel({
  conversationId,
  conversationName,
  currentUserId,
  initialKind = "VOICE",
  existingCallId,
  onClose,
}: Props) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const hadCallRef = useRef(false);

  const engine = useGroupCall(currentUserId ?? undefined);
  const [context, setContext] = useState<CallContext | null>(null);
  const [existing, setExisting] = useState<GroupCall | null>(null);
  const [ready, setReady] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const dialog = dialogRef.current;

    if (dialog && !dialog.open) {
      dialog.showModal();
    }

    return () => {
      if (dialog?.open) dialog.close();
    };
  }, []);

  useEffect(() => {
    let active = true;
    setReady(false);
    setError("");

    void Promise.all([
      api.get<CallContext>(
        existingCallId
          ? `/calls/${existingCallId}/context`
          : `/calls/context/${encodeURIComponent(conversationId)}`,
      ),
      existingCallId
        ? groupsService.getCall(existingCallId)
        : Promise.resolve(null),
    ]).then(([details, call]) => {
      if (!active) return;

      if (
        call &&
        (
          call.conversation_id !== conversationId ||
          ["ENDED", "CANCELLED"].includes(call.status)
        )
      ) {
        throw new Error("This call is no longer available.");
      }

      setContext(details);
      setExisting(call);
      setReady(true);
    }).catch((cause) => {
      if (active) {
        setError(
          cause instanceof Error
            ? cause.message
            : "Unable to load this call.",
        );
      }
    });

    return () => {
      active = false;
    };
  }, [conversationId, existingCallId, currentUserId]);

  useEffect(() => {
    const id = engine.call?.id;
    if (!id) return;

    let stopped = false;

    const refresh = () => {
      void api.get<CallContext>(
        `/calls/${id}/context`,
      ).then(value => {
        if (!stopped) setContext(value);
      }).catch(() => undefined);
    };

    refresh();

    const timer = setInterval(refresh, 5000);

    window.addEventListener("focus", refresh);

    return () => {
      stopped = true;
      clearInterval(timer);
      window.removeEventListener("focus", refresh);
    };
  }, [engine.call?.id]);

  const start = engine.start;

  useEffect(() => {
    if (!ready || !context || !currentUserId || engine.call) return;

    const timer = window.setTimeout(() => {
      void start(
        context,
        (existing?.kind ?? initialKind) === "VIDEO"
          ? "video"
          : "voice",
        existing ?? undefined,
      );
    }, 0);

    return () => window.clearTimeout(timer);
  }, [
    ready,
    context,
    currentUserId,
    existing,
    initialKind,
    start,
  ]);

  useEffect(() => {
    if (engine.call) {
      hadCallRef.current = true;
    } else if (hadCallRef.current && !engine.busy) {
      onClose();
    }
  }, [engine.call, engine.busy, onClose]);

  function person(userId: string): Person | undefined {
    return context?.members.find(
      (member) => member.user_id === userId,
    );
  }

  async function finish(): Promise<void> {
    await engine.leave(
      engine.call?.started_by_user_id === currentUserId,
    );
    onClose();
  }

  async function action(
    operation: () => Promise<void>,
  ): Promise<void> {
    setError("");

    try {
      await operation();
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Call action failed.",
      );
    }
  }

  const localPerson = currentUserId
    ? person(currentUserId)
    : undefined;

  return (
    <dialog
      ref={dialogRef}
      className="wcDialog"
      aria-labelledby="workforce-call-title"
      onCancel={(event) => {
        event.preventDefault();
        void finish();
      }}
    >
      <header className="wcHeader">
        <div>
          <h2 id="workforce-call-title">
            {context?.name || conversationName}
          </h2>
          <p role="status">
            {!ready ? "Loading call..." : engine.status}
          </p>
        </div>

        <button
          type="button"
          aria-label="Close call"
          onClick={() => void finish()}
        >
          <X size={19} />
        </button>
      </header>

      {(error || engine.error) && (
        <p className="wcError" role="alert">
          {error || engine.error}
        </p>
      )}

      {engine.call
        && engine.call.started_by_user_id === currentUserId
        && engine.call.participants.some(
          person => person.state === "INVITED",
        )
        && !engine.call.participants.some(
          person =>
            person.user_id !== currentUserId
            && person.state === "JOINED",
        )
        && (
          <CallRingtone
            callId={engine.call.id}
            mode="outgoing"
          />
        )}

      <div className="wcMedia">
        <section className="wcTile">
          <strong>
            {localPerson?.name || "You"}
            <SpeakingIndicator stream={engine.localStream} />
          </strong>

          {engine.localStream && engine.cameraEnabled ? (
            <Media
              stream={engine.localStream}
              kind="video"
              muted
            />
          ) : (
            <div className="wcIdentity">
              <UserAvatar
                userId={currentUserId}
                src={localPerson?.avatar_url}
                name={localPerson?.name || "You"}
                size={64}
              />
              <p>{localPerson?.name || "You"}</p>
            </div>
          )}
        </section>

        {engine.screenStream && (
          <section className="wcTile">
            <strong>Your screen</strong>
            <Media
              stream={engine.screenStream}
              kind="video"
              muted
            />
          </section>
        )}

        {engine.remoteMedia
          .filter(media => media.kind === "audio")
          .map(media => (
            <Media
              key={media.key}
              stream={media.stream}
              kind="audio"
            />
          ))}

        {(engine.call?.participants ?? [])
          .filter(participant =>
            participant.user_id !== currentUserId &&
            participant.state === "JOINED",
          )
          .map(participant => {
            const member = person(participant.user_id);

            const camera = engine.remoteMedia.find(
              media =>
                media.userId === participant.user_id &&
                media.source === "camera",
            );

            const screen = engine.remoteMedia.find(
              media =>
                media.userId === participant.user_id &&
                media.source === "screen",
            );

            return (
              <div
                key={participant.user_id}
                className="wcRemotePerson"
              >
                <section className="wcTile">
                  <strong>
                    {member?.name || member?.username || "Participant"}

                    <SpeakingIndicator
                      stream={
                        engine.remoteMedia.find(
                          media =>
                            media.userId === participant.user_id
                            && media.source === "microphone",
                        )?.stream
                      }
                    />
                  </strong>

                  {member?.username && (
                    <small className="wcUsername">
                      @{member.username}
                    </small>
                  )}

                  {participant.camera_enabled && camera ? (
                    <Media
                      stream={camera.stream}
                      kind="video"
                      muted
                    />
                  ) : (
                    <div className="wcIdentity">
                      <UserAvatar
                        userId={participant.user_id}
                        src={member?.avatar_url}
                        name={member?.name || member?.username}
                        size={64}
                      />
                      <p>
                        {participant.camera_enabled
                          ? "Connecting camera…"
                          : "Camera off"}
                      </p>
                    </div>
                  )}
                </section>

                {participant.screen_share_state === "ACTIVE" && (
                  <section className="wcTile wcScreenTile">
                    <strong>
                      {member?.name ||
                        member?.username ||
                        "Participant"} · Screen
                    </strong>

                    {screen ? (
                      <Media
                        stream={screen.stream}
                        kind="video"
                        muted
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

      <section className="wcParticipants">
        <h3>Participants</h3>

        {engine.call && currentUserId && <DirectCallInvite callId={engine.call.id} userId={currentUserId} />}

        {(engine.call?.participants ?? []).map((participant) => {
          const member = person(participant.user_id);

          return (
            <div className="wcParticipant" key={participant.user_id}>
              <UserAvatar
                userId={participant.user_id}
                src={member?.avatar_url}
                name={
                  member?.name ||
                  member?.username ||
                  "Participant"
                }
                size={36}
              />

              <div>
                <strong>
                  {member?.name || "Participant"}
                  {participant.user_id === currentUserId
                    ? " (You)"
                    : ""}
                </strong>

                {member?.username && (
                  <small>@{member.username}</small>
                )}
              </div>

              <small>{participant.state.toLowerCase()}</small>
            </div>
          );
        })}
      </section>

      {ready && !engine.call && !engine.busy && (
        <button
          type="button"
          onClick={() => {
            if (context) {
              void start(
                context,
                (existing?.kind ?? initialKind) === "VIDEO"
                  ? "video"
                  : "voice",
                existing ?? undefined,
              );
            }
          }}
        >
          Retry call
        </button>
      )}

      <footer className="wcControls">
        <button
          type="button"
          disabled={!engine.call || engine.busy}
          aria-label="Toggle microphone"
          aria-pressed={engine.microphoneEnabled}
          onClick={() => void action(engine.toggleMicrophone)}
        >
          <Mic size={20} />
          {engine.microphoneEnabled ? "Mute" : "Unmute"}
        </button>

        <button
          type="button"
          disabled={!engine.call || engine.busy}
          aria-label="Toggle camera"
          aria-pressed={engine.cameraEnabled}
          onClick={() => void action(engine.toggleCamera)}
        >
          <Camera size={20} />
          Camera
        </button>

        <button
          type="button"
          disabled={!engine.call || engine.busy}
          onClick={() =>
            void action(
              engine.screenStream
                ? engine.stopScreen
                : engine.startScreen,
            )
          }
        >
          <MonitorUp size={20} />
          {engine.screenStream ? "Stop sharing" : "Share screen"}
        </button>

        <button
          type="button"
          className="wcHangup"
          onClick={() => void finish()}
        >
          <PhoneOff size={20} />
          Hang up
        </button>
      </footer>

      <style jsx>{`
        .wcRemotePerson {
          display: contents;
        }
        .wcUsername {
          display: block;
          margin: 3px 0 8px;
          color: #c6c0b2;
          font-size: 11px;
        }
        .wcScreenTile {
          grid-column: 1 / -1;
        }
        .wcDialog {
          outline: none;
          box-shadow: none;
          box-sizing: border-box;
          width: 960px;
          max-width: calc(100vw - 32px);
          max-height: calc(100dvh - 32px);
          margin: auto;
          padding: 20px;
          overflow: auto;
          border: 1px solid #414141;
          border-radius: 16px;
          background: #202222;
          color: #f7f5ef;
          font: inherit;
        }

        .wcDialog::backdrop {
          background: rgba(0, 0, 0, 0.55);
        }

        .wcHeader,
        .wcParticipant,
        .wcControls {
          display: flex;
          align-items: center;
          gap: 12px;
        }

        .wcHeader {
          justify-content: space-between;
          margin-bottom: 16px;
        }

        .wcHeader h2 {
          margin: 0;
          font-size: 18px;
        }

        .wcHeader p,
        .wcParticipant small {
          color: #bababa;
          font-size: 12px;
        }

        .wcMedia {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
          gap: 12px;
        }

        .wcTile {
          padding: 12px;
          border: 1px solid #414141;
          border-radius: 12px;
          background: #171919;
        }

        .wcTile > strong {
          display: block;
          margin-bottom: 10px;
          font-size: 13px;
        }

        .wcIdentity {
          display: grid;
          place-items: center;
          min-height: 180px;
        }

        .wcIdentity img,
        .wcIdentity > span {
          display: grid;
          place-items: center;
          width: 72px;
          height: 72px;
          border-radius: 50%;
          object-fit: cover;
          background: #383a3a;
          font-size: 30px;
        }

        .wcParticipants {
          margin-top: 16px;
        }

        .wcParticipants h3 {
          font-size: 14px;
        }

        .wcParticipant {
          padding: 10px 0;
          border-top: 1px solid #414141;
        }

        .wcParticipant > div {
          flex: 1;
        }

        .wcParticipant strong,
        .wcParticipant small {
          display: block;
        }

        .wcParticipant strong {
          font-size: 13px;
        }

        .wcParticipant img,
        .wcInitial {
          display: grid;
          place-items: center;
          width: 36px;
          height: 36px;
          border-radius: 50%;
          object-fit: cover;
          background: #383a3a;
        }

        .wcControls {
          justify-content: center;
          flex-wrap: wrap;
          margin-top: 20px;
        }

        button {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          gap: 7px;
          min-height: 38px;
          padding: 8px 12px;
          border: 1px solid #505252;
          border-radius: 8px;
          background: #303232;
          color: inherit;
          font: inherit;
          font-size: 12px;
          cursor: pointer;
        }

        button:disabled {
          opacity: 0.45;
          cursor: default;
        }

        button:focus-visible {
          outline: 2px solid #ffcf36;
          outline-offset: 2px;
        }

        .wcHangup {
          background: #8e3030;
        }

        .wcError {
          padding: 10px;
          border-radius: 8px;
          background: #5a2828;
          font-size: 13px;
        }
      `}</style>
    </dialog>
  );
}