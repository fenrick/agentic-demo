import React, { useEffect, useState } from "react";
import { toast } from "sonner";
import exportClient, { ExportUrls } from "../api/exportClient";
import {Box, Link} from '@primer/react'

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
<Box sx={{display: 'flex', gap: 3}}>
  <Link href={urls.pdf} download>PDF</Link>
  <Link href={urls.md} download>Markdown</Link>
</Box>

    </>
  );
};

export default DownloadsPanel;
