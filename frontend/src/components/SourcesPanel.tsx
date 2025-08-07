import React from "react";

interface Props {
  sources: unknown[];
}

// Stub component showing sources related to the workspace.
const SourcesPanel: React.FC<Props> = ({ sources }) => {
  return (
    <ul className="list-disc space-y-1 pl-5 text-sm">
      {sources.map((s, idx) => (
        <li key={idx}>{String(s)}</li>
      ))}
    </ul>
  );
};

export default SourcesPanel;
