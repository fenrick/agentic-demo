import { apiFetch } from "./http";

/** Simple client for posting control commands to workspace endpoints. */
export async function run(workspaceId: string, topic: string): Promise<void> {
  await post(`/workspaces/${workspaceId}/run`, { topic });
}

/** Retry the graph using the last inputs. */
export async function retry(workspaceId: string): Promise<void> {
  await post(`/workspaces/${workspaceId}/retry`);
}

/** Helper performing POST requests and surfacing failures. */
async function post(
  url: string,
  body?: Record<string, unknown>,
): Promise<void> {
  const res = await apiFetch(url, {
    method: "POST",
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    throw new Error(`Control request failed for ${url}`);
  }
}

export default { run, retry };
