// frontend/src/components/ThemeToggle.tsx
// Simple theme toggle that talks directly to Primer's ThemeProvider.
// Persists the user's choice and keeps the mobile address bar colour in sync.

import * as React from "react";
import { useTheme, Button, ButtonGroup } from "@primer/react";

type Mode = "auto" | "day" | "night";

const STORAGE_KEY = "theme-mode";

export default function ThemeToggle() {
  const { setColorMode, colorMode, resolvedColorMode } = useTheme();

  // Load saved preference on mount
  React.useEffect(() => {
    const saved = (localStorage.getItem(STORAGE_KEY) as Mode | null) ?? "auto";
    if (saved === "auto" || saved === "day" || saved === "night") {
      setColorMode(saved);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Keep <meta name="theme-color"> in sync (nice for mobile address bar)
  React.useEffect(() => {
    const ensureMeta = () => {
      let meta = document.querySelector<HTMLMetaElement>('meta[name="theme-color"]');
      if (!meta) {
        meta = document.createElement("meta");
        meta.setAttribute("name", "theme-color");
        document.head.appendChild(meta);
      }
      return meta;
    };

    const meta = ensureMeta();
    const content = resolvedColorMode === "night" ? "#0d1117" : "#ffffff";
    meta.setAttribute("content", content);
  }, [resolvedColorMode]);

  const apply = (next: Mode) => {
    setColorMode(next);
    localStorage.setItem(STORAGE_KEY, next);
  };

  return (
    <ButtonGroup aria-label="Theme">
      <Button
        onClick={() => apply("day")}
        variant={colorMode === "day" ? "primary" : "default"}
      >
        Light
      </Button>
      <Button
        onClick={() => apply("night")}
        variant={colorMode === "night" ? "primary" : "default"}
      >
        Dark
      </Button>
      <Button
        onClick={() => apply("auto")}
        variant={colorMode === "auto" ? "primary" : "default"}
      >
        System
      </Button>
    </ButtonGroup>
  );
}
