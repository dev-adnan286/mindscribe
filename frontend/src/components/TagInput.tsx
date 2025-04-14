"use client";

import { useId, useState, type KeyboardEvent } from "react";

import { tagSchema } from "@/lib/schemas";
import { cn } from "@/lib/utils";

export interface TagInputProps {
  value: string[];
  onChange: (tags: string[]) => void;
  suggestions?: string[];
  max?: number;
  placeholder?: string;
  label?: string;
  disabled?: boolean;
}

export function TagInput({
  value,
  onChange,
  suggestions = [],
  max = 20,
  placeholder = "Add a tag and press Enter",
  label = "Tags",
  disabled = false,
}: TagInputProps) {
  const [draft, setDraft] = useState("");
  const [error, setError] = useState<string | null>(null);
  const inputId = useId();

  const commit = (raw: string) => {
    const parsed = tagSchema.safeParse(raw);
    if (!raw.trim()) return;
    if (!parsed.success) {
      setError(parsed.error.issues[0]?.message ?? "Invalid tag");
      return;
    }
    const tag = parsed.data;
    if (value.includes(tag)) {
      setDraft("");
      return;
    }
    if (value.length >= max) {
      setError(`At most ${max} tags`);
      return;
    }
    onChange([...value, tag]);
    setDraft("");
    setError(null);
  };

  const remove = (tag: string) => onChange(value.filter((item) => item !== tag));

  const onKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "Enter" || event.key === ",") {
      event.preventDefault();
      commit(draft);
    } else if (event.key === "Backspace" && draft === "" && value.length > 0) {
      remove(value[value.length - 1]!);
    }
  };

  const available = suggestions.filter((s) => !value.includes(s)).slice(0, 8);

  return (
    <div className="space-y-1">
      <label htmlFor={inputId} className="block text-sm font-medium text-slate-700 dark:text-slate-300">
        {label}
      </label>
      <div
        className={cn(
          "input flex min-h-[42px] flex-wrap items-center gap-1.5 py-1.5",
          error && "border-red-500",
          disabled && "opacity-60",
        )}
      >
        {value.map((tag) => (
          <span
            key={tag}
            className="inline-flex items-center gap-1 rounded-full bg-brand-100 px-2 py-0.5 text-xs font-medium text-brand-800 dark:bg-brand-900/50 dark:text-brand-100"
          >
            #{tag}
            <button
              type="button"
              onClick={() => remove(tag)}
              disabled={disabled}
              className="rounded-full px-0.5 hover:bg-brand-200 dark:hover:bg-brand-800"
              aria-label={`Remove tag ${tag}`}
            >
              x
            </button>
          </span>
        ))}
        <input
          id={inputId}
          value={draft}
          disabled={disabled}
          onChange={(event) => {
            setDraft(event.target.value);
            setError(null);
          }}
          onKeyDown={onKeyDown}
          onBlur={() => draft && commit(draft)}
          placeholder={value.length === 0 ? placeholder : ""}
          className="min-w-[120px] flex-1 border-0 bg-transparent p-0 text-sm outline-none focus:ring-0"
          aria-describedby={error ? `${inputId}-error` : undefined}
        />
      </div>
      {error && (
        <p id={`${inputId}-error`} className="text-xs text-red-600 dark:text-red-400" role="alert">
          {error}
        </p>
      )}
      {available.length > 0 && (
        <div className="flex flex-wrap gap-1 pt-1" aria-label="Suggested tags">
          {available.map((suggestion) => (
            <button
              key={suggestion}
              type="button"
              onClick={() => commit(suggestion)}
              disabled={disabled}
              className="rounded-full border border-dashed border-slate-300 px-2 py-0.5 text-xs text-slate-600 hover:border-brand-500 hover:text-brand-700 dark:border-slate-600 dark:text-slate-300"
            >
              + {suggestion}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
