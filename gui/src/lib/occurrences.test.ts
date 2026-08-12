import { describe, expect, it } from 'vitest';
import type { OccurrenceContract, OccurrenceGroup } from './bridge';
import {
  availableWheels,
  drawNumbersForWheel,
  formatLottoNumber,
  referencePosition,
  wheelSummary
} from './occurrences';

const group: OccurrenceGroup = {
  reference: { draw_number: 128, draw_date: '2026-08-11' },
  range: {
    newest: { draw_number: 128, draw_date: '2026-08-11' },
    oldest: { draw_number: 127, draw_date: '2026-08-08' }
  },
  actual_size: 2,
  draws: [
    {
      draw_number: 128,
      draw_date: '2026-08-11',
      wheels: [
        { wheel: 'Bari', numbers: [1, 22, 33, 44, 55] },
        { wheel: 'Roma', numbers: [1, 2, 3, 4, 5] }
      ]
    }
  ],
  wheels: [
    {
      wheel: 'Bari',
      reference_numbers: [1, 22, 33, 44, 55],
      occurrence_counts: [2, 1, 1, 1, 1]
    },
    {
      wheel: 'Roma',
      reference_numbers: [1, 2, 3, 4, 5],
      occurrence_counts: [1, 1, 1, 1, 1]
    }
  ]
};

const report: OccurrenceContract = {
  schema: 'lotto.occurrence-groups',
  schema_version: 1,
  number_representation: {
    type: 'integer',
    minimum: 1,
    maximum: 90,
    display_width: 2
  },
  reference: {
    draw_number: 128,
    draw_date: '2026-08-11',
    kind: 'automatico'
  },
  group_size: 2,
  groups: [group]
};

describe('occurrence presentation helpers', () => {
  it('preserves the leading-zero display contract', () => {
    expect(formatLottoNumber(1)).toBe('01');
    expect(formatLottoNumber(90)).toBe('90');
    expect(() => formatLottoNumber(0)).toThrow(RangeError);
  });

  it('keeps same-wheel numbers isolated', () => {
    expect(drawNumbersForWheel(group.draws[0], 'Bari')).toEqual([1, 22, 33, 44, 55]);
    expect(drawNumbersForWheel(group.draws[0], 'Roma')).toEqual([1, 2, 3, 4, 5]);
    expect(wheelSummary(group, 'Bari')?.occurrence_counts).toEqual([2, 1, 1, 1, 1]);
  });

  it('maps a hit to the exact reference position', () => {
    const reference = [1, 22, 33, 44, 55];
    expect(referencePosition(33, reference)).toBe(2);
    expect(referencePosition(77, reference)).toBeNull();
  });

  it('derives wheel order from the structured report', () => {
    expect(availableWheels(report)).toEqual(['Bari', 'Roma']);
  });
});
