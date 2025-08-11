import "@testing-library/jest-dom";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { vi } from "vitest";

vi.mock("sonner", () => ({ toast: { error: vi.fn() } }));

vi.mock("@/api/controlClient", () => ({
  __esModule: true,
  default: {
    run: vi.fn().mockRejectedValue(new Error("fail")),
    retry: vi.fn(),
  },
}));

import ControlsPanel from "@/components/ControlsPanel";
import controlClient from "@/api/controlClient";
import { toast } from "sonner";
import { useWorkspaceStore } from "../frontend/src/store/useWorkspaceStore";

it("shows error toast on run failure", async () => {
  useWorkspaceStore.setState({ topics: ["topic"], status: "idle" });
  const infoSpy = vi.spyOn(console, "info").mockImplementation(() => {});
  const errorSpy = vi.spyOn(console, "error").mockImplementation(() => {});
  const client = controlClient as unknown as {
    run: ReturnType<typeof vi.fn>;
  };
  render(<ControlsPanel workspaceId="1" />);
  fireEvent.click(screen.getByText("Run"));
  await waitFor(() => expect(client.run).toHaveBeenCalledWith("1", "topic"));
  await waitFor(() =>
    expect(infoSpy).toHaveBeenCalledWith(
      'Running workspace 1 with topic "topic"',
    ),
  );
  await waitFor(() =>
    expect(errorSpy).toHaveBeenCalledWith("Run failed", expect.any(Error)),
  );
  await waitFor(() =>
    expect(vi.mocked(toast.error)).toHaveBeenCalledWith("Run failed"),
  );
});

it("disables run button with no topics", () => {
  useWorkspaceStore.setState({ topics: [], status: "idle" });
  render(<ControlsPanel workspaceId="1" />);
  expect(screen.getByText("Run")).toBeDisabled();
});
