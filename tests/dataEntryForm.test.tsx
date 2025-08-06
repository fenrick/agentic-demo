import "@testing-library/jest-dom";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { vi } from "vitest";
import DataEntryForm from "@/components/DataEntryForm";

describe("DataEntryForm", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    global.fetch = vi
      .fn()
      .mockResolvedValueOnce({ ok: true, json: async () => [] })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ id: 1, topic: "Graph Theory" }),
      });
  });

  it("adds entries to tracking table", async () => {
    render(<DataEntryForm />);
    fireEvent.change(screen.getByPlaceholderText(/enter topic/i), {
      target: { value: "Graph Theory" },
    });
    fireEvent.click(screen.getByRole("button", { name: /add/i }));

    await waitFor(() => {
      expect(screen.getByText("Graph Theory")).toBeInTheDocument();
    });
    expect(global.fetch).toHaveBeenCalledWith(
      "/entries",
      expect.objectContaining({ method: "POST" }),
    );
  });
});
