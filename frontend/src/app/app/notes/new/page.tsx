"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";

import { Button } from "@/components/Button";
import { NoteEditor } from "@/components/NoteEditor";
import { TagInput } from "@/components/TagInput";
import { useToast } from "@/components/Toast";
import { ApiError, aiApi, notebooksApi, notesApi, tagsApi } from "@/lib/api";
import { fieldErrors, noteSchema } from "@/lib/schemas";

function NewNoteForm() {
  const router = useRouter();
  const params = useSearchParams();
  const queryClient = useQueryClient();
  const toast = useToast();

  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [tags, setTags] = useState<string[]>([]);
  const [notebookId, setNotebookId] = useState<string>(params.get("notebook_id") ?? "");
  const [suggested, setSuggested] = useState<string[]>([]);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const notebooks = useQuery({ queryKey: ["notebooks"], queryFn: notebooksApi.list });
  const existingTags = useQuery({ queryKey: ["tags"], queryFn: tagsApi.list });

  const suggest = useMutation({
    mutationFn: () => aiApi.suggestTags({ content: `${title}\n\n${content}`, max_tags: 6 }),
    onSuccess: (result) => {
      setSuggested(result.tags);
      if (result.tags.length === 0) toast.info("No tag suggestions", "Write a little more first.");
    },
    onError: (error) => toast.error("Could not suggest tags", error instanceof ApiError ? error.message : undefined),
  });

  const create = useMutation({
    mutationFn: notesApi.create,
    onSuccess: (note) => {
      void queryClient.invalidateQueries({ queryKey: ["notes"] });
      void queryClient.invalidateQueries({ queryKey: ["tags"] });
      void queryClient.invalidateQueries({ queryKey: ["notebooks"] });
      void queryClient.invalidateQueries({ queryKey: ["stats"] });
      toast.success("Note created");
      router.replace(`/app/notes/${note.id}`);
    },
    onError: (error) => {
      if (error instanceof ApiError) {
        setErrors(error.fieldErrors);
        toast.error("Could not create note", error.message);
      }
    },
  });

  const submit = () => {
    const parsed = noteSchema.safeParse({ title, content, tags, notebook_id: notebookId || null });
    if (!parsed.success) {
      setErrors(fieldErrors(parsed.error));
      return;
    }
    setErrors({});
    create.mutate({ ...parsed.data, notebook_id: parsed.data.notebook_id ?? null });
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-lg font-semibold text-slate-500">New note</h1>
        <div className="flex gap-2">
          <Button variant="secondary" onClick={() => router.back()}>
            Cancel
          </Button>
          <Button onClick={submit} loading={create.isPending}>
            Create note
          </Button>
        </div>
      </div>

      <NoteEditor title={title} content={content} onTitleChange={setTitle} onContentChange={setContent} titleError={errors.title} />

      <div className="grid gap-4 md:grid-cols-[1fr_240px]">
        <div className="space-y-2">
          <TagInput
            value={tags}
            onChange={setTags}
            suggestions={[...suggested, ...(existingTags.data?.map((t) => t.name) ?? [])]}
          />
          <Button variant="ghost" size="sm" onClick={() => suggest.mutate()} loading={suggest.isPending} disabled={!content.trim()}>
            Suggest tags with AI
          </Button>
        </div>
        <div>
          <label htmlFor="notebook" className="block text-sm font-medium text-slate-700 dark:text-slate-300">
            Notebook
          </label>
          <select id="notebook" value={notebookId} onChange={(e) => setNotebookId(e.target.value)} className="input mt-1">
            <option value="">No notebook</option>
            {notebooks.data?.map((nb) => (
              <option key={nb.id} value={nb.id}>
                {nb.name}
              </option>
            ))}
          </select>
        </div>
      </div>
    </div>
  );
}

export default function NewNotePage() {
  return (
    <Suspense fallback={null}>
      <NewNoteForm />
    </Suspense>
  );
}
