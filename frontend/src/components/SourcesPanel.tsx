import React from 'react';

interface Props {
  sources: unknown[];
}

// Stub component showing sources related to the workspace.
const SourcesPanel: React.FC<Props> = ({ sources }) => {
  return (
    <ul>
      {sources.map((s, idx) => (
        <li key={idx}>{String(s)}</li>
      ))}
    </ul>
  );
};

export default SourcesPanel;
