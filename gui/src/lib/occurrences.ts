import type {
  OccurrenceContract,
  OccurrenceDraw,
  OccurrenceGroup,
  OccurrenceWheelSummary
} from './bridge';

export function formatLottoNumber(value: number): string {
  if (!Number.isInteger(value) || value < 1 || value > 90) {
    throw new RangeError(`Numero Lotto fuori intervallo: ${value}`);
  }
  return String(value).padStart(2, '0');
}

export function availableWheels(report: OccurrenceContract): string[] {
  const firstGroup = report.groups[0];
  return firstGroup ? firstGroup.wheels.map((wheel) => wheel.wheel) : [];
}

export function wheelSummary(
  group: OccurrenceGroup,
  wheel: string
): OccurrenceWheelSummary | undefined {
  return group.wheels.find((item) => item.wheel === wheel);
}

export function drawNumbersForWheel(
  draw: OccurrenceDraw,
  wheel: string
): number[] | undefined {
  return draw.wheels.find((item) => item.wheel === wheel)?.numbers;
}

export function referencePosition(
  value: number,
  referenceNumbers: number[]
): number | null {
  const index = referenceNumbers.indexOf(value);
  return index === -1 ? null : index;
}
