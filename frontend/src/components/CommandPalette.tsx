import React, { useEffect, useRef, useState } from "react";
import * as Dialog from "@radix-ui/react-dialog";
import controlClient from "../api/controlClient";
import exportClient from "../api/exportClient";
import { useWorkspaceStore } from "../store/useWorkspaceStore";

interface Command {
  name: string;
  action: () => Promise<void> | void;
  disabled?: boolean;
}

/**
 * Command palette component bound to Cmd/Ctrl+K.
 * Provides quick actions for running, retrying and exporting a workspace.
 */
const CommandPalette: React.FC = () => {
  const workspaceId = useWorkspaceStore((s) => s.workspaceId);
  const setStatus = useWorkspaceStore((s) => s.setStatus);
  const topics = useWorkspaceStore((s) => s.topics);
  const [open, setOpen] = useState(false);
  const firstItemRef = useRef<HTMLButtonElement | null>(null);
  const previouslyFocusedRef = useRef<HTMLElement | null>(null);

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

  useEffect(() => {
    if (open) {
      previouslyFocusedRef.current = document.activeElement as HTMLElement;
      requestAnimationFrame(() => firstItemRef.current?.focus());
    } else {
      previouslyFocusedRef.current?.focus();
    }
  }, [open]);

  const commands: Command[] = [
    {
      name: "Run",
      disabled: topics.length === 0,
      action: async () => {
        if (!workspaceId) return;
        const topic = topics[0];
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

  return (
    <Dialog.Root open={open} onOpenChange={setOpen}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-50 bg-black/50" />
        <Dialog.Content
          aria-label="Command palette"
          aria-modal="true"
          aria-describedby=""
          className="fixed left-1/2 top-1/4 z-50 w-full max-w-md -translate-x-1/2 rounded-md bg-white p-2 shadow-lg focus:outline-none"
        >
          <Dialog.Title className="sr-only">Command palette</Dialog.Title>
          <ul>
            {commands.map((cmd, idx) => (
              <li key={cmd.name}>
                <button
                  ref={idx === 0 ? firstItemRef : undefined}
                  className="w-full rounded p-2 text-left hover:bg-gray-100 disabled:opacity-50"
                  onClick={() => !cmd.disabled && cmd.action()}
                  disabled={cmd.disabled}
                >
                  {cmd.name}
                </button>
              </li>
            ))}
          </ul>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
};

export default CommandPalette;
