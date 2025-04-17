"use client";

import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import { notesApi, type NoteVersion } from "@/lib/api";
import { cn, formatDate, truncate } from "@/lib/utils";

import { Badge } from "./Badge";
import { Button } from "./Button";
import { LineSkeleton } from "./Skeleton";

export function VersionHistoryDrawer({
  noteId,
  currentVersion,
  open,
  onClose,
  onRestore,
  restoring,
}: {
  noteId: string;
  currentVersion: number;
  open: boolean;
  onClose: () => void;
  onRestore: (version: number) => void;
  restoring: boolean;
}) {
  const [selected, setSelected] = useState<NoteVersion | null>(null);
  const versions = useQuery({
    queryKey: ["note-versions", noteId],
    queryFn: () => notesApi.versions(noteId),
    enabled: open,
  });

  useEffect(() => {
    if (!open) setSelected(null);
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const onKey = (event: KeyboardEvent) => event.key === "Escape" && onClose();
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  return (
    <>
      {open && <div className="fixed inset-0 z-30 bg-slate-900/40" onClick={onClose} aria-hidden="true" />}
      <aside
        className={cn(
          "fixed inset-y-0 right-0 z-40 flex w-full max-w-md flex-col border-l border-slate-200 bg-white shadow-xl transition-transform dark:border-slate-800 dark:bg-slate-950",
          open ? "translate-x-0" : "translate-x-full",
        )}
        aria-label="Version history"
        aria-hidden={!open}
      >
        <header className="flex items-center justify-between border-b border-slate-200 px-4 py-3 dark:border-slate-800">
          <h2 className="font-semibold">Version history</h2>
          <button type="button" onClick={onClose} className="text-sm text-slate-500 hover:text-slate-900 dark:hover:text-white">
            Close
          </button>
        </header>
        <div className="flex-1 overflow-y-auto p-4">
          {versions.isLoading && <LineSkeleton lines={6} />}
          {versions.data && (
            <ul className="space-y-2">
              {versions.data.map((version) => (
                <li key={version.id}>
                  <button
                    type="button"
                    onClick={() => setSelected(version)}
                    className={cn(
                      "card w-full p-3 text-left transition hover:border-brand-400",
                      selected?.id === version.id && "border-brand-500 ring-1 ring-brand-500",
                    )}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium">
                        v{version.version} {version.version === currentVersion && <Badge tone="success">current</Badge>}
                      </span>
                      <time className="text-xs text-slate-500" dateTime={version.created_at}>
                        {formatDate(version.created_at, { hour: "2-digit", minute: "2-digit" })}
                      </time>
                    </div>
                    <p className="mt-1 truncate text-sm text-slate-700 dark:text-slate-300">{version.title}</p>
                    <p className="mt-0.5 text-xs text-slate-500">{truncate(version.content, 90)}</p>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
        {selected && (
          <footer className="space-y-3 border-t border-slate-200 p-4 dark:border-slate-800">
            <div className="max-h-40 overflow-y-auto rounded-lg bg-slate-50 p-3 text-xs dark:bg-slate-900">
              <p className="mb-1 font-semibold">{selected.title}</p>
              <pre className="whitespace-pre-wrap font-sans">{truncate(selected.content, 600)}</pre>
            </div>
            <Button
              className="w-full"
              onClick={() => onRestore(selected.version)}
              disabled={selected.version === currentVersion}
              loading={restoring}
            >
              Restore v{selected.version}
            </Button>
          </footer>
        )}
      </aside>
    </>
  );
}
