# Lotto Coverage Research

Laboratorio privato per l'acquisizione e l'analisi esplorativa delle estrazioni
del Lotto italiano.

Il progetto studia proprietà descrittive e combinatorie delle cifre decimali
presenti nei numeri estratti, con particolare attenzione alla copertura delle
cifre `0–9` su finestre mobili della stessa ruota.

## Obiettivi

- importare archivi annuali in database SQLite separati;
- verificare integrità, continuità e completezza dei dati;
- analizzare la copertura delle cifre `0–9`;
- costruire backtest riproducibili;
- distinguere una percentuale grezza da un vantaggio rispetto al caso;
- documentare anche ipotesi respinte o confutate.

## Stato della ricerca

La regola principale sottoposta a replica indipendente è stata:

> Dopo tre estrazioni consecutive sulla stessa ruota, quando manca esattamente
> una cifra tra `0–9`, verificare se quella cifra compare nella quarta
> estrazione.

Risultato della replica sull'intero archivio 2025:

- segnali: 775;
- hit: 459;
- tasso osservato: 59,23%;
- tasso teorico ponderato: 59,82%;
- delta: −0,59%;
- prima metà dell'anno: −1,04%;
- seconda metà dell'anno: −0,16%.

La regola non ha mostrato un vantaggio predittivo replicabile.

Una precedente anomalia osservata su un piccolo campione del 2026 non è stata
confermata dal campione indipendente 2025. I test di permutazione successivamente
riconosciuti come contaminati dalla costruzione delle finestre sono stati
rimossi dal repository.

## Struttura

```text
data/
    lotto-2025.sqlite3
    lotto-2026.sqlite3

strategies/
    digit_coverage.py
    twin_digits.py

tests/
    test_coverage_backtest.py
    test_digit_coverage.py
    test_frozen_coverage_rule.py
    test_twin_digits.py
    test_two_missing_backtest.py

analyze_digit_coverage.py
analyze_coverage_backtest.py
analyze_frozen_coverage_rule.py
analyze_strategies.py
analyze_twin_history.py
analyze_two_missing_backtest.py
import_lotto.py
```

Importazione

Il comportamento predefinito mantiene l'importazione delle ultime 60
estrazioni del 2026:

python3 import_lotto.py

Per importare un archivio completo in un database separato:

python3 import_lotto.py \
  --source "_work/archive-2025.html" \
  --database "data/lotto-2025.sqlite3" \
  --source-url \
    "https://www.estrazionedellotto.it/risultati/archivio-lotto-2025" \
  --limit all
Analisi della copertura
python3 analyze_digit_coverage.py \
  --database "data/lotto-2026.sqlite3" \
  --max-window-size 3

Replica indipendente della regola congelata sul 2025:

python3 analyze_frozen_coverage_rule.py \
  --database "data/lotto-2025.sqlite3"
Test

Il progetto usa esclusivamente la libreria standard Python.

python3 -m unittest discover -v
Dati

Gli archivi HTML di origine non sono versionati e rimangono sotto _work/.

Fonti utilizzate:

https://www.estrazionedellotto.it/risultati/archivio-lotto-2025
https://www.estrazionedellotto.it/risultati/archivio-lotto-2026

I database SQLite contengono una copia strutturata delle estrazioni usata per
la ricerca privata e riproducibile.

Avvertenza

Questo progetto è un laboratorio statistico e didattico.

Non fornisce sistemi di gioco, previsioni affidabili o garanzie economiche.
Una regolarità descrittiva, una percentuale elevata o un risultato favorevole
su un campione limitato non implicano un vantaggio sul gioco futuro.
