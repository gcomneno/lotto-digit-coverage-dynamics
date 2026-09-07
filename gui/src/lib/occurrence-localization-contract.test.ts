import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';

const source = readFileSync(
  new URL('../components/OccurrenceExplorer.svelte', import.meta.url),
  'utf8',
);

describe('OccurrenceExplorer localization boundary', () => {
  it('keeps locale out of the occurrenceGroups request payload', () => {
    const call = source.match(/bridge\.occurrenceGroups\(([\s\S]*?)\);/);

    expect(call).not.toBeNull();
    expect(call?.[1]).toContain('groupSize');
    expect(call?.[1]).toContain('requestedDraw ?? null');
    expect(call?.[1]).toContain('occurrenceLimit ?? null');
    expect(call?.[1]).not.toContain('locale');
  });

  it('preserves the three existing validation predicates', () => {
    expect(source).toContain('!Number.isInteger(groupSize) || groupSize <= 0');
    expect(source).toContain('!Number.isInteger(occurrenceLimit) || occurrenceLimit <= 0');
    expect(source).toContain('!Number.isInteger(requestedDraw) || requestedDraw <= 0');
  });

  it('renders structured occurrence values directly from the report', () => {
    for (const expression of [
      'report.reference.draw_number',
      'report.reference.draw_date',
      'report.reference.kind',
      'report.group_size',
      'report.occurrence_limit',
      'report.examined_draw_count',
      'report.groups.length',
      'group.reference.draw_number',
      'group.actual_size',
      'summary.occurrence_counts[index]',
      'summary.total_occurrences',
      'report.grand_total_occurrences',
    ]) {
      expect(source).toContain(expression);
    }
  });
});
