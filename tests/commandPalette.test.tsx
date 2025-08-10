import { act, fireEvent, render, screen } from "@testing-library/react";
import { vi } from "vitest";
import CommandPalette from "../frontend/src/components/CommandPalette";
import { useWorkspaceStore } from "../frontend/src/store/useWorkspaceStore";
import controlClient from "../frontend/src/api/controlClient";

vi.mock("../frontend/src/api/controlClient", () => ({
  default: { run: vi.fn(), retry: vi.fn() },
}));

vi.mock("../frontend/src/api/exportClient", () => ({
  default: { getUrls: vi.fn() },
}));

describe("CommandPalette", () => {
  beforeEach(() => {
    useWorkspaceStore.setState({ workspaceId: "abc", status: "idle" });
  });

  it("opens with Cmd+K and triggers run", async () => {
    render(<CommandPalette />);
    await act(async () => {
      fireEvent.keyDown(window, { key: "k", metaKey: true });
    });
    const runButton = await screen.findByText("Run");
    await act(async () => {
      fireEvent.click(runButton);
    });
    expect((controlClient as any).run).toHaveBeenCalledWith("abc");
  });
});
