import Link from "next/link";

import type { Citation } from "@/lib/api";
import { scoreToPercent } from "@/lib/utils";

export function CitationChip({ citation }: { citation: Citation }) {
  return (
    <Link
      href={`/app/notes/${citation.note_id}`}
      className="inline-flex max-w-full items-center gap-1.5 rounded-full border border-brand-200 bg-brand-50 px-2.5 py-1 text-xs text-brand-800 transition hover:border-brand-400 hover:bg-brand-100 dark:border-brand-800 dark:bg-brand-900/30 dark:text-brand-100 dark:hover:bg-brand-900/60"
      title={citation.snippet}
    >
      <span className="flex h-4 w-4 items-center justify-center rounded-full bg-brand-600 text-[10px] font-bold text-white">
        {citation.index}
      </span>
      <span className="truncate">{citation.title}</span>
      <span className="text-brand-500 dark:text-brand-300">{scoreToPercent(citation.score)}</span>
    </Link>
  );
}
