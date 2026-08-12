export type GuiError = {
  type: string;
  message: string;
};

export type Envelope<T> = {
  ok: boolean;
  data: T | null;
  error: GuiError | null;
};

export type CurrentState = {
  wheel: string;
  wheel_order: number;
  latest_draw: number;
  latest_date: string;
  completed_cycles: number;
  draws_in_cycle: number;
  covered_digits: number[];
  missing_digits: number[];
  most_present_digits: number[];
  synchronized: boolean;
};

export type MarkovRow = {
  position: number;
  wheel: string;
  wheel_order: number;
  expected_remaining_draws: number;
  completion_within: Record<string, number>;
};

export type CoverageHitRow = {
  position: number;
  wheel: string;
  wheel_order: number;
  draws_in_cycle: number;
  class: {
    most_present_count: number;
    missing_count: number;
  };
  most_present_digits: number[];
  missing_digits: number[];
  historical: {
    threshold: number;
    cases: number;
    obtained: number;
    success_rate: number;
    expected_probability: number;
    evidence_level: string;
  };
  current_event_probability: number;
  completion_within_one: number;
  lower_success_bound: number;
  conservative_excess: number;
  conservative_probability: number;
};

export type ConsensusRow = {
  digit: number;
  missing_count: number;
  top_count: number;
  missing_wheels: string[];
  top_wheels: string[];
  involved_wheels: string[];
};

export type AnomalyRow = {
  category: string;
  signature: string;
  recurrence_key: string;
  wheel: string;
  wheel_order: number;
  cycle_number: number;
  event_index: number;
  target_draw: number;
  target_date: string;
  source_state: string;
  target_state: string;
  horizon: number | null;
  conditional_probability: number;
  atom_probability: number | null;
  previous_conditional_probability: number | null;
  pair_probability: number | null;
  surprisal: number;
  severity: string;
  right_censored: boolean;
  previous_target_draw: number | null;
  previous_target_date: string | null;
  recurrence_gap: number | null;
};

export type ValidationDraw = {
  draw_number: number;
  draw_date: string;
  wheel: string;
  wheel_order: number;
  numbers: number[];
};

export type CurrentContract = {
  schema: 'lotto.current';
  schema_version: number;
  number_representation: {
    type: string;
    minimum: number;
    maximum: number;
    display_width: number;
  };
  target: {
    draw_number: number;
    draw_date: string;
  };
  states: CurrentState[];
  markov_ranking: MarkovRow[];
  coverage_hit_ranking: CoverageHitRow[];
  consensus: ConsensusRow[];
  anomalies: {
    transition_count: number;
    history: AnomalyRow[];
    active: AnomalyRow[];
  };
  next_draw_validation: ValidationDraw[];
};

export type OccurrenceDrawWheel = {
  wheel: string;
  numbers: number[];
};

export type OccurrenceDraw = {
  draw_number: number;
  draw_date: string;
  wheels: OccurrenceDrawWheel[];
};

export type OccurrenceWheelSummary = {
  wheel: string;
  reference_numbers: number[];
  occurrence_counts: number[];
};

export type OccurrenceGroup = {
  reference: {
    draw_number: number;
    draw_date: string;
  };
  range: {
    newest: {
      draw_number: number;
      draw_date: string;
    };
    oldest: {
      draw_number: number;
      draw_date: string;
    };
  };
  actual_size: number;
  draws: OccurrenceDraw[];
  wheels: OccurrenceWheelSummary[];
};

export type OccurrenceContract = {
  schema: 'lotto.occurrence-groups';
  schema_version: number;
  number_representation: {
    type: string;
    minimum: number;
    maximum: number;
    display_width: number;
  };
  reference: {
    draw_number: number;
    draw_date: string;
    kind: string;
  };
  group_size: number;
  groups: OccurrenceGroup[];
};

export type ResearchCatalogItem = {
  id: string;
  title: string;
  summary: string;
  interpretation: string;
};

export type ResearchMetric = {
  label: string;
  value: string | number | boolean | null;
  format: string;
};

export type ResearchColumn = {
  key: string;
  label: string;
  format: string;
};

export type ResearchTable = {
  title: string;
  columns: ResearchColumn[];
  rows: Array<Record<string, string | number | boolean | null>>;
};

export type ResearchReport = {
  id: string;
  title: string;
  interpretation: string;
  source: string;
  metrics: ResearchMetric[];
  tables: ResearchTable[];
  notes: string[];
};

export type ResearchCatalog = {
  reports: ResearchCatalogItem[];
};

export type Capabilities = {
  bridge_version: number;
  contracts: Array<{ schema: string; version: number }>;
  research_reports: string[];
  scientific_mode: string;
};

export type PywebviewApi = {
  get_capabilities(): Promise<Envelope<Capabilities>>;
  get_current(
    database?: string,
    to_draw_number?: number | null,
    to_date?: string | null,
    use_checkpoint?: boolean
  ): Promise<Envelope<CurrentContract>>;
  get_occurrence_groups(
    database?: string,
    group_size?: number,
    requested_draw_number?: number | null
  ): Promise<Envelope<OccurrenceContract>>;
  get_research_catalog(): Promise<Envelope<ResearchCatalog>>;
  get_research_report(report_id: string): Promise<Envelope<ResearchReport>>;
};

export type LottoBridge = {
  capabilities(): Promise<Envelope<Capabilities>>;
  current(): Promise<Envelope<CurrentContract>>;
  occurrenceGroups(
    groupSize: number,
    requestedDrawNumber?: number | null
  ): Promise<Envelope<OccurrenceContract>>;
  researchCatalog(): Promise<Envelope<ResearchCatalog>>;
  researchReport(reportId: string): Promise<Envelope<ResearchReport>>;
};

export function createBridge(api: PywebviewApi): LottoBridge {
  return {
    capabilities: () => api.get_capabilities(),
    current: () => api.get_current(),
    occurrenceGroups: (groupSize, requestedDrawNumber = null) =>
      api.get_occurrence_groups(undefined, groupSize, requestedDrawNumber),
    researchCatalog: () => api.get_research_catalog(),
    researchReport: (reportId) => api.get_research_report(reportId)
  };
}

declare global {
  interface Window {
    pywebview?: {
      api: PywebviewApi;
    };
  }
}

export async function desktopBridge(): Promise<LottoBridge> {
  if (window.pywebview?.api) {
    return createBridge(window.pywebview.api);
  }

  await new Promise<void>((resolve) => {
    window.addEventListener('pywebviewready', () => resolve(), { once: true });
  });

  if (!window.pywebview?.api) {
    throw new Error('Bridge pywebview non disponibile.');
  }

  return createBridge(window.pywebview.api);
}
