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
  total_occurrences: number;
};

export type OccurrenceGroup = {
  reference: OccurrenceDraw;
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
  total_occurrences: number;
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
  occurrence_limit: number | null;
  examined_draw_count: number;
  grand_total_occurrences: number;
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
    requested_draw_number?: number | null,
    occurrence_limit?: number | null
  ): Promise<Envelope<OccurrenceContract>>;
  get_research_catalog(): Promise<Envelope<ResearchCatalog>>;
  get_research_report(report_id: string): Promise<Envelope<ResearchReport>>;
};

export type LottoBridge = {
  capabilities(): Promise<Envelope<Capabilities>>;
  current(): Promise<Envelope<CurrentContract>>;
  occurrenceGroups(
    groupSize: number,
    requestedDrawNumber?: number | null,
    occurrenceLimit?: number | null
  ): Promise<Envelope<OccurrenceContract>>;
  researchCatalog(): Promise<Envelope<ResearchCatalog>>;
  researchReport(reportId: string): Promise<Envelope<ResearchReport>>;
};

function withTimeout<T>(
  promise: Promise<T>,
  timeoutMs: number,
  operation: string
): Promise<T> {
  return new Promise<T>((resolve, reject) => {
    const timeout = globalThis.setTimeout(() => {
      reject(new Error(`${operation}: nessuna risposta dal bridge Python entro ${timeoutMs / 1000}s.`));
    }, timeoutMs);

    promise.then(
      (value) => {
        globalThis.clearTimeout(timeout);
        resolve(value);
      },
      (error) => {
        globalThis.clearTimeout(timeout);
        reject(error);
      }
    );
  });
}

export function isCompletePywebviewApi(value: unknown): value is PywebviewApi {
  if (!value || typeof value !== 'object') return false;
  const api = value as Record<string, unknown>;
  return [
    'get_capabilities',
    'get_current',
    'get_occurrence_groups',
    'get_research_catalog',
    'get_research_report'
  ].every((method) => typeof api[method] === 'function');
}

export function createBridge(api: PywebviewApi): LottoBridge {
  return {
    capabilities: () => withTimeout(api.get_capabilities(), 10_000, 'Handshake GUI'),
    current: () => withTimeout(api.get_current(), 15_000, 'Report corrente'),
    occurrenceGroups: (groupSize, requestedDrawNumber = null, occurrenceLimit = null) =>
      withTimeout(
        api.get_occurrence_groups(
          undefined,
          groupSize,
          requestedDrawNumber,
          occurrenceLimit
        ),
        15_000,
        'Occorrenze'
      ),
    researchCatalog: () =>
      withTimeout(api.get_research_catalog(), 10_000, 'Catalogo ricerca'),
    researchReport: (reportId) =>
      withTimeout(api.get_research_report(reportId), 120_000, 'Report di ricerca')
  };
}

declare global {
  interface Window {
    pywebview?: {
      api: PywebviewApi;
    };
  }
}

async function waitForPywebviewApi(): Promise<PywebviewApi> {
  if (isCompletePywebviewApi(window.pywebview?.api)) {
    return window.pywebview.api;
  }

  return withTimeout(
    new Promise<PywebviewApi>((resolve) => {
      let interval: ReturnType<typeof globalThis.setInterval> | undefined;
      const finishIfReady = () => {
        const api = window.pywebview?.api;
        if (!isCompletePywebviewApi(api)) return;
        if (interval !== undefined) globalThis.clearInterval(interval);
        window.removeEventListener('pywebviewready', finishIfReady);
        resolve(api);
      };

      window.addEventListener('pywebviewready', finishIfReady);
      interval = globalThis.setInterval(finishIfReady, 25);
      finishIfReady();
    }),
    10_000,
    'Inizializzazione API pywebview completa'
  );
}

export async function desktopBridge(): Promise<LottoBridge> {
  const bridge = createBridge(await waitForPywebviewApi());
  const capabilities = await bridge.capabilities();

  if (!capabilities.ok || !capabilities.data) {
    throw new Error(
      capabilities.error?.message ?? 'Handshake con il core Python non riuscito.'
    );
  }

  return bridge;
}
