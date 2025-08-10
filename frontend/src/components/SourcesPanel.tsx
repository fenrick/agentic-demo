import React from "react";

interface SourceItem {
  url?: string;
  title?: string;
}

interface Props {
  sources: (SourceItem | string)[];
}

// Display source links with hostnames.
const SourcesPanel: React.FC<Props> = ({ sources }) => {
  if (!sources?.length)
    return <p className="text-sm text-gray-500">No sources yet.</p>;
  return (
    <ul className="space-y-2">
      {sources.map((s, idx) => {
        const url = typeof s === "string" ? s : s.url;
        const title = typeof s === "string" ? s : (s.title ?? s.url);
        const host = url ? new URL(url).host : "";
        return (
          <li key={idx} className="text-sm">
            <a
              href={url}
              target="_blank"
              rel="noreferrer"
              className="underline decoration-black/30 hover:decoration-black dark:decoration-white/30"
            >
              {title}
            </a>
            {host && <span className="text-gray-500"> — {host}</span>}
          </li>
        );
      })}
    </ul>
  );
};

export default SourcesPanel;
