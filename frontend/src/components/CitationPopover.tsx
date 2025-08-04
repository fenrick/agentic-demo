import React, { useEffect, useState } from 'react';
import { getCitation, type Citation } from '../api/citationClient';

interface Props {
  citationId: string;
}

/**
 * Displays citation metadata in a simple popover.
 */
const CitationPopover: React.FC<Props> = ({ citationId }) => {
  const [data, setData] = useState<Citation | null>(null);

  useEffect(() => {
    const loadMetadata = async () => {
      try {
        const meta = await getCitation('default', citationId);
        setData(meta);
      } catch (err) {
        console.error('Failed to load citation', err);
      }
    };
    loadMetadata();
  }, [citationId]);

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
