import "@testing-library/jest-dom";
import { render, screen } from "@testing-library/react";
import SourcesPanel from "@/components/SourcesPanel";

describe("SourcesPanel", () => {
  it("shows skeleton when empty", () => {
    render(<SourcesPanel sources={[]} />);
    expect(screen.getByTestId("sources-skeleton")).toBeInTheDocument();
  });

  it("renders sources when provided", () => {
    const sources = ["https://example.com"];
    render(<SourcesPanel sources={sources} />);
    expect(screen.queryByTestId("sources-skeleton")).toBeNull();
    expect(screen.getByText("https://example.com")).toBeInTheDocument();
  });

  it("ignores invalid source URLs", () => {
    const sources = ["not a url"];
    render(<SourcesPanel sources={sources} />);
    expect(screen.getByText("not a url")).toBeInTheDocument();
    expect(screen.queryByText(/—/)).toBeNull();
  });
});
