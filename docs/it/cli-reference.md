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
| `update` | `update_lotto_database.py` | Aggiornamento sicuro dell’archivio completo |
| `db` | `view_lotto_database.sh` | Esplorazione del database da terminale |
| `anomalies` | `analyze_coverage_anomalies.py` | Analisi storica delle anomalie A1–A4 |
| `completion` | `analyze_coverage_completion.py` | Analisi del completamento dei cicli naturali |
| `residuals` | `analyze_coverage_markov_residuals.py` | Confronto dei tempi residui teorici e osservati |
| `validation` | `analyze_coverage_markov_validation.py` | Calibrazione empirica delle probabilità Markov |
| `digit-coverage` | `analyze_digit_coverage.py` | Copertura delle cifre su finestre mobili |
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
- `returns` → `return-times`;
- `cycle-distribution` → `cycles`;
- `symmetry` → `symmetry-history`.

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
./lotto.py anomalies --help
./lotto.py kernel \
    --output _work/transition-kernel-verification.json
./lotto.py db --digit 1,6,7
./lotto.py db --number 1,17,90
./lotto.py db --digit 7 --number 17,90
./lotto.py db --latest-occurrences
./lotto.py db --database data/lotto-2025.sqlite3 --latest-occurrences 100
```
