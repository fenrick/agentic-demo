import React from "react";
import { Button } from "@primer/react";
import { toast } from "sonner";
import controlClient from "../api/controlClient";
import { useWorkspaceStore } from "../store/useWorkspaceStore";

interface Props {
  workspaceId: string;
}

// Renders basic graph controls.
const ControlsPanel: React.FC<Props> = ({ workspaceId }) => {
  const { status, setStatus, topics } = useWorkspaceStore();

  const onRunClick = async () => {
    const topic = topics[0];
    if (!topic) return;
    console.info(`Running workspace ${workspaceId} with topic "${topic}"`);
    try {
      await controlClient.run(workspaceId, topic);
      setStatus("running");
    } catch (err) {
      console.error("Run failed", err);
      toast.error("Run failed");
    }
  };

  const onRetryClick = async () => {
    try {
      await controlClient.retry(workspaceId);
      setStatus("running");
    } catch {
      toast.error("Retry failed");
    }
  };

  const runDisabled = status === "running" || topics.length === 0;

  return (
    <div className="d-flex flex-wrap flex-items-center">
      <Button
        onClick={onRunClick}
        className="mr-3"
        aria-busy={status === "running"}
        disabled={runDisabled}
        variant="primary"
      >
        {status === "running" ? "Running…" : "Run"}
      </Button>
      <Button onClick={onRetryClick} disabled={status === "running"}>
        Retry
      </Button>
    </div>
  );
};

export default ControlsPanel;
