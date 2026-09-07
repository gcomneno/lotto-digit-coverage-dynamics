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
  'current.eyebrow': 'Current state',
  'current.title': 'Research dashboard',
  'current.loading': 'Loading…',
  'current.refresh': 'Refresh',
  'current.loading_report': 'Loading current report from the Python core…',
  'current.unknown_bridge_error': 'Unknown error from the Python bridge.',
  'current.intro': 'Descriptive view of the observed state. Reported probabilities belong to the declared model; they are not gambling recommendations. Validation with the next draw is separate from the ex-ante calculation.',
  'current.target_panel': 'Analysis target',
  'current.draw': 'Draw',
  'current.date': 'Date',
  'current.contract': 'Contract',
  'current.active_anomalies': 'Active anomalies',
  'current.valid_transitions': 'valid transitions in the analyzed history.',
  'current.states_panel': 'Current state by wheel',
  'current.age': 'age',
  'current.missing': 'Missing',
  'current.completed_cycles': 'Completed cycles',
  'current.no_digits': 'no digits',
  'current.markov_panel': 'Markov ranking',
  'current.position': 'Pos.',
  'current.wheel': 'Wheel',
  'current.within1': 'Within 1',
  'current.within3': 'Within 3',
  'current.expected_remaining': 'Expected remaining',
  'current.coverage_panel': 'Coverage-hits — descriptive ranking',
  'current.coverage_intro': 'The event counts missing digits hit on the same wheel. Success on digits does not equal a win on complete Lotto numbers.',
  'current.event_probability': 'P event',
  'current.conservative_estimate': 'Estimate95-',
  'current.historical_cases': 'Historical cases',
  'current.consensus_panel': 'Cross-wheel consensus',
  'current.consensus_intro': 'Descriptive: for each digit, count how many active-cycle wheels still miss it and how many have it among the most present digits in the current cycle. It does not combine digits into numbers and does not represent a gambling advantage.',
  'current.digit': 'Digit',
  'current.deficit_wheels': 'Deficit wheels',
  'current.top_wheels': 'Predominant wheels',
  'current.where_deficit': 'Where missing',
  'current.where_top': 'Where predominant',
  'current.anomaly_detail_panel': 'Active anomaly details',
  'current.no_active_anomalies': 'No active anomalies at the cutoff.',
  'current.next_draw_panel': 'Next-draw validation — outside calculation',
  'current.no_next_draw': 'No subsequent draw is present in the database.',
  'current.next_draw_intro': 'The following section uses only data after the target for ex-post validation. These numbers do not participate in the state, probabilities, or rankings above.',
};

const ITALIAN_CATALOG: Catalog = {
  'app.nav_label': 'Sezioni ricerca',
  'app.nav.dashboard': 'Dashboard',
  'app.nav.occurrences': 'Occorrenze',
  'app.nav.research': 'Ricerca',
  'app.connecting': 'Connessione al core Python…',
  'app.language_label': 'Lingua',
  'current.eyebrow': 'Stato corrente',
  'current.title': 'Research dashboard',
  'current.loading': 'Caricamento…',
  'current.refresh': 'Aggiorna',
  'current.loading_report': 'Caricamento del report corrente dal core Python…',
  'current.unknown_bridge_error': 'Errore sconosciuto dal bridge Python.',
  'current.intro': "Quadro descrittivo dello stato osservato. Le probabilità riportate appartengono al modello dichiarato; non sono raccomandazioni di gioco. La validazione con l'estrazione successiva è separata dal calcolo ex ante.",
  'current.target_panel': 'Target di analisi',
  'current.draw': 'Concorso',
  'current.date': 'Data',
  'current.contract': 'Contratto',
  'current.active_anomalies': 'Anomalie attive',
  'current.valid_transitions': 'transizioni valide nella storia analizzata.',
  'current.states_panel': 'Stato corrente per ruota',
  'current.age': 'età',
  'current.missing': 'Mancanti',
  'current.completed_cycles': 'Cicli completi',
  'current.no_digits': 'nessuna cifra',
  'current.markov_panel': 'Classifica Markov',
  'current.position': 'Pos.',
  'current.wheel': 'Ruota',
  'current.within1': 'Entro 1',
  'current.within3': 'Entro 3',
  'current.expected_remaining': 'Attesa residua',
  'current.coverage_panel': 'Coverage-hits — classifica descrittiva',
  'current.coverage_intro': "L'evento conta le cifre mancanti intercettate sulla stessa ruota. Il successo dell'evento sulle cifre non equivale a una vincita su numeri Lotto completi.",
  'current.event_probability': 'P evento',
  'current.conservative_estimate': 'Stima95-',
  'current.historical_cases': 'Casi storici',
  'current.consensus_panel': 'Consensus trasversale',
  'current.consensus_intro': 'Descrittivo: per ogni cifra conta in quante ruote con ciclo attivo è ancora assente e in quante è tra le più presenti nel ciclo corrente. Non combina cifre in numeri e non rappresenta un vantaggio sul gioco.',
  'current.digit': 'Cifra',
  'current.deficit_wheels': 'Ruote in deficit',
  'current.top_wheels': 'Ruote in predominanza',
  'current.where_deficit': 'Dove in deficit',
  'current.where_top': 'Dove predominante',
  'current.anomaly_detail_panel': 'Dettaglio anomalie attive',
  'current.no_active_anomalies': 'Nessuna anomalia attiva al cutoff.',
  'current.next_draw_panel': 'Validazione successiva — fuori dal calcolo',
  'current.no_next_draw': 'Nessuna estrazione successiva presente nel database.',
  'current.next_draw_intro': 'La sezione seguente usa soltanto dati successivi al target per verifica ex post. Questi numeri non partecipano allo stato, alle probabilità o alle classifiche sopra.',
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
