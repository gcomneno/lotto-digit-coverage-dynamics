export const CANONICAL_LOCALE = 'en' as const;
export const SUPPORTED_LOCALES = ['en', 'it'] as const;

export type Locale = (typeof SUPPORTED_LOCALES)[number];

type Catalog = Record<string, string>;

const ENGLISH_CATALOG: Catalog = {
  'app.nav_label': 'Research sections',
  'app.nav.dashboard': 'Dashboard',
  'app.nav.occurrences': 'Occurrences',
  'app.nav.research': 'Research',
  'app.connecting': 'Connecting to the Python core…',
  'app.language_label': 'Language',
};

const ITALIAN_CATALOG: Catalog = {
  'app.nav_label': 'Sezioni ricerca',
  'app.nav.dashboard': 'Dashboard',
  'app.nav.occurrences': 'Occorrenze',
  'app.nav.research': 'Ricerca',
  'app.connecting': 'Connessione al core Python…',
  'app.language_label': 'Lingua',
};

export interface LocalizedText {
  key: string;
  text: string;
  requestedLocale: string;
  resolvedLocale: Locale;
  fellBack: boolean;
}

export function resolveText(key: string, locale: string = CANONICAL_LOCALE): LocalizedText {
  const canonical = ENGLISH_CATALOG[key];
  if (canonical === undefined) {
    throw new Error(`unknown canonical presentation key: ${key}`);
  }

  if (locale === CANONICAL_LOCALE) {
    return {
      key,
      text: canonical,
      requestedLocale: locale,
      resolvedLocale: CANONICAL_LOCALE,
      fellBack: false,
    };
  }

  if (locale === 'it') {
    const translated = ITALIAN_CATALOG[key];
    if (translated !== undefined) {
      return {
        key,
        text: translated,
        requestedLocale: locale,
        resolvedLocale: 'it',
        fellBack: false,
      };
    }
  }

  return {
    key,
    text: canonical,
    requestedLocale: locale,
    resolvedLocale: CANONICAL_LOCALE,
    fellBack: true,
  };
}

export function text(key: string, locale: string = CANONICAL_LOCALE): string {
  return resolveText(key, locale).text;
}
