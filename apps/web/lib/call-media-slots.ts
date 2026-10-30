
export type MediaRole =
  | "microphone"
  | "camera"
  | "screen";

export function mediaSlots(
  pc: RTCPeerConnection,
  microphone: RTCRtpSender,
  camera: RTCRtpSender,
  screen: RTCRtpSender,
): Record<string, MediaRole> {
  const result: Record<string, MediaRole> = {};

  for (const transceiver of pc.getTransceivers()) {
    if (transceiver.mid === null) continue;

    const role =
      transceiver.sender === screen
        ? "screen"
        : transceiver.sender === camera
          ? "camera"
          : transceiver.sender === microphone
            ? "microphone"
            : null;

    if (role) {
      result[transceiver.mid] = role;
    }
  }

  return result;
}

export function roleFor(
  event: RTCTrackEvent,
  slots: Record<string, MediaRole>,
  screen: RTCRtpSender,
): MediaRole {
  if (event.track.kind === "audio") {
    return "microphone";
  }

  return (
    (
      event.transceiver.mid !== null
        ? slots[event.transceiver.mid]
        : undefined
    )
    || (
      event.transceiver.sender === screen
        ? "screen"
        : "camera"
    )
  );
}
