import { describe, expect, it } from 'vitest';
import type { ConsensusRow } from './bridge';
import { consensusPresentation } from './consensus';

describe('consensusPresentation', () => {
  it('keeps deficit and predominance wheel provenance separate', () => {
    const row: ConsensusRow = {
      digit: 6,
      missing_count: 3,
      top_count: 1,
      missing_wheels: ['Bari', 'Roma', 'Venezia'],
      top_wheels: ['Genova'],
      involved_wheels: ['Bari', 'Genova', 'Roma', 'Venezia']
    };

    expect(consensusPresentation(row)).toEqual({
      missingWheels: 'Bari, Roma, Venezia',
      topWheels: 'Genova'
    });
  });

  it('renders empty provenance independently', () => {
    const row: ConsensusRow = {
      digit: 4,
      missing_count: 0,
      top_count: 1,
      missing_wheels: [],
      top_wheels: ['Torino'],
      involved_wheels: ['Torino']
    };

    expect(consensusPresentation(row)).toEqual({
      missingWheels: '—',
      topWheels: 'Torino'
    });
  });
});
