"use client";

import { useState, type FormEvent, type KeyboardEvent } from "react";

import { Button } from "./Button";

export interface ChatInputProps {
  onSend: (question: string) => void | Promise<void>;
  disabled?: boolean;
  placeholder?: string;
  maxLength?: number;
}

export function ChatInput({ onSend, disabled = false, placeholder = "Ask something about your notes...", maxLength = 4000 }: ChatInputProps) {
  const [value, setValue] = useState("");
  const trimmed = value.trim();

  const submit = async (event?: FormEvent) => {
    event?.preventDefault();
    if (!trimmed || disabled) return;
    setValue("");
    await onSend(trimmed);
  };

  const onKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      void submit();
    }
  };

  return (
    <form onSubmit={submit} className="card flex items-end gap-2 p-2">
      <textarea
        value={value}
        onChange={(event) => setValue(event.target.value.slice(0, maxLength))}
        onKeyDown={onKeyDown}
        placeholder={placeholder}
        disabled={disabled}
        rows={2}
        className="max-h-40 flex-1 resize-none border-0 bg-transparent px-2 py-1.5 text-sm outline-none focus:ring-0"
        aria-label="Message"
      />
      <div className="flex flex-col items-end gap-1">
        <span className="text-[10px] text-slate-400">
          {value.length}/{maxLength}
        </span>
        <Button type="submit" size="sm" disabled={!trimmed || disabled} loading={disabled}>
          Send
        </Button>
      </div>
    </form>
  );
}
