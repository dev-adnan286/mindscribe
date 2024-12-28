"use client";

import { keepPreviousData, useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { Suspense, useCallback } from "react";

import { Badge } from "@/components/Badge";
import { Button } from "@/components/Button";
import { EmptyState } from "@/components/EmptyState";
import { NoteCard } from "@/components/NoteCard";
import { Pagination } from "@/components/Pagination";
import { SearchBar } from "@/components/SearchBar";
import { NoteGridSkeleton } from "@/components/Skeleton";
import { notebooksApi, notesApi, type NoteSort } from "@/lib/api";

const SORTS: { value: NoteSort; label: string }[] = [
  { value: "updated_desc", label: "Recently updated" },
  { value: "created_desc", label: "Newest" },
  { value: "title_asc", label: "Title A-Z" },
  { value: "updated_asc", label: "Oldest updated" },
];

function NotesList() {
  const router = useRouter();
  const pathname = usePathname();
  const params = useSearchParams();

  const page = Math.max(1, Number(params.get("page") ?? 1));
  const q = params.get("q") ?? "";
  const tag = params.get("tag") ?? undefined;
  const notebookId = params.get("notebook_id") ?? undefined;
  const sort = (params.get("sort") as NoteSort | null) ?? "updated_desc";

  const setParams = useCallback(
    (changes: Record<string, string | undefined>) => {
      const next = new URLSearchParams(params.toString());
      for (const [key, value] of Object.entries(changes)) {
        if (value) next.set(key, value);
        else next.delete(key);
      }
      if (!("page" in changes)) next.delete("page");
      router.push(`${pathname}?${next.toString()}`);
    },
    [params, pathname, router],
  );

  const notes = useQuery({
    queryKey: ["notes", { page, q, tag, notebookId, sort }],
    queryFn: () => notesApi.list({ page, page_size: 12, q: q || undefined, tag, notebook_id: notebookId, sort }),
    placeholderData: keepPreviousData,
  });
  const notebooks = useQuery({ queryKey: ["notebooks"], queryFn: notebooksApi.list });
  const notebookById = new Map((notebooks.data ?? []).map((nb) => [nb.id, nb]));
  const activeNotebook = notebookId ? notebookById.get(notebookId) : undefined;

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold">{activeNotebook ? activeNotebook.name : "All notes"}</h1>
          <p className="text-sm text-slate-500">
            {notes.data ? `${notes.data.total} ${notes.data.total === 1 ? "note" : "notes"}` : "Loading..."}
          </p>
        </div>
        <Link href={`/app/notes/new${notebookId ? `?notebook_id=${notebookId}` : ""}`}>
          <Button>New note</Button>
        </Link>
      </div>

      <div className="flex flex-col gap-3 md:flex-row md:items-center">
        <SearchBar value={q} onSearch={(value) => setParams({ q: value || undefined })} className="flex-1" />
        <select
          value={sort}
          onChange={(event) => setParams({ sort: event.target.value })}
          className="input md:w-48"
          aria-label="Sort notes"
        >
          {SORTS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>

      {(tag || notebookId || q) && (
        <div className="flex flex-wrap items-center gap-2 text-sm">
          <span className="text-slate-500">Filters:</span>
          {notebookId && (
            <button type="button" onClick={() => setParams({ notebook_id: undefined })}>
              <Badge tone="brand">Notebook: {activeNotebook?.name ?? "..."} x</Badge>
            </button>
          )}
          {tag && (
            <button type="button" onClick={() => setParams({ tag: undefined })}>
              <Badge tone="brand">#{tag} x</Badge>
            </button>
          )}
          {q && (
            <button type="button" onClick={() => setParams({ q: undefined })}>
              <Badge tone="brand">&quot;{q}&quot; x</Badge>
            </button>
          )}
        </div>
      )}

      {notes.isLoading ? (
        <NoteGridSkeleton />
      ) : notes.isError ? (
        <EmptyState title="Could not load notes" description="Check that the API is running and try again." icon="!" />
      ) : notes.data && notes.data.items.length > 0 ? (
        <>
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
            {notes.data.items.map((note) => {
              const nb = note.notebook_id ? notebookById.get(note.notebook_id) : undefined;
              return (
                <NoteCard
                  key={note.id}
                  note={note}
                  notebookName={nb?.name}
                  notebookColor={nb?.color}
                  onTagClick={(value) => setParams({ tag: value })}
                />
              );
            })}
          </div>
          <Pagination page={notes.data.page} pages={notes.data.pages} total={notes.data.total} onChange={(p) => setParams({ page: String(p) })} />
        </>
      ) : (
        <EmptyState
          title={q || tag || notebookId ? "No notes match these filters" : "No notes yet"}
          description={q || tag || notebookId ? "Try clearing a filter or searching for something else." : "Create your first note to get started."}
          action={
            <Link href="/app/notes/new">
              <Button>Write a note</Button>
            </Link>
          }
        />
      )}
    </div>
  );
}

export default function NotesPage() {
  return (
    <Suspense fallback={<NoteGridSkeleton />}>
      <NotesList />
    </Suspense>
  );
}
