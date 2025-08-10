import React from "react";
import { useVirtualizer } from "@tanstack/react-virtual";
import { SseEvent } from "../store/useWorkspaceStore";

interface Props {
  logs: SseEvent[];
}

/**
 * Displays log events with virtualization to handle long lists efficiently.
 */
const LogPanel: React.FC<Props> = ({ logs }) => {
  if (!logs?.length)
    return <p className="text-sm text-gray-500">No activity yet.</p>;

  const parentRef = React.useRef<HTMLDivElement>(null);
  const rowVirtualizer = useVirtualizer({
    count: logs.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 32,
  });

  return (
    <div ref={parentRef} className="max-h-64 overflow-auto">
      <ul
        style={{
          height: `${rowVirtualizer.getTotalSize()}px`,
          position: "relative",
        }}
      >
        {rowVirtualizer.getVirtualItems().map((virtualRow) => {
          const log = logs[virtualRow.index];
          return (
            <li
              key={virtualRow.key}
              ref={rowVirtualizer.measureElement}
              data-index={virtualRow.index}
              className="absolute right-0 left-0 flex items-start gap-2 text-sm"
              style={{
                transform: `translateY(${virtualRow.start}px)`,
                top: 0,
              }}
            >
              <span className="inline-flex h-6 shrink-0 items-center rounded-full border px-2 capitalize">
                {log.type}
              </span>
              <time className="text-gray-500">
                {new Date(log.timestamp).toLocaleTimeString()}
              </time>
            </li>
          );
        })}
      </ul>
    </div>
  );
};

export default LogPanel;
