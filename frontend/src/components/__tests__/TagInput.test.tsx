import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";
import { describe, expect, it, vi } from "vitest";

import { TagInput } from "@/components/TagInput";

function Harness({ initial = [] as string[], suggestions = [] as string[], onChange = vi.fn() }) {
  const [tags, setTags] = useState<string[]>(initial);
  return (
    <TagInput
      value={tags}
      onChange={(next) => {
        setTags(next);
        onChange(next);
      }}
      suggestions={suggestions}
      max={3}
    />
  );
}

describe("TagInput", () => {
  it("adds a normalised tag on Enter and clears the draft", async () => {
    const onChange = vi.fn();
    render(<Harness onChange={onChange} />);
    const input = screen.getByRole("textbox", { name: "Tags" });
    await userEvent.type(input, "Machine Learning{Enter}");
    expect(onChange).toHaveBeenLastCalledWith(["machine-learning"]);
    expect(screen.getByText("#machine-learning")).toBeInTheDocument();
    expect(input).toHaveValue("");
  });

  it("ignores duplicates and rejects invalid characters", async () => {
    const onChange = vi.fn();
    render(<Harness initial={["python"]} onChange={onChange} />);
    const input = screen.getByRole("textbox", { name: "Tags" });
    await userEvent.type(input, "python{Enter}");
    expect(onChange).not.toHaveBeenCalled();
    await userEvent.type(input, "bad!tag{Enter}");
    expect(screen.getByRole("alert")).toHaveTextContent(/letters, numbers/);
    expect(onChange).not.toHaveBeenCalled();
  });

  it("removes a tag via its button and with Backspace on an empty draft", async () => {
    const onChange = vi.fn();
    render(<Harness initial={["alpha", "beta"]} onChange={onChange} />);
    await userEvent.click(screen.getByRole("button", { name: "Remove tag alpha" }));
    expect(onChange).toHaveBeenLastCalledWith(["beta"]);
    await userEvent.type(screen.getByRole("textbox", { name: "Tags" }), "{Backspace}");
    expect(onChange).toHaveBeenLastCalledWith([]);
  });

  it("enforces the maximum and offers suggestions not already selected", async () => {
    const onChange = vi.fn();
    render(<Harness initial={["a", "b", "c"]} suggestions={["a", "delta"]} onChange={onChange} />);
    expect(screen.queryByRole("button", { name: "+ a" })).not.toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "+ delta" }));
    expect(screen.getByRole("alert")).toHaveTextContent("At most 3 tags");
    expect(onChange).not.toHaveBeenCalled();
  });
});
