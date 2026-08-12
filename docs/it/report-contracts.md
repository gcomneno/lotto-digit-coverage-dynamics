# Contratti dei report applicativi

Issue correlate: #9, #12, #13, #14, #17.

I casi d'uso interattivi già migrati espongono report Python indipendenti dalla presentazione. `lotto_digit_coverage.application.reporting` definisce il confine machine-readable stabile senza trasformare tutte le dataclass interne in un'API pubblica permanente.

## Versionamento

La versione iniziale dei contratti è `1`.

Ogni payload contiene:

- un nome `schema` stabile;
- `schema_version`;
- campi primitivi espliciti, senza ANSI o testo terminale preformattato;
- una dichiarazione `number_representation`: i numeri Lotto sono interi in `1..90` e le interfacce li visualizzano con larghezza 2 (`01`–`90`).

Una modifica incompatibile di campo o significato richiede una nuova versione dello schema. Campi additivi possono essere introdotti con cautela quando i consumer possono ignorare quelli sconosciuti.

## Stato corrente

`current_report_to_dict()` produce lo schema `lotto.current` e comprende:

- estrazione/data target analizzata;
- stati di copertura per ruota;
- probabilità Markov grezze e attesa residua;
- ranking coverage-hits ed evidenza storica;
- consensus descrittivo;
- storico anomalie e anomalie attive;
- validazione sull'estrazione successiva esplicitamente separata dal target analizzato.

Le probabilità restano valori numerici grezzi. La formattazione percentuale appartiene all'interfaccia.

## Gruppi di occorrenze

`occurrence_group_report_to_dict()` produce lo schema `lotto.occurrence-groups` e comprende:

- riferimento risolto e sua modalità;
- dimensione configurata del gruppo;
- dimensione reale e intervallo di ogni gruppo;
- estrazioni storiche ordinate;
- cinque numeri di riferimento ordinati per ruota;
- conteggi delle occorrenze allineati alle rispettive posizioni di riferimento.

## JSON deterministico

`dumps_current_report()` e `dumps_occurrence_group_report()` producono JSON deterministico, UTF-8 friendly, con chiavi ordinate, indentazione e newline finale. NaN e Infinity vengono rifiutati.

Sono helper di serializzazione dell'application layer, non un'API HTTP. Una futura opzione CLI `--json` potrà usarli senza modificare questi contratti.

## Confine GUI

La futura GUI, con GIADA UI come fondazione canonica per design system e componenti riusabili, deve consumare gli stessi report e la stessa semantica usati dalla CLI. Non deve fare parsing dell'output terminale né reimplementare i calcoli di ricerca.
