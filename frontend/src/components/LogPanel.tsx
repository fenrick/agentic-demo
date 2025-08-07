import React from "react";
import { SseEvent } from "../store/useWorkspaceStore";

interface Props {
  logs: SseEvent[];
}

// Stub component rendering log events.
const LogPanel: React.FC<Props> = ({ logs }) => {
  return (
    <ul className="space-y-1 text-sm">
      {logs.map((log, idx) => (
        <li key={idx}>{log.type}</li>
      ))}
    </ul>
  );
};

export default LogPanel;
