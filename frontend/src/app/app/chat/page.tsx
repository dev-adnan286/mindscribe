"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";

import { Button } from "@/components/Button";
import { ChatInput } from "@/components/ChatInput";
import { ChatMessageList, type DisplayMessage } from "@/components/ChatMessageList";
import { EmptyState } from "@/components/EmptyState";
import { LineSkeleton } from "@/components/Skeleton";
import { useToast } from "@/components/Toast";
import { ApiError, aiApi, notebooksApi, type ChatMessage } from "@/lib/api";
import { cn, timeAgo } from "@/lib/utils";

const REVEAL_INTERVAL_MS = 18;
const REVEAL_CHUNK_WORDS = 2;

const SUGGESTIONS = [
  "What did I write about recently?",
  "Summarise my notes on architecture",
  "What are my open action items?",
];

export default function ChatPage() {
  const queryClient = useQueryClient();
  const toast = useToast();
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [notebookId, setNotebookId] = useState("");
  const [messages, setMessages] = useState<DisplayMessage[]>([]);
  const revealTimer = useRef<ReturnType<typeof setInterval> | null>(null);

  const sessions = useQuery({ queryKey: ["chat-sessions"], queryFn: aiApi.sessions });
  const notebooks = useQuery({ queryKey: ["notebooks"], queryFn: notebooksApi.list });
  const history = useQuery({
    queryKey: ["chat-messages", sessionId],
    queryFn: () => aiApi.messages(sessionId!),
    enabled: Boolean(sessionId),
  });

  useEffect(() => {
    if (history.data) setMessages(history.data);
  }, [history.data]);

  useEffect(
    () => () => {
      if (revealTimer.current) clearInterval(revealTimer.current);
    },
    [],
  );

  /** Reveal the assistant reply word-by-word so long answers feel responsive. */
  const revealAssistant = (message: ChatMessage) => {
    const words = message.content.split(/(\s+)/);
    let index = 0;
    setMessages((current) => [...current, { ...message, content: "", streaming: true }]);
    revealTimer.current = setInterval(() => {
      index = Math.min(words.length, index + REVEAL_CHUNK_WORDS * 2);
      const partial = words.slice(0, index).join("");
      const done = index >= words.length;
      setMessages((current) =>
        current.map((m) => (m.id === message.id ? { ...m, content: done ? message.content : partial, streaming: !done } : m)),
      );
      if (done && revealTimer.current) {
        clearInterval(revealTimer.current);
        revealTimer.current = null;
      }
    }, REVEAL_INTERVAL_MS);
  };

  const ask = useMutation({
    mutationFn: (question: string) =>
      aiApi.ask({ question, session_id: sessionId ?? undefined, notebook_id: notebookId || undefined, top_k: 5 }),
    onMutate: (question) => {
      const optimistic: DisplayMessage = {
        id: `pending-${Date.now()}`,
        session_id: sessionId ?? "",
        role: "user",
        content: question,
        citations: [],
        created_at: new Date().toISOString(),
      };
      setMessages((current) => [...current, optimistic]);
      return { optimisticId: optimistic.id };
    },
    onSuccess: (result, _question, context) => {
      setMessages((current) => current.map((m) => (m.id === context?.optimisticId ? result.user_message : m)));
      if (!sessionId) setSessionId(result.session_id);
      revealAssistant(result.assistant_message);
      void queryClient.invalidateQueries({ queryKey: ["chat-sessions"] });
      void queryClient.invalidateQueries({ queryKey: ["stats"] });
    },
    onError: (error, _question, context) => {
      setMessages((current) => current.filter((m) => m.id !== context?.optimisticId));
      toast.error("The assistant could not answer", error instanceof ApiError ? error.message : undefined);
    },
  });

  const deleteSession = useMutation({
    mutationFn: (id: string) => aiApi.deleteSession(id),
    onSuccess: (_result, id) => {
      void queryClient.invalidateQueries({ queryKey: ["chat-sessions"] });
      if (id === sessionId) startNew();
    },
  });

  const startNew = () => {
    setSessionId(null);
    setMessages([]);
  };

  return (
    <div className="grid gap-6 lg:grid-cols-[260px_1fr]">
      <aside className="space-y-3">
        <Button variant="secondary" className="w-full" onClick={startNew}>
          + New conversation
        </Button>
        <div>
          <label htmlFor="scope" className="block text-xs font-medium uppercase tracking-wide text-slate-500">
            Scope
          </label>
          <select id="scope" value={notebookId} onChange={(e) => setNotebookId(e.target.value)} className="input mt-1">
            <option value="">All notebooks</option>
            {notebooks.data?.map((nb) => (
              <option key={nb.id} value={nb.id}>
                {nb.name}
              </option>
            ))}
          </select>
        </div>
        <div>
          <h2 className="mb-1 text-xs font-medium uppercase tracking-wide text-slate-500">Conversations</h2>
          <ul className="max-h-[50vh] space-y-1 overflow-y-auto">
            {sessions.data?.map((session) => (
              <li key={session.id} className="group flex items-center gap-1">
                <button
                  type="button"
                  onClick={() => setSessionId(session.id)}
                  className={cn(
                    "flex-1 truncate rounded-lg px-3 py-2 text-left text-sm",
                    session.id === sessionId
                      ? "bg-brand-50 text-brand-700 dark:bg-brand-900/40 dark:text-brand-100"
                      : "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800",
                  )}
                >
                  <span className="block truncate">{session.title}</span>
                  <span className="block text-xs text-slate-400">
                    {session.message_count} messages · {timeAgo(session.updated_at)}
                  </span>
                </button>
                <button
                  type="button"
                  onClick={() => deleteSession.mutate(session.id)}
                  className="rounded p-1 text-xs text-slate-400 opacity-0 hover:text-red-600 group-hover:opacity-100 focus:opacity-100"
                  aria-label={`Delete conversation ${session.title}`}
                >
                  x
                </button>
              </li>
            ))}
            {sessions.data?.length === 0 && <li className="px-3 text-xs text-slate-400">No conversations yet</li>}
          </ul>
        </div>
      </aside>

      <section className="flex min-h-[70vh] flex-col">
        <div className="flex-1 overflow-y-auto pb-4">
          {history.isLoading ? (
            <LineSkeleton lines={5} />
          ) : messages.length === 0 ? (
            <EmptyState
              title="Chat with your notes"
              description="Ask a question and the assistant answers from your own notes, citing its sources."
              icon="✉"
              action={
                <div className="flex flex-wrap justify-center gap-2">
                  {SUGGESTIONS.map((suggestion) => (
                    <Button key={suggestion} variant="secondary" size="sm" onClick={() => ask.mutate(suggestion)}>
                      {suggestion}
                    </Button>
                  ))}
                </div>
              }
            />
          ) : (
            <ChatMessageList messages={messages} pending={ask.isPending} />
          )}
        </div>
        <ChatInput onSend={(question) => ask.mutateAsync(question).then(() => undefined, () => undefined)} disabled={ask.isPending} />
      </section>
    </div>
  );
}
