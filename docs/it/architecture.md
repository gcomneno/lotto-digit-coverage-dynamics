# Confini architetturali

Issue correlate: #9, #10.

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

Un futuro package `interfaces/gui/` potrà essere introdotto soltanto dopo il superamento del gate architetturale definito nella #9.

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
- `interfaces` può consumare servizi applicativi e helper di presentazione; il composition code può collegare implementazioni infrastrutturali ai servizi.

## Collocazione di result e value object

Usare sempre il layer stabile più ristretto:

- identità o invariante matematica/del dominio -> `domain`;
- risultato immutabile di uno specifico caso d’uso -> `application`;
- rappresentazione di trasporto SQLite/archivio -> soltanto `infrastructure`, senza farla trapelare oltre il confine;
- colori, label, larghezze di colonna, stringhe localizzate o widget -> `interfaces`.

I contratti JSON stabili e serializzabili sono volutamente rimandati alla #14, dopo la migrazione dei primi casi d’uso interattivi.

## Migrazione incrementale

Gli script top-level e il package `strategies/` rimangono supportati durante la transizione. Sono ammessi moduli di compatibilità quando preservano gli import esistenti rendendo però esplicita la nuova responsabilità.

Il primo spostamento concreto della #10 riguarda la primitiva CLI tabellare `Column`:

- posizione canonica: `lotto_digit_coverage.interfaces.cli.table`;
- import legacy: `strategies.cli_table` rimane come compatibility shim.

La #10 non richiede uno spostamento massivo dei moduli. Le issue successive migreranno i casi d’uso verticalmente, uno alla volta.

## Controlli automatici dei confini

`tests/test_architecture_boundaries.py` applica le prime regole sulle dipendenze analizzando gli import via AST Python. In particolare, domain/application non possono acquisire dipendenze dirette da SQLite, subprocess, parser CLI o framework GUI; gli import tra layer vietati fanno fallire la suite.

I controlli restano volutamente piccoli ed espliciti: proteggono la direzione architetturale senza introdurre framework esterni di dependency injection o architecture enforcement.
