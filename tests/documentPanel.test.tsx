import "@testing-library/jest-dom";
import { render, screen } from "@testing-library/react";
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
