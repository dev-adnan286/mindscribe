"use client";

import { Suspense, useState, type ReactNode } from "react";

import { Navbar } from "@/components/Navbar";
import { Sidebar } from "@/components/Sidebar";
import { LineSkeleton } from "@/components/Skeleton";
import { useRequireAuth } from "@/lib/auth/hooks";

export default function AppLayout({ children }: { children: ReactNode }) {
  const status = useRequireAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  if (status !== "authenticated") {
    return (
      <div className="flex min-h-screen items-center justify-center p-6">
        <div className="w-full max-w-md">
          <LineSkeleton lines={5} />
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen flex-col">
      <Navbar onToggleSidebar={() => setSidebarOpen((open) => !open)} />
      <div className="flex flex-1">
        <Suspense fallback={<div className="hidden w-64 lg:block" />}>
          <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
        </Suspense>
        <main className="min-w-0 flex-1 px-4 py-6 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-6xl">{children}</div>
        </main>
      </div>
    </div>
  );
}
