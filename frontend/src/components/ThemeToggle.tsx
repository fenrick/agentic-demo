import React, { useEffect, useState } from "react";
import { Moon, Sun, Monitor } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
} from "@radix-ui/react-dropdown-menu";

/**
 * Allows the user to switch between light and dark themes.
 * Focus is returned to the trigger button when the menu closes.
 */
const ThemeToggle: React.FC = () => {
  const [theme, setTheme] = useState<"light" | "dark" | "system">(() => {
    const saved = localStorage.getItem("theme") as
      | "light"
      | "dark"
      | "system"
      | null;
    return saved || "system";
  });
  const mql = window.matchMedia("(prefers-color-scheme: dark)");
  const resolved =
    theme === "system" ? (mql.matches ? "dark" : "light") : theme;

  useEffect(() => {
    const apply = (t: "light" | "dark") => {
      document.documentElement.classList.toggle("dark", t === "dark");
      localStorage.setItem("theme", theme);
      document.dispatchEvent(new CustomEvent("theme-change", { detail: t }));
      // keep meta theme-color in sync (see next point)
      const meta = document.querySelector('meta[name="theme-color"]');
      if (meta)
        meta.setAttribute("content", t === "dark" ? "#0d1117" : "#ffffff");
    };
    apply(resolved);
    if (theme === "system") {
      const handler = () =>
        apply(
          window.matchMedia("(prefers-color-scheme: dark)").matches
            ? "dark"
            : "light",
        );
      mql.addEventListener("change", handler);
      return () => mql.removeEventListener("change", handler);
    }
  }, [mql, resolved, theme]);

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="outline"
          size="icon"
          aria-pressed={resolved === "dark"}
        >
          {resolved === "dark" ? (
            <Sun className="h-4 w-4" />
          ) : (
            <Moon className="h-4 w-4" />
          )}
          <span className="sr-only">Toggle theme</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuRadioGroup
          value={theme}
          onValueChange={(value) =>
            setTheme(value as "light" | "dark" | "system")
          }
        >
          <DropdownMenuRadioItem
            value="light"
            className="flex items-center gap-2"
          >
            <Sun className="h-4 w-4" /> Light
          </DropdownMenuRadioItem>
          <DropdownMenuRadioItem
            value="dark"
            className="flex items-center gap-2"
          >
            <Moon className="h-4 w-4" /> Dark
          </DropdownMenuRadioItem>
          <DropdownMenuRadioItem
            value="system"
            className="flex items-center gap-2"
          >
            <Monitor className="h-4 w-4" /> System
          </DropdownMenuRadioItem>
        </DropdownMenuRadioGroup>
      </DropdownMenuContent>
    </DropdownMenu>
  );
};

export default ThemeToggle;
