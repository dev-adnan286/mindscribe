"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";

import { Button } from "@/components/Button";
import { EmptyState } from "@/components/EmptyState";
import { NoteCard } from "@/components/NoteCard";
import { NoteGridSkeleton, Skeleton } from "@/components/Skeleton";
import { aiApi, authApi, notebooksApi, notesApi } from "@/lib/api";
import { useAuth } from "@/lib/auth/hooks";

function StatTile({ label, value, hint }: { label: string; value: number | string; hint?: string }) {
  return (
    <div className="card p-4">
      <p className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-1 text-2xl font-bold">{value}</p>
      {hint && <p className="text-xs text-slate-500">{hint}</p>}
    </div>
  );
}

export default function DashboardPage() {
  const { user } = useAuth();
  const stats = useQuery({ queryKey: ["stats"], queryFn: authApi.stats });
  const recent = useQuery({ queryKey: ["notes", "recent"], queryFn: () => notesApi.recent(6) });
  const notebooks = useQuery({ queryKey: ["notebooks"], queryFn: notebooksApi.list });
  const ai = useQuery({ queryKey: ["ai-status"], queryFn: aiApi.status });

  const notebookById = new Map((notebooks.data ?? []).map((nb) => [nb.id, nb]));
  const hour = new Date().getHours();
  const greeting = hour < 12 ? "Good morning" : hour < 18 ? "Good afternoon" : "Good evening";

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">
            {greeting}, {user?.name.split(" ")[0]}
          </h1>
          <p className="mt-1 text-sm text-slate-500">Here is what is happening in your knowledge base.</p>
        </div>
        <div className="flex gap-2">
          <Link href="/app/chat">
            <Button variant="secondary">Ask your notes</Button>
          </Link>
          <Link href="/app/notes/new">
            <Button>New note</Button>
          </Link>
        </div>
      </div>

      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        {stats.isLoading ? (
          Array.from({ length: 5 }, (_, i) => <Skeleton key={i} className="h-24" />)
        ) : (
          <>
            <StatTile label="Notes" value={stats.data?.notes ?? 0} />
            <StatTile label="Notebooks" value={stats.data?.notebooks ?? 0} />
            <StatTile label="Tags" value={stats.data?.tags ?? 0} />
            <StatTile label="Words written" value={(stats.data?.words ?? 0).toLocaleString()} />
            <StatTile label="Chats" value={stats.data?.chat_sessions ?? 0} hint={ai.data ? `${ai.data.provider} provider` : undefined} />
          </>
        )}
      </section>

      <section>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-lg font-semibold">Recent notes</h2>
          <Link href="/app/notes" className="text-sm text-brand-600 hover:underline dark:text-brand-400">
            View all
          </Link>
        </div>
        {recent.isLoading ? (
          <NoteGridSkeleton count={3} />
        ) : recent.data && recent.data.length > 0 ? (
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
            {recent.data.map((note) => {
              const nb = note.notebook_id ? notebookById.get(note.notebook_id) : undefined;
              return <NoteCard key={note.id} note={note} notebookName={nb?.name} notebookColor={nb?.color} />;
            })}
          </div>
        ) : (
          <EmptyState
            title="No notes yet"
            description="Create your first note and MindScribe will summarise, tag and index it automatically."
            action={
              <Link href="/app/notes/new">
                <Button>Write a note</Button>
              </Link>
            }
          />
        )}
      </section>

      {notebooks.data && notebooks.data.length > 0 && (
        <section>
          <h2 className="mb-3 text-lg font-semibold">Notebooks</h2>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {notebooks.data.map((notebook) => (
              <Link key={notebook.id} href={`/app/notes?notebook_id=${notebook.id}`} className="card p-4 transition hover:shadow-md">
                <div className="flex items-center gap-2">
                  <span className="h-3 w-3 rounded-full" style={{ backgroundColor: notebook.color }} aria-hidden="true" />
                  <span className="truncate font-medium">{notebook.name}</span>
                </div>
                <p className="mt-1 text-xs text-slate-500">
                  {notebook.note_count} {notebook.note_count === 1 ? "note" : "notes"}
                </p>
              </Link>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
