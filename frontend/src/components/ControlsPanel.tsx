import React from "react";
import { toast } from "sonner";
import controlClient from "../api/controlClient";
import { useWorkspaceStore } from "../store/useWorkspaceStore";

interface Props {
  workspaceId: string;
}

// Renders basic graph controls.
const ControlsPanel: React.FC<Props> = ({ workspaceId }) => {
  const { status, setStatus } = useWorkspaceStore();

  const onRunClick = async () => {
    try {
      await controlClient.run(workspaceId);
      setStatus("running");
    } catch {
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

  return (
    <div className="flex flex-wrap items-center gap-3">
      <button
        onClick={onRunClick}
        className="btn"
        aria-busy={status === "running"}
      >
        {status === "running" ? "Running…" : "Run"}
      </button>
      <button
        onClick={onRetryClick}
        disabled={status === "running"}
        className="btn disabled:opacity-50"
      >
        Retry
      </button>
    </div>
  );
};

export default ControlsPanel;
