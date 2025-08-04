import create from 'zustand';
import { connectToWorkspaceStream } from '../api/sseClient';

export interface SseEvent {
  type: string;
  payload: Record<string, unknown>;
  timestamp: string;
}

interface WorkspaceStore {
  document: unknown;
  logs: SseEvent[];
  sources: unknown[];
  exportStatus: string;
  connect: (workspaceId: string) => void;
  updateState: (event: SseEvent) => void;
}

// Global workspace state accessed throughout the UI.
export const useWorkspaceStore = create<WorkspaceStore>((set, get) => ({
  document: null,
  logs: [],
  sources: [],
  exportStatus: 'idle',
  connect: (workspaceId: string) => {
    const es = connectToWorkspaceStream(workspaceId);
    es.onmessage = (e: MessageEvent) => {
      try {
        const event: SseEvent = JSON.parse(e.data);
        get().updateState(event);
      } catch (err) {
        console.error('Failed to parse SSE event', err);
      }
    };
  },
  updateState: (event: SseEvent) => {
    switch (event.type) {
      case 'document':
        set({ document: event.payload });
        break;
      case 'log':
        set((state) => ({ logs: [...state.logs, event] }));
        break;
      case 'source':
        set({ sources: Array.isArray(event.payload) ? (event.payload as unknown[]) : [] });
        break;
      case 'export':
        set({ exportStatus: String(event.payload) });
        break;
      default:
        break;
    }
  },
}));

// Selectors provide convenient accessors to slices of the workspace state.
export const documentState = () => useWorkspaceStore.getState().document;
export const logEvents = () => useWorkspaceStore.getState().logs;
export const sources = () => useWorkspaceStore.getState().sources;
export const exportStatus = () => useWorkspaceStore.getState().exportStatus;
