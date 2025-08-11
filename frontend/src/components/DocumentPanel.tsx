import React, { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import rehypeRaw from "rehype-raw";
import rehypeSanitize, { defaultSchema } from "rehype-sanitize";
import { computeDiff, type DiffPatch } from "../utils/diffUtils";
import { Skeleton } from "./ui/skeleton";

interface Props {
  /** Current markdown text to display. */
  text: string;
  /** Callback fired once an incoming diff has been applied. */
  onAcceptDiff: (diffs: DiffPatch[]) => void;
}

/**
 * Renders the live document using a markdown renderer with diff highlights.
 */
const DocumentPanel: React.FC<Props> = ({ text, onAcceptDiff }) => {
  const [rendered, setRendered] = useState<string>(text);
  const prevText = useRef(text);

  useEffect(() => {
    if (prevText.current !== text) {
      const diffs = computeDiff(prevText.current, text);
      const escapeHtml = (t: string) =>
        t.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
      const highlighted = diffs
        .filter((d) => d.type !== "delete")
        .map((d) => {
          const token = escapeHtml(d.token);
          return d.type === "insert"
            ? `<mark class=\"color-bg-attention\">${token}</mark>`
            : token;
        })
        .join("");
      setRendered(highlighted);
      prevText.current = text;
      onAcceptDiff(diffs);
    }
  }, [text, onAcceptDiff]);

  if (text.length === 0) {
    return (
      <div data-testid="document-skeleton" className="stack">
        <Skeleton style={{ height: "1rem", width: "100%" }} />
        <Skeleton style={{ height: "1rem", width: "100%" }} />
        <Skeleton style={{ height: "1rem", width: "66%" }} />
      </div>
    );
  }

  const sanitizeSchema = {
    ...defaultSchema,
    tagNames: [...(defaultSchema.tagNames || []), "mark"],
    attributes: {
      ...defaultSchema.attributes,
      mark: ["className"],
    },
  };

  return (
    <div className="markdown-body" aria-live="polite">
      <ReactMarkdown
        rehypePlugins={[rehypeRaw, [rehypeSanitize, sanitizeSchema]]}
      >
        {rendered}
      </ReactMarkdown>
    </div>
  );
};

export default DocumentPanel;
