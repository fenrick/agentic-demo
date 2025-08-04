import { describe, expect, it } from 'vitest';
import { computeDiff } from '../../../frontend/src/utils/diffUtils';

describe('computeDiff', () => {
  it('detects inserted tokens', () => {
    const before = 'hello world';
    const after = 'hello brave new world';
    const diffs = computeDiff(before, after);
    const inserts = diffs.filter((d) => d.type === 'insert').map((d) => d.token.trim());
    expect(inserts).toContain('brave');
    expect(inserts).toContain('new');
  });
});
