// Utility for connecting to server-sent event streams.
// Includes basic reconnect logic with a fixed backoff.
export function connectToWorkspaceStream(
  token?: string,
  channel = "messages",
): EventSource {
  const url = token
    ? `/stream/${channel}?token=${encodeURIComponent(token)}`
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
