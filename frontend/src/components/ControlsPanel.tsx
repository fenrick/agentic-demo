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
    <div className="flex flex-wrap items-center gap-3">
      <button
        onClick={onRunClick}
        className="btn"
        aria-busy={status === "running"}
      >
        {status === "running" ? "Running…" : "Run"}
      </button>
      <button
        onClick={onPauseClick}
        disabled={status !== "running"}
        className="btn disabled:opacity-50"
      >
        Pause
      </button>
      <button
        onClick={onRetryClick}
        disabled={status === "running"}
        className="btn disabled:opacity-50"
      >
        Retry
      </button>
      <button
        onClick={onResumeClick}
        disabled={status !== "paused"}
        className="btn disabled:opacity-50"
      >
        Resume
      </button>
      <label className="text-sm" htmlFor="model">
        Model
      </label>
      <select
        id="model"
        value={model}
        onChange={onModelChange}
        className="rounded-lg border border-black/10 bg-white/80 px-3 py-2 text-sm shadow-sm dark:border-white/15 dark:bg-gray-900/80"
      >
        <option value="o4-mini">o4-mini</option>
        <option value="o3">o3</option>
      </select>
    </div>
  );
};

export default ControlsPanel;
