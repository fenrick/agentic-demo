import "@testing-library/jest-dom";
import { render, screen } from "@testing-library/react";
import SourcesPanel from "@/components/SourcesPanel";

describe("SourcesPanel", () => {
  it("shows placeholder when empty", () => {
    render(<SourcesPanel sources={[]} />);
    expect(screen.getByText("No sources yet")).toBeInTheDocument();
  });

  it("renders sources when provided", () => {
    const sources = ["https://example.com"];
    render(<SourcesPanel sources={sources} />);
    expect(screen.queryByText("No sources yet")).toBeNull();
    expect(screen.getByText("example.com/")).toBeInTheDocument();
  });

  it("displays host for valid URLs", () => {
    const sources = ["https://example.com/path"];
    render(<SourcesPanel sources={sources} />);
    expect(screen.getByText(/— example\.com/)).toBeInTheDocument();
  });

  it("ignores invalid URLs", () => {
    const sources = ["not a url"];
    render(<SourcesPanel sources={sources} />);
    expect(screen.getByText("No sources yet")).toBeInTheDocument();
  });
});
