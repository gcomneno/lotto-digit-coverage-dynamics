import { describe, expect, it } from 'vitest';
import {
  filterResearchRows,
  formatResearchValue,
  uniqueResearchValues
} from './research';

const twinRows = [
  { condition: 'baseline', twin: 11, candidate: false },
  { condition: 'missing', twin: 11, candidate: true },
  { condition: 'missing', twin: 22, candidate: false }
];

describe('research value formatting', () => {
  it('keeps probability formatting in the presentation layer', () => {
    expect(formatResearchValue(0.6816, 'percentage')).toBe('68.16%');
    expect(formatResearchValue(-0.011, 'percentage-signed')).toBe('-1.10%');
    expect(formatResearchValue(0.011, 'percentage-signed')).toBe('+1.10%');
  });

  it('uses the Lotto two-digit display rule only for lotto-number fields', () => {
    expect(formatResearchValue(1, 'lotto-number')).toBe('01');
    expect(formatResearchValue(1, 'integer')).toBe('1');
  });

  it('labels exploratory candidates without turning them into recommendations', () => {
    expect(formatResearchValue(true, 'candidate')).toBe('CANDIDATO');
    expect(formatResearchValue(false, 'candidate')).toBe('—');
  });
});

describe('research table presentation filters', () => {
  it('filters twin rows without changing the underlying report', () => {
    expect(filterResearchRows(twinRows, { condition: 'missing' })).toHaveLength(2);
    expect(filterResearchRows(twinRows, { twin: 11 })).toHaveLength(2);
    expect(filterResearchRows(twinRows, { candidatesOnly: true })).toEqual([
      { condition: 'missing', twin: 11, candidate: true }
    ]);
    expect(twinRows).toHaveLength(3);
  });

  it('derives stable condition and twin choices from report rows', () => {
    expect(uniqueResearchValues(twinRows, 'condition')).toEqual(['baseline', 'missing']);
    expect(uniqueResearchValues(twinRows, 'twin')).toEqual([11, 22]);
  });
});
