import React from "react";
import { SseEvent } from "../store/useWorkspaceStore";

interface Props {
  logs: SseEvent[];
}

// Display log events with type badges and timestamps.
const LogPanel: React.FC<Props> = ({ logs }) => {
  if (!logs?.length)
    return <p className="text-sm text-gray-500">No activity yet.</p>;
  return (
    <ul className="space-y-2">
      {logs.map((log, idx) => (
        <li key={idx} className="flex items-start gap-2 text-sm">
          <span className="inline-flex h-6 shrink-0 items-center rounded-full border px-2 capitalize">
            {log.type}
          </span>
          <time className="text-gray-500">
            {new Date(log.timestamp).toLocaleTimeString()}
          </time>
        </li>
      ))}
    </ul>
  );
};

export default LogPanel;
