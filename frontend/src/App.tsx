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
      <header className="position-sticky top-0 border-bottom color-border-muted">
        <div className="mx-auto d-flex flex-items-center flex-justify-between p-3">
          <h1 className="h4 m-0">Lecture Builder</h1>
          <ThemeToggle />
        </div>
      </header>

      <main className="mx-auto p-3 d-flex flex-column flex-lg-row">
        <section className="flex-1 d-flex flex-column">
          <div className="card mb-3">
            <DataEntryForm />
          </div>
          <div className="card">
            <DocumentPanel text={document} onAcceptDiff={() => {}} />
          </div>
        </section>
        <aside className="flex-1 d-flex flex-column ml-lg-3">
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
        </aside>
      </main>
    </>
  );
};

export default App;
