import { act, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import DownloadsPanel from "../../../frontend/src/components/DownloadsPanel";
import exportClient from "../../../frontend/src/api/exportClient";

describe("DownloadsPanel", () => {
  it("polls until ready and renders links", async () => {
    vi.useFakeTimers();
    const statusMock = vi
      .spyOn(exportClient, "getStatus")
      .mockResolvedValueOnce({ ready: false })
      .mockResolvedValueOnce({ ready: true });
    const urlsMock = vi.spyOn(exportClient, "getUrls").mockResolvedValue({
      md: "/md",
      docx: "/docx",
      pdf: "/pdf",
      zip: "/zip",
    });

    render(<DownloadsPanel workspaceId="ws1" />);

    expect(statusMock).toHaveBeenCalledTimes(1);

    await vi.runOnlyPendingTimersAsync();
    await vi.runOnlyPendingTimersAsync();

    expect(statusMock).toHaveBeenCalledTimes(2);
    expect(urlsMock).toHaveBeenCalledWith("ws1");
    expect(screen.getByText("Markdown").getAttribute("href")).toBe("/md");

    await vi.runOnlyPendingTimersAsync();
    expect(statusMock).toHaveBeenCalledTimes(2);
    vi.useRealTimers();
  });
});
