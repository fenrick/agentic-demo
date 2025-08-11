import React, { useEffect, useState } from "react";
import {ActionMenu, ActionList, Button} from '@primer/react'
import {SunIcon, MoonIcon, DeviceDesktopIcon} from '@primer/octicons-react'

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
<ActionMenu>
  <ActionMenu.Anchor>
    <Button>
      Theme
    </Button>
  </ActionMenu.Anchor>
  <ActionMenu.Overlay>
    <ActionList selectionVariant="single">
      <ActionList.Item onSelect={()=>setTheme('light')} selected={theme==='light'}>
        <SunIcon /> Light
      </ActionList.Item>
      <ActionList.Item onSelect={()=>setTheme('dark')} selected={theme==='dark'}>
        <MoonIcon /> Dark
      </ActionList.Item>
      <ActionList.Item onSelect={()=>setTheme('system')} selected={theme==='system'}>
        <DeviceDesktopIcon /> System
      </ActionList.Item>
    </ActionList>
  </ActionMenu.Overlay>
</ActionMenu>
  );
};

export default ThemeToggle;
