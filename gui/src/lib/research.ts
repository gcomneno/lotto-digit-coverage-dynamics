import { formatLottoNumber } from './occurrences';

export type ResearchValue = string | number | boolean | null;

function numeric(value: ResearchValue): number {
  if (typeof value !== 'number' || !Number.isFinite(value)) {
    throw new TypeError(`Valore numerico atteso, ricevuto: ${String(value)}`);
  }
  return value;
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
