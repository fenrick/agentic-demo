import React from 'react';

interface Props {
  status: string;
}

// Stub component indicating export status.
const ExportPanel: React.FC<Props> = ({ status }) => {
  return <div>Export status: {status}</div>;
};

export default ExportPanel;
