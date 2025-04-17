import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ChatInput } from "@/components/ChatInput";

describe("ChatInput", () => {
  it("disables send until there is text", async () => {
    render(<ChatInput onSend={vi.fn()} />);
    const send = screen.getByRole("button", { name: "Send" });
    expect(send).toBeDisabled();
    await userEvent.type(screen.getByRole("textbox", { name: "Message" }), "hi");
    expect(send).toBeEnabled();
  });

  it("sends on Enter, trims, and clears the box", async () => {
    const onSend = vi.fn();
    render(<ChatInput onSend={onSend} />);
    const box = screen.getByRole("textbox", { name: "Message" });
    await userEvent.type(box, "  What is idempotency?  {Enter}");
    expect(onSend).toHaveBeenCalledWith("What is idempotency?");
    expect(box).toHaveValue("");
  });

  it("inserts a newline on Shift+Enter without sending", async () => {
    const onSend = vi.fn();
    render(<ChatInput onSend={onSend} />);
    const box = screen.getByRole("textbox", { name: "Message" });
    await userEvent.type(box, "line one{Shift>}{Enter}{/Shift}line two");
    expect(onSend).not.toHaveBeenCalled();
    expect(box).toHaveValue("line one\nline two");
  });

  it("does not send while disabled and shows the counter", async () => {
    const onSend = vi.fn();
    render(<ChatInput onSend={onSend} disabled maxLength={50} />);
    expect(screen.getByRole("textbox", { name: "Message" })).toBeDisabled();
    expect(screen.getByText("0/50")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Send" }));
    expect(onSend).not.toHaveBeenCalled();
  });
});
