"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";

import { useAuth } from "@/lib/auth/hooks";
import { initials } from "@/lib/utils";

import { Button } from "./Button";
import { ThemeToggle } from "./ThemeToggle";

export function Navbar({ onToggleSidebar }: { onToggleSidebar?: () => void }) {
  const { user, logout } = useAuth();
  const router = useRouter();

  const handleLogout = async () => {
    await logout();
    router.replace("/login");
  };

  return (
    <header className="sticky top-0 z-30 flex h-14 items-center gap-3 border-b border-slate-200 bg-white/90 px-4 backdrop-blur dark:border-slate-800 dark:bg-slate-950/90">
      {onToggleSidebar && (
        <button
          type="button"
          onClick={onToggleSidebar}
          className="rounded-lg p-2 text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800 lg:hidden"
          aria-label="Toggle navigation"
        >
          ☰
        </button>
      )}
      <Link href="/app" className="flex items-center gap-2 font-semibold tracking-tight">
        <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-brand-600 text-sm text-white">M</span>
        MindScribe
      </Link>
      <div className="ml-auto flex items-center gap-2">
        <Link href="/app/notes/new">
          <Button size="sm">New note</Button>
        </Link>
        <ThemeToggle />
        {user && (
          <div className="flex items-center gap-2 pl-2">
            <Link
              href="/app/settings"
              className="flex h-8 w-8 items-center justify-center rounded-full bg-brand-100 text-xs font-semibold text-brand-800 dark:bg-brand-900/50 dark:text-brand-100"
              title={user.name}
              aria-label="Settings"
            >
              {initials(user.name)}
            </Link>
            <Button variant="ghost" size="sm" onClick={handleLogout}>
              Log out
            </Button>
          </div>
        )}
      </div>
    </header>
  );
}
