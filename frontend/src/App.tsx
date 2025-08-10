import React, { useEffect } from "react";
import DocumentPanel from "./components/DocumentPanel";
import LogPanel from "./components/LogPanel";
import SourcesPanel from "./components/SourcesPanel";
import ControlsPanel from "./components/ControlsPanel";
import DownloadsPanel from "./components/DownloadsPanel";
import DataEntryForm from "./components/DataEntryForm";
import ThemeToggle from "./components/ThemeToggle";
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
      <Toaster />
      <header className="sticky top-0 z-30 border-b border-black/5 backdrop-blur supports-[backdrop-filter]:bg-white/70 dark:border-white/10 dark:supports-[backdrop-filter]:bg-gray-950/70">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
          <h1 className="text-base font-semibold tracking-tight">
            Lecture Builder
          </h1>
          <ThemeToggle />
        </div>
      </header>

      <main className="mx-auto grid max-w-6xl gap-4 p-4 md:grid-cols-3">
        <section className="space-y-4 md:col-span-2">
          <div className="card">
            <DataEntryForm />
          </div>
          <div className="card">
            <DocumentPanel text={document} onAcceptDiff={() => {}} />
          </div>
        </section>
        <aside className="space-y-4">
          <div className="card">
            <ControlsPanel workspaceId={workspaceId!} />
          </div>
          <div className="card">
            <LogPanel logs={logs} />
          </div>
          <div className="card">
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
