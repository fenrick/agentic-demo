import React from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import "./index.css";
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

// Bootstraps the React application and mounts it to the DOM root element.
const container = document.getElementById("root");
if (container) {
  const root = createRoot(container);
  root.render(<App />);
}
