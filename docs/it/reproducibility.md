# Riproducibilità

[English](../reproducibility.md) | **Italiano**

Eseguire tutti i comandi dalla radice del repository.

Gli output transitori devono essere scritti sotto `_work/`. Gli artefatti
deterministici destinati alla pubblicazione sono tracciati sotto `generated/`.

## Suite automatizzata

```bash
python3 -m unittest discover -v
```

Al checkpoint di pubblicazione di luglio 2026, la fonte di verità potata contiene
170 test superati.

## Dispatcher unificato

Elencare i 15 strumenti eseguibili e consultare l’help di qualunque tool:

```bash
./lotto.py list
./lotto.py help current
```

Il dispatcher inoltra senza modifiche tutti gli argomenti rimanenti e conserva
il codice di uscita del comando sottostante. L’invocazione diretta di ogni
script originale resta supportata.

Vedere la [guida ai comandi](cli-reference.md).

## Verifica indipendente del kernel

```bash
python3 verify_transition_kernel.py \
    --output _work/reproduction/transition-kernel.json
```

Fra gli invarianti attesi:

- `verified: true`;
- `draw_combinations: 43949268`;
- `observed_digit_mask_classes: 968`;
- `states_verified: 1024`;
- errore assoluto massimo inferiore a `1e-12`.

## Atlante degli stati

Rigenerare in una directory temporanea:

```bash
python3 generate_state_atlas.py \
    --csv-output _work/reproduction/coverage-state-atlas.csv \
    --json-output _work/reproduction/coverage-state-atlas.json \
    --summary-output _work/reproduction/state-atlas-summary.md
```

Confrontare gli artefatti machine-readable:

```bash
cmp generated/coverage-state-atlas.csv \
    _work/reproduction/coverage-state-atlas.csv

cmp generated/coverage-state-atlas.json \
    _work/reproduction/coverage-state-atlas.json
```

## Analisi strutturale

```bash
python3 generate_structural_analysis.py \
    --classes-csv \
    _work/reproduction/coverage-symmetry-classes.csv \
    --cardinality-csv \
    _work/reproduction/coverage-cardinality-loss.csv \
    --json-output \
    _work/reproduction/coverage-structural-analysis.json \
    --summary-output \
    _work/reproduction/structural-symmetry-analysis.md
```

Confrontare con gli output tracciati:

```bash
cmp generated/coverage-symmetry-classes.csv \
    _work/reproduction/coverage-symmetry-classes.csv

cmp generated/coverage-cardinality-loss.csv \
    _work/reproduction/coverage-cardinality-loss.csv

cmp generated/coverage-structural-analysis.json \
    _work/reproduction/coverage-structural-analysis.json
```

Al checkpoint di luglio 2026, tutti e cinque gli artefatti teorici rigenerati
coincidevano byte per byte con le versioni tracciate.

## Distribuzione storica dei cicli

```bash
python3 analyze_historical_cycle_distribution.py \
    --primary-databases \
    data/lotto-2023.sqlite3 \
    data/lotto-2024.sqlite3 \
    data/lotto-2025.sqlite3 \
    data/lotto-2026.sqlite3 \
    --text-output \
    _work/reproduction/historical-cycle-distribution.txt \
    --json-output \
    _work/reproduction/historical-cycle-distribution.json
```

Intervallo atteso:

```text
2023-01-03 -> 2026-07-28
```

Numero atteso di cicli completi:

```text
2253
```

Il segmento secondario predefinito è vuoto.

## Classi strutturali storiche

```bash
python3 analyze_historical_symmetry_classes.py \
    --database data/lotto-2023.sqlite3 \
    --database data/lotto-2024.sqlite3 \
    --database data/lotto-2025.sqlite3 \
    --database data/lotto-2026.sqlite3 \
    --csv-output \
    _work/reproduction/historical-symmetry-classes.csv \
    --json-output \
    _work/reproduction/historical-symmetry-classes.json
```

Sintesi attesa:

```text
27 classi strutturali
7869 osservazioni a un passo
```

## Anomalie storiche

```bash
python3 analyze_coverage_anomalies.py \
    --database data/lotto-2023.sqlite3 \
    --database data/lotto-2024.sqlite3 \
    --database data/lotto-2025.sqlite3 \
    --database data/lotto-2026.sqlite3 \
    --label historical-2023-2026 \
    --output-prefix \
    _work/reproduction/coverage-anomalies-2023-2026
```

Al checkpoint corrente, la soglia predefinita dell’`1%` produce:

```text
A1=21
A2=3
A3=12
A4=0
totale=36
```

## Stato corrente

```bash
./lotto.py current
./lotto.py current --to 2026-07-25
./lotto.py current --to-num 119
```

L’output deve dichiarare il limite esatto applicato al database. `--to` limita
l’analisi mediante una data ISO inclusiva; `--to-num` la limita mediante il
numero inclusivo del concorso. È accettata anche la grafia equivalente
`--to_num`; i due tipi di limite non possono essere combinati.

La riga finale `TUTTE` utilizza le ruote con età positiva nel ciclo corrente.
L’insieme delle cifre più presenti è l’unione su tutte le ruote attive, mentre
l’insieme delle cifre mancanti è l’unione soltanto sulle ruote attive a pari
merito per la massima probabilità di completamento entro una estrazione.
Mostra quindi la loro intersezione e le codifiche valide di due cifre ordinate
e distinte appartenenti all’intersezione. La riga è descrittiva e non definisce
un modello probabilistico alterato.

Gli stati correnti e le anomalie attive cambiano con l’importazione di nuove
estrazioni.

## Integrità e aggiornamento del database

Esaminare le opzioni:

```bash
python3 import_lotto.py --help
python3 update_lotto_database.py --help
```

Aggiornare l’archivio annuale corrente:

```bash
python3 update_lotto_database.py
```

L’aggiornamento richiede un archivio completo e contiguo che inizi dal concorso
1, costruisce un database temporaneo, lo verifica e sostituisce la destinazione
in modo atomico.

## Pulizia Git

Un’esecuzione di riproduzione diretta interamente sotto `_work/` non deve
modificare file tracciati:

```bash
git status --short
```

`docs/validation-results.md` è intenzionalmente assente. Le prove di
riproducibilità vengono generate dall’implementazione corrente anziché
conservate in un documento manuale da mantenere sincronizzato.
