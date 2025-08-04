import React, { useEffect, useState } from "react";
import { getCitation, type Citation } from "../api/citationClient";
import { useWorkspaceStore } from "../store/useWorkspaceStore";

interface Props {
  citationId: string;
}

/**
 * Displays citation metadata in a simple popover.
 */
const CitationPopover: React.FC<Props> = ({ citationId }) => {
  const [data, setData] = useState<Citation | null>(null);
  const workspaceId = useWorkspaceStore((s) => s.workspaceId);

  useEffect(() => {
    const loadMetadata = async () => {
      if (!workspaceId) return;
      try {
        const meta = await getCitation(workspaceId, citationId);
        setData(meta);
      } catch (err) {
        console.error("Failed to load citation", err);
      }
    };
    loadMetadata();
  }, [workspaceId, citationId]);

  if (!data) return <div>Loading...</div>;

  return (
    <div className="citation-popover">
      <div>{data.title}</div>
      <div>{data.url}</div>
      <div>{data.retrieved_at}</div>
      <div>{data.licence}</div>
    </div>
  );
};

export default CitationPopover;
