import React from "react";
import controlClient from "../api/controlClient";
import { useWorkspaceStore } from "../store/useWorkspaceStore";

interface Props {
  workspaceId: string;
}

// Renders basic graph controls and a model selector.
const ControlsPanel: React.FC<Props> = ({ workspaceId }) => {
  const { status, model, setStatus, setModel } = useWorkspaceStore();

  const onRunClick = async () => {
    await controlClient.run(workspaceId);
    setStatus("running");
  };

  const onPauseClick = async () => {
    await controlClient.pause(workspaceId);
    setStatus("paused");
  };

  const onRetryClick = async () => {
    await controlClient.retry(workspaceId);
    setStatus("running");
  };

  const onResumeClick = async () => {
    await controlClient.resume(workspaceId);
    setStatus("running");
  };

  const onModelChange = async (e: React.ChangeEvent<HTMLSelectElement>) => {
    const m = e.target.value;
    await controlClient.selectModel(workspaceId, m);
    setModel(m);
  };

  return (
    <div>
      <button onClick={onRunClick} disabled={status === "running"}>
        Run
      </button>
      <button onClick={onPauseClick} disabled={status !== "running"}>
        Pause
      </button>
      <button onClick={onRetryClick} disabled={status === "running"}>
        Retry
      </button>
      <button onClick={onResumeClick} disabled={status !== "paused"}>
        Resume
      </button>
      <select value={model} onChange={onModelChange}>
        <option value="o4-mini">o4-mini</option>
        <option value="o3">o3</option>
      </select>
    </div>
  );
};

export default ControlsPanel;
