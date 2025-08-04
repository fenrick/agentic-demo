import React, { useEffect } from "react";
import DocumentPanel from "./components/DocumentPanel";
import LogPanel from "./components/LogPanel";
import SourcesPanel from "./components/SourcesPanel";
import DownloadsPanel from "./components/DownloadsPanel";
import { useWorkspaceStore } from "./store/useWorkspaceStore";

// Top-level layout component that connects to the workspace stream
// and renders the various panels bound to the global workspace store.
const App: React.FC = () => {
  const connect = useWorkspaceStore((s) => s.connect);
  const document = useWorkspaceStore((s) => s.document) as string;
  const logs = useWorkspaceStore((s) => s.logs);
  const sources = useWorkspaceStore((s) => s.sources);
  const workspaceId = useWorkspaceStore((s) => s.workspaceId);

  useEffect(() => {
    connect("default");
  }, [connect]);

  return (
    <div>
      <DocumentPanel text={document || ""} onAcceptDiff={() => {}} />
      <LogPanel logs={logs} />
      <SourcesPanel sources={sources} />
      {workspaceId && <DownloadsPanel workspaceId={workspaceId} />}
    </div>
  );
};

export default App;
