import React from "react";
import { createRoot } from "react-dom/client";
import { ThemeProvider, BaseStyles } from "@primer/react";
import App from "./App";
import "./index.css";
import "github-markdown-css";
import { configure } from "@pydantic/logfire-browser";
import { FetchInstrumentation } from "@opentelemetry/instrumentation-fetch";

const traceUrl = import.meta.env.VITE_LOGFIRE_TRACE_URL as string | undefined;
if (traceUrl) {
  configure({
    traceUrl,
    serviceName: import.meta.env.VITE_LOGFIRE_PROJECT,
    instrumentations: [new FetchInstrumentation()],
  });
}

// Seed a development JWT so API requests succeed without a login flow.
// Token payload: {"role":"user"}
if (import.meta.env.DEV && !localStorage.getItem("jwt")) {
  localStorage.setItem(
    "jwt",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoidXNlciJ9.hM2ErG_O2e4d9YiCeVoTbiRDoo4ziDiIPfDFE40GUlg",
  );
}

// Bootstraps the React application and mounts it to the DOM root element.
const container = document.getElementById("root");
if (container) {
  const root = createRoot(container);
  root.render(
<ThemeProvider colorMode="auto" dayScheme="light" nightScheme="dark_dimmed" preventSSRMismatch>
  <BaseStyles>
    <App />
  </BaseStyles>
</ThemeProvider>,
  );
}
