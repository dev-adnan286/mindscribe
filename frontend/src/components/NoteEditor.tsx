"use client";

import { useState } from "react";

import { cn, readingTime, wordCount } from "@/lib/utils";

import { MarkdownPreview } from "./MarkdownPreview";

export interface NoteEditorProps {
  title: string;
  content: string;
  onTitleChange: (title: string) => void;
  onContentChange: (content: string) => void;
  titleError?: string;
  disabled?: boolean;
}

type Mode = "write" | "preview" | "split";

export function NoteEditor({ title, content, onTitleChange, onContentChange, titleError, disabled }: NoteEditorProps) {
  const [mode, setMode] = useState<Mode>("write");
  const words = wordCount(content);

  const modeButton = (value: Mode, label: string) => (
    <button
      type="button"
      onClick={() => setMode(value)}
      className={cn(
        "rounded-md px-2.5 py-1 text-xs font-medium transition",
        mode === value
          ? "bg-white text-slate-900 shadow-sm dark:bg-slate-700 dark:text-white"
          : "text-slate-500 hover:text-slate-800 dark:hover:text-slate-200",
      )}
      aria-pressed={mode === value}
    >
      {label}
    </button>
  );

  return (
    <div className="space-y-3">
      <div>
        <input
          value={title}
          onChange={(event) => onTitleChange(event.target.value)}
          placeholder="Untitled note"
          disabled={disabled}
          className={cn(
            "w-full border-0 bg-transparent px-0 text-3xl font-bold tracking-tight outline-none placeholder:text-slate-300 focus:ring-0 dark:placeholder:text-slate-600",
            titleError && "text-red-600",
          )}
          aria-label="Note title"
          aria-invalid={titleError ? true : undefined}
        />
        {titleError && <p className="mt-1 text-xs text-red-600">{titleError}</p>}
      </div>

      <div className="flex items-center justify-between">
        <div className="inline-flex gap-1 rounded-lg bg-slate-100 p-1 dark:bg-slate-800" role="tablist" aria-label="Editor mode">
          {modeButton("write", "Write")}
          {modeButton("split", "Split")}
          {modeButton("preview", "Preview")}
        </div>
        <span className="text-xs text-slate-500">
          {words} {words === 1 ? "word" : "words"} · {readingTime(content)}
        </span>
      </div>

      <div className={cn("grid gap-4", mode === "split" && "lg:grid-cols-2")}>
        {mode !== "preview" && (
          <textarea
            value={content}
            onChange={(event) => onContentChange(event.target.value)}
            placeholder="Write in Markdown... # headings, **bold**, - lists, `code`"
            disabled={disabled}
            className="input min-h-[420px] resize-y font-mono text-[14px] leading-6"
            aria-label="Note content"
            spellCheck
          />
        )}
        {mode !== "write" && (
          <div className="card min-h-[420px] overflow-auto p-5">
            <MarkdownPreview content={content} />
          </div>
        )}
      </div>
    </div>
  );
}
