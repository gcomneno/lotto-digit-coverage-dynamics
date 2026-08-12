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

export type CurrentContract = {
  schema: 'lotto.current';
  schema_version: number;
  target: {
    draw_number: number;
    draw_date: string;
  };
  states: CurrentState[];
  markov_ranking: Array<{
    position: number;
    wheel: string;
    wheel_order: number;
    expected_remaining_draws: number;
    completion_within: Record<string, number>;
  }>;
  coverage_hit_ranking: Array<Record<string, unknown>>;
  consensus: Array<Record<string, unknown>>;
  anomalies: {
    transition_count: number;
    history: Array<Record<string, unknown>>;
    active: Array<Record<string, unknown>>;
  };
  next_draw_validation: Array<Record<string, unknown>>;
};

export type OccurrenceContract = {
  schema: 'lotto.occurrence-groups';
  schema_version: number;
  reference: {
    draw_number: number;
    draw_date: string;
    kind: string;
  };
  group_size: number;
  groups: Array<Record<string, unknown>>;
};

export type Capabilities = {
  bridge_version: number;
  contracts: Array<{ schema: string; version: number }>;
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
};

export type LottoBridge = {
  capabilities(): Promise<Envelope<Capabilities>>;
  current(): Promise<Envelope<CurrentContract>>;
  occurrenceGroups(groupSize: number): Promise<Envelope<OccurrenceContract>>;
};

export function createBridge(api: PywebviewApi): LottoBridge {
  return {
    capabilities: () => api.get_capabilities(),
    current: () => api.get_current(),
    occurrenceGroups: (groupSize) =>
      api.get_occurrence_groups(undefined, groupSize, null)
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
