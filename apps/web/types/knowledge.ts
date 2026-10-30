export type KnowledgeCategory =
  | "general"
  | "process"
  | "reference"
  | "learning";


export type KnowledgeStatus =
  | "draft"
  | "published"
  | "archived";


export type KnowledgeVisibility =
  | "private"
  | "workspace";


export interface KnowledgePublic {
  id: string;

  owner_employee_id: string;

  title: string;

  content: string;

  category: KnowledgeCategory;

  status: KnowledgeStatus;

  visibility: KnowledgeVisibility;

  created_at: string;

  updated_at: string;
}


export interface KnowledgeListResponse {
  items: KnowledgePublic[];

  total: number;
}


export interface KnowledgeCreateRequest {
  owner_employee_id: string;

  title: string;

  content?: string;

  category?: KnowledgeCategory;

  visibility?: KnowledgeVisibility;
}


export interface KnowledgeUpdateRequest {
  title?: string | null;

  content?: string | null;

  category?: KnowledgeCategory | null;

  status?: KnowledgeStatus | null;

  visibility?: KnowledgeVisibility | null;
}