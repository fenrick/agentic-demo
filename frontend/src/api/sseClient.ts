// Utility for connecting to server-sent event streams for a workspace.
// Includes basic reconnect logic with a fixed backoff.
export function connectToWorkspaceStream(
  workspaceId: string,
  channel = "state",
): EventSource {
  const url = `/stream/${workspaceId}/${channel}`;
  let source = new EventSource(url);

  source.onerror = () => {
    source.close();
    setTimeout(() => {
      source = connectToWorkspaceStream(workspaceId, channel);
    }, 1000);
  };

  return source;
}
