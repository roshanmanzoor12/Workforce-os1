import { attachmentsService } from "@/services/attachments.service";
import { chatFeaturesService } from "@/services/chat-features.service";

export async function startVoiceRecording(
  conversationId: string,
) {
  if (
    !navigator.mediaDevices?.getUserMedia ||
    typeof MediaRecorder === "undefined"
  ) {
    throw new Error(
      "Voice recording requires HTTPS or localhost and a supported browser.",
    );
  }

  const stream =
    await navigator.mediaDevices.getUserMedia({
      audio: true,
    });

  let recorder: MediaRecorder;

  try {
    const mimeType = [
      "audio/webm;codecs=opus",
      "audio/mp4",
      "audio/ogg;codecs=opus",
    ].find(value =>
      MediaRecorder.isTypeSupported(value),
    );

    recorder = new MediaRecorder(
      stream,
      mimeType ? { mimeType } : undefined,
    );
  } catch (cause) {
    stream.getTracks().forEach(track => track.stop());
    throw cause;
  }

  const chunks: Blob[] = [];

  let cancelled = false;
  let failure: Error | null = null;

  const stopTracks = () => {
    stream.getTracks().forEach(track => track.stop());
  };

  const done = new Promise<void>(resolve => {
    recorder.ondataavailable = event => {
      if (event.data.size) {
        chunks.push(event.data);
      }
    };

    recorder.onerror = () => {
      failure = new Error(
        "Voice recording failed. Please record again.",
      );

      stopTracks();
      resolve();
    };

    recorder.onstop = () => {
      stopTracks();
      resolve();
    };
  });

  try {
    recorder.start();
  } catch (cause) {
    stopTracks();
    throw cause;
  }

  async function sendRecording() {
    if (recorder.state !== "inactive") {
      recorder.stop();
    }

    await done;
    stopTracks();

    if (cancelled) return null;
    if (failure) throw failure;

    const type = recorder.mimeType || "audio/webm";
    const blob = new Blob(chunks, { type });

    if (!blob.size) {
      throw new Error(
        "The recording was empty. Please try again.",
      );
    }

    const suffix = type.includes("mp4")
      ? "m4a"
      : type.includes("ogg")
        ? "ogg"
        : "webm";

    const file = new File(
      [blob],
      `voice-${Date.now()}.${suffix}`,
      { type },
    );

    const uploaded =
      await attachmentsService.uploadConversationFile(
        conversationId,
        file,
      );

    if (cancelled) return null;

    const message =
      await chatFeaturesService.sendMessage(
        conversationId,
        "🎙️ Voice message",
        {
          clientMessageId: crypto.randomUUID(),
        },
      );

    await attachmentsService.bindConversationAttachments(
      conversationId,
      message.id,
      [uploaded.attachment_id],
    );

    return message;
  }

  let sending:
    ReturnType<typeof sendRecording> | null = null;

  return {
    stream,

    pause: () => {
      if (recorder.state === "recording") {
        recorder.pause();
      }
    },

    resume: () => {
      if (recorder.state === "paused") {
        recorder.resume();
      }
    },

    stop: () => {
      sending ??= sendRecording();
      return sending;
    },

    cancel: () => {
      cancelled = true;

      if (recorder.state !== "inactive") {
        recorder.stop();
      }

      stopTracks();
    },
  };
}

export type VoiceRecordingSession =
  Awaited<ReturnType<typeof startVoiceRecording>>;

export async function recordAndSendVoiceMessage(
  conversationId: string,
  seconds = 120,
) {
  const recording =
    await startVoiceRecording(conversationId);

  try {
    await new Promise<void>(resolve => {
      window.setTimeout(
        resolve,
        Math.max(1, seconds) * 1000,
      );
    });

    return await recording.stop();
  } finally {
    recording.cancel();
  }
}