/**
 * Utility types and functions to compute token-level diffs between two strings.
 * The diff is used to animate live document updates in the DocumentPanel.
 */

/**
 * Represents a single change in the diff sequence.
 * - `type` describes how the token was changed.
 * - `token` is the text content of the token.
 */
export interface DiffPatch {
  type: 'equal' | 'insert' | 'delete';
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
 * Computes a diff between two strings at the token level using a
 * longest-common-subsequence approach.
 *
 * @param oldText - Previous document text.
 * @param newText - Incoming document text.
 * @returns Sequence of `DiffPatch` objects describing changes.
 */
export function computeDiff(oldText: string, newText: string): DiffPatch[] {
  const oldTokens = tokenize(oldText);
  const newTokens = tokenize(newText);
  const m = oldTokens.length;
  const n = newTokens.length;

  // Dynamic programming table for LCS lengths.
  const dp: number[][] = Array.from({ length: m + 1 }, () =>
    Array(n + 1).fill(0),
  );
  for (let i = m - 1; i >= 0; i -= 1) {
    for (let j = n - 1; j >= 0; j -= 1) {
      dp[i][j] =
        oldTokens[i] === newTokens[j]
          ? dp[i + 1][j + 1] + 1
          : Math.max(dp[i + 1][j], dp[i][j + 1]);
    }
  }

  // Walk the table to build the diff patches.
  const patches: DiffPatch[] = [];
  let i = 0;
  let j = 0;
  while (i < m && j < n) {
    if (oldTokens[i] === newTokens[j]) {
      patches.push({ type: 'equal', token: oldTokens[i] });
      i += 1;
      j += 1;
    } else if (dp[i + 1][j] >= dp[i][j + 1]) {
      patches.push({ type: 'delete', token: oldTokens[i] });
      i += 1;
    } else {
      patches.push({ type: 'insert', token: newTokens[j] });
      j += 1;
    }
  }
  while (i < m) {
    patches.push({ type: 'delete', token: oldTokens[i] });
    i += 1;
  }
  while (j < n) {
    patches.push({ type: 'insert', token: newTokens[j] });
    j += 1;
  }
  return patches;
}
