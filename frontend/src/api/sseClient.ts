// Utility for connecting to server-sent event streams for a workspace.
// Includes basic reconnect logic with a fixed backoff.
export function connectToWorkspaceStream(
  token?: string,
  channel = "state",
): EventSource {
  const url = token
    ? `/stream/${channel}?token=${token}`
    : `/stream/${channel}`;
  let source = new EventSource(url);

  source.onerror = () => {
    source.close();
    setTimeout(() => {
      source = connectToWorkspaceStream(token, channel);
    }, 1000);
  };

  return source;
}
