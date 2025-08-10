import "@testing-library/jest-dom";
import { render, screen } from "@testing-library/react";
import LogPanel from "@/components/LogPanel";

describe("LogPanel", () => {
  it("shows skeleton when empty", () => {
    render(<LogPanel logs={[]} />);
    expect(screen.getByTestId("logs-skeleton")).toBeInTheDocument();
  });

  it("renders log entries when provided", () => {
    const logs = [
      {
        type: "info",
        payload: {},
        timestamp: new Date().toISOString(),
      },
    ];
    render(<LogPanel logs={logs} />);
    expect(screen.queryByTestId("logs-skeleton")).toBeNull();
    expect(screen.getByRole("list")).toBeInTheDocument();
  });
});
