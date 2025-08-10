// Utility for connecting to server-sent event streams for a workspace.
// Includes basic reconnect logic with a fixed backoff.
export function connectToWorkspaceStream(
  workspaceId: string,
  token: string,
  channel = "messages",
): EventSource {
  const url = `/stream/${workspaceId}/${channel}?token=${token}`;
  let source = new EventSource(url);

  source.onerror = () => {
    source.close();
    setTimeout(() => {
      source = connectToWorkspaceStream(workspaceId, token, channel);
    }, 1000);
  };

  return source;
}
