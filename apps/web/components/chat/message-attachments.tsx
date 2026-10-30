
"use client";

import { useEffect, useRef, useState } from "react";
import {
  Download,
  FileText,
  RefreshCw,
} from "lucide-react";
import { attachmentsService } from "@/services/attachments.service";
import type { BoundAttachmentResponse } from "@/types/attachments";
import { AudioAttachmentPlayer } from "./audio-attachment-player";

type FileItem = Pick<
  BoundAttachmentResponse,
  "attachment_id" | "kind" | "filename" | "size_bytes"
>;

export function AttachmentPreview({
  file,
}: {
  file: FileItem;
}) {
  const [url, setUrl] = useState("");
  const [error, setError] = useState("");
  const [retry, setRetry] = useState(0);
  const [busy, setBusy] = useState(false);
  const frame = useRef<HTMLDivElement>(null);

  const media =
    file.kind === "IMAGE" || file.kind === "VIDEO";

  useEffect(() => {
    if (!media) return;

    let stopped = false;
    let requested = false;

    setUrl("");
    setError("");

    async function load() {
      if (requested) return;
      requested = true;

      try {
        const result =
          await attachmentsService.createDownload(
            file.attachment_id,
          );

        const source = new URL(
          result.download_url,
          window.location.origin,
        );

        if (
          !["http:", "https:"].includes(source.protocol)
        ) {
          throw new Error("Invalid media URL.");
        }

        if (!stopped) setUrl(source.href);
      } catch (cause) {
        if (!stopped) {
          setError(
            cause instanceof Error
              ? cause.message
              : "Preview unavailable.",
          );
        }
      }
    }

    const observer = new IntersectionObserver(
      entries => {
        if (
          entries.some(entry => entry.isIntersecting)
        ) {
          observer.disconnect();
          void load();
        }
      },
      { rootMargin: "240px" },
    );

    if (frame.current) observer.observe(frame.current);

    return () => {
      stopped = true;
      observer.disconnect();
    };
  }, [file.attachment_id, media, retry]);

  if (file.kind === "AUDIO") {
    return (
      <AudioAttachmentPlayer
        attachmentId={file.attachment_id}
        filename={file.filename}
      />
    );
  }

  async function download() {
    if (busy) return;

    const popup = window.open("about:blank", "_blank");

    if (popup) popup.opener = null;

    setBusy(true);
    setError("");

    try {
      const result =
        await attachmentsService.createDownload(
          file.attachment_id,
        );

      const source = new URL(
        result.download_url,
        window.location.origin,
      );

      if (
        !["http:", "https:"].includes(source.protocol)
      ) {
        throw new Error("Invalid download URL.");
      }

      if (!popup) {
        throw new Error(
          "Allow pop-ups for this site to download the file.",
        );
      }

      popup.location.replace(source.href);
    } catch (cause) {
      popup?.close();

      setError(
        cause instanceof Error
          ? cause.message
          : "Download failed.",
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <div ref={frame} className="chatAttachment">
      {media &&
        !error &&
        (url ? (
          file.kind === "IMAGE" ? (
            <a
              href={url}
              target="_blank"
              rel="noopener noreferrer"
              aria-label={`Open ${file.filename}`}
            >
              <img
                src={url}
                alt={file.filename}
                loading="lazy"
                onError={() =>
                  setError(
                    "Image preview could not load. Retry or download it.",
                  )
                }
              />
            </a>
          ) : (
            <video
              src={url}
              controls
              playsInline
              preload="metadata"
              onError={() =>
                setError(
                  "Video preview could not load. Retry or download it.",
                )
              }
            />
          )
        ) : (
          <div
            className="mediaPlaceholder"
            role="status"
          >
            Loading {file.kind.toLowerCase()}…
          </div>
        ))}

      <div className="fileRow">
        {!media && <FileText size={20} />}

        <span>
          <strong>{file.filename}</strong>
          <small>
            {Math.ceil(file.size_bytes / 1024)} KB
            {" · "}
            {file.kind.toLowerCase()}
          </small>
        </span>

        <button
          type="button"
          aria-label={`Download ${file.filename}`}
          disabled={busy}
          onClick={() => void download()}
        >
          <Download size={17} />
        </button>
      </div>

      {error && (
        <div className="mediaError" role="alert">
          {error}{" "}
          {media && (
            <button
              type="button"
              onClick={() => {
                setError("");
                setRetry(value => value + 1);
              }}
            >
              <RefreshCw size={13} /> Retry
            </button>
          )}
        </div>
      )}

      <style jsx>{`
        .chatAttachment {
          width: 320px;
          max-width: 100%;
          overflow: hidden;
          border-radius: 10px;
          background: #fffdf7;
          color: #252627;
        }
        img,
        video {
          display: block;
          width: 100%;
          max-height: 300px;
          object-fit: contain;
          background: #171817;
        }
        .mediaPlaceholder {
          display: grid;
          place-items: center;
          height: 150px;
          font-size: 12px;
          color: #655b40;
          background: #fff3c5;
        }
        .fileRow {
          display: flex;
          align-items: center;
          gap: 9px;
          padding: 8px 10px;
        }
        .fileRow span {
          flex: 1;
          min-width: 0;
        }
        strong {
          display: block;
          overflow: hidden;
          white-space: nowrap;
          text-overflow: ellipsis;
          font-size: 12px;
        }
        small {
          display: block;
          margin-top: 3px;
          font-size: 10px;
          color: #655b40;
        }
        button {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          gap: 4px;
          padding: 7px;
          border: 0;
          border-radius: 6px;
          background: transparent;
          color: inherit;
          cursor: pointer;
        }
        button:hover,
        button:focus-visible {
          background: #ffe69a;
          outline: none;
        }
        button:disabled {
          opacity: 0.5;
          cursor: wait;
        }
        .mediaError {
          padding: 8px;
          color: #9b2424;
          font-size: 11px;
        }
      `}</style>
    </div>
  );
}

export function isAutomaticVoiceText(
  content: string,
  filenames: string[],
): boolean {
  const text = content.trim();

  return (
    filenames.length > 0 &&
    (
      /^(?:🎙️?\s*)?Voice message$/iu.test(text) ||
      text === filenames.join(", ")
    )
  );
}

export function MessageAttachments({
  conversationId,
  messageId,
  content,
}: {
  conversationId: string;
  messageId: string;
  content?: string;
}) {
  const [files, setFiles] = useState<
    BoundAttachmentResponse[]
  >([]);
  const [error, setError] = useState("");
  const [retry, setRetry] = useState(0);

  useEffect(() => {
    let stopped = false;

    setFiles([]);
    setError("");

    void attachmentsService
      .listConversationAttachments(
        conversationId,
        messageId,
      )
      .then(result => {
        if (!stopped) {
          setFiles(result.attachments ?? []);
        }
      })
      .catch(cause => {
        if (!stopped) {
          setError(
            cause instanceof Error
              ? cause.message
              : "Attachments could not load.",
          );
        }
      });

    return () => {
      stopped = true;
    };
  }, [conversationId, messageId, retry]);

  const generatedVoice =
    /^(?:🎙️?\s*)?Voice message$/iu.test(
      content?.trim() ?? "",
    );

  const automaticCaption =
    files.length > 0 &&
    content?.trim() ===
      files.map(file => file.filename).join(", ");

  return (
    <>
      {content &&
        !generatedVoice &&
        !automaticCaption && (
          <p className="pmMessageBody">{content}</p>
        )}

      <div
        style={{
          display: "grid",
          gap: 7,
          maxWidth: "100%",
        }}
      >
        {files.map(file => (
          <AttachmentPreview
            key={file.attachment_id}
            file={file}
          />
        ))}

        {error && (
          <span
            role="alert"
            style={{
              color: "#9b2424",
              fontSize: 11,
            }}
          >
            {error}{" "}
            <button
              type="button"
              onClick={() =>
                setRetry(value => value + 1)
              }
            >
              Retry attachments
            </button>
          </span>
        )}
      </div>
    </>
  );
}

export default MessageAttachments;
