/*
 * WorkforceOS workspace channel type bridge.
 *
 * The current canonical channel + voice contracts live in
 * services/workspace-channels.service.ts.
 *
 * Re-exporting them here keeps older components compatible with:
 *
 *   import type { ... } from "@/types/workspace-channels";
 *
 * while newer files may import directly from the service.
 *
 * IMPORTANT:
 * Do not redefine WorkspaceChannelType in this file.
 * Backend currently supports:
 *
 *   text
 *   announcement
 *   voice
 */

export type {
  WorkspaceChannelType,
  WorkspaceChannelMessageType,

  WorkspaceChannelPublic,
  WorkspaceChannelCreateRequest,
  WorkspaceChannelUpdateRequest,

  WorkspaceChannelMessagePublic,
  WorkspaceChannelMessageCreateRequest,

  VoicePresenceState,
  VoiceSignalType,

  VoiceParticipantPublic,
  VoiceCallPublic,
  VoiceJoinResponse,
  VoiceParticipantListResponse,

  VoiceSelfStateRequest,
  VoiceModeratorStateRequest,
  VoiceModerationReasonRequest,

  VoiceBanResponse,

  VoiceScreenShareResponse,

  VoiceSignalRequest,
  VoiceSignalEnvelope,
  VoiceSignalResponse,
  VoiceSignalPollResponse,

  VoicePresenceHeartbeatRequest,
  VoiceSpeakingRequest,
  VoiceRealtimeStateResponse,

  VoiceCapabilitiesResponse,
} from "@/services/workspace-channels.service";