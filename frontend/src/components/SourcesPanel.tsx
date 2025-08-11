import React from "react";
import { Skeleton } from "./ui/skeleton";

interface SourceItem {
  url?: string;
  title?: string;
}

interface Props {
  sources: (SourceItem | string)[];
}

// Display source links with hostnames.
const SourcesPanel: React.FC<Props> = ({ sources }) => {
  if (!sources.length)
    return (
      <div data-testid="sources-skeleton" className="stack">
        <Skeleton className="h-4 w-2/3" />
        <Skeleton className="h-4 w-1/3" />
      </div>
    );
  return (
    <ul className="stack">
      {sources.map((s, idx) => {
        const url = typeof s === "string" ? s : s.url;
        const title = typeof s === "string" ? s : (s.title ?? s.url);
        let host = "";
        try {
          host = url ? new URL(url).host : "";
        } catch {
          // ignore malformed URLs
        }
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
