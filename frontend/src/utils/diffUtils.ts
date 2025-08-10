/**
 * Utility types and functions to compute token-level diffs between two strings.
 * The diff is used to animate live document updates in the DocumentPanel.
 */

import {
  diff_match_patch,
  DIFF_DELETE,
  DIFF_EQUAL,
  DIFF_INSERT,
} from "diff-match-patch";
const dmp = new diff_match_patch();
const SEP = "\u0000";

/**
 * Represents a single change in the diff sequence.
 * - `type` describes how the token was changed.
 * - `token` is the text content of the token.
 */
export interface DiffPatch {
  type: "equal" | "insert" | "delete";
  token: string;
}

/**
 * Splits a block of text into tokens while preserving whitespace.
 *
 * @param text - Raw markdown string.
 * @returns Array of tokens including words and whitespace.
 */
export function tokenize(text: string): string[] {
  return text.split(/(\s+)/).filter((t) => t.length > 0);
}

/**
 * Computes a diff between two strings at the token level using
 * Google's `diff-match-patch` algorithm.
 *
 * @param oldText - Previous document text.
 * @param newText - Incoming document text.
 * @returns Sequence of `DiffPatch` objects describing changes.
 */
export function computeDiff(oldText: string, newText: string): DiffPatch[] {
  const oldTokens = tokenize(oldText);
  const newTokens = tokenize(newText);
  const diffs = dmp.diff_main(oldTokens.join(SEP), newTokens.join(SEP), false);
  dmp.diff_cleanupEfficiency(diffs);

  const patches: DiffPatch[] = [];
  for (const [op, data] of diffs) {
    const tokens = data.split(SEP).filter((t) => t.length > 0);
    tokens.forEach((token) => {
      if (op === DIFF_EQUAL) {
        patches.push({ type: "equal", token });
      } else if (op === DIFF_INSERT) {
        patches.push({ type: "insert", token });
      } else if (op === DIFF_DELETE) {
        patches.push({ type: "delete", token });
      }
    });
  }
  return patches;
}
