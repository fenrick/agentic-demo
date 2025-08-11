import React, { useEffect, useState } from "react";
import { SunIcon, MoonIcon, DeviceDesktopIcon } from "@primer/octicons-react";
import { Button } from "@primer/react";
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
    const apply = (mode: "light" | "dark" | "system") => {
      const root = document.documentElement;
      root.setAttribute("data-color-mode", mode === "system" ? "auto" : mode);
      root.setAttribute("data-light-theme", "light");
      root.setAttribute("data-dark-theme", "dark_dimmed");
      localStorage.setItem("theme", mode);
      const res = mode === "system" ? (mql.matches ? "dark" : "light") : mode;
      document.dispatchEvent(new CustomEvent("theme-change", { detail: res }));
      // keep meta theme-color in sync (see next point)
      const meta = document.querySelector('meta[name="theme-color"]');
      if (meta)
        meta.setAttribute("content", res === "dark" ? "#0d1117" : "#ffffff");
    };
    apply(theme);
    if (theme === "system") {
      const handler = () => apply("system");
      mql.addEventListener("change", handler);
      return () => mql.removeEventListener("change", handler);
    }
  }, [mql, theme]);

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="invisible"
          size="small"
          aria-pressed={resolved === "dark"}
        >
          {resolved === "dark" ? <SunIcon size={16} /> : <MoonIcon size={16} />}
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
            <SunIcon className="h-4 w-4" /> Light
          </DropdownMenuRadioItem>
          <DropdownMenuRadioItem
            value="dark"
            className="flex items-center gap-2"
          >
            <MoonIcon className="h-4 w-4" /> Dark
          </DropdownMenuRadioItem>
          <DropdownMenuRadioItem
            value="system"
            className="flex items-center gap-2"
          >
            <DeviceDesktopIcon className="h-4 w-4" /> System
          </DropdownMenuRadioItem>
        </DropdownMenuRadioGroup>
      </DropdownMenuContent>
    </DropdownMenu>
  );
};

export default ThemeToggle;
