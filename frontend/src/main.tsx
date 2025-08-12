import React from "react";
import { createRoot } from "react-dom/client";
import { ThemeProvider, BaseStyles, Box } from "@primer/react";
import App from "./App";
import "./index.css";

createRoot(document.getElementById("root")!).render(
  <ThemeProvider colorMode="auto" dayScheme="light" nightScheme="dark_dimmed">
    <BaseStyles>
      {/* This wrapper owns the page background */}
      <Box sx={{ bg: "canvas.default", color: "fg.default", minHeight: "100vh" }}>
        <App />
      </Box>
    </BaseStyles>
  </ThemeProvider>
);
