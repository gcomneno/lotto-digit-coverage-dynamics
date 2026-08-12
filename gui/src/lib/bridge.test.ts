import { describe, expect, it, vi } from 'vitest';
import {
  createBridge,
  type Capabilities,
  type CurrentContract,
  type Envelope,
  type OccurrenceContract,
  type PywebviewApi,
  type ResearchCatalog,
  type ResearchReport
} from './bridge';

const numberRepresentation = {
  type: 'integer',
  minimum: 1,
  maximum: 90,
  display_width: 2
};

describe('createBridge', () => {
  it('forwards structured calls without CLI text', async () => {
    const capabilities: Envelope<Capabilities> = {
      ok: true,
      data: {
        bridge_version: 2,
        contracts: [],
        research_reports: ['completion'],
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
    const catalogPayload: Envelope<ResearchCatalog> = {
      ok: true,
      data: {
        reports: [
          {
            id: 'completion',
            title: 'Completion',
            summary: 'Summary',
            interpretation: 'Descriptive'
          }
        ]
      },
      error: null
    };
    const researchPayload: Envelope<ResearchReport> = {
      ok: true,
      data: {
        id: 'completion',
        title: 'Completion',
        interpretation: 'Descriptive',
        source: 'historical archive',
        metrics: [],
        tables: [],
        notes: []
      },
      error: null
    };
    const api: PywebviewApi = {
      get_capabilities: vi.fn(async () => capabilities),
      get_current: vi.fn(async () => currentPayload),
      get_occurrence_groups: vi.fn(async () => occurrencePayload),
      get_research_catalog: vi.fn(async () => catalogPayload),
      get_research_report: vi.fn(async () => researchPayload)
    };

    const bridge = createBridge(api);
    const current = await bridge.current();
    const occurrences = await bridge.occurrenceGroups(10, 120);
    const catalog = await bridge.researchCatalog();
    const research = await bridge.researchReport('completion');

    expect(current.data?.schema).toBe('lotto.current');
    expect(occurrences.data?.schema).toBe('lotto.occurrence-groups');
    expect(catalog.data?.reports[0]?.id).toBe('completion');
    expect(research.data?.id).toBe('completion');
    expect(api.get_current).toHaveBeenCalledOnce();
    expect(api.get_occurrence_groups).toHaveBeenCalledWith(undefined, 10, 120);
    expect(api.get_research_catalog).toHaveBeenCalledOnce();
    expect(api.get_research_report).toHaveBeenCalledWith('completion');
  });
});
