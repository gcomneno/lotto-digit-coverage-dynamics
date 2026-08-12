# Confini architetturali

Issue correlate: #9, #10, #11, #17.

## Scopo

Il progetto sta migrando in modo incrementale da un laboratorio organizzato principalmente come insieme di script a un core indipendente dalla presentazione, utilizzabile sia dalla CLI esistente sia da una futura GUI.

Questo lavoro è esclusivamente architetturale. Definizioni matematiche, protocolli statistici, cutoff, regole anti-look-ahead e semantica della CLI non devono cambiare come effetto collaterale degli spostamenti di codice.

## Package di destinazione

```text
lotto_digit_coverage/
├── domain/
├── application/
├── infrastructure/
└── interfaces/
    └── cli/
```

Un futuro package `interfaces/gui/` potrà essere introdotto soltanto dopo il superamento del gate architetturale definito nella #9. Quando inizierà il lavoro grafico, GIADA UI sarà il fondamento canonico riusabile per design system e componenti, non un semplice riferimento visivo o una fonte opzionale di ispirazione.

## Responsabilità

### `domain`

Contiene concetti matematici/statistici puri e value object del dominio.

Esempi: stati di copertura, transizioni, probabilità, definizioni delle anomalie e altre regole valutabili senza sapere come i dati sono memorizzati o visualizzati.

Il dominio non deve conoscere SQLite, path dei database, `argparse`, colori ANSI, `less`, subprocess o framework GUI.

### `application`

Contiene l’orchestrazione dei casi d’uso e result/report object indipendenti dalla presentazione.

I servizi applicativi possono dipendere dal dominio e da contratti astratti. Non devono dipendere da adapter SQLite concreti né da implementazioni CLI/GUI.

Un caso d’uso deve restituire valori strutturati; formattazione di percentuali, tabelle o testi localizzati appartiene alle interfacce.

### `infrastructure`

Contiene gli adapter concreti per persistenza e risorse esterne, per esempio repository SQLite, sorgenti degli archivi, checkpoint e storage dei report.

L’infrastruttura può implementare contratti consumati dall’application layer. Non deve contenere logica di presentazione CLI/GUI.

### `interfaces`

Contiene gli adapter rivolti all’utente.

`interfaces/cli` contiene gestione degli argomenti, formattazione ANSI/terminale, paging e altri helper specifici della riga di comando. Una futura GUI sarà un altro adapter sopra gli stessi servizi applicativi e non dovrà mai fare parsing dell’output CLI.

## Futura GUI e GIADA UI

Se verrà introdotta un’interfaccia grafica, questo repository non dovrà sviluppare un design system general-purpose indipendente.

GIADA UI è la fonte primaria per gli aspetti grafici riusabili:

- componenti e pattern di interazione;
- design token, temi e linguaggio visivo;
- convenzioni di accessibilità e navigazione da tastiera;
- primitive riusabili per tabelle, filtri, navigazione e feedback, quando disponibili.

Questo repository deve possedere soltanto composizione specifica del Lotto, mapping verso i view model e workflow di ricerca. Quando manca una primitiva grafica generalmente riusabile, va valutata prima l’aggiunta o l’evoluzione in GIADA UI, anziché introdurre subito un duplicato locale.

La scelta del framework GUI è quindi vincolata anche dalla capacità di riuso di GIADA UI. Uno stack che impedisca un riuso sostanziale richiede una giustificazione architetturale esplicita e non deve introdurre silenziosamente una seconda fondazione UI.

## Direzione delle dipendenze

Direzione consentita:

```text
interfaces  --->  application  --->  domain
     |                 ^
     +------ wiring ---|--- infrastructure
```

Più precisamente:

- `domain` non importa `application`, `infrastructure` o `interfaces`;
- `application` può importare `domain` e contratti astratti, ma non `infrastructure` concreta o `interfaces`;
- `infrastructure` può dipendere dai tipi domain/application necessari a implementare i contratti, ma non da `interfaces`;
- `interfaces` può consumare servizi applicativi e helper di presentazione; il composition code può collegare implementazioni infrastrutturali ai servizi;
- il futuro codice GUI potrà dipendere da GIADA UI nel layer `interfaces`, ma domain/application dovranno rimanere indipendenti sia da GIADA UI sia dal framework GUI scelto.

## Collocazione di result e value object

Usare sempre il layer stabile più ristretto:

- identità o invariante matematica/del dominio -> `domain`;
- risultato immutabile di uno specifico caso d’uso -> `application`;
- rappresentazione di trasporto SQLite/archivio -> soltanto `infrastructure`, senza farla trapelare oltre il confine;
- colori, label, larghezze di colonna, stringhe localizzate o widget -> `interfaces`.

I contratti JSON stabili e serializzabili sono volutamente rimandati alla #14, dopo la migrazione dei primi casi d’uso interattivi.

## Confine di accesso ai dati

La #11 introduce il primo contratto esplicito di persistenza per le analisi basate sulle estrazioni:

- `lotto_digit_coverage.domain.draws.DrawSnapshot` è il value object immutabile canonico dell’estrazione di una ruota; la formattazione a due cifre e la scomposizione che conserva lo zero iniziale sono primitive di dominio perché la loro semantica non dipende dallo storage;
- `lotto_digit_coverage.application.repositories.DrawRepository` definisce le operazioni di lettura richieste dalle analisi e restituisce esclusivamente valori strutturati del dominio;
- `lotto_digit_coverage.infrastructure.sqlite_lotto_repository.SQLiteLottoRepository` implementa il contratto su SQLite;
- il codice di analisi non deve eseguire SQL attraverso una connection del repository né ricevere `sqlite3.Row`, cursori o altri valori specifici di SQLite;
- l’adapter SQLite per le analisi apre i database con `mode=ro`, impedendo ai casi d’uso in sola lettura di modificare accidentalmente un archivio;
- i path dei database restano parametri del costruttore e non assunzioni globali specifiche della CLI o della futura GUI;
- gli errori relativi a schema e invarianti dei dati persistiti vengono normalizzati in errori di repository rivolti all’application layer.

Il modulo legacy `strategies.lotto_repository` rimane uno shim di compatibilità durante la migrazione. `LottoRepository` è un alias dell’adapter SQLite, mentre `DrawSnapshot`, `format_number` e `split_digits` vengono riesportati dalla loro posizione canonica nel dominio.

I comandi di import/update rimangono percorsi infrastrutturali separati orientati alla scrittura. La #11 non modifica il loro schema né la loro semantica di aggiornamento.

## Migrazione incrementale

Gli script top-level e il package `strategies/` rimangono supportati durante la transizione. Sono ammessi moduli di compatibilità quando preservano gli import esistenti rendendo però esplicita la nuova responsabilità.

Il primo spostamento concreto della #10 riguarda la primitiva CLI tabellare `Column`:

- posizione canonica: `lotto_digit_coverage.interfaces.cli.table`;
- import legacy: `strategies.cli_table` rimane come compatibility shim.

La #11 aggiunge il confine del repository delle estrazioni senza richiedere una migrazione massiva di tutti gli strumenti storici. Le issue successive migreranno i casi d’uso verticalmente, uno alla volta.

L’implementazione grafica resta rimandata alla #17. Quella issue dovrà preservare gli stessi confini application/domain e trattare GIADA UI come layer UI riusabile canonico.

## Controlli automatici dei confini

`tests/test_architecture_boundaries.py` applica le prime regole sulle dipendenze analizzando gli import via AST Python. In particolare, domain/application non possono acquisire dipendenze dirette da SQLite, subprocess, parser CLI o framework GUI; gli import tra layer vietati fanno fallire la suite.

`tests/test_sqlite_lotto_repository.py` verifica il contratto concreto su fixture SQLite temporanee, includendo ordine delle ruote, cronologia attraverso il reset annuale del numero di estrazione, dati incompleti, errori di schema, semantica dello zero iniziale e apertura in sola lettura.

I controlli restano volutamente piccoli ed espliciti: proteggono la direzione architetturale senza introdurre ORM, framework esterni di dependency injection o architecture enforcement.
