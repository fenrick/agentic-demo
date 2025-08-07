import React, { useEffect } from "react";
import DocumentPanel from "./components/DocumentPanel";
import LogPanel from "./components/LogPanel";
import SourcesPanel from "./components/SourcesPanel";
import ControlsPanel from "./components/ControlsPanel";
import DownloadsPanel from "./components/DownloadsPanel";
import DataEntryForm from "./components/DataEntryForm";
import { useWorkspaceStore } from "./store/useWorkspaceStore";

// Top-level layout component that connects to the workspace stream
// and renders the various panels bound to the global workspace store.
const App: React.FC = () => {
  const connect = useWorkspaceStore((s) => s.connect);
  const document = useWorkspaceStore((s) => s.document) as string;
  const logs = useWorkspaceStore((s) => s.logs);
  const sources = useWorkspaceStore((s) => s.sources);
  const workspaceId = useWorkspaceStore((s) => s.workspaceId);
  const exportStatus = useWorkspaceStore((s) => s.exportStatus);

  useEffect(() => {
    connect("default");
  }, [connect]);

  return (
    <div className="mx-auto max-w-4xl space-y-6 p-6">
      <div className="card">
        <DataEntryForm />
      </div>
      <div className="card">
        <DocumentPanel text={document || ""} onAcceptDiff={() => {}} />
      </div>
      <div className="card">
        <LogPanel logs={logs} />
      </div>
      <div className="card">
        <SourcesPanel sources={sources} />
      </div>
      {workspaceId && (
        <div className="card">
          <ControlsPanel workspaceId={workspaceId} />
        </div>
      )}
      {workspaceId && exportStatus === "ready" && (
        <div className="card">
          <DownloadsPanel workspaceId={workspaceId} />
        </div>
      )}
    </div>
  );
};

export default App;
