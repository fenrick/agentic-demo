import "@testing-library/jest-dom";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import ThemeToggle from "@/components/ThemeToggle";

describe("ThemeToggle", () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.classList.remove("dark");
  });

  it("returns focus to trigger after selecting a theme", async () => {
    render(<ThemeToggle />);
    const trigger = screen.getByRole("button", { name: /toggle theme/i });
    await userEvent.click(trigger);
    await userEvent.click(screen.getByText("Dark"));
    await waitFor(() => expect(trigger).toHaveFocus());
    await waitFor(() => expect(document.documentElement).toHaveClass("dark"));
  });
});
