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
  'occurrence.eyebrow': 'Database',
  'occurrence.title': 'Occurrence explorer',
  'occurrence.intro': 'Retrospective exploration by groups. Each group has its own reference draw identifying the five numbers under observation but excluded from counts. Subsequent draws in the panel are the historical draws actually analyzed on the same wheel. The global limit also includes reference rows. Colors identify the five reference positions and do not represent intensity or probability.',
  'occurrence.controls': 'Controls',
  'occurrence.group_size': 'Group size',
  'occurrence.group_size_hint': 'Number of historical draws counted; the reference is additional and excluded.',
  'occurrence.global_limit': 'Global limit',
  'occurrence.global_limit_hint': 'Maximum number of consecutive draws examined, including reference rows.',
  'occurrence.cutoff': 'Cutoff',
  'occurrence.cutoff_hint': 'Draw to use as the first reference; empty = latest complete draw.',
  'occurrence.optional': 'optional',
  'occurrence.wheel': 'Wheel',
  'occurrence.wheel_hint': 'The filter is presentation-only: the report contains all wheels.',
  'occurrence.loading': 'Loading…',
  'occurrence.apply': 'Apply',
  'occurrence.building': 'Building groups from the read-only database…',
  'occurrence.invalid_group_size': 'Group size must be a positive integer.',
  'occurrence.invalid_global_limit': 'Global limit must be a positive integer.',
  'occurrence.invalid_cutoff': 'Cutoff must be a positive draw number.',
  'occurrence.unknown_bridge_error': 'Unknown error from the Python bridge.',
  'occurrence.global_reference': 'Global reference',
  'occurrence.draw': 'Draw',
  'occurrence.date': 'Date',
  'occurrence.selection': 'Selection',
  'occurrence.configuration': 'Configuration',
  'occurrence.counted_draws': 'Counted draws',
  'occurrence.examined_draws': 'Examined draws',
  'occurrence.groups': 'Groups',
  'occurrence.visible_wheel': 'Visible wheel',
  'occurrence.reference_abbrev': 'Ref.',
  'occurrence.analysis': 'analysis',
  'occurrence.reference': 'reference',
  'occurrence.excluded_from_counts': 'excluded from counts',
  'occurrence.draws_counted': 'draws counted',
  'occurrence.references': 'References',
  'occurrence.occurrence_abbrev': 'occ.',
  'occurrence.use': 'Use',
  'occurrence.count': 'Count',
  'occurrence.total': 'Tot',
  'occurrence.wheel_missing': 'Wheel not present in this group.',
  'occurrence.global_total': 'Global total',
  'occurrence.sum_of_sums': 'Sum of sums',
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
  'occurrence.eyebrow': 'Database',
  'occurrence.title': 'Occurrence explorer',
  'occurrence.intro': 'Esplorazione retrospettiva per gruppi. Ogni gruppo ha una propria estrazione di riferimento che identifica i cinque numeri sotto osservazione ma è esclusa dai conteggi. Le estrazioni successive nel pannello sono quelle storiche effettivamente analizzate sulla stessa ruota. Il limite globale comprende anche le righe di riferimento. I colori identificano le cinque posizioni del riferimento e non rappresentano intensità o probabilità.',
  'occurrence.controls': 'Controlli',
  'occurrence.group_size': 'Dimensione gruppo',
  'occurrence.group_size_hint': 'Numero di estrazioni storiche conteggiate; il riferimento è aggiuntivo ed escluso.',
  'occurrence.global_limit': 'Limite globale',
  'occurrence.global_limit_hint': 'Numero massimo di concorsi consecutivi esaminati, incluse le righe di riferimento.',
  'occurrence.cutoff': 'Cutoff',
  'occurrence.cutoff_hint': 'Concorso da usare come primo riferimento; vuoto = ultimo completo.',
  'occurrence.optional': 'opzionale',
  'occurrence.wheel': 'Ruota',
  'occurrence.wheel_hint': 'Il filtro è solo grafico: il report contiene tutte le ruote.',
  'occurrence.loading': 'Caricamento…',
  'occurrence.apply': 'Applica',
  'occurrence.building': 'Costruzione dei gruppi dal database read-only…',
  'occurrence.invalid_group_size': 'La dimensione del gruppo deve essere un intero positivo.',
  'occurrence.invalid_global_limit': 'Il limite globale deve essere un intero positivo.',
  'occurrence.invalid_cutoff': 'Il cutoff deve essere un numero di concorso positivo.',
  'occurrence.unknown_bridge_error': 'Errore sconosciuto dal bridge Python.',
  'occurrence.global_reference': 'Riferimento globale',
  'occurrence.draw': 'Concorso',
  'occurrence.date': 'Data',
  'occurrence.selection': 'Selezione',
  'occurrence.configuration': 'Configurazione',
  'occurrence.counted_draws': 'Estratti conteggiati',
  'occurrence.examined_draws': 'Concorsi esaminati',
  'occurrence.groups': 'Gruppi',
  'occurrence.visible_wheel': 'Ruota visibile',
  'occurrence.reference_abbrev': 'Rif.',
  'occurrence.analysis': 'analisi',
  'occurrence.reference': 'riferimento',
  'occurrence.excluded_from_counts': 'escluso dai conteggi',
  'occurrence.draws_counted': 'estrazioni conteggiate',
  'occurrence.references': 'Riferimenti',
  'occurrence.occurrence_abbrev': 'occ.',
  'occurrence.use': 'Uso',
  'occurrence.count': 'Conta',
  'occurrence.total': 'Tot',
  'occurrence.wheel_missing': 'Ruota non presente nel gruppo.',
  'occurrence.global_total': 'Totale globale',
  'occurrence.sum_of_sums': 'Somma delle somme',
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
