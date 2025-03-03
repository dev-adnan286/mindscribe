"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { cn } from "@/lib/utils";

export function MarkdownPreview({ content, className }: { content: string; className?: string }) {
  if (!content.trim()) {
    return <p className={cn("text-sm italic text-slate-400", className)}>Nothing to preview yet.</p>;
  }
  return (
    <div className={cn("prose-note", className)}>
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
    </div>
  );
}
