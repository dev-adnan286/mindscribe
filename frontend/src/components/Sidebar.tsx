"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import { useState } from "react";

import { ApiError, notebooksApi, tagsApi } from "@/lib/api";
import { notebookSchema, fieldErrors } from "@/lib/schemas";
import { cn } from "@/lib/utils";

import { Button } from "./Button";
import { Input } from "./Input";
import { Modal } from "./Modal";
import { useToast } from "./Toast";

const NAV = [
  { href: "/app", label: "Dashboard", icon: "▦" },
  { href: "/app/notes", label: "Notes", icon: "✎" },
  { href: "/app/search", label: "Search", icon: "⌕" },
  { href: "/app/chat", label: "Chat", icon: "✉" },
  { href: "/app/settings", label: "Settings", icon: "⚙" },
];

const COLORS = ["#6366f1", "#10b981", "#f59e0b", "#ef4444", "#3b82f6", "#8b5cf6", "#ec4899", "#14b8a6"];

export function Sidebar({ open, onClose }: { open: boolean; onClose: () => void }) {
  const pathname = usePathname();
  const params = useSearchParams();
  const activeNotebook = params.get("notebook_id");
  const activeTag = params.get("tag");
  const [creating, setCreating] = useState(false);

  const notebooks = useQuery({ queryKey: ["notebooks"], queryFn: notebooksApi.list });
  const tags = useQuery({ queryKey: ["tags"], queryFn: tagsApi.list });

  const linkClass = (active: boolean) =>
    cn(
      "flex items-center gap-2 rounded-lg px-3 py-2 text-sm transition",
      active
        ? "bg-brand-50 font-medium text-brand-700 dark:bg-brand-900/40 dark:text-brand-100"
        : "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800",
    );

  return (
    <>
      {open && <div className="fixed inset-0 z-20 bg-slate-900/40 lg:hidden" onClick={onClose} aria-hidden="true" />}
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-20 flex w-64 flex-col border-r border-slate-200 bg-white pt-14 transition-transform dark:border-slate-800 dark:bg-slate-950 lg:static lg:translate-x-0 lg:pt-0",
          open ? "translate-x-0" : "-translate-x-full",
        )}
        aria-label="Sidebar"
      >
        <nav className="space-y-1 p-3">
          {NAV.map((item) => {
            const active = item.href === "/app" ? pathname === "/app" : pathname.startsWith(item.href);
            return (
              <Link key={item.href} href={item.href} className={linkClass(active)} onClick={onClose}>
                <span className="w-4 text-center" aria-hidden="true">
                  {item.icon}
                </span>
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="flex-1 space-y-6 overflow-y-auto px-3 pb-6">
          <section>
            <div className="mb-1 flex items-center justify-between px-3">
              <h3 className="text-xs font-semibold uppercase tracking-wide text-slate-500">Notebooks</h3>
              <button
                type="button"
                onClick={() => setCreating(true)}
                className="text-xs text-brand-600 hover:underline dark:text-brand-300"
              >
                + New
              </button>
            </div>
            <ul className="space-y-0.5">
              {notebooks.data?.map((notebook) => (
                <li key={notebook.id}>
                  <Link
                    href={`/app/notes?notebook_id=${notebook.id}`}
                    className={linkClass(activeNotebook === notebook.id)}
                    onClick={onClose}
                  >
                    <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: notebook.color }} aria-hidden="true" />
                    <span className="flex-1 truncate">{notebook.name}</span>
                    <span className="text-xs text-slate-400">{notebook.note_count}</span>
                  </Link>
                </li>
              ))}
              {notebooks.data?.length === 0 && <li className="px-3 text-xs text-slate-400">No notebooks yet</li>}
            </ul>
          </section>

          <section>
            <h3 className="mb-1 px-3 text-xs font-semibold uppercase tracking-wide text-slate-500">Tags</h3>
            <div className="flex flex-wrap gap-1.5 px-3">
              {tags.data?.slice(0, 30).map((tag) => (
                <Link
                  key={tag.id}
                  href={`/app/notes?tag=${encodeURIComponent(tag.name)}`}
                  onClick={onClose}
                  className={cn(
                    "rounded-full border px-2 py-0.5 text-xs transition",
                    activeTag === tag.name
                      ? "border-brand-500 bg-brand-50 text-brand-700 dark:bg-brand-900/40 dark:text-brand-100"
                      : "border-slate-200 text-slate-600 hover:border-slate-400 dark:border-slate-700 dark:text-slate-300",
                  )}
                >
                  #{tag.name} <span className="text-slate-400">{tag.note_count}</span>
                </Link>
              ))}
              {tags.data?.length === 0 && <span className="text-xs text-slate-400">No tags yet</span>}
            </div>
          </section>
        </div>
      </aside>
      <NotebookDialog open={creating} onClose={() => setCreating(false)} />
    </>
  );
}

export function NotebookDialog({ open, onClose }: { open: boolean; onClose: () => void }) {
  const queryClient = useQueryClient();
  const toast = useToast();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [color, setColor] = useState(COLORS[0]!);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const mutation = useMutation({
    mutationFn: notebooksApi.create,
    onSuccess: (notebook) => {
      void queryClient.invalidateQueries({ queryKey: ["notebooks"] });
      toast.success("Notebook created", notebook.name);
      setName("");
      setDescription("");
      setErrors({});
      onClose();
    },
    onError: (error) => {
      if (error instanceof ApiError) {
        setErrors(error.status === 409 ? { name: error.message } : error.fieldErrors);
        if (error.status !== 409 && Object.keys(error.fieldErrors).length === 0) toast.error(error.message);
      }
    },
  });

  const submit = () => {
    const parsed = notebookSchema.safeParse({ name, description: description || undefined, color });
    if (!parsed.success) {
      setErrors(fieldErrors(parsed.error));
      return;
    }
    mutation.mutate({ ...parsed.data, description: parsed.data.description ?? null });
  };

  return (
    <Modal
      open={open}
      onClose={onClose}
      title="New notebook"
      description="Notebooks group related notes together."
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={submit} loading={mutation.isPending}>
            Create
          </Button>
        </>
      }
    >
      <div className="space-y-4">
        <Input label="Name" value={name} onChange={(e) => setName(e.target.value)} error={errors.name} autoFocus />
        <Input
          label="Description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          error={errors.description}
        />
        <div>
          <p className="mb-1 text-sm font-medium text-slate-700 dark:text-slate-300">Colour</p>
          <div className="flex gap-2">
            {COLORS.map((option) => (
              <button
                key={option}
                type="button"
                onClick={() => setColor(option)}
                className={cn("h-7 w-7 rounded-full ring-offset-2", color === option && "ring-2 ring-slate-500")}
                style={{ backgroundColor: option }}
                aria-label={`Colour ${option}`}
                aria-pressed={color === option}
              />
            ))}
          </div>
        </div>
      </div>
    </Modal>
  );
}
