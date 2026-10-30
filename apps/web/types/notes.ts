export interface NotePublic {
  id: string;

  owner_employee_id: string;

  title: string;

  content: string;

  is_pinned: boolean;

  is_archived: boolean;

  created_at: string;

  updated_at: string;
}


export interface NoteListResponse {
  items: NotePublic[];

  total: number;
}


export interface NoteCreateRequest {
  owner_employee_id: string;

  title: string;

  content?: string;
}


export interface NoteUpdateRequest {
  title?: string | null;

  content?: string | null;

  is_pinned?: boolean | null;

  is_archived?: boolean | null;
}