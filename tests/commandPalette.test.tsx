import { act, fireEvent, render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import { vi } from "vitest";
import CommandPalette from "../frontend/src/components/CommandPalette";
import { useWorkspaceStore } from "../frontend/src/store/useWorkspaceStore";
import controlClient from "../frontend/src/api/controlClient";

beforeAll(() => {
  // Polyfill ResizeObserver used by Primer components
  // @ts-ignore
  global.ResizeObserver = class {
    observe() {}
    unobserve() {}
    disconnect() {}
  };
});

vi.mock("../frontend/src/api/controlClient", () => ({
  default: { run: vi.fn(), retry: vi.fn() },
}));

vi.mock("../frontend/src/api/exportClient", () => ({
  default: { getUrls: vi.fn() },
}));

describe("CommandPalette", () => {
  beforeEach(() => {
    useWorkspaceStore.setState({
      workspaceId: "abc",
      status: "idle",
      topics: [],
    });
  });

  it("opens with Cmd+K, focuses first item and triggers run", async () => {
    useWorkspaceStore.setState({
      topics: ["topic"],
      workspaceId: "abc",
      status: "idle",
    });
    render(
      <>
        <button>Trigger</button>
        <CommandPalette />
      </>,
    );
    const trigger = screen.getByText("Trigger");
    trigger.focus();
    await act(async () => {
      fireEvent.keyDown(window, { key: "k", metaKey: true });
    });
    const runButton = await screen.findByRole("button", { name: "Run" });
    expect(runButton).toHaveFocus();
    await act(async () => {
      fireEvent.click(runButton);
    });
    expect((controlClient as any).run).toHaveBeenCalledWith("abc", "topic");
    expect(trigger).toHaveFocus();
  });

  it("closes on Escape and restores focus", async () => {
    render(
      <>
        <button>Trigger</button>
        <CommandPalette />
      </>,
    );
    const trigger = screen.getByText("Trigger");
    trigger.focus();
    await act(async () => {
      fireEvent.keyDown(window, { key: "k", metaKey: true });
    });
    const runButton = await screen.findByRole("button", { name: "Run" });
    expect(runButton).toBeInTheDocument();
    await act(async () => {
      fireEvent.keyDown(runButton, { key: "Escape" });
    });
    expect(screen.queryByRole("button", { name: "Run" })).toBeNull();
    expect(trigger).toHaveFocus();
  });
});
