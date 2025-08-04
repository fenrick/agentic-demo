import React, { useEffect, useRef, useState } from 'react';
import { computeDiff, tokenize, type DiffPatch } from '../utils/diffUtils';

interface Props {
  /** Current markdown text to display. */
  text: string;
  /** Callback fired once an incoming diff has been applied. */
  onAcceptDiff: (diffs: DiffPatch[]) => void;
}

/** Duration a token stays highlighted (ms). */
const HIGHLIGHT_MS = 1000;
/** Delay between token animations (ms). */
const STEP_MS = 50;

/**
 * Renders the live document with a simple typewriter diff animation.
 */
const DocumentPanel: React.FC<Props> = ({ text, onAcceptDiff }) => {
  const [tokens, setTokens] = useState<string[]>(() => tokenize(text));
  const [highlighted, setHighlighted] = useState<Set<number>>(new Set());
  const prevText = useRef(text);

  // React to incoming text updates from props.
  useEffect(() => {
    if (prevText.current !== text) {
      handleIncomingText(text);
    }
  }, [text]);

  /** Compute the diff and animate inserted tokens. */
  const handleIncomingText = (newText: string) => {
    const diffs = computeDiff(prevText.current, newText);
    animateDiff(diffs, newText);
    prevText.current = newText;
    onAcceptDiff(diffs);
  };

  /** Sequentially highlights inserted tokens to mimic a typewriter. */
  const animateDiff = (diffs: DiffPatch[], newText: string) => {
    const newTokens = tokenize(newText);
    setTokens(newTokens);
    let delay = 0;
    let searchIndex = 0;
    diffs.forEach((d) => {
      if (d.type !== 'insert') return;
      const idx = newTokens.indexOf(d.token, searchIndex);
      if (idx === -1) return;
      searchIndex = idx + 1;
      setTimeout(() => {
        setHighlighted((prev) => new Set(prev).add(idx));
        setTimeout(() => {
          setHighlighted((prev) => {
            const copy = new Set(prev);
            copy.delete(idx);
            return copy;
          });
        }, HIGHLIGHT_MS);
      }, delay);
      delay += STEP_MS;
    });
  };

  return (
    <div>
      {tokens.map((t, i) => (
        <span key={i} className={highlighted.has(i) ? 'highlight' : ''}>
          {t}
        </span>
      ))}
    </div>
  );
};

export default DocumentPanel;
