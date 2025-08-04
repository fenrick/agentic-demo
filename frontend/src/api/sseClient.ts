// Utility for connecting to the server-sent events workspace stream.
// Includes very basic reconnect logic with a fixed backoff.
export function connectToWorkspaceStream(workspaceId: string): EventSource {
  const url = `/stream/${workspaceId}`;
  let source = new EventSource(url);

  source.onerror = () => {
    source.close();
    setTimeout(() => {
      source = connectToWorkspaceStream(workspaceId);
    }, 1000);
  };

  return source;
}
