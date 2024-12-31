"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useState } from "react";

import { Badge } from "@/components/Badge";
import { EmptyState } from "@/components/EmptyState";
import { SearchBar } from "@/components/SearchBar";
import { LineSkeleton } from "@/components/Skeleton";
import { searchApi, type SearchMode } from "@/lib/api";
import { cn, scoreToPercent, timeAgo } from "@/lib/utils";

const MODES: { value: SearchMode; label: string; help: string }[] = [
  { value: "keyword", label: "Keyword", help: "Exact terms in titles and content" },
  { value: "semantic", label: "Semantic", help: "Similar meaning, ranked by embedding similarity" },
  { value: "hybrid", label: "Hybrid", help: "Blend of both signals" },
];

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [mode, setMode] = useState<SearchMode>("semantic");

  const results = useQuery({
    queryKey: ["search", query, mode],
    queryFn: () => searchApi.search(query, mode, 20),
    enabled: query.length > 0,
  });

  const current = MODES.find((m) => m.value === mode)!;

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold">Search</h1>
        <p className="text-sm text-slate-500">Find notes by keyword or by meaning.</p>
      </div>

      <SearchBar value={query} onSearch={setQuery} placeholder="What are you looking for?" autoFocus debounceMs={400} />

      <div className="flex flex-wrap items-center gap-3">
        <div className="inline-flex rounded-lg bg-slate-100 p-1 dark:bg-slate-800" role="radiogroup" aria-label="Search mode">
          {MODES.map((option) => (
            <button
              key={option.value}
              type="button"
              role="radio"
              aria-checked={mode === option.value}
              onClick={() => setMode(option.value)}
              className={cn(
                "rounded-md px-3 py-1.5 text-sm font-medium transition",
                mode === option.value
                  ? "bg-white text-slate-900 shadow-sm dark:bg-slate-700 dark:text-white"
                  : "text-slate-500 hover:text-slate-800 dark:hover:text-slate-200",
              )}
            >
              {option.label}
            </button>
          ))}
        </div>
        <span className="text-xs text-slate-500">{current.help}</span>
        {results.data && <Badge className="ml-auto">engine: {results.data.engine}</Badge>}
      </div>

      {!query ? (
        <EmptyState title="Start typing to search" description="Semantic mode understands paraphrases, so describe what you remember." icon="⌕" />
      ) : results.isLoading ? (
        <LineSkeleton lines={6} />
      ) : results.data && results.data.hits.length > 0 ? (
        <ul className="space-y-3">
          {results.data.hits.map((hit) => (
            <li key={hit.note_id}>
              <Link href={`/app/notes/${hit.note_id}`} className="card block p-4 transition hover:border-brand-400 hover:shadow-md">
                <div className="flex items-start justify-between gap-4">
                  <h3 className="font-semibold">{hit.title}</h3>
                  <div className="flex shrink-0 items-center gap-2" title="Relevance">
                    <div className="h-1.5 w-20 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-700">
                      <div className="h-full bg-brand-500" style={{ width: scoreToPercent(hit.score) }} />
                    </div>
                    <span className="w-9 text-right text-xs tabular-nums text-slate-500">{scoreToPercent(hit.score)}</span>
                  </div>
                </div>
                <p className="mt-1 line-clamp-2 text-sm text-slate-600 dark:text-slate-400">{hit.snippet}</p>
                <div className="mt-2 flex flex-wrap items-center gap-1.5 text-xs text-slate-500">
                  {hit.tags.slice(0, 5).map((tag) => (
                    <Badge key={tag} tone="brand">
                      #{tag}
                    </Badge>
                  ))}
                  <span className="ml-auto">{timeAgo(hit.updated_at)}</span>
                </div>
              </Link>
            </li>
          ))}
        </ul>
      ) : (
        <EmptyState title="No results" description={`Nothing matched "${query}" in ${mode} mode. Try another mode or different words.`} />
      )}
    </div>
  );
}
