import { api } from "@/lib/api/client";

export interface NoteAttachment {
  id: string;
  original_filename: string;
  content_type: string;
  size_bytes: number;
  kind: "IMAGE" | "VIDEO" | "AUDIO" | "FILE";
  status: "PENDING" | "READY" | "DELETED" | "FAILED";
  personal_note_id: string | null;
}

interface PrepareResponse {
  attachment_id: string;
  upload_url: string;
  upload_method: string;
  max_size_bytes: number;
}

function httpURL(value: string) {
  const url = new URL(value);

  if (!["http:", "https:"].includes(url.protocol)) {
    throw new Error("The storage URL is invalid.");
  }

  return url.href;
}

export function listNoteAttachments(noteId: string) {
  return api.get<{ items: NoteAttachment[] }>(
    `/notes/me/${encodeURIComponent(noteId)}/attachments`,
  );
}

export function removeNoteAttachment(attachmentId: string) {
  return api.delete<void>(
    `/attachments/${encodeURIComponent(attachmentId)}`,
  );
}

export async function noteAttachmentDownload(
  attachmentId: string,
) {
  const result = await api.post<{
    download_url: string;
  }>(
    `/attachments/${encodeURIComponent(attachmentId)}/download`,
    {},
  );

  return httpURL(result.download_url);
}

function uploadBytes(
  url: string,
  file: File,
  signal: AbortSignal,
  onProgress: (percent: number) => void,
) {
  return new Promise<void>((resolve, reject) => {
    const xhr = new XMLHttpRequest();

    const abort = () => xhr.abort();

    function finish(error?: Error) {
      signal.removeEventListener("abort", abort);

      if (error) {
        reject(error);
      } else {
        resolve();
      }
    }

    if (signal.aborted) {
      reject(
        new DOMException(
          "Upload cancelled.",
          "AbortError",
        ),
      );
      return;
    }

    xhr.open("PUT", httpURL(url));
    xhr.withCredentials = false;
    xhr.timeout = 300000;

    xhr.setRequestHeader(
      "Content-Type",
      file.type || "application/octet-stream",
    );

    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable) {
        onProgress(
          Math.round(
            (event.loaded / event.total) * 100,
          ),
        );
      }
    };

    xhr.onload = () => {
      finish(
        xhr.status >= 200 && xhr.status < 300
          ? undefined
          : new Error(
              `Storage upload failed (${xhr.status}).`,
            ),
      );
    };

    xhr.onerror = () => {
      finish(
        new Error(
          "Could not upload to storage. Check storage availability and CORS.",
        ),
      );
    };

    xhr.ontimeout = () => {
      finish(
        new Error(
          "The upload timed out. Try again.",
        ),
      );
    };

    xhr.onabort = () => {
      finish(
        new DOMException(
          "Upload cancelled.",
          "AbortError",
        ),
      );
    };

    signal.addEventListener(
      "abort",
      abort,
      { once: true },
    );

    // Upload bytes directly to the signed storage URL.
    // Do not send the application bearer token here.
    xhr.send(file);
  });
}

export async function uploadNoteAttachment(
  noteId: string,
  file: File,
  signal: AbortSignal,
  onProgress: (percent: number) => void,
) {
  if (!file.size) {
    throw new Error(
      "Empty files cannot be uploaded.",
    );
  }

  if (signal.aborted) {
    throw new DOMException(
      "Upload cancelled.",
      "AbortError",
    );
  }

  const prepared = await api.post<PrepareResponse>(
    "/attachments/prepare",
    {
      scope: "NOTE",
      personal_note_id: noteId,
      filename: file.name,
      content_type:
        file.type || "application/octet-stream",
      size_bytes: file.size,
    },
  );

  try {
    if (prepared.upload_method !== "PUT") {
      throw new Error(
        "Unsupported upload method.",
      );
    }

    if (file.size > prepared.max_size_bytes) {
      throw new Error(
        "This file exceeds your plan limit.",
      );
    }

    await uploadBytes(
      prepared.upload_url,
      file,
      signal,
      onProgress,
    );

    if (signal.aborted) {
      throw new DOMException(
        "Upload cancelled.",
        "AbortError",
      );
    }

    return await api.post<NoteAttachment>(
      `/attachments/${encodeURIComponent(
        prepared.attachment_id,
      )}/complete`,
      {},
    );
  } catch (error) {
    try {
      await removeNoteAttachment(
        prepared.attachment_id,
      );
    } catch {
      // Keep the record available for server-side cleanup
      // if cancellation cleanup cannot reach the backend.
    }

    throw error;
  }
}