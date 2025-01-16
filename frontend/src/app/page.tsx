import Link from "next/link";

import { Button } from "@/components/Button";
import { ThemeToggle } from "@/components/ThemeToggle";

const FEATURES = [
  {
    title: "AI summaries",
    body: "Turn long notes into a crisp three-sentence summary you can skim before opening the note.",
    icon: "≡",
  },
  {
    title: "Automatic tags",
    body: "Get topical tag suggestions from your writing and keep your knowledge base consistently organised.",
    icon: "#",
  },
  {
    title: "Semantic search",
    body: "Find notes by meaning, not just keywords. Backed by pgvector in production with an offline fallback for local use.",
    icon: "⌕",
  },
  {
    title: "Chat with your notes",
    body: "Ask questions and get grounded answers with citations that link straight back to the source note.",
    icon: "✉",
  },
  {
    title: "Version history",
    body: "Every meaningful edit is versioned. Browse the history and restore any previous revision in one click.",
    icon: "↺",
  },
  {
    title: "Your data, your keys",
    body: "Runs fully offline with a mock provider by default. Bring an Anthropic or OpenAI key when you want the real thing.",
    icon: "⚿",
  },
];

const STEPS = [
  ["Capture", "Write in Markdown with live preview and autosave. Group notes into colour-coded notebooks."],
  ["Enrich", "One click adds a summary and tags. Every note is embedded for semantic search as you type."],
  ["Recall", "Search by meaning or ask the assistant. Answers cite the exact notes they came from."],
];

export default function LandingPage() {
  return (
    <main className="min-h-screen">
      <header className="mx-auto flex max-w-6xl items-center justify-between px-6 py-5">
        <span className="flex items-center gap-2 text-lg font-semibold tracking-tight">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-600 text-white">M</span>
          MindScribe
        </span>
        <nav className="flex items-center gap-2">
          <ThemeToggle />
          <Link href="/login">
            <Button variant="ghost" size="sm">
              Log in
            </Button>
          </Link>
          <Link href="/register">
            <Button size="sm">Get started</Button>
          </Link>
        </nav>
      </header>

      <section className="mx-auto max-w-6xl px-6 pb-20 pt-16 text-center">
        <span className="inline-block rounded-full border border-brand-200 bg-brand-50 px-3 py-1 text-xs font-medium text-brand-700 dark:border-brand-800 dark:bg-brand-900/30 dark:text-brand-200">
          Notes that remember for you
        </span>
        <h1 className="mx-auto mt-6 max-w-3xl text-4xl font-bold tracking-tight sm:text-6xl">
          The knowledge base that <span className="text-brand-600 dark:text-brand-400">summarises, tags and answers</span>
        </h1>
        <p className="mx-auto mt-6 max-w-2xl text-lg text-slate-600 dark:text-slate-400">
          MindScribe is an AI-powered notes app. Write in Markdown, let the assistant organise everything, then
          search by meaning or simply ask your notes a question.
        </p>
        <div className="mt-8 flex justify-center gap-3">
          <Link href="/register">
            <Button size="lg">Create a free account</Button>
          </Link>
          <Link href="/login">
            <Button size="lg" variant="secondary">
              I already have one
            </Button>
          </Link>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-6 pb-20">
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map((feature) => (
            <div key={feature.title} className="card p-6">
              <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-lg bg-brand-100 text-lg text-brand-700 dark:bg-brand-900/40 dark:text-brand-200">
                {feature.icon}
              </div>
              <h3 className="font-semibold">{feature.title}</h3>
              <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">{feature.body}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="border-y border-slate-200 bg-white py-16 dark:border-slate-800 dark:bg-slate-900">
        <div className="mx-auto max-w-6xl px-6">
          <h2 className="text-center text-2xl font-bold">How it works</h2>
          <ol className="mt-10 grid gap-8 md:grid-cols-3">
            {STEPS.map(([title, body], index) => (
              <li key={title} className="relative">
                <span className="mb-3 flex h-8 w-8 items-center justify-center rounded-full bg-brand-600 text-sm font-semibold text-white">
                  {index + 1}
                </span>
                <h3 className="font-semibold">{title}</h3>
                <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">{body}</p>
              </li>
            ))}
          </ol>
        </div>
      </section>

      <footer className="mx-auto flex max-w-6xl items-center justify-between px-6 py-8 text-sm text-slate-500">
        <span>MindScribe - MIT licensed</span>
        <span>FastAPI + Next.js + pgvector</span>
      </footer>
    </main>
  );
}
