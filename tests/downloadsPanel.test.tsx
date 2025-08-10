import "@testing-library/jest-dom";
import { render, screen, waitFor } from "@testing-library/react";
import { vi } from "vitest";

vi.mock("sonner", () => ({ toast: { success: vi.fn() } }));

vi.mock("@/api/exportClient", () => {
  const getStatus = vi.fn().mockResolvedValue({ ready: true });
  const getUrls = vi.fn().mockResolvedValue({
    md: "/md",
    docx: "/docx",
    pdf: "/pdf",
    zip: "/zip",
  });
  return {
    __esModule: true,
    default: { getStatus, getUrls },
    getStatus,
    getUrls,
  };
});

import DownloadsPanel from "@/components/DownloadsPanel";
import exportClient from "@/api/exportClient";
import { toast } from "sonner";

describe("DownloadsPanel", () => {
  it("shows toast when export completes", async () => {
    const client = exportClient as unknown as {
      getStatus: ReturnType<typeof vi.fn>;
      getUrls: ReturnType<typeof vi.fn>;
    };

    render(<DownloadsPanel workspaceId="1" />);

    await waitFor(() => expect(client.getStatus).toHaveBeenCalled());
    await waitFor(() =>
      expect(screen.getByText("Markdown")).toBeInTheDocument(),
    );
    expect(vi.mocked(toast.success)).toHaveBeenCalledWith("Export ready!");
  });
});
