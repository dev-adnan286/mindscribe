"use client";

import { useEffect, useRef } from "react";

import type { ChatMessage } from "@/lib/api";
import { cn } from "@/lib/utils";

import { CitationChip } from "./CitationChip";
import { MarkdownPreview } from "./MarkdownPreview";

export interface DisplayMessage extends ChatMessage {
  /** True while the assistant reply is being revealed incrementally. */
  streaming?: boolean;
}

export function ChatMessageList({ messages, pending }: { messages: DisplayMessage[]; pending?: boolean }) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, pending]);

  return (
    <div className="space-y-4" role="log" aria-live="polite">
      {messages.map((message) => (
        <div key={message.id} className={cn("flex", message.role === "user" ? "justify-end" : "justify-start")}>
          <div
            className={cn(
              "max-w-[85%] rounded-2xl px-4 py-3 text-sm shadow-sm",
              message.role === "user"
                ? "rounded-br-sm bg-brand-600 text-white"
                : "card rounded-bl-sm",
            )}
          >
            {message.role === "user" ? (
              <p className="whitespace-pre-wrap">{message.content}</p>
            ) : (
              <>
                <MarkdownPreview content={message.content} className="text-sm leading-6" />
                {message.streaming && <span className="ml-0.5 inline-block h-4 w-1.5 animate-pulse bg-brand-500 align-middle" aria-hidden="true" />}
                {!message.streaming && message.citations.length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-1.5 border-t border-slate-100 pt-3 dark:border-slate-800">
                    {message.citations.map((citation) => (
                      <CitationChip key={`${message.id}-${citation.index}`} citation={citation} />
                    ))}
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      ))}
      {pending && (
        <div className="flex justify-start">
          <div className="card flex items-center gap-1.5 rounded-2xl rounded-bl-sm px-4 py-3" aria-label="Assistant is thinking">
            {[0, 1, 2].map((i) => (
              <span
                key={i}
                className="h-2 w-2 animate-bounce rounded-full bg-slate-400"
                style={{ animationDelay: `${i * 120}ms` }}
              />
            ))}
          </div>
        </div>
      )}
      <div ref={bottomRef} />
    </div>
  );
}
