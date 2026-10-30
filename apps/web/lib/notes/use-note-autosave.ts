"use client";

import {
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";

import {
  notesService,
  type NotePublic,
} from "@/services/notes-page.service";

import {
  createAutosaveQueue,
  type QueueSnapshot,
} from "@/lib/notes/autosave-queue";

type Patch = {
  title: string;
  content: string;
};

type Queue = ReturnType<
  typeof createAutosaveQueue<Patch, NotePublic>
>;

type Scope = {
  key: string;
  queue: Queue;
};

export function useNoteAutosave(options: {
  workspaceId: string | null;
  noteId: string | null;
  title: string;
  content: string;
  dirty: boolean;
  enabled: boolean;
  onSaved: (note: NotePublic) => void;
}) {
  const {
    workspaceId,
    noteId,
    title,
    content,
    dirty,
    enabled,
  } = options;

  const key = noteId
    ? `${workspaceId ?? "personal"}:${noteId}`
    : "none";

  const value: Patch = {
    title: title.trim() || "Untitled Note",
    content,
  };

  const signature = JSON.stringify(value);

  const callbacks = useRef(options);
  callbacks.current = options;

  const current = useRef<Scope | null>(null);
  const mounted = useRef(false);

  const [status, setStatus] = useState<
    QueueSnapshot & { key: string }
  >({
    key,
    saving: false,
    error: null,
  });

  if (
    !current.current ||
    current.current.key !== key
  ) {
    const scope = { key } as Scope;

    scope.queue = createAutosaveQueue<Patch, NotePublic>({
      initial: value,
      initialSignature: signature,
      acknowledged: !dirty,

      persist: async (patch) => {
        if (!noteId) {
          throw new Error(
            "Select a note before saving.",
          );
        }

        if (
          patch.title.length > 200 ||
          patch.content.length > 100000
        ) {
          throw new Error(
            "This note exceeds the title or content size limit.",
          );
        }

        return notesService.updateMine(
          workspaceId,
          noteId,
          patch,
        );
      },

      onSaved: (note) => {
        if (
          mounted.current &&
          current.current === scope
        ) {
          callbacks.current.onSaved(note);
        }
      },

      onState: (state) => {
        if (
          mounted.current &&
          current.current === scope
        ) {
          setStatus({
            key,
            ...state,
          });
        }
      },
    });

    current.current = scope;
  }

  current.current.queue.update(
    value,
    signature,
    !dirty,
  );

  useEffect(() => {
    mounted.current = true;

    return () => {
      mounted.current = false;
    };
  }, []);

  useEffect(() => {
    const scope = current.current;

    if (
      !scope ||
      scope.key !== key ||
      !noteId
    ) {
      return;
    }

    return () => {
      // Attempt to finish queued changes when leaving this note.
      void scope.queue.flush().catch(() => {});
    };
  }, [key, noteId]);

  const flush = useCallback(async () => {
    await current.current?.queue.flush();
  }, []);

  useEffect(() => {
    if (!enabled || !noteId || !dirty) return;

    const scope = current.current;

    const timer = window.setTimeout(() => {
      void scope?.queue.flush().catch(() => {});
    }, 800);

    return () => {
      window.clearTimeout(timer);
    };
  }, [
    key,
    signature,
    dirty,
    enabled,
    noteId,
  ]);

  useEffect(() => {
    if (!enabled || !noteId) return;

    const save = () => {
      void current.current?.queue.flush().catch(() => {});
    };

    const visibility = () => {
      if (document.visibilityState === "hidden") {
        save();
      }
    };

    window.addEventListener("online", save);

    document.addEventListener(
      "visibilitychange",
      visibility,
    );

    return () => {
      window.removeEventListener("online", save);

      document.removeEventListener(
        "visibilitychange",
        visibility,
      );
    };
  }, [key, enabled, noteId]);

  const state =
    status.key === key
      ? status
      : current.current.queue.snapshot();

  return {
    saving: state.saving,
    error: state.error,
    flush,
  };
}