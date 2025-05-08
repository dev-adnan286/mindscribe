import { describe, expect, it, vi } from "vitest";

import { debounce, initials, isSafeInternalPath, readingTime, scoreToPercent, timeAgo, truncate, wordCount } from "@/lib/utils";

describe("utils", () => {
  it("truncates on word boundaries", () => {
    expect(truncate("short text", 20)).toBe("short text");
    expect(truncate("the quick brown fox jumps over the lazy dog", 20)).toBe("the quick brown fox...");
    expect(truncate("multiple   spaces\nand newlines", 100)).toBe("multiple spaces and newlines");
  });

  it("counts words and estimates reading time", () => {
    expect(wordCount("")).toBe(0);
    expect(wordCount("  one two\nthree ")).toBe(3);
    expect(readingTime("word ".repeat(500))).toBe("3 min read");
    expect(readingTime("")).toBe("1 min read");
  });

  it("formats relative time", () => {
    const now = new Date("2026-01-10T12:00:00Z");
    expect(timeAgo(new Date("2026-01-10T11:59:50Z"), now)).toBe("just now");
    expect(timeAgo(new Date("2026-01-10T11:30:00Z"), now)).toBe("30 minutes ago");
    expect(timeAgo(new Date("2026-01-10T09:00:00Z"), now)).toBe("3 hours ago");
    expect(timeAgo(new Date("2026-01-09T12:00:00Z"), now)).toBe("1 day ago");
    expect(timeAgo(new Date("2025-12-01T12:00:00Z"), now)).toBe("1 month ago");
  });

  it("debounces calls and supports cancel/flush", () => {
    vi.useFakeTimers();
    const fn = vi.fn();
    const debounced = debounce(fn, 100);
    debounced("a");
    debounced("b");
    vi.advanceTimersByTime(99);
    expect(fn).not.toHaveBeenCalled();
    vi.advanceTimersByTime(1);
    expect(fn).toHaveBeenCalledWith("b");
    debounced("c");
    debounced.cancel();
    vi.advanceTimersByTime(200);
    expect(fn).toHaveBeenCalledTimes(1);
    debounced.flush("d");
    expect(fn).toHaveBeenLastCalledWith("d");
    vi.useRealTimers();
  });

  it("derives initials and percentages", () => {
    expect(initials("Ada Lovelace")).toBe("AL");
    expect(initials("  grace  ")).toBe("G");
    expect(scoreToPercent(0.456)).toBe("46%");
    expect(scoreToPercent(2)).toBe("100%");
  });

  it("only accepts safe internal redirect paths", () => {
    expect(isSafeInternalPath("/app/notes")).toBe(true);
    expect(isSafeInternalPath("//evil.example")).toBe(false);
    expect(isSafeInternalPath("https://evil.example")).toBe(false);
    expect(isSafeInternalPath(null)).toBe(false);
  });
});
