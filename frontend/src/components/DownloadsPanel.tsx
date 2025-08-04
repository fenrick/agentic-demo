import React, { useEffect, useState } from "react";
import exportClient, { ExportUrls } from "../api/exportClient";

interface Props {
  workspaceId: string;
}

// Polls export status and renders download links when ready.
const DownloadsPanel: React.FC<Props> = ({ workspaceId }) => {
  const [urls, setUrls] = useState<ExportUrls | null>(null);

  useEffect(() => {
    let interval: number;
    let cancelled = false;

    const poll = async () => {
      try {
        const status = await exportClient.getStatus(workspaceId);
        if (status.ready) {
          const u = await exportClient.getUrls(workspaceId);
          if (!cancelled) {
            setUrls(u);
          }
          clearInterval(interval);
        }
      } catch (err) {
        // ignore transient errors and retry on next tick
      }
    };

    poll();
    interval = window.setInterval(poll, 2000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [workspaceId]);

  if (!urls) {
    return <div>Preparing export…</div>;
  }

  return (
    <div>
      <a href={urls.md}>Markdown</a>
      <a href={urls.docx}>DOCX</a>
      <a href={urls.pdf}>PDF</a>
      <a href={urls.zip}>ZIP</a>
    </div>
  );
};

export default DownloadsPanel;
