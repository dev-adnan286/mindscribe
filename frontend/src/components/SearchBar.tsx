"use client";

import { useEffect, useState, type FormEvent } from "react";

import { cn } from "@/lib/utils";

export interface SearchBarProps {
  value?: string;
  onSearch: (query: string) => void;
  placeholder?: string;
  autoFocus?: boolean;
  debounceMs?: number;
  className?: string;
}

/** Controlled-ish search input: debounced onSearch while typing, immediate on submit. */
export function SearchBar({
  value = "",
  onSearch,
  placeholder = "Search notes...",
  autoFocus = false,
  debounceMs = 300,
  className,
}: SearchBarProps) {
  const [query, setQuery] = useState(value);

  useEffect(() => {
    setQuery(value);
  }, [value]);

  useEffect(() => {
    if (query === value) return;
    const timer = setTimeout(() => onSearch(query.trim()), debounceMs);
    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [query, debounceMs]);

  const submit = (event: FormEvent) => {
    event.preventDefault();
    onSearch(query.trim());
  };

  return (
    <form onSubmit={submit} role="search" className={cn("relative", className)}>
      <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" aria-hidden="true">
        ⌕
      </span>
      <input
        type="search"
        value={query}
        onChange={(event) => setQuery(event.target.value)}
        placeholder={placeholder}
        autoFocus={autoFocus}
        className="input pl-9 pr-16"
        aria-label="Search"
      />
      {query && (
        <button
          type="button"
          onClick={() => {
            setQuery("");
            onSearch("");
          }}
          className="absolute right-2 top-1/2 -translate-y-1/2 rounded px-2 py-0.5 text-xs text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800"
          aria-label="Clear search"
        >
          Clear
        </button>
      )}
    </form>
  );
}
