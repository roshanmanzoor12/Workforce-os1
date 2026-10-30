"use client";

import {
  useEffect,
  useRef,
  useState,
} from "react";

import { Link2, X } from "lucide-react";

import {
  normalizeNoteLink,
} from "@/lib/notes/export-note";

interface NoteLinkDialogProps {
  initialURL: string;
  selectedText: string;
  onApply: (url: string) => void;
  onCancel: () => void;
}

export function NoteLinkDialog({
  initialURL,
  selectedText,
  onApply,
  onCancel,
}: NoteLinkDialogProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const [url, setURL] = useState(initialURL);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!dialogRef.current?.open) {
      dialogRef.current?.showModal();
    }

    inputRef.current?.focus({
      preventScroll: true,
    });

    inputRef.current?.select();
  }, []);

  return (
    <dialog
      ref={dialogRef}
      className="wn-link-dialog"
      aria-labelledby="wn-link-title"
      onCancel={(event) => {
        event.preventDefault();
        onCancel();
      }}
      onClick={(event) => {
        if (event.target !== dialogRef.current) return;

        const rect =
          dialogRef.current.getBoundingClientRect();

        if (
          event.clientX < rect.left ||
          event.clientX > rect.right ||
          event.clientY < rect.top ||
          event.clientY > rect.bottom
        ) {
          onCancel();
        }
      }}
    >
      <form
        onSubmit={(event) => {
          event.preventDefault();

          try {
            const normalized = normalizeNoteLink(url);

            dialogRef.current?.close();
            onApply(normalized);
          } catch (cause) {
            setError(
              cause instanceof Error
                ? cause.message
                : "Enter a valid link.",
            );
          }
        }}
      >
        <header>
          <h2 id="wn-link-title">
            <Link2 size={18} />
            Add link
          </h2>

          <button
            type="button"
            aria-label="Close link dialog"
            onClick={onCancel}
          >
            <X size={18} />
          </button>
        </header>

        <p className="wn-link-selection">
          {selectedText
            ? `Selected text: ${selectedText}`
            : "The link will be inserted at the cursor."}
        </p>

        <label htmlFor="wn-link-url">
          Website or URL
        </label>

        <input
          ref={inputRef}
          id="wn-link-url"
          type="text"
          inputMode="url"
          autoComplete="url"
          autoCapitalize="none"
          spellCheck={false}
          placeholder="clickronix.com or https://example.com"
          value={url}
          onChange={(event) => {
            setURL(event.target.value);
            setError(null);
          }}
        />

        {error && (
          <p className="wn-link-error" role="alert">
            {error}
          </p>
        )}

        <footer>
          <button
            type="button"
            onClick={onCancel}
          >
            Cancel
          </button>

          <button
            type="submit"
            className="wn-link-done"
          >
            Done
          </button>
        </footer>
      </form>

      <style jsx>{`
        .wn-link-dialog {
          width: min(440px, calc(100vw - 28px));
          max-width: calc(100vw - 28px);
          max-height: calc(100dvh - 32px);
          margin: auto;
          padding: 0;
          overflow: auto;
          border: 0;
          border-radius: 14px;
          outline: none;
          color: #222638;
          background: #fffefa;
          box-shadow: 0 18px 60px rgb(24 24 36 / 20%);
          font-family: inherit;
        }

        .wn-link-dialog::backdrop {
          background: rgb(22 24 35 / 35%);
        }

        form {
          padding: 20px;
        }

        header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 14px;
        }

        h2 {
          display: flex;
          align-items: center;
          gap: 8px;
          margin: 0;
          font-size: 17px;
          font-weight: 600;
        }

        header button {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 32px;
          height: 32px;
          border: 0;
          border-radius: 6px;
          color: #60677b;
          background: transparent;
          cursor: pointer;
        }

        .wn-link-selection {
          max-height: 80px;
          margin: 12px 0 16px;
          overflow: auto;
          color: #686f80;
          font-size: 12px;
          overflow-wrap: anywhere;
        }

        label {
          display: block;
          margin-bottom: 7px;
          font-size: 12px;
          font-weight: 500;
        }

        input {
          display: block;
          box-sizing: border-box;
          width: 100%;
          height: 42px;
          padding: 0 11px;
          border: 1px solid #ddd7c9;
          border-radius: 8px;
          outline: none !important;
          box-shadow: none !important;
          color: #282c40;
          background: #ffffff;
          font: inherit;
          font-size: 14px;
        }

        input:focus {
          border-color: #bba361;
        }

        .wn-link-error {
          margin: 8px 0 0;
          color: #b2362c;
          font-size: 12px;
        }

        footer {
          display: flex;
          justify-content: flex-end;
          gap: 8px;
          margin-top: 20px;
        }

        footer button {
          min-height: 36px;
          padding: 8px 15px;
          border: 1px solid #ddd7c9;
          border-radius: 7px;
          color: #454c60;
          background: #fffefa;
          font: inherit;
          font-size: 12px;
          cursor: pointer;
        }

        footer .wn-link-done {
          border-color: #25252c;
          color: #ffffff;
          background: #25252c;
        }

        button:focus-visible {
          outline: none;
          background: #eae4d5;
        }

        .wn-link-done:focus-visible {
          background: #08080c;
        }

        @media (max-width: 600px) {
          form {
            padding: 17px;
          }

          input {
            font-size: 16px;
          }

          footer button,
          header button {
            min-width: 44px;
            min-height: 44px;
          }
        }
      `}</style>
    </dialog>
  );
}