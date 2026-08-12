import { describe, expect, it, vi } from 'vitest';
import {
  createBridge,
  type Capabilities,
  type CurrentContract,
  type Envelope,
  type OccurrenceContract,
  type PywebviewApi
} from './bridge';

const numberRepresentation = {
  type: 'integer',
  minimum: 1,
  maximum: 90,
  display_width: 2
};

describe('createBridge', () => {
  it('forwards current and occurrence calls without CLI text', async () => {
    const capabilities: Envelope<Capabilities> = {
      ok: true,
      data: {
        bridge_version: 1,
        contracts: [],
        scientific_mode: 'descriptive-research'
      },
      error: null
    };
    const currentPayload: Envelope<CurrentContract> = {
      ok: true,
      data: {
        schema: 'lotto.current',
        schema_version: 1,
        number_representation: numberRepresentation,
        target: { draw_number: 128, draw_date: '2026-08-11' },
        states: [],
        markov_ranking: [],
        coverage_hit_ranking: [],
        consensus: [],
        anomalies: { transition_count: 0, history: [], active: [] },
        next_draw_validation: []
      },
      error: null
    };
    const occurrencePayload: Envelope<OccurrenceContract> = {
      ok: true,
      data: {
        schema: 'lotto.occurrence-groups',
        schema_version: 1,
        number_representation: numberRepresentation,
        reference: {
          draw_number: 128,
          draw_date: '2026-08-11',
          kind: 'automatico'
        },
        group_size: 10,
        groups: []
      },
      error: null
    };
    const api: PywebviewApi = {
      get_capabilities: vi.fn(async () => capabilities),
      get_current: vi.fn(async () => currentPayload),
      get_occurrence_groups: vi.fn(async () => occurrencePayload)
    };

    const bridge = createBridge(api);
    const current = await bridge.current();
    const occurrences = await bridge.occurrenceGroups(10, 120);

    expect(current.data?.schema).toBe('lotto.current');
    expect(occurrences.data?.schema).toBe('lotto.occurrence-groups');
    expect(api.get_current).toHaveBeenCalledOnce();
    expect(api.get_occurrence_groups).toHaveBeenCalledWith(undefined, 10, 120);
  });
});
