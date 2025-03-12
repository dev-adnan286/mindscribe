import Link from "next/link";

import type { NoteSummary } from "@/lib/api";
import { timeAgo } from "@/lib/utils";

import { Badge } from "./Badge";

export interface NoteCardProps {
  note: NoteSummary;
  notebookName?: string;
  notebookColor?: string;
  onTagClick?: (tag: string) => void;
}

export function NoteCard({ note, notebookName, notebookColor, onTagClick }: NoteCardProps) {
  const visibleTags = note.tags.slice(0, 4);
  const hiddenCount = note.tags.length - visibleTags.length;

  return (
    <article className="card group flex h-full flex-col p-4 transition hover:-translate-y-0.5 hover:shadow-md" data-testid="note-card">
      <Link href={`/app/notes/${note.id}`} className="block flex-1">
        <h3 className="line-clamp-2 text-base font-semibold text-slate-900 group-hover:text-brand-700 dark:text-slate-100 dark:group-hover:text-brand-300">
          {note.title}
        </h3>
        <p className="mt-2 line-clamp-3 text-sm text-slate-600 dark:text-slate-400">
          {note.summary ?? note.excerpt ?? "No content yet."}
        </p>
      </Link>
      <div className="mt-3 flex flex-wrap items-center gap-1.5">
        {visibleTags.map((tag) =>
          onTagClick ? (
            <button key={tag} type="button" onClick={() => onTagClick(tag)} className="focus:outline-none">
              <Badge tone="brand">#{tag}</Badge>
            </button>
          ) : (
            <Badge key={tag} tone="brand">
              #{tag}
            </Badge>
          ),
        )}
        {hiddenCount > 0 && <Badge>+{hiddenCount}</Badge>}
      </div>
      <footer className="mt-3 flex items-center justify-between text-xs text-slate-500">
        <span className="flex items-center gap-1.5">
          {notebookName && (
            <>
              <span className="h-2 w-2 rounded-full" style={{ backgroundColor: notebookColor ?? "#94a3b8" }} aria-hidden="true" />
              <span className="truncate">{notebookName}</span>
              <span aria-hidden="true">·</span>
            </>
          )}
          <time dateTime={note.updated_at}>{timeAgo(note.updated_at)}</time>
        </span>
        <span title="Version">v{note.version}</span>
      </footer>
    </article>
  );
}
