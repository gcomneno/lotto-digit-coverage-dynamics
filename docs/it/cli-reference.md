# Guida ai comandi

[English](../cli-reference.md) | **Italiano**

Eseguire i comandi dalla radice del repository.

## Punto di ingresso unificato

```bash
./lotto.py list
./lotto.py <comando> [argomenti del tool]
./lotto.py help <comando>
```

`lotto.py` è un dispatcher sottile. Non reimplementa la logica matematica o di
gestione dei dati: seleziona uno degli eseguibili esistenti, inoltra senza
modifiche gli argomenti rimanenti e restituisce il codice di uscita del tool.

Tutti gli script originali restano direttamente eseguibili.

## Comandi

| Comando | Eseguibile sottostante | Scopo |
|:---|:---|:---|
| `current` | `analyze_current_coverage.py` | Classifica Markov corrente, riga trasversale e anomalie attive |
| `update` | `update_lotto_database.py` | Aggiornamento prudente del database corrente |
| `db update` | `update_lotto_databases.py` | Orchestrazione sicura per anno, intervallo e rollover |
| `db` | `view_lotto_database.sh` | Esplorazione del database da terminale |
| `anomalies` | `analyze_coverage_anomalies.py` | Analisi storica delle anomalie A1–A4 |
| `completion` | `analyze_coverage_completion.py` | Analisi del completamento dei cicli naturali |
| `residuals` | `analyze_coverage_markov_residuals.py` | Confronto dei tempi residui teorici e osservati |
| `validation` | `analyze_coverage_markov_validation.py` | Calibrazione empirica delle probabilità Markov |
| `digit-coverage` | `analyze_digit_coverage.py` | Copertura delle cifre su finestre mobili |
| `rolling-frequency` | `analyze_rolling_frequency.py` | Backtest walk-forward delle frequenze rolling contro rose casuali equivalenti |
| `coverage-hits` | `analyze_coverage_hit_statistics.py` | Statistiche recenti delle quasi-chiusure per quantità TOP e Mancanti |
| `return-times` | `analyze_digit_return_times.py` | Analisi dei tempi di ritorno delle cifre |
| `cycles` | `analyze_historical_cycle_distribution.py` | Confronto storico delle durate dei cicli |
| `symmetry-history` | `analyze_historical_symmetry_classes.py` | Analisi storica delle classi strutturali |
| `atlas` | `generate_state_atlas.py` | Atlante completo dei 1.023 stati non vuoti |
| `structure` | `generate_structural_analysis.py` | Classi strutturali e artefatti sulla perdita di informazione |
| `kernel` | `verify_transition_kernel.py` | Verifica indipendente esaustiva del kernel |
| `import` | `import_lotto.py` | Importazione dell’archivio annuale |

Alias:

- `now` → `current`;
- `view` → `db`;
- `digits` → `digit-coverage`;
- `rolling` → `rolling-frequency`;
- `hits` → `coverage-hits`;
- `returns` → `return-times`;
- `cycle-distribution` → `cycles`;
- `symmetry` → `symmetry-history`.

## Backtest delle frequenze rolling

```bash
./lotto.py rolling-frequency
./lotto.py coverage-hits --last 10
./lotto.py coverage-hits --last 10 --details
./lotto.py coverage-hits \
  --database data/lotto-2021-2025.sqlite3 \
  --last 912 \
  --csv _work/reports/coverage-hits-2021-2025.csv
./lotto.py rolling-frequency --window-size 6
./lotto.py rolling-frequency --repetitions 1000 --seed 20260731
```

L’esportazione CSV contiene valori numerici grezzi, così colonne come
`success_rate`, `excess` e `cases` possono essere ordinate correttamente
nei visualizzatori tabellari.

La colonna `evidence_level` classifica le righe in base alla numerosità
del campione:

- `anecdotal`: da 1 a 9 casi;
- `exploratory`: da 10 a 29 casi;
- `preliminary`: da 30 a 99 casi;
- `moderate`: da 100 a 499 casi;
- `strong`: almeno 500 casi.

L’etichetta descrive soltanto la solidità numerica del campione:
non dimostra un vantaggio predittivo.


### Ordinamento di `coverage-hits`

Il riepilogo usa per impostazione predefinita:

```text
missing,top
```

Le colonne sono separate da virgole e vengono applicate da sinistra
a destra. Il prefisso `-` richiede l’ordine decrescente.

Esempi:

```bash
./lotto.py coverage-hits --sort=-cases

./lotto.py coverage-hits \
  --sort=missing,-success_rate

./lotto.py coverage-hits \
  --sort=evidence,-excess
```

Quando il primo nome di colonna è preceduto da `-`, si usa la forma
`--sort=-cases`, con il segno `=`, affinché il valore non venga
interpretato come una nuova opzione della CLI.

L’ordinamento scelto viene mostrato prima della tabella ed è applicato
nello stesso modo anche alle righe esportate tramite `--csv`.

Per visualizzare tutte le colonne disponibili:

```bash
./lotto.py coverage-hits --list-sort-columns
```

L’esecuzione predefinita:

- legge in sola lettura gli archivi annuali 2023–2026;
- valuta le finestre `3`, `6`, `8` e `12`;
- usa il 2023–2025 come periodo di sviluppo;
- usa il 2026 come periodo held-out;
- esegue `1.000` repliche casuali a parità di dimensione per confronto;
- scrive artefatti CSV e JSON deterministici sotto `_work/`.

Le opzioni `--database` e `--window-size` possono essere ripetute. I percorsi
degli output possono essere modificati con `--csv-output` e `--json-output`.

Il comando riporta esposizione dei candidati, numeri centrati, ambi centrati,
medie casuali, rapporti osservato/casuale e p-value empirici unilaterali. Non
riporta posta virtuale, vincite o ritorno finanziario.

Vedere il
[report completo sulle frequenze rolling](rolling-frequency-backtest.md).

## Limiti dello stato corrente

```bash
./lotto.py current --to 2026-07-25
./lotto.py current --to-num 119
```

`--to` seleziona tutte le estrazioni con data non successiva alla data ISO
indicata. `--to-num` seleziona tutte le estrazioni il cui numero annuale non è
superiore all’intero positivo indicato. Entrambi i limiti sono inclusivi.

È accettata anche la grafia equivalente `--to_num`. Il limite per data e quello
per numero sono mutuamente esclusivi.

Quando il database contiene anche un concorso successivo e allineato, il report
lo mostra separatamente e non lo usa nel calcolo dello stato storico limitato.

## La riga `TUTTE`

La riga finale `TUTTE` del comando `current` considera soltanto le ruote il cui
ciclo naturale corrente ha età positiva.

Definiamo:

- `P` come unione degli insiemi delle cifre più presenti su tutte le ruote
  attive;
- il gruppo massimo come l’insieme di tutte le ruote attive a pari merito per
  la massima probabilità di completamento entro una estrazione;
- `M` come unione degli insiemi delle cifre mancanti soltanto nel gruppo
  massimo;
- `C = P ∩ M`.

Il campo `Numeri` contiene ogni numero valido `01`–`90` formato da una coppia
ordinata di cifre appartenenti a `C`, ammettendo anche cifre ripetute.

Per esempio, `C={1,6,7}` produce:

```text
{11,16,17,61,66,67,71,76,77}
```

La costruzione è deterministica e riproducibile. È una descrizione trasversale
e, facoltativamente, una convenzione per il gioco virtuale, non un risultato
previsionale. Nel modello ideale ogni singolo numero del Lotto conserva la
medesima probabilità di inclusione in una estrazione.

## Orchestrazione dei database annuali

Il comando per gestire uno o più anni è:

```bash
./lotto.py db update
./lotto.py db update --year 2025
./lotto.py db update --from-year 2021 --to-year 2026
./lotto.py db update --from-year 2021 --to-year 2026 --dry-run
./lotto.py db update --from-year 2021 --to-year 2026 --keep-going
```

Senza opzioni viene selezionato l'anno di sistema corrente. `--year` è
mutuamente esclusivo con la coppia inclusiva `--from-year` / `--to-year`.
Gli anni futuri e quelli precedenti al 1871 vengono rifiutati.

Gli anni conclusi usano `data/lotto-YYYY.sqlite3`; l'anno corrente usa
`data/lotto-current.sqlite3`. Gli archivi storici possono contenere meno ruote
o concorsi mancanti e vengono classificati come `complete` o `partial`, senza
essere rifiutati soltanto per queste differenze storiche.

Ogni database modificato viene costruito e verificato in un file SQLite
temporaneo prima della sostituzione atomica. Per una destinazione già esistente
viene creato un backup con timestamp. L'orchestratore protegge i dati locali
quando la sorgente remota perde concorsi o risultati di ruota, oppure modifica
date o numeri già registrati.

Quando il database corrente contiene ancora l'anno precedente, l'orchestratore
recupera e verifica prima l'archivio definitivo di quell'anno, quindi ricostruisce
`data/lotto-YYYY.sqlite3`. Soltanto dopo il completamento senza errori o avvisi
può ricostruire `data/lotto-current.sqlite3` per il nuovo anno.

`--dry-run` esegue recupero, parsing e confronto senza scrivere database.
`--keep-going` continua dopo errori indipendenti dal rollover; un errore o una
protezione sull'anno da archiviare blocca sempre la sostituzione del database
corrente.

Il comando precedente `./lotto.py update` resta disponibile per
l'aggiornamento prudente del solo database corrente.

## Evidenziazione e tracciamento storico del database

### Evidenziazione manuale

Il comando `db` supporta due selettori indipendenti e componibili:

- `--digit CIFRE` evidenzia singole cifre da `0` a `9`;
- `--number NUMERI` evidenzia numeri del Lotto completi da `1` a `90`.

Entrambe le opzioni possono essere ripetute e ogni valore può contenere una lista separata da virgole. Le selezioni ripetute vengono deduplicate. Un numero selezionato viene rappresentato nella forma a due cifre usata dal database: quindi `--number 1` evidenzia `01`. Quando sono selezionati sia un numero completo sia una sua cifra, prevale l'evidenziazione del numero completo.

### Occorrenze storiche dall'estrazione di riferimento

`--latest-occurrences [NUM_ESTRAZIONE]` traccia indipendentemente su ogni
ruota i cinque numeri dell'estrazione di riferimento.

Senza `NUM_ESTRAZIONE`, il comando seleziona deterministicamente l'ultima
estrazione completa tramite la tupla `(draw_date, draw_number)`. Con un intero
positivo risolve esattamente una estrazione con quel numero e usa la relativa
tupla come cutoff storico inclusivo.

In questa modalità:

- l'estrazione di riferimento appare subito sotto l'intestazione;
- il riferimento e tutte le estrazioni precedenti sono mostrati in ordine cronologico discendente;
- le estrazioni successive a un riferimento esplicito vengono escluse;
- i cinque numeri di ogni ruota ricevono cinque colori posizionali distinti;
- ogni occorrenza precedente mantiene il colore corrispondente soltanto sulla stessa ruota;
- gli stessi valori presenti su altre ruote non costituiscono corrispondenze;
- la palette viene riutilizzata indipendentemente per ogni ruota.

La modalità è mutuamente esclusiva con `--digit` e `--number`. Per
scegliere un altro database usare una delle forme non ambigue seguenti:

```bash
./lotto.py db --database data/lotto-2025.sqlite3 --latest-occurrences
./lotto.py db --database data/lotto-2025.sqlite3 --latest-occurrences 100
```

Il database non viene mai riordinato o modificato. Si tratta di una
visualizzazione retrospettiva, non di un segnale previsionale, una modifica
delle probabilità o una raccomandazione di gioco.

## Esempi

```bash
./lotto.py current
./lotto.py current --to-num 119
./lotto.py update --year 2026
./lotto.py db update --year 2025
./lotto.py db update --from-year 2021 --to-year 2026 --dry-run
./lotto.py anomalies --help
./lotto.py rolling-frequency
./lotto.py kernel \
    --output _work/transition-kernel-verification.json
./lotto.py db --digit 1,6,7
./lotto.py db --number 1,17,90
./lotto.py db --digit 7 --number 17,90
./lotto.py db --latest-occurrences
./lotto.py db --database data/lotto-2025.sqlite3 --latest-occurrences 100
```
