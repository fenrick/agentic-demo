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

it("shows error toast on run failure", async () => {
  vi.spyOn(window, "prompt").mockReturnValue("topic");
  const client = controlClient as unknown as {
    run: ReturnType<typeof vi.fn>;
  };
  render(<ControlsPanel workspaceId="1" />);
  fireEvent.click(screen.getByText("Run"));
  await waitFor(() => expect(client.run).toHaveBeenCalledWith("1", "topic"));
  await waitFor(() =>
    expect(vi.mocked(toast.error)).toHaveBeenCalledWith("Run failed"),
  );
});
