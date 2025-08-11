import "@testing-library/jest-dom";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import ThemeToggle from "@/components/ThemeToggle";
import { ThemeProvider } from "@primer/react";

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
    document.documentElement.removeAttribute("data-color-mode");
    document.documentElement.removeAttribute("data-light-theme");
    document.documentElement.removeAttribute("data-dark-theme");
  });

  it("returns focus to trigger after selecting a theme", async () => {
    render(
      <ThemeProvider>
        <ThemeToggle />
      </ThemeProvider>,
    );
    const trigger = screen.getByRole("button", { name: "Theme" });
    await userEvent.click(trigger);
    await userEvent.click(screen.getByText("Dark"));
    await waitFor(() => expect(trigger).toHaveFocus());
    await waitFor(() =>
      expect(document.documentElement).toHaveAttribute(
        "data-color-mode",
        "dark",
      ),
    );
  });
});
