import { apiFetch } from "./http";

/** Simple client for posting control commands to workspace endpoints. */
export async function run(workspaceId: string): Promise<void> {
  await post(`/workspaces/${workspaceId}/run`);
}

/** Pause the graph execution for a workspace. */
export async function pause(workspaceId: string): Promise<void> {
  await post(`/workspaces/${workspaceId}/pause`);
}

/** Retry the graph using the last inputs. */
export async function retry(workspaceId: string): Promise<void> {
  await post(`/workspaces/${workspaceId}/retry`);
}

/** Resume a previously paused graph. */
export async function resume(workspaceId: string): Promise<void> {
  await post(`/workspaces/${workspaceId}/resume`);
}

/** Select the model to run subsequent operations against. */
export async function selectModel(
  workspaceId: string,
  model: string,
): Promise<void> {
  await post(`/workspaces/${workspaceId}/model`, { model });
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

export default { run, pause, retry, resume, selectModel };
