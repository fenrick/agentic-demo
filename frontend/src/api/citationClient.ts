export interface Citation {
  url: string;
  title: string;
  retrieved_at: string;
  licence: string;
}

export async function getCitation(
  workspaceId: string,
  citationId: string,
): Promise<Citation> {
  const res = await fetch(
    `/workspaces/${workspaceId}/citations/${citationId}`,
  );
  if (!res.ok) {
    throw new Error(`Failed to fetch citation ${citationId}`);
  }
  return res.json();
}

export default { getCitation };
