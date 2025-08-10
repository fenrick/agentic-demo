import "@testing-library/jest-dom";
import { render, screen } from "@testing-library/react";

import { vi } from "vitest";
import DocumentPanel from "@/components/DocumentPanel";

describe("DocumentPanel", () => {
  it("renders markdown with diff highlights", () => {
    const onAcceptDiff = vi.fn();
    const { rerender } = render(
      <DocumentPanel text="Hello world" onAcceptDiff={onAcceptDiff} />,
    );
    rerender(
      <DocumentPanel
        text="Hello brave new world"
        onAcceptDiff={onAcceptDiff}
      />,
    );
    const marks = screen.getAllByText(/brave|new/);
    expect(marks).toHaveLength(2);
    marks.forEach((m) => {
      expect(m.tagName).toBe("MARK");
      expect(m).toHaveClass("bg-yellow-200");
    });

import DocumentPanel from "@/components/DocumentPanel";

describe("DocumentPanel", () => {
  it("shows skeleton when empty", () => {
    render(<DocumentPanel text="" onAcceptDiff={() => {}} />);
    expect(screen.getByTestId("document-skeleton")).toBeInTheDocument();
  });

  it("renders tokens when text provided", () => {
    render(<DocumentPanel text="Hello" onAcceptDiff={() => {}} />);
    expect(screen.queryByTestId("document-skeleton")).toBeNull();
    expect(screen.getByText("Hello")).toBeInTheDocument();
  });
});
