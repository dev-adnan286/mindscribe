/** Types mirroring the FastAPI response schemas. */

export interface User {
  id: string;
  email: string;
  name: string;
  created_at: string;
}

export interface UserStats {
  notes: number;
  notebooks: number;
  tags: number;
  chat_sessions: number;
  words: number;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface AuthResponse extends TokenPair {
  user: User;
}

/** What the Next.js auth route handlers return to the browser (refresh token stays in a cookie). */
export interface ClientSession {
  access_token: string;
  expires_in: number;
  user: User;
}

export interface Notebook {
  id: string;
  owner_id: string;
  name: string;
  description: string | null;
  color: string;
  note_count: number;
  created_at: string;
  updated_at: string;
}

export interface NotebookInput {
  name: string;
  description?: string | null;
  color?: string;
}

export interface Note {
  id: string;
  owner_id: string;
  notebook_id: string | null;
  title: string;
  content: string;
  summary: string | null;
  tags: string[];
  version: number;
  has_embedding: boolean;
  created_at: string;
  updated_at: string;
}

export interface NoteSummary {
  id: string;
  notebook_id: string | null;
  title: string;
  excerpt: string;
  summary: string | null;
  tags: string[];
  version: number;
  created_at: string;
  updated_at: string;
}

export interface NoteVersion {
  id: string;
  note_id: string;
  version: number;
  title: string;
  content: string;
  summary: string | null;
  tags: string[];
  created_at: string;
}

export interface NoteCreateInput {
  title: string;
  content: string;
  notebook_id?: string | null;
  tags?: string[];
}

export interface NoteUpdateInput {
  title?: string;
  content?: string;
  notebook_id?: string | null;
  clear_notebook?: boolean;
  tags?: string[];
  summary?: string | null;
}

export type NoteSort = "updated_desc" | "updated_asc" | "created_desc" | "title_asc";

export interface NoteListParams {
  page?: number;
  page_size?: number;
  notebook_id?: string;
  tag?: string;
  q?: string;
  sort?: NoteSort;
}

export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface Tag {
  id: string;
  name: string;
  note_count: number;
}

export type SearchMode = "keyword" | "semantic" | "hybrid";

export interface SearchHit {
  note_id: string;
  title: string;
  snippet: string;
  tags: string[];
  notebook_id: string | null;
  score: number;
  updated_at: string;
}

export interface SearchResponse {
  query: string;
  mode: SearchMode;
  engine: string;
  total: number;
  hits: SearchHit[];
}

export interface SummarizeResponse {
  note_id: string | null;
  summary: string;
  provider: string;
  applied: boolean;
}

export interface TagSuggestResponse {
  note_id: string | null;
  tags: string[];
  provider: string;
  applied: boolean;
}

export interface AIStatus {
  provider: string;
  model: string;
  embedding_provider: string;
  embedding_dim: number;
}

export interface Citation {
  index: number;
  note_id: string;
  title: string;
  snippet: string;
  score: number;
}

export interface ChatMessage {
  id: string;
  session_id: string;
  role: "user" | "assistant";
  content: string;
  citations: Citation[];
  created_at: string;
}

export interface ChatSession {
  id: string;
  title: string;
  message_count: number;
  created_at: string;
  updated_at: string;
}

export interface AskResponse {
  session_id: string;
  user_message: ChatMessage;
  assistant_message: ChatMessage;
  provider: string;
}

export interface Problem {
  type: string;
  title: string;
  status: number;
  detail: string;
  instance?: string;
  errors?: { loc: string[]; msg: string; type: string }[];
}
