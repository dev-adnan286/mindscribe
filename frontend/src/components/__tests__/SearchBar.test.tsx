import { act, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { SearchBar } from "@/components/SearchBar";

describe("SearchBar", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });
  afterEach(() => {
    vi.useRealTimers();
  });

  it("debounces onSearch while typing", () => {
    const onSearch = vi.fn();
    render(<SearchBar onSearch={onSearch} debounceMs={300} />);
    const input = screen.getByRole("searchbox", { name: "Search" });
    fireEvent.change(input, { target: { value: "post" } });
    fireEvent.change(input, { target: { value: "postgres" } });
    expect(onSearch).not.toHaveBeenCalled();
    act(() => {
      vi.advanceTimersByTime(300);
    });
    expect(onSearch).toHaveBeenCalledTimes(1);
    expect(onSearch).toHaveBeenCalledWith("postgres");
  });

  it("searches immediately on submit and trims whitespace", () => {
    const onSearch = vi.fn();
    render(<SearchBar onSearch={onSearch} />);
    const input = screen.getByRole("searchbox", { name: "Search" });
    fireEvent.change(input, { target: { value: "  hello  " } });
    fireEvent.submit(screen.getByRole("search"));
    expect(onSearch).toHaveBeenCalledWith("hello");
  });

  it("clears the query with the clear button", () => {
    const onSearch = vi.fn();
    render(<SearchBar value="existing" onSearch={onSearch} />);
    fireEvent.click(screen.getByRole("button", { name: "Clear search" }));
    expect(onSearch).toHaveBeenCalledWith("");
    expect(screen.getByRole("searchbox", { name: "Search" })).toHaveValue("");
  });
});
