import type { HTMLAttributes } from "react";

import { cn } from "@/lib/utils";

type Tone = "neutral" | "brand" | "success" | "warning";

const tones: Record<Tone, string> = {
  neutral: "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300",
  brand: "bg-brand-100 text-brand-800 dark:bg-brand-900/50 dark:text-brand-200",
  success: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-200",
  warning: "bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-200",
};

export function Badge({ tone = "neutral", className, ...props }: HTMLAttributes<HTMLSpanElement> & { tone?: Tone }) {
  return (
    <span
      className={cn("inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium", tones[tone], className)}
      {...props}
    />
  );
}
