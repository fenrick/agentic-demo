import { create } from "zustand";
import { connectToWorkspaceStream } from "../api/sseClient";

export interface SseEvent {
  type: string;
  payload: Record<string, unknown>;
  timestamp: string;
}

export type DocState = string;

interface SourceItem {
  url?: string;
  title?: string;
}

interface WorkspaceStore {
  workspaceId: string | null;
  document: DocState;
  logs: SseEvent[];
  sources: (string | SourceItem)[];
  exportStatus: string;
  status: "idle" | "running";
  connect: (workspaceId: string) => void;
  setWorkspaceId: (workspaceId: string | null) => void;
  updateState: (event: SseEvent) => void;
  setStatus: (status: "idle" | "running") => void;
}

// Global workspace state accessed throughout the UI.
export const useWorkspaceStore = create<WorkspaceStore>((set, get) => ({
  workspaceId: null,
  document: "",
  logs: [],
  sources: [],
  exportStatus: "idle",
  status: "idle",
  connect: (workspaceId: string) => {
    set({ workspaceId });
    (async () => {
      try {
        const resp = await fetch("/stream/token");
        const { token } = (await resp.json()) as { token: string };
        const es = connectToWorkspaceStream(token);
        es.onmessage = (e: MessageEvent) => {
          try {
            const event: SseEvent = JSON.parse(e.data);
            get().updateState(event);
          } catch (err) {
            console.error("Failed to parse SSE event", err);
          }
        };
      } catch (err) {
        console.error("Failed to connect to workspace stream", err);
      }
    })();
  },
  setWorkspaceId: (workspaceId) => set({ workspaceId }),
  updateState: (event: SseEvent) => {
    switch (event.type) {
      case "document":
        set({ document: String(event.payload) });
        break;
      case "log":
        set((state) => ({ logs: [...state.logs, event] }));
        break;
      case "source":
        set({
          sources: Array.isArray(event.payload)
            ? (event.payload as (string | SourceItem)[])
            : [],
        });
        break;
      case "export":
        set({ exportStatus: String(event.payload) });
        break;
      default:
        break;
    }
  },
  setStatus: (status) => set({ status }),
}));

// Selectors provide convenient accessors to slices of the workspace state.
export const documentState = () => useWorkspaceStore.getState().document;
export const logEvents = () => useWorkspaceStore.getState().logs;
export const sources = () => useWorkspaceStore.getState().sources;
export const exportStatus = () => useWorkspaceStore.getState().exportStatus;
export const runStatus = () => useWorkspaceStore.getState().status;
export const currentWorkspaceId = () =>
  useWorkspaceStore.getState().workspaceId;
