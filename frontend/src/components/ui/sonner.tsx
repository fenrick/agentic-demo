"use client";

import { useEffect, useState } from "react";
import { Toaster as SonnerToaster } from "sonner";

export function Toaster() {
  const [theme, setTheme] = useState<"light" | "dark">(
    document.documentElement.classList.contains("dark") ? "dark" : "light",
  );

  useEffect(() => {
    const handler = (e: Event) => {
      const newTheme = (e as CustomEvent<"light" | "dark">).detail;
      setTheme(newTheme);
    };
    document.addEventListener("theme-change", handler);
    return () => document.removeEventListener("theme-change", handler);
  }, []);

  return <SonnerToaster position="bottom-right" richColors theme={theme} />;
}

export default Toaster;
