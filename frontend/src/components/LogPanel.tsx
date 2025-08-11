import React from "react";
import { useVirtualizer } from "@tanstack/react-virtual";
import { SseEvent } from "../store/useWorkspaceStore";
import { Skeleton } from "./ui/skeleton";
import { Box, Label, Text } from "@primer/react";

interface Props {
  logs: SseEvent[];
}

/**
 * Displays log events with virtualization to handle long lists efficiently.
 */
const LogPanel: React.FC<Props> = ({ logs }) => {
  const parentRef = React.useRef<HTMLDivElement>(null);
  const rowVirtualizer = useVirtualizer({
    count: logs.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 32,
  });

  if (!logs.length)
    return (
      <div data-testid="logs-skeleton" className="stack">
        <Skeleton style={{ height: "1rem", width: "75%" }} />
        <Skeleton style={{ height: "1rem", width: "66%" }} />
        <Skeleton style={{ height: "1rem", width: "50%" }} />
      </div>
    );

  return (
    <Box
      ref={parentRef}
      role="list"
      sx={{ height: 280, overflow: "auto", position: "relative" }}
    >
      <Box sx={{ height: rowVirtualizer.getTotalSize(), position: "relative" }}>
        {rowVirtualizer.getVirtualItems().map((v) => {
          const log = logs[v.index];
          return (
            <Box
              key={v.key}
              role="listitem"
              sx={{
                position: "absolute",
                insetInline: 0,
                transform: `translateY(${v.start}px)`,
              }}
            >
              <Box
                sx={{
                  display: "flex",
                  alignItems: "flex-start",
                  gap: 2,
                  fontSize: 0,
                }}
              >
                <Label variant="secondary" sx={{ textTransform: "capitalize" }}>
                  {log.type}
                </Label>
                <Text sx={{ whiteSpace: "pre-wrap" }}>{log.message}</Text>
              </Box>
            </Box>
          );
        })}
      </Box>
    </Box>
  );
};

export default LogPanel;
