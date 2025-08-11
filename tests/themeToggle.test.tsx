import "@testing-library/jest-dom";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import ThemeToggle from "@/components/ThemeToggle";

describe("ThemeToggle", () => {
  beforeAll(() => {
    Object.defineProperty(window, "matchMedia", {
      writable: true,
      value: vi.fn().mockImplementation((query) => ({
        matches: false,
        media: query,
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
      })),
    });
  });
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
