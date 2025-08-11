import React, { useEffect } from "react";
import DocumentPanel from "./components/DocumentPanel";
import LogPanel from "./components/LogPanel";
import SourcesPanel from "./components/SourcesPanel";
import ControlsPanel from "./components/ControlsPanel";
import DownloadsPanel from "./components/DownloadsPanel";
import DataEntryForm from "./components/DataEntryForm";
import ThemeToggle from "./components/ThemeToggle";
import CommandPalette from "./components/CommandPalette";
import { useWorkspaceStore } from "./store/useWorkspaceStore";
import { Toaster } from "./components/ui/sonner";
import { PageLayout } from "@primer/react";

// Top-level layout component that connects to the workspace stream
// and renders the various panels bound to the global workspace store.
const App: React.FC = () => {
  const connect = useWorkspaceStore((s) => s.connect);
  const document = useWorkspaceStore((s) => s.document);
  const logs = useWorkspaceStore((s) => s.logs);
  const sources = useWorkspaceStore((s) => s.sources);
  const workspaceId = useWorkspaceStore((s) => s.workspaceId);
  const exportStatus = useWorkspaceStore((s) => s.exportStatus);

  useEffect(() => {
    connect("default");
  }, [connect]);

  return (
    <>
      <CommandPalette />
      <Toaster />
      <PageLayout>
        <PageLayout.Header
          sx={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            p: 3,
            position: "sticky",
            top: 0,
            borderBottom: "1px solid",
            borderColor: "border.default",
          }}
        >
          <h1 className="h4 m-0">Lecture Builder</h1>
          <ThemeToggle />
        </PageLayout.Header>
        <PageLayout.Content sx={{ p: 3 }}>
          <div className="card mb-3">
            <DataEntryForm />
          </div>
          <div className="card">
            <DocumentPanel text={document} onAcceptDiff={() => {}} />
          </div>
        </PageLayout.Content>
        <PageLayout.Pane position="end" sx={{ p: 3 }}>
          <div className="card mb-3">
            <ControlsPanel workspaceId={workspaceId!} />
          </div>
          <div className="card mb-3">
            <LogPanel logs={logs} />
          </div>
          <div className="card mb-3">
            <SourcesPanel sources={sources} />
          </div>
          {workspaceId && exportStatus === "ready" && (
            <div className="card">
              <DownloadsPanel workspaceId={workspaceId} />
            </div>
          )}
        </PageLayout.Pane>
      </PageLayout>
    </>
  );
};

export default App;
