import React, { useEffect } from 'react';
import DocumentPanel from './components/DocumentPanel';
import LogPanel from './components/LogPanel';
import SourcesPanel from './components/SourcesPanel';
import ExportPanel from './components/ExportPanel';
import { useWorkspaceStore } from './store/useWorkspaceStore';

// Top-level layout component that connects to the workspace stream
// and renders the various panels bound to the global workspace store.
const App: React.FC = () => {
  const connect = useWorkspaceStore((s) => s.connect);
  const document = useWorkspaceStore((s) => s.document);
  const logs = useWorkspaceStore((s) => s.logs);
  const sources = useWorkspaceStore((s) => s.sources);
  const exportStatus = useWorkspaceStore((s) => s.exportStatus);

  useEffect(() => {
    connect('default');
  }, [connect]);

  return (
    <div>
      <DocumentPanel document={document} />
      <LogPanel logs={logs} />
      <SourcesPanel sources={sources} />
      <ExportPanel status={exportStatus} />
    </div>
  );
};

export default App;
