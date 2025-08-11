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

const App: React.FC = () => {
  const connect = useWorkspaceStore((s) => s.connect);
  const documentText = useWorkspaceStore((s) => s.document);
  const logs = useWorkspaceStore((s) => s.logs);
  const sources = useWorkspaceStore((s) => s.sources);
  const workspaceId = useWorkspaceStore((s) => s.workspaceId);
  const exportStatus = useWorkspaceStore((s) => s.exportStatus);

  // Connect to the default workspace on mount.
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
            bg: "canvas.default",
            zIndex: 1,
          }}
        >
          <h1 style={{ margin: 0, fontSize: 20, fontWeight: 600 }}>
            Lecture Builder
          </h1>
          <ThemeToggle />
        </PageLayout.Header>

        <PageLayout.Content sx={{ p: 3 }}>
          <div className="card" style={{ marginBottom: "var(--base-size-16)" }}>
            <DataEntryForm />
          </div>

          <div className="card">
            <DocumentPanel text={documentText} onAcceptDiff={() => {}} />
          </div>
        </PageLayout.Content>

        <PageLayout.Pane position="end" sx={{ p: 3, width: 360 }}>
          <div className="card" style={{ marginBottom: "var(--base-size-16)" }}>
            <ControlsPanel workspaceId={workspaceId ?? "default"} />
          </div>

          <div className="card" style={{ marginBottom: "var(--base-size-16)" }}>
            <LogPanel logs={logs} />
          </div>

          <div className="card">
            <SourcesPanel sources={sources} />
          </div>

          {workspaceId && exportStatus === "ready" && (
            <div className="card" style={{ marginTop: "var(--base-size-16)" }}>
              <DownloadsPanel workspaceId={workspaceId} />
            </div>
          )}
        </PageLayout.Pane>
      </PageLayout>
    </>
  );
};

export default App;
