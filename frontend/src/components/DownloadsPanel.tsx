import React, { useEffect, useState } from "react";
import { toast } from "sonner";
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
            toast.success("Export ready!");
          }
          clearInterval(interval);
        }
      } catch {
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
    return <div className="text-sm text-gray-500">Preparing export…</div>;
  }

  return (
    <>
      <div className="flex gap-4">
        <a className="text-blue-600 hover:underline" href={urls.md}>
          Markdown
        </a>
        <a className="text-blue-600 hover:underline" href={urls.docx}>
          DOCX
        </a>
        <a className="text-blue-600 hover:underline" href={urls.pdf}>
          PDF
        </a>
        <a className="text-blue-600 hover:underline" href={urls.zip}>
          ZIP
        </a>
      </div>
    </>
  );
};

export default DownloadsPanel;
