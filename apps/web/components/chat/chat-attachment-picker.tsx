
"use client";

import {
  useEffect,
  useRef,
  useState,
  type ChangeEvent,
} from "react";
import { createPortal } from "react-dom";
import {
  Camera,
  CalendarDays,
  FileText,
  Image as ImageIcon,
  ListChecks,
  Music2,
  Paperclip,
  Sticker,
  UserRound,
  X,
} from "lucide-react";

function LocalPreview({ file }: { file: File }) {
  const [url, setUrl] = useState("");

  useEffect(() => {
    const value = URL.createObjectURL(file);
    setUrl(value);

    return () => URL.revokeObjectURL(value);
  }, [file]);

  return file.type.startsWith("image/") ? (
    <img
      src={url}
      alt={file.name}
      style={{
        width: 58,
        height: 48,
        objectFit: "cover",
        borderRadius: 6,
      }}
    />
  ) : file.type.startsWith("video/") ? (
    <video
      src={url}
      muted
      playsInline
      preload="metadata"
      style={{
        width: 58,
        height: 48,
        objectFit: "cover",
        borderRadius: 6,
      }}
    />
  ) : (
    <FileText size={24} />
  );
}

export function ChatAttachmentPicker({
  files,
  disabled = false,
  onChange,
}: {
  files: File[];
  disabled?: boolean;
  onChange: (files: File[]) => void;
}) {
  const root = useRef<HTMLDivElement>(null);
  const menu = useRef<HTMLDivElement>(null);
  const input = useRef<HTMLInputElement>(null);
  const cameraInput =
    useRef<HTMLInputElement>(null);
  const button =
    useRef<HTMLButtonElement>(null);

  const [open, setOpen] = useState(false);
  const [position, setPosition] = useState({
    left: 12,
    bottom: 60,
  });
  const [error, setError] = useState("");

  useEffect(() => {
    if (!open) return;

    function outside(event: PointerEvent) {
      if (
        event.target instanceof Node &&
        !root.current?.contains(event.target) &&
        !menu.current?.contains(event.target)
      ) {
        setOpen(false);
      }
    }

    function escape(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setOpen(false);
        button.current?.focus();
      }
    }

    menu.current
      ?.querySelector<HTMLButtonElement>(
        "button:not(:disabled)",
      )
      ?.focus();

    document.addEventListener(
      "pointerdown",
      outside,
    );
    document.addEventListener("keydown", escape);

    const close = () => setOpen(false);

    window.addEventListener("resize", close);
    document.addEventListener(
      "scroll",
      close,
      true,
    );

    return () => {
      document.removeEventListener(
        "pointerdown",
        outside,
      );
      document.removeEventListener(
        "keydown",
        escape,
      );
      window.removeEventListener(
        "resize",
        close,
      );
      document.removeEventListener(
        "scroll",
        close,
        true,
      );
    };
  }, [open]);

  function choose(accept: string) {
    if (disabled || files.length >= 10) return;

    setOpen(false);

    if (input.current) {
      input.current.accept = accept;
      input.current.click();
    }
  }

  function selected(
    event: ChangeEvent<HTMLInputElement>,
  ) {
    const chosen = Array.from(
      event.target.files ?? [],
    );

    event.target.value = "";

    const next = [...files];
    let exceeded = false;

    for (const file of chosen) {
      if (
        next.some(
          item =>
            item.name === file.name &&
            item.size === file.size &&
            item.lastModified ===
              file.lastModified,
        )
      ) {
        continue;
      }

      if (next.length >= 10) {
        exceeded = true;
        break;
      }

      next.push(file);
    }

    setError(
      exceeded
        ? "Maximum 10 attachments per message."
        : "",
    );

    onChange(next);
  }

  const actions = [
    {
      label: "Document",
      icon: FileText,
      accept: "*/*",
      color: "#6450a1",
    },
    {
      label: "Photos & videos",
      icon: ImageIcon,
      accept: "image/*,video/*",
      color: "#225c94",
    },
    {
      label: "Camera",
      icon: Camera,
      camera: true,
      color: "#a02d50",
    },
    {
      label: "Audio",
      icon: Music2,
      accept: "audio/*",
      color: "#985300",
    },
    {
      label: "Contact",
      icon: UserRound,
      unavailable: true,
      color: "#225c94",
    },
    {
      label: "Poll",
      icon: ListChecks,
      unavailable: true,
      color: "#856000",
    },
    {
      label: "Event",
      icon: CalendarDays,
      unavailable: true,
      color: "#a02d50",
    },
    {
      label: "New sticker",
      icon: Sticker,
      unavailable: true,
      color: "#24715b",
    },
  ];

  return (
    <div
      ref={root}
      className="attachmentPicker"
    >
      <input
        ref={input}
        type="file"
        multiple
        hidden
        disabled={disabled}
        onChange={selected}
      />
      <input
        ref={cameraInput}
        type="file"
        accept="image/*"
        capture="environment"
        hidden
        disabled={disabled}
        onChange={selected}
      />

      <button
        ref={button}
        type="button"
        className="attachToggle"
        aria-label="Attachment options"
        aria-expanded={open}
        disabled={
          disabled || files.length >= 10
        }
        onClick={() => {
          const rect =
            button.current
              ?.getBoundingClientRect();

          if (rect) {
            setPosition({
              left: Math.max(
                8,
                Math.min(
                  rect.left,
                  window.innerWidth - 226,
                ),
              ),
              bottom: Math.max(
                8,
                window.innerHeight -
                  rect.top +
                  8,
              ),
            });
          }

          setOpen(value => !value);
        }}
      >
        <Paperclip size={18} />
      </button>

      {open &&
        createPortal(
          <div
            ref={menu}
            className="attachmentOptions"
            aria-label="Attachment options"
            style={{
              left: position.left,
              bottom: position.bottom,
            }}
          >
            {actions.map(action => (
              <button
                key={action.label}
                type="button"
                disabled={
                  action.unavailable ||
                  disabled
                }
                title={
                  action.unavailable
                    ? "This feature needs a backend implementation."
                    : action.camera
                      ? "Use your camera on supported devices, or choose a photo."
                      : action.label
                }
                onClick={() => {
                  if (action.camera) {
                    setOpen(false);
                    cameraInput.current?.click();
                  } else {
                    choose(
                      action.accept ?? "*/*",
                    );
                  }
                }}
              >
                <action.icon
                  size={18}
                  color={action.color}
                />
                <span>
                  {action.label}
                  {action.unavailable && (
                    <small>
                      Not available yet
                    </small>
                  )}
                </span>
              </button>
            ))}
          </div>,
          document.body,
        )}

      {files.length > 0 && (
        <div
          className="pendingFiles"
          aria-label="Selected attachments"
        >
          <header>
            <strong>
              {files.length}/10 attachments
            </strong>
            <button
              type="button"
              disabled={disabled}
              onClick={() => onChange([])}
            >
              Clear all
            </button>
          </header>

          {files.map((file, index) => (
            <div
              className="pendingFile"
              key={`${file.name}:${file.size}:${file.lastModified}`}
            >
              <LocalPreview file={file} />
              <span>
                {file.name}
                <small>
                  {Math.ceil(
                    file.size / 1024,
                  )} KB
                </small>
              </span>
              <button
                type="button"
                disabled={disabled}
                aria-label={`Remove ${file.name}`}
                onClick={() =>
                  onChange(
                    files.filter(
                      (_, position) =>
                        position !== index,
                    ),
                  )
                }
              >
                <X size={16} />
              </button>
            </div>
          ))}

          <button
            type="button"
            disabled={
              disabled ||
              files.length >= 10
            }
            onClick={() => choose("*/*")}
          >
            Add more
          </button>
        </div>
      )}

      {error && (
        <span
          role="alert"
          className="pickerError"
        >
          {error}
        </span>
      )}

      <style jsx global>{`
        .attachmentPicker {
          position: relative;
          flex: 0 0 auto;
        }
        .attachmentPicker button,
        .attachmentOptions button {
          font: inherit;
          color: #252627;
          cursor: pointer;
        }
        .attachmentPicker .attachToggle {
          display: grid;
          place-items: center;
          width: 36px;
          height: 36px;
          padding: 0;
          border: 0;
          background: transparent;
          border-radius: 6px;
        }
        .attachmentOptions {
          position: fixed;
          z-index: 300;
          width: 218px;
          max-height: min(420px, 72dvh);
          overflow: auto;
          padding: 6px;
          border: 1px solid #e7dfca;
          border-radius: 12px;
          background: #fffdf7;
          color: #252627;
          box-shadow:
            0 12px 30px rgba(0, 0, 0, 0.14);
        }
        .attachmentOptions button {
          display: flex;
          align-items: center;
          gap: 12px;
          width: 100%;
          padding: 9px;
          border: 0;
          border-radius: 6px;
          background: transparent;
          text-align: left;
          font-size: 12px;
        }
        .attachmentOptions small {
          display: block;
          font-size: 9px;
          margin-top: 2px;
        }
        .attachmentOptions button:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
        .attachmentPicker button:focus-visible,
        .attachmentOptions button:focus-visible,
        .attachmentOptions button:hover:not(:disabled) {
          outline: none;
          background: #ffe69a;
        }
        .pendingFiles {
          position: absolute;
          left: 0;
          bottom: 46px;
          z-index: 70;
          width: min(
            340px,
            calc(100vw - 40px)
          );
          max-height: 300px;
          overflow: auto;
          padding: 10px;
          border: 1px solid #e7dfca;
          border-radius: 10px;
          background: #fffdf7;
          box-shadow:
            0 12px 30px rgba(0, 0, 0, 0.12);
        }
        .pendingFiles header,
        .pendingFile {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 11px;
        }
        .pendingFiles header {
          justify-content: space-between;
          margin-bottom: 8px;
        }
        .pendingFile {
          padding: 7px 0;
        }
        .pendingFile > span {
          flex: 1;
          min-width: 0;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
        .pendingFile small {
          display: block;
          margin-top: 3px;
          color: #655b40;
        }
        .pendingFiles button {
          padding: 5px;
          border: 0;
          border-radius: 5px;
          background: transparent;
          font-size: 11px;
        }
        .pickerError {
          position: absolute;
          bottom: 40px;
          left: 0;
          width: 240px;
          color: #9b2424;
          background: #fffdf7;
          font-size: 11px;
        }
      `}</style>
    </div>
  );
}
