import type { ConsensusRow } from './bridge';

export type ConsensusPresentation = {
  missingWheels: string;
  topWheels: string;
};

function wheelList(wheels: string[]): string {
  return wheels.join(', ') || '—';
}

export function consensusPresentation(row: ConsensusRow): ConsensusPresentation {
  return {
    missingWheels: wheelList(row.missing_wheels),
    topWheels: wheelList(row.top_wheels)
  };
}
