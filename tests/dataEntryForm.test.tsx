import "@testing-library/jest-dom";
import { render, screen, fireEvent } from "@testing-library/react";
import DataEntryForm from "@/components/DataEntryForm";

describe("DataEntryForm", () => {
  it("adds entries to tracking table", () => {
    render(<DataEntryForm />);
    fireEvent.change(screen.getByLabelText(/name/i), {
      target: { value: "Alice" },
    });
    fireEvent.change(screen.getByLabelText(/email/i), {
      target: { value: "alice@example.com" },
    });
    fireEvent.click(screen.getByRole("button", { name: /add/i }));
    expect(screen.getByText("Alice")).toBeInTheDocument();
    expect(screen.getByText("alice@example.com")).toBeInTheDocument();
  });
});
