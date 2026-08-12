import { formatLottoNumber } from './occurrences';

export type ResearchValue = string | number | boolean | null;
export type ResearchRow = Record<string, ResearchValue>;

export type ResearchRowFilters = {
  condition?: string;
  twin?: number | null;
  candidatesOnly?: boolean;
};

function numeric(value: ResearchValue): number {
  if (typeof value !== 'number' || !Number.isFinite(value)) {
    throw new TypeError(`Valore numerico atteso, ricevuto: ${String(value)}`);
  }
  return value;
}

export function filterResearchRows(
  rows: ResearchRow[],
  filters: ResearchRowFilters
): ResearchRow[] {
  return rows.filter((row) => {
    if (filters.condition && row.condition !== filters.condition) return false;
    if (filters.twin != null && row.twin !== filters.twin) return false;
    if (filters.candidatesOnly && row.candidate !== true) return false;
    return true;
  });
}

export function uniqueResearchValues(
  rows: ResearchRow[],
  key: string
): Array<string | number> {
  const values = new Set<string | number>();
  for (const row of rows) {
    const value = row[key];
    if (typeof value === 'string' || typeof value === 'number') values.add(value);
  }
  return [...values].sort((left, right) =>
    typeof left === 'number' && typeof right === 'number'
      ? left - right
      : String(left).localeCompare(String(right))
  );
}

export function formatResearchValue(
  value: ResearchValue,
  valueFormat: string
): string {
  if (value === null) return '—';

  switch (valueFormat) {
    case 'integer':
      return String(Math.trunc(numeric(value)));
    case 'percentage':
      return `${(numeric(value) * 100).toFixed(2)}%`;
    case 'percentage-signed': {
      const amount = numeric(value) * 100;
      return `${amount >= 0 ? '+' : ''}${amount.toFixed(2)}%`;
    }
    case 'decimal-2':
      return numeric(value).toFixed(2);
    case 'decimal-3':
      return numeric(value).toFixed(3);
    case 'decimal-4':
      return numeric(value).toFixed(4);
    case 'decimal-signed-3': {
      const amount = numeric(value);
      return `${amount >= 0 ? '+' : ''}${amount.toFixed(3)}`;
    }
    case 'lotto-number':
      return formatLottoNumber(numeric(value));
    case 'candidate':
      return value === true ? 'CANDIDATO' : '—';
    default:
      return String(value);
  }
}
