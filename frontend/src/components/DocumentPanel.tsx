import React from 'react';

interface Props {
  document: unknown;
}

// Stub component displaying the current document state.
const DocumentPanel: React.FC<Props> = ({ document }) => {
  return <div>{JSON.stringify(document)}</div>;
};

export default DocumentPanel;
