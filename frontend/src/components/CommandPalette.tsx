import React, { useEffect, useState } from "react";
import controlClient from "../api/controlClient";
import exportClient from "../api/exportClient";
import { useWorkspaceStore } from "../store/useWorkspaceStore";

interface Command {
  name: string;
  action: () => Promise<void> | void;
}

/**
 * Command palette component bound to Cmd/Ctrl+K.
 * Provides quick actions for running, retrying and exporting a workspace.
 */
const CommandPalette: React.FC = () => {
  const workspaceId = useWorkspaceStore((s) => s.workspaceId);
  const setStatus = useWorkspaceStore((s) => s.setStatus);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setOpen((o) => !o);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  const commands: Command[] = [
    {
      name: "Run",
      action: async () => {
        if (!workspaceId) return;
        const topic = window.prompt("Enter topic");
        if (!topic) return;
        await controlClient.run(workspaceId, topic);
        setStatus("running");
        setOpen(false);
      },
    },
    {
      name: "Retry",
      action: async () => {
        if (!workspaceId) return;
        await controlClient.retry(workspaceId);
        setStatus("running");
        setOpen(false);
      },
    },
    {
      name: "Export",
      action: async () => {
        if (!workspaceId) return;
        try {
          const urls = await exportClient.getUrls(workspaceId);
          window.open(urls.md, "_blank");
        } catch (err) {
          console.error("Failed to fetch export URLs", err);
        }
        setOpen(false);
      },
    },
  ];

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center bg-black/50 pt-24"
      role="dialog"
    >
      <div className="w-full max-w-md rounded-md bg-white p-2 shadow-lg">
        <ul>
          {commands.map((cmd) => (
            <li key={cmd.name}>
              <button
                className="w-full rounded p-2 text-left hover:bg-gray-100"
                onClick={() => cmd.action()}
              >
                {cmd.name}
              </button>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
};

export default CommandPalette;
