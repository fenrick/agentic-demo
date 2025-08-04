export interface ExportStatus {
  ready: boolean;
}

export type ExportUrls = Record<'md' | 'docx' | 'pdf' | 'zip', string>;

/** Retrieve current export generation status for a workspace. */
export async function getStatus(
  workspaceId: string,
): Promise<ExportStatus> {
  const res = await fetch(`/workspaces/${workspaceId}/export/status`);
  if (!res.ok) {
    throw new Error('Failed to fetch export status');
  }
  return res.json();
}

/** Fetch download URLs for generated export artifacts. */
export async function getUrls(
  workspaceId: string,
): Promise<ExportUrls> {
  const res = await fetch(`/workspaces/${workspaceId}/export/urls`);
  if (!res.ok) {
    throw new Error('Failed to fetch export URLs');
  }
  return res.json();
}

export default { getStatus, getUrls };
