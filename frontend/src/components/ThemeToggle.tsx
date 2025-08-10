import React, { useEffect, useState } from "react";

const ThemeToggle: React.FC = () => {
  const [dark, setDark] = useState<boolean>(() => {
    const saved = localStorage.getItem("theme");
    if (saved) return saved === "dark";
    return window.matchMedia?.("(prefers-color-scheme: dark)").matches ?? false;
  });

  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
    localStorage.setItem("theme", dark ? "dark" : "light");
  }, [dark]);

  return (
    <button
      type="button"
      onClick={() => setDark((v) => !v)}
      aria-pressed={dark}
      className="rounded-full border border-black/10 px-3 py-2 text-sm shadow-sm transition hover:bg-black/5 dark:border-white/15 dark:hover:bg-white/10"
    >
      {dark ? "🌙 Dark" : "☀️ Light"}
    </button>
  );
};

export default ThemeToggle;
