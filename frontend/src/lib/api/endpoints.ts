import { api } from "./client";
import type {
  AIStatus,
  AskResponse,
  ChatMessage,
  ChatSession,
  ClientSession,
  Note,
  NoteCreateInput,
  NoteListParams,
  NoteSummary,
  NoteUpdateInput,
  NoteVersion,
  Notebook,
  NotebookInput,
  Page,
  SearchMode,
  SearchResponse,
  SummarizeResponse,
  Tag,
  TagSuggestResponse,
  User,
  UserStats,
} from "./types";

/** Same-origin calls to the Next.js auth route handlers (they own the refresh cookie). */
async function sessionRequest(path: string, body?: unknown): Promise<ClientSession> {
  const response = await fetch(`/api/auth/${path}`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const data = (await response.json().catch(() => null)) as (ClientSession & { detail?: string }) | null;
  if (!response.ok) {
    const { ApiError } = await import("./client");
    throw new ApiError(response.status, data?.detail ?? "Authentication failed", data as never);
  }
  return data as ClientSession;
}

export const authApi = {
  login: (email: string, password: string) => sessionRequest("login", { email, password }),
  register: (email: string, password: string, name: string) => sessionRequest("register", { email, password, name }),
  logout: async (): Promise<void> => {
    await fetch("/api/auth/logout", { method: "POST", credentials: "include" });
  },
  me: () => api.get<User>("/auth/me"),
  updateMe: (data: { name?: string; current_password?: string; new_password?: string }) =>
    api.patch<User>("/auth/me", data),
  stats: () => api.get<UserStats>("/auth/me/stats"),
};

export const notebooksApi = {
  list: () => api.get<Notebook[]>("/notebooks"),
  get: (id: string) => api.get<Notebook>(`/notebooks/${id}`),
  create: (data: NotebookInput) => api.post<Notebook>("/notebooks", data),
  update: (id: string, data: Partial<NotebookInput>) => api.patch<Notebook>(`/notebooks/${id}`, data),
  remove: (id: string) => api.delete(`/notebooks/${id}`),
};

export const notesApi = {
  list: (params: NoteListParams = {}) => api.get<Page<NoteSummary>>("/notes", { ...params }),
  recent: (limit = 6) => api.get<NoteSummary[]>("/notes/recent", { limit }),
  get: (id: string) => api.get<Note>(`/notes/${id}`),
  create: (data: NoteCreateInput) => api.post<Note>("/notes", data),
  update: (id: string, data: NoteUpdateInput) => api.patch<Note>(`/notes/${id}`, data),
  remove: (id: string) => api.delete(`/notes/${id}`),
  versions: (id: string) => api.get<NoteVersion[]>(`/notes/${id}/versions`),
  restore: (id: string, version: number) => api.post<Note>(`/notes/${id}/versions/${version}/restore`),
};

export const tagsApi = {
  list: () => api.get<Tag[]>("/tags"),
};

export const searchApi = {
  search: (q: string, mode: SearchMode, limit = 10) => api.get<SearchResponse>("/search", { q, mode, limit }),
};

export const aiApi = {
  status: () => api.get<AIStatus>("/ai/status"),
  summarize: (data: { note_id?: string; content?: string; apply?: boolean; max_sentences?: number }) =>
    api.post<SummarizeResponse>("/ai/summarize", data),
  suggestTags: (data: { note_id?: string; content?: string; apply?: boolean; max_tags?: number }) =>
    api.post<TagSuggestResponse>("/ai/tags", data),
  ask: (data: { question: string; session_id?: string; notebook_id?: string; top_k?: number }) =>
    api.post<AskResponse>("/ai/ask", data),
  sessions: () => api.get<ChatSession[]>("/ai/sessions"),
  messages: (sessionId: string) => api.get<ChatMessage[]>(`/ai/sessions/${sessionId}/messages`),
  deleteSession: (sessionId: string) => api.delete(`/ai/sessions/${sessionId}`),
};
