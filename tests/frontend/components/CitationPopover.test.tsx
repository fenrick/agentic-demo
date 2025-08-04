import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import CitationPopover from "../../../frontend/src/components/CitationPopover";
import * as citationClient from "../../../frontend/src/api/citationClient";
import { useWorkspaceStore } from "../../../frontend/src/store/useWorkspaceStore";

describe("CitationPopover", () => {
  it("loads and displays citation metadata", async () => {
    vi.spyOn(citationClient, "getCitation").mockResolvedValue({
      url: "https://example.com",
      title: "Example Title",
      retrieved_at: "2024-01-01",
      licence: "CC-BY",
    });

    useWorkspaceStore.setState({ workspaceId: "ws1" });

    render(<CitationPopover citationId="abc" />);

    expect(await screen.findByText("Example Title")).toBeDefined();
    expect(screen.getByText("https://example.com")).toBeDefined();
    expect(screen.getByText("2024-01-01")).toBeDefined();
    expect(screen.getByText("CC-BY")).toBeDefined();
    expect(citationClient.getCitation).toHaveBeenCalledWith("ws1", "abc");
  });
});
