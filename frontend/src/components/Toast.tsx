"use client";

import { createContext, useCallback, useContext, useMemo, useRef, useState, type ReactNode } from "react";

import { cn } from "@/lib/utils";

export type ToastTone = "info" | "success" | "error";

export interface ToastItem {
  id: number;
  title: string;
  description?: string;
  tone: ToastTone;
}

interface ToastContextValue {
  toasts: ToastItem[];
  push: (toast: Omit<ToastItem, "id">) => void;
  dismiss: (id: number) => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

const toneClasses: Record<ToastTone, string> = {
  info: "border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-900",
  success: "border-emerald-300 bg-emerald-50 dark:border-emerald-800 dark:bg-emerald-950",
  error: "border-red-300 bg-red-50 dark:border-red-800 dark:bg-red-950",
};

export function ToastProvider({ children, duration = 4000 }: { children: ReactNode; duration?: number }) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);
  const counter = useRef(0);

  const dismiss = useCallback((id: number) => {
    setToasts((current) => current.filter((toast) => toast.id !== id));
  }, []);

  const push = useCallback(
    (toast: Omit<ToastItem, "id">) => {
      const id = ++counter.current;
      setToasts((current) => [...current.slice(-4), { ...toast, id }]);
      setTimeout(() => dismiss(id), duration);
    },
    [dismiss, duration],
  );

  const value = useMemo(() => ({ toasts, push, dismiss }), [toasts, push, dismiss]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div
        className="pointer-events-none fixed bottom-4 right-4 z-50 flex w-80 max-w-[calc(100vw-2rem)] flex-col gap-2"
        aria-live="polite"
        aria-relevant="additions"
      >
        {toasts.map((toast) => (
          <div
            key={toast.id}
            role="status"
            className={cn(
              "pointer-events-auto animate-fade-in rounded-lg border p-3 text-sm shadow-lg",
              toneClasses[toast.tone],
            )}
          >
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="font-medium">{toast.title}</p>
                {toast.description && <p className="mt-0.5 text-xs text-slate-600 dark:text-slate-400">{toast.description}</p>}
              </div>
              <button
                type="button"
                onClick={() => dismiss(toast.id)}
                className="text-slate-400 hover:text-slate-700 dark:hover:text-slate-200"
                aria-label="Dismiss notification"
              >
                x
              </button>
            </div>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) throw new Error("useToast must be used within a ToastProvider");
  return {
    toast: context.push,
    success: (title: string, description?: string) => context.push({ title, description, tone: "success" }),
    error: (title: string, description?: string) => context.push({ title, description, tone: "error" }),
    info: (title: string, description?: string) => context.push({ title, description, tone: "info" }),
  };
}
