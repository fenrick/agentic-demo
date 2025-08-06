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
    <div className="max-w-4xl mx-auto p-4 space-y-4">
      <div className="bg-white rounded shadow p-4">
        <DataEntryForm />
      </div>
      <div className="bg-white rounded shadow p-4">
        <DocumentPanel text={document || ""} onAcceptDiff={() => {}} />
      </div>
      <div className="bg-white rounded shadow p-4">
        <LogPanel logs={logs} />
      </div>
      <div className="bg-white rounded shadow p-4">
        <SourcesPanel sources={sources} />
      </div>
      {workspaceId && (
        <div className="bg-white rounded shadow p-4">
          <ControlsPanel workspaceId={workspaceId} />
        </div>
      )}
      {workspaceId && exportStatus === "ready" && (
        <div className="bg-white rounded shadow p-4">
          <DownloadsPanel workspaceId={workspaceId} />
        </div>
      )}
    </div>
  );
};

export default App;
