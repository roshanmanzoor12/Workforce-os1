import {
  api,
} from "@/lib/api/client";

import type {
  NoteCreateRequest,
  NoteListResponse,
  NotePublic,
  NoteUpdateRequest,
} from "@/types/notes";


async function listMine(
  workspaceId: string,
  includeArchived = false,
): Promise<NoteListResponse> {
  return api.get<NoteListResponse>(
    `/workspaces/${workspaceId}/notes/me`,
    {
      query: {
        include_archived:
          includeArchived,
      },
    },
  );
}


async function createMine(
  workspaceId: string,
  payload: NoteCreateRequest,
): Promise<NotePublic> {
  return api.post<NotePublic>(
    `/workspaces/${workspaceId}/notes/me`,
    payload,
  );
}


async function getMine(
  workspaceId: string,
  noteId: string,
): Promise<NotePublic> {
  return api.get<NotePublic>(
    `/workspaces/${workspaceId}/notes/me/${noteId}`,
  );
}


async function updateMine(
  workspaceId: string,
  noteId: string,
  payload: NoteUpdateRequest,
): Promise<NotePublic> {
  return api.patch<NotePublic>(
    `/workspaces/${workspaceId}/notes/me/${noteId}`,
    payload,
  );
}


async function deleteMine(
  workspaceId: string,
  noteId: string,
): Promise<void> {
  await api.delete<void>(
    `/workspaces/${workspaceId}/notes/me/${noteId}`,
  );
}


async function listEmployee(
  workspaceId: string,
  employeeId: string,
  includeArchived = false,
): Promise<NoteListResponse> {
  return api.get<NoteListResponse>(
    `/workspaces/${workspaceId}/notes/employee/${employeeId}`,
    {
      query: {
        include_archived:
          includeArchived,
      },
    },
  );
}


export const notesService = {
  listMine,

  createMine,

  getMine,

  updateMine,

  deleteMine,

  listEmployee,
};