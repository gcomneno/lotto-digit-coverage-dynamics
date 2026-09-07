import { describe, expect, it } from 'vitest';

import {
  CANONICAL_LOCALE,
  PresentationCatalog,
  SUPPORTED_LOCALES,
  resolveText,
  text,
} from './localization';

describe('GUI localization contract', () => {
  it('uses canonical English by default', () => {
    expect(CANONICAL_LOCALE).toBe('en');
    expect(SUPPORTED_LOCALES).toEqual(['en', 'it']);
    expect(text('app.nav.occurrences')).toBe('Occurrences');
    expect(text('app.connecting')).toBe('Connecting to the Python core…');
    expect(text('current.eyebrow')).toBe('Current state');
    expect(text('current.markov_panel')).toBe('Markov ranking');
    expect(text('current.coverage_panel')).toBe('Coverage-hits — descriptive ranking');
    expect(text('current.consensus_panel')).toBe('Cross-wheel consensus');
    expect(text('current.anomaly_detail_panel')).toBe('Active anomaly details');
    expect(text('current.next_draw_panel')).toBe('Next-draw validation — outside calculation');
    expect(text('occurrence.controls')).toBe('Controls');
    expect(text('occurrence.group_size')).toBe('Group size');
    expect(text('occurrence.global_reference')).toBe('Global reference');
    expect(text('occurrence.global_total')).toBe('Global total');
    expect(text('research.eyebrow')).toBe('Historical analyses');
    expect(text('research.catalog')).toBe('Catalog');
    expect(text('research.condition')).toBe('Condition');
    expect(text('research.candidate')).toBe('CANDIDATE');
  });

  it('resolves deterministic Italian presentation', () => {
    expect(text('app.nav.occurrences', 'it')).toBe('Occorrenze');
    expect(text('app.nav.research', 'it')).toBe('Ricerca');
    expect(text('app.connecting', 'it')).toBe('Connessione al core Python…');
    expect(text('current.eyebrow', 'it')).toBe('Stato corrente');
    expect(text('current.markov_panel', 'it')).toBe('Classifica Markov');
    expect(text('current.coverage_panel', 'it')).toBe('Coverage-hits — classifica descrittiva');
    expect(text('current.consensus_panel', 'it')).toBe('Consensus trasversale');
    expect(text('current.anomaly_detail_panel', 'it')).toBe('Dettaglio anomalie attive');
    expect(text('current.next_draw_panel', 'it')).toBe('Validazione successiva — fuori dal calcolo');
    expect(text('occurrence.controls', 'it')).toBe('Controlli');
    expect(text('occurrence.group_size', 'it')).toBe('Dimensione gruppo');
    expect(text('occurrence.global_reference', 'it')).toBe('Riferimento globale');
    expect(text('occurrence.global_total', 'it')).toBe('Totale globale');
    expect(text('research.eyebrow', 'it')).toBe('Analisi storiche');
    expect(text('research.catalog', 'it')).toBe('Catalogo');
    expect(text('research.condition', 'it')).toBe('Condizione');
    expect(text('research.candidate', 'it')).toBe('CANDIDATO');
  });

  it('keeps structured, domain, and dynamic research values out of the presentation catalog', () => {
    for (const value of [
      'Bari',
      'Napoli',
      'Roma',
      'coverage-current-v1',
      'lotto.occurrence-groups',
      'automatico',
      'A1',
      '0,1,2,3,4',
      '0.375',
      'severe',
      '128',
      '2026-08-11',
      'twins',
      'baseline',
      'missing',
      'dynamic-report-title',
      'dynamic-report-summary',
      'dynamic-report-interpretation',
      'dynamic-metric-label',
      'dynamic-table-title',
      'dynamic-column-label',
      'dynamic-note',
      'dynamic-source',
    ]) {
      expect(() => text(value, 'it')).toThrow('unknown canonical presentation key');
    }
  });

  it('falls back to canonical English when an Italian translation is missing', () => {
    const catalog = new PresentationCatalog(
      { known: 'Canonical English' },
      { it: {} },
    );
    const resolved = catalog.resolve('known', 'it');

    expect(resolved.text).toBe('Canonical English');
    expect(resolved.resolvedLocale).toBe('en');
    expect(resolved.fellBack).toBe(true);
    expect(resolved.fallbackReason).toBe('missing-translation');
  });

  it('falls back to canonical English for unsupported locale identifiers', () => {
    const resolved = resolveText('app.nav.research', 'fr');

    expect(resolved.text).toBe('Research');
    expect(resolved.requestedLocale).toBe('fr');
    expect(resolved.resolvedLocale).toBe('en');
    expect(resolved.fellBack).toBe(true);
    expect(resolved.fallbackReason).toBe('unsupported-locale');
  });

  it('treats an unknown canonical key as a programmer error', () => {
    expect(() => text('app.unknown', 'it')).toThrow(
      'unknown canonical presentation key: app.unknown',
    );
  });
});
