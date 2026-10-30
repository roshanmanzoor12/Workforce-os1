import { api } from "@/lib/api/client";

import type {
  NotePublic as WorkspaceNotePublic,
} from "@/types/notes";

interface PersonalNotePublic {
  id: string;
  owner_user_id: string;
  title: string;
  content: string;
  is_pinned: boolean;
  is_archived: boolean;
  created_at: string;
  updated_at: string;
}

export type NotePublic =
  | WorkspaceNotePublic
  | PersonalNotePublic;

interface NoteListResponse {
  items: NotePublic[];
  total: number;
}

interface NoteCreateRequest {
  owner_employee_id?: string;
  title: string;
  content: string;
}

interface NoteUpdateRequest {
  title?: string;
  content?: string;
  is_pinned?: boolean;
  is_archived?: boolean;
}

function notesPath(workspaceId: string | null) {
  return workspaceId
    ? `/workspaces/${workspaceId}/notes/me`
    : "/notes/me";
}

function listMine(
  workspaceId: string | null,
  includeArchived: boolean,
) {
  return api.get<NoteListResponse>(
    notesPath(workspaceId),
    {
      query: {
        include_archived: includeArchived,
      },
    },
  );
}

function getMine(
  workspaceId: string | null,
  noteId: string,
) {
  return api.get<NotePublic>(
    `${notesPath(workspaceId)}/${noteId}`,
  );
}

function createMine(
  workspaceId: string | null,
  payload: NoteCreateRequest,
) {
  if (workspaceId) {
    if (!payload.owner_employee_id) {
      throw new Error(
        "A linked employee account is required for workspace notes.",
      );
    }

    return api.post<NotePublic>(
      notesPath(workspaceId),
      payload,
    );
  }

  // Personal ownership is resolved by backend authentication.
  return api.post<NotePublic>(
    notesPath(null),
    {
      title: payload.title,
      content: payload.content,
    },
  );
}

function updateMine(
  workspaceId: string | null,
  noteId: string,
  payload: NoteUpdateRequest,
) {
  return api.patch<NotePublic>(
    `${notesPath(workspaceId)}/${noteId}`,
    payload,
  );
}

function deleteMine(
  workspaceId: string | null,
  noteId: string,
) {
  return api.delete<void>(
    `${notesPath(workspaceId)}/${noteId}`,
  );
}

export const notesService = {
  listMine,
  getMine,
  createMine,
  updateMine,
  deleteMine,
};