"use client";

import {
  Ban,
  Headphones,
  Mic,
  MicOff,
  MonitorUp,
  UserMinus,
  VolumeX,
} from "lucide-react";

import type {
  VoiceParticipant,
} from "@/types/channels";


interface VoiceParticipantListProps {
  participants: VoiceParticipant[];

  selfUserId:
    | string
    | null;

  canModerate: boolean;

  onServerMute(
    userId: string,
    muted: boolean,
  ): Promise<void>;

  onServerDeafen(
    userId: string,
    deafened: boolean,
  ): Promise<void>;

  onKick(
    userId: string,
  ): Promise<void>;

  onBan(
    userId: string,
  ): Promise<void>;
}


export function VoiceParticipantList({
  participants,
  selfUserId,
  canModerate,
  onServerMute,
  onServerDeafen,
  onKick,
  onBan,
}: VoiceParticipantListProps) {
  if (
    participants.length ===
    0
  ) {
    return (
      <div
        style={{
          padding: 18,
          opacity: 0.65,
        }}
      >
        Nobody is connected.
      </div>
    );
  }


  return (
    <div
      style={{
        display: "grid",
        gap: 8,
      }}
    >
      {participants.map(
        (participant) => {
          const isSelf =
            participant.user_id ===
            selfUserId;

          return (
            <div
              key={
                participant.id
              }
              style={{
                display: "flex",

                alignItems:
                  "center",

                justifyContent:
                  "space-between",

                gap: 10,

                padding:
                  "10px 12px",

                border:
                  participant.speaking
                    ? "1px solid #22c55e"
                    : "1px solid var(--border, #e5e7eb)",

                borderRadius:
                  10,
              }}
            >
              <div
                style={{
                  minWidth: 0,

                  display:
                    "flex",

                  alignItems:
                    "center",

                  gap: 10,
                }}
              >
                <div
                  style={{
                    width: 34,

                    height: 34,

                    borderRadius:
                      "50%",

                    display:
                      "grid",

                    placeItems:
                      "center",

                    background:
                      "rgba(99,102,241,.12)",

                    fontWeight:
                      800,
                  }}
                >
                  {participant.user_id
                    .slice(
                      0,
                      2,
                    )
                    .toUpperCase()}
                </div>

                <div
                  style={{
                    minWidth: 0,
                  }}
                >
                  <div
                    style={{
                      fontWeight:
                        700,
                    }}
                  >
                    {isSelf
                      ? "You"
                      : participant.user_id.slice(
                          0,
                          8,
                        )}
                  </div>

                  <div
                    style={{
                      display:
                        "flex",

                      gap: 6,

                      alignItems:
                        "center",

                      opacity:
                        0.65,

                      fontSize:
                        12,
                    }}
                  >
                    {participant.effective_muted ? (
                      <MicOff
                        size={13}
                      />
                    ) : (
                      <Mic
                        size={13}
                      />
                    )}

                    {participant.effective_deafened ? (
                      <VolumeX
                        size={13}
                      />
                    ) : null}

                    {participant.screen_sharing ? (
                      <MonitorUp
                        size={13}
                      />
                    ) : null}

                    <span>
                      {
                        participant.presence
                      }
                    </span>
                  </div>
                </div>
              </div>

              {canModerate &&
              !isSelf ? (
                <div
                  style={{
                    display:
                      "flex",

                    gap: 4,
                  }}
                >
                  <button
                    type="button"
                    title={
                      participant.server_muted
                        ? "Server unmute"
                        : "Server mute"
                    }
                    onClick={() =>
                      void onServerMute(
                        participant.user_id,
                        !participant.server_muted,
                      )
                    }
                  >
                    {participant.server_muted ? (
                      <Mic
                        size={15}
                      />
                    ) : (
                      <MicOff
                        size={15}
                      />
                    )}
                  </button>

                  <button
                    type="button"
                    title={
                      participant.server_deafened
                        ? "Server undeafen"
                        : "Server deafen"
                    }
                    onClick={() =>
                      void onServerDeafen(
                        participant.user_id,
                        !participant.server_deafened,
                      )
                    }
                  >
                    <Headphones
                      size={15}
                    />
                  </button>

                  <button
                    type="button"
                    title="Kick"
                    onClick={() =>
                      void onKick(
                        participant.user_id,
                      )
                    }
                  >
                    <UserMinus
                      size={15}
                    />
                  </button>

                  <button
                    type="button"
                    title="Ban"
                    onClick={() =>
                      void onBan(
                        participant.user_id,
                      )
                    }
                  >
                    <Ban
                      size={15}
                    />
                  </button>
                </div>
              ) : null}
            </div>
          );
        },
      )}
    </div>
  );
}