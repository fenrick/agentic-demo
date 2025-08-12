"use client";

import { Toaster as SonnerToaster } from "sonner";
import { useTheme } from "@primer/react";

export function Toaster() {
  const { resolvedColorMode } = useTheme();
  const theme = resolvedColorMode === "night" ? "dark" : "light";
return <SonnerToaster position="bottom-right" richColors theme={theme} />;
}

export default Toaster;
