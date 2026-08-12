import { describe, expect, it } from 'vitest';
import { formatResearchValue } from './research';

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
