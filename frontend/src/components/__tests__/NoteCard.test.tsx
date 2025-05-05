import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { NoteCard } from "@/components/NoteCard";
import type { NoteSummary } from "@/lib/api";

const note: NoteSummary = {
  id: "abc123",
  notebook_id: "nb1",
  title: "Event-driven architecture",
  excerpt: "Services communicate by publishing events...",
  summary: null,
  tags: ["architecture", "events", "kafka", "queues", "extra"],
  version: 3,
  created_at: new Date(Date.now() - 86_400_000).toISOString(),
  updated_at: new Date(Date.now() - 3_600_000).toISOString(),
};

describe("NoteCard", () => {
  it("renders title, excerpt, version and links to the note", () => {
    render(<NoteCard note={note} notebookName="Engineering" notebookColor="#10b981" />);
    expect(screen.getByRole("heading", { name: "Event-driven architecture" })).toBeInTheDocument();
    expect(screen.getByText(/Services communicate/)).toBeInTheDocument();
    expect(screen.getByText("v3")).toBeInTheDocument();
    expect(screen.getByText("Engineering")).toBeInTheDocument();
    expect(screen.getByText("1 hour ago")).toBeInTheDocument();
    const link = screen.getAllByRole("link")[0];
    expect(link).toHaveAttribute("href", "/app/notes/abc123");
  });

  it("prefers the AI summary over the excerpt when present", () => {
    render(<NoteCard note={{ ...note, summary: "A concise summary." }} />);
    expect(screen.getByText("A concise summary.")).toBeInTheDocument();
    expect(screen.queryByText(/Services communicate/)).not.toBeInTheDocument();
  });

  it("shows at most four tags plus an overflow badge", () => {
    render(<NoteCard note={note} />);
    expect(screen.getByText("#architecture")).toBeInTheDocument();
    expect(screen.getByText("#queues")).toBeInTheDocument();
    expect(screen.queryByText("#extra")).not.toBeInTheDocument();
    expect(screen.getByText("+1")).toBeInTheDocument();
  });

  it("calls onTagClick when a tag is clicked", async () => {
    const onTagClick = vi.fn();
    render(<NoteCard note={note} onTagClick={onTagClick} />);
    await userEvent.click(screen.getByRole("button", { name: "#events" }));
    expect(onTagClick).toHaveBeenCalledWith("events");
  });
});
