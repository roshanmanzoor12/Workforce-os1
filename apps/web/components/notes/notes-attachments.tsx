"use client";

import {
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";

import {
  Download,
  FileText,
  LoaderCircle,
  Paperclip,
  Plus,
  RefreshCcw,
  X,
} from "lucide-react";

import {
  listNoteAttachments,
  noteAttachmentDownload,
  removeNoteAttachment,
  uploadNoteAttachment,
  type NoteAttachment,
} from "@/services/notes-attachments.service";

interface NotesAttachmentsProps {
  noteId: string;
  workspaceId: string | null;
}

function formatBytes(value: number) {
  if (value >= 1048576) {
    return `${(value / 1048576).toFixed(1)} MB`;
  }

  if (value >= 1024) {
    return `${(value / 1024).toFixed(1)} KB`;
  }

  return `${value} B`;
}

function errorMessage(error: unknown) {
  return error instanceof Error
    ? error.message
    : "The attachment action failed.";
}

export function NotesAttachments({
  noteId,
  workspaceId,
}: NotesAttachmentsProps) {
  const [items, setItems] = useState<NoteAttachment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activity, setActivity] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);

  const inputRef = useRef<HTMLInputElement>(null);
  const alive = useRef(false);
  const sequence = useRef(0);
  const locked = useRef(false);
  const controller = useRef<AbortController | null>(null);

  useEffect(() => {
    alive.current = true;

    return () => {
      alive.current = false;
      sequence.current += 1;
      controller.current?.abort();
    };
  }, []);

  const load = useCallback(async () => {
    if (workspaceId) {
      setLoading(false);
      return;
    }

    const requestId = ++sequence.current;
    setLoading(true);

    try {
      const result = await listNoteAttachments(noteId);

      if (
        alive.current &&
        requestId === sequence.current
      ) {
        setItems(result.items);
      }
    } catch (cause) {
      if (
        alive.current &&
        requestId === sequence.current
      ) {
        setError(errorMessage(cause));
      }
    } finally {
      if (
        alive.current &&
        requestId === sequence.current
      ) {
        setLoading(false);
      }
    }
  }, [noteId, workspaceId]);

  useEffect(() => {
    void load();
  }, [load]);

  async function upload(files: File[]) {
    if (
      locked.current ||
      workspaceId ||
      !files.length
    ) {
      return;
    }

    locked.current = true;

    const abort = new AbortController();
    controller.current = abort;

    setError(null);

    try {
      for (const file of files) {
        if (abort.signal.aborted) break;

        if (alive.current) {
          setActivity(`Uploading ${file.name}`);
          setProgress(0);
        }

        await uploadNoteAttachment(
          noteId,
          file,
          abort.signal,
          (percent) => {
            if (alive.current) {
              setProgress(percent);
            }
          },
        );
      }
    } catch (cause) {
      if (alive.current) {
        setError(errorMessage(cause));
      }
    } finally {
      locked.current = false;
      controller.current = null;

      if (alive.current) {
        setActivity(null);
        await load();
      }
    }
  }

  async function remove(item: NoteAttachment) {
    if (locked.current) return;

    if (
      !window.confirm(
        `Remove "${item.original_filename}" permanently?`,
      )
    ) {
      return;
    }

    locked.current = true;
    setActivity("Removing attachment");
    setError(null);

    try {
      await removeNoteAttachment(item.id);

      if (alive.current) {
        setItems((current) => {
          return current.filter(
            (entry) => entry.id !== item.id,
          );
        });
      }
    } catch (cause) {
      if (alive.current) {
        setError(errorMessage(cause));
      }
    } finally {
      locked.current = false;

      if (alive.current) {
        setActivity(null);
      }
    }
  }

  async function download(item: NoteAttachment) {
    if (locked.current) return;

    locked.current = true;
    setActivity("Preparing download");
    setError(null);

    // Open synchronously from the click to avoid losing
    // the browser's user-activation permission.
    const tab = window.open(
      "about:blank",
      "_blank",
    );

    if (tab) tab.opener = null;

    try {
      const url = await noteAttachmentDownload(item.id);

      if (!alive.current) {
        tab?.close();
        return;
      }

      if (tab) {
        tab.location.href = url;
      } else {
        window.location.assign(url);
      }
    } catch (cause) {
      tab?.close();

      if (alive.current) {
        setError(errorMessage(cause));
      }
    } finally {
      locked.current = false;

      if (alive.current) {
        setActivity(null);
      }
    }
  }

  return (
    <section
      className="wna-section"
      aria-label="Note attachments"
    >
      <div className="wna-heading">
        <span>
          <Paperclip size={14} />
          Attachments
          {items.length ? ` (${items.length})` : ""}
        </span>

        {!workspaceId && (
          <button
            type="button"
            title="Refresh attachments"
            aria-label="Refresh attachments"
            disabled={Boolean(activity) || loading}
            onClick={() => {
              setError(null);
              void load();
            }}
          >
            <RefreshCcw size={13} />
          </button>
        )}
      </div>

      {workspaceId ? (
        <p className="wna-muted">
          These uploads support Personal Notes.
          Workspace note attachments need a separate
          destination connection.
        </p>
      ) : (
        <>
          <input
            ref={inputRef}
            type="file"
            multiple
            hidden
            onChange={(event) => {
              const files = Array.from(
                event.target.files ?? [],
              );

              event.target.value = "";
              void upload(files);
            }}
          />

          {error && (
            <p
              className="wna-error"
              role="alert"
            >
              {error}
            </p>
          )}

          <div className="wna-grid">
            {items.map((item) => (
              <div
                key={item.id}
                className="wna-file"
              >
                <span
                  className={
                    item.content_type === "application/pdf"
                      ? "wna-file-icon is-pdf"
                      : "wna-file-icon"
                  }
                >
                  <FileText size={19} />
                </span>

                <button
                  type="button"
                  className="wna-file-name"
                  title={`Download ${item.original_filename}`}
                  disabled={Boolean(activity)}
                  onClick={() => void download(item)}
                >
                  <strong>
                    {item.original_filename}
                  </strong>

                  <small>
                    {formatBytes(item.size_bytes)}
                  </small>
                </button>

                <button
                  type="button"
                  className="wna-icon"
                  aria-label={`Download ${item.original_filename}`}
                  disabled={Boolean(activity)}
                  onClick={() => void download(item)}
                >
                  <Download size={14} />
                </button>

                <button
                  type="button"
                  className="wna-icon"
                  aria-label={`Remove ${item.original_filename}`}
                  disabled={Boolean(activity)}
                  onClick={() => void remove(item)}
                >
                  <X size={15} />
                </button>
              </div>
            ))}

            <button
              type="button"
              className="wna-add"
              disabled={
                Boolean(activity) ||
                loading ||
                items.length >= 20
              }
              onClick={() => {
                inputRef.current?.click();
              }}
            >
              {loading ? (
                <LoaderCircle
                  size={16}
                  className="wn-spin"
                />
              ) : (
                <Plus size={17} />
              )}

              {loading
                ? "Loading attachments"
                : "Add attachment"}
            </button>
          </div>

          {activity && (
            <div
              className="wna-status"
              role="status"
            >
              <LoaderCircle
                size={13}
                className="wn-spin"
              />

              <span>
                {activity}
                {controller.current
                  ? ` · ${progress}%`
                  : ""}
              </span>

              {controller.current && (
                <button
                  type="button"
                  onClick={() => {
                    controller.current?.abort();
                  }}
                >
                  Cancel
                </button>
              )}
            </div>
          )}
        </>
      )}

      <style jsx>{`
        .wna-section {
          margin-top: 6px;
          padding-top: 13px;
          border-top: 1px solid #e5e1da;
        }

        .wna-heading {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 8px;
          margin-bottom: 8px;
          color: #272a3c;
          font-size: 12px;
        }

        .wna-heading > span {
          display: flex;
          align-items: center;
          gap: 7px;
        }

        .wna-heading > button,
        .wna-icon {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
          width: 24px;
          height: 26px;
          padding: 0;
          border: 0;
          border-radius: 5px;
          color: #626679;
          background: transparent;
        }

        .wna-grid {
          display: grid;
          grid-template-columns: repeat(
            auto-fit,
            minmax(min(100%, 220px), 1fr)
          );
          gap: 8px;
        }

        .wna-file {
          display: flex;
          align-items: center;
          gap: 7px;
          min-width: 0;
          min-height: 50px;
          padding: 7px 8px;
          border: 1px solid #dfdcd6;
          border-radius: 8px;
          background: #fffefd;
        }

        .wna-file-icon {
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
          width: 27px;
          height: 31px;
          border-radius: 4px;
          color: #4a6686;
          background: #eaf0f7;
        }

        .wna-file-icon.is-pdf {
          color: #ffffff;
          background: #cf3027;
        }

        .wna-file-name {
          display: flex;
          flex: 1;
          flex-direction: column;
          align-items: flex-start;
          justify-content: center;
          gap: 2px;
          min-width: 0;
          padding: 0;
          border: 0;
          color: #24273d;
          background: transparent;
          text-align: left;
        }

        .wna-file-name strong {
          display: block;
          max-width: 100%;
          overflow: hidden;
          font-size: 12px;
          font-weight: 500;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .wna-file-name small {
          color: #686d80;
          font-size: 11px;
        }

        .wna-add {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 9px;
          min-height: 50px;
          padding: 9px 12px;
          border: 1px dashed #dcd8d0;
          border-radius: 8px;
          color: #62687b;
          background: #fffefd;
          font-size: 12px;
        }

        .wna-add:hover:not(:disabled),
        .wna-icon:hover:not(:disabled) {
          background: #f7f2e7;
        }

        .wna-error {
          margin: 0 0 9px;
          padding: 8px;
          border-radius: 6px;
          color: #ac352a;
          background: #fff1ef;
          font-size: 11px;
          overflow-wrap: anywhere;
        }

        .wna-muted {
          margin: 0;
          color: #727181;
          font-size: 11px;
          line-height: 1.5;
        }

        .wna-status {
          display: flex;
          align-items: center;
          gap: 7px;
          margin-top: 8px;
          color: #666a7b;
          font-size: 11px;
        }

        .wna-status > span {
          min-width: 0;
          overflow-wrap: anywhere;
        }

        .wna-status > button {
          margin-left: auto;
          padding: 3px 6px;
          border: 0;
          color: #805d18;
          background: transparent;
          font-size: 11px;
        }

        button:focus-visible {
          outline: 2px solid #a77800;
          outline-offset: 3px;
        }

        button:disabled {
          cursor: not-allowed;
          opacity: 0.55;
        }
      `}</style>
    </section>
  );
}