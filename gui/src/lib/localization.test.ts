import { describe, expect, it } from 'vitest';

import {
  CANONICAL_LOCALE,
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
  });

  it('resolves deterministic Italian presentation', () => {
    expect(text('app.nav.occurrences', 'it')).toBe('Occorrenze');
    expect(text('app.nav.research', 'it')).toBe('Ricerca');
    expect(text('app.connecting', 'it')).toBe('Connessione al core Python…');
  });

  it('falls back to canonical English for unsupported locale identifiers', () => {
    const resolved = resolveText('app.nav.research', 'fr');

    expect(resolved.text).toBe('Research');
    expect(resolved.requestedLocale).toBe('fr');
    expect(resolved.resolvedLocale).toBe('en');
    expect(resolved.fellBack).toBe(true);
  });

  it('treats an unknown canonical key as a programmer error', () => {
    expect(() => text('app.unknown', 'it')).toThrow(
      'unknown canonical presentation key: app.unknown',
    );
  });
});
