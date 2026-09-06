export const CANONICAL_LOCALE = 'en' as const;
export const SUPPORTED_LOCALES = ['en', 'it'] as const;

export type Locale = (typeof SUPPORTED_LOCALES)[number];

type Catalog = Record<string, string>;
type DerivedCatalogs = Partial<Record<Locale, Catalog>>;

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
  fallbackReason?: 'unsupported-locale' | 'missing-translation';
}

export class PresentationCatalog {
  constructor(
    private readonly canonical: Catalog,
    private readonly derived: DerivedCatalogs,
  ) {}

  resolve(key: string, locale: string = CANONICAL_LOCALE): LocalizedText {
    const canonicalText = this.canonical[key];
    if (canonicalText === undefined) {
      throw new Error(`unknown canonical presentation key: ${key}`);
    }

    if (locale === CANONICAL_LOCALE) {
      return {
        key,
        text: canonicalText,
        requestedLocale: locale,
        resolvedLocale: CANONICAL_LOCALE,
        fellBack: false,
      };
    }

    if (!SUPPORTED_LOCALES.includes(locale as Locale)) {
      return {
        key,
        text: canonicalText,
        requestedLocale: locale,
        resolvedLocale: CANONICAL_LOCALE,
        fellBack: true,
        fallbackReason: 'unsupported-locale',
      };
    }

    const translated = this.derived[locale as Locale]?.[key];
    if (translated === undefined) {
      return {
        key,
        text: canonicalText,
        requestedLocale: locale,
        resolvedLocale: CANONICAL_LOCALE,
        fellBack: true,
        fallbackReason: 'missing-translation',
      };
    }

    return {
      key,
      text: translated,
      requestedLocale: locale,
      resolvedLocale: locale as Locale,
      fellBack: false,
    };
  }
}

export const DEFAULT_PRESENTATION_CATALOG = new PresentationCatalog(
  ENGLISH_CATALOG,
  { it: ITALIAN_CATALOG },
);

export function resolveText(key: string, locale: string = CANONICAL_LOCALE): LocalizedText {
  return DEFAULT_PRESENTATION_CATALOG.resolve(key, locale);
}

export function text(key: string, locale: string = CANONICAL_LOCALE): string {
  return resolveText(key, locale).text;
}
