# Dinamiche di copertura delle cifre nel Lotto

[English](README.md) | **Italiano**

Un modello esatto a stati finiti della copertura delle cifre decimali nelle
estrazioni del Lotto italiano.

Il progetto rappresenta le cifre ancora mancanti in un ciclo naturale di
copertura come un processo stocastico assorbente, ne deriva le proprietà
teoriche e le confronta con le osservazioni storiche.

Il repository è un progetto matematico e di riproducibilità. Non è un sistema
di gioco, uno strumento per selezionare numeri o una prova che le estrazioni
passate modifichino le probabilità future.

## Risultato principale

Per una singola ruota:

- i numeri del Lotto sono rappresentati come `01`–`90`;
- lo zero iniziale fa parte della rappresentazione;
- uno stato è l’insieme delle cifre ancora mancanti nel ciclo corrente;
- esistono \(2^{10}=1.024\) stati;
- l’insieme vuoto è assorbente nel modello matematico;
- dopo il completamento, il processo storico naturale riparte con tutte le
  dieci cifre mancanti.

Il kernel di transizione esatto è calcolato combinatoriamente e verificato in
modo indipendente mediante una programmazione dinamica intera su tutte le
estrazioni non ordinate di cinque numeri.

Stato attuale della verifica:

| Quantità | Risultato |
|:---|---:|
| Estrazioni non ordinate di cinque numeri | 43.949.268 |
| Maschere di unione delle cifre osservate | 968 |
| Stati verificati | 1.024 |
| Celle di transizione verificate | 58.848 |
| Massima discrepanza assoluta | 2,2894 × 10⁻¹⁵ |
| Stati non vuoti nell’atlante | 1.023 |
| Classi strutturali di simmetria | 27 |

Il tempo teorico di assorbimento dallo stato iniziale con tutte le dieci cifre
mancanti ha:

| Metrica | Valore esatto |
|:---|---:|
| Media | 3,506190 estrazioni |
| Varianza | 1,924821 |
| Deviazione standard | 1,387379 |
| Mediana | 3 estrazioni |
| 90º percentile | 5 estrazioni |
| 95º percentile | 6 estrazioni |
| 99º percentile | 8 estrazioni |
| Completamento entro 3 estrazioni | 60,47% |
| Completamento entro 5 estrazioni | 92,28% |

## Confronto storico

L’archivio continuo attuale comprende tutte le estrazioni dal 3 gennaio 2023
al 28 luglio 2026:

| Archivio | Intervallo dei concorsi |
|:---|:---|
| 2023 | 1–182 |
| 2024 | 1–209 |
| 2025 | 1–208 |
| 2026 | 1–120 |

Dopo l’applicazione delle regole documentate di censura a sinistra e a destra,
la storia aggregata contiene 2.253 cicli naturali completi.

| Metrica | Osservata | Modello esatto |
|:---|---:|---:|
| Durata media | 3,481580 | 3,506190 |
| Varianza | 1,938964 | 1,924821 |
| Deviazione standard | 1,392467 | 1,387379 |
| Mediana | 3 | 3 |
| 90º percentile | 5 | 5 |
| 95º percentile | 6 | 6 |
| 99º percentile | 8 | 8 |

Lungo la distribuzione cumulativa delle durate fino al massimo osservato di
18 estrazioni:

- differenza assoluta massima: `0.013189`;
- differenza assoluta media: `0.001867`.

Si tratta di confronti aggregati descrittivi. Le ruote condividono il calendario
delle estrazioni e non sono trattate come repliche indipendenti ai fini di un
test inferenziale.

## Interpretazione dello stato esatto

Nel modello ideale di estrazione casuale, l’insieme esatto delle cifre mancanti
è sufficiente a determinare la legge delle transizioni future.

L’età del ciclo, l’ordine delle precedenti apparizioni e la durata di
un’assenza non modificano le probabilità dello stato successivo quando lo stato
corrente è già noto.

L’identità delle cifre è invece importante:

- gli stati singoletti `{0}`–`{8}` si chiudono alla prossima estrazione con
  probabilità `68,1643%`;
- lo stato singoletto `{9}` si chiude alla prossima estrazione con probabilità
  `45,3005%`.

La differenza deriva dalla struttura decimale dei numeri `01–90`. Non è un
effetto di ritardo e non rappresenta una forza compensativa.

## Anomalie storiche

Il rilevatore registra quattro categorie descrittive retrospettive:

- A1 — persistenza insolitamente lunga di uno stato aperto;
- A2 — completamento immediato insolitamente raro;
- A3 — transizione non terminale insolitamente rara;
- A4 — ricorrenza della stessa chiave di anomalia primaria entro una finestra
  prefissata.

Con una soglia primaria dell’`1%` sull’archivio continuo 2023–2026:

| Categoria | Eventi |
|:---|---:|
| A1 | 21 |
| A2 | 3 |
| A3 | 12 |
| A4 | 0 |
| Totale | 36 |

Gli eventi sono etichette storiche, non prove di un vantaggio previsionale.
Al concorso 120 del 28 luglio 2026 non era attiva alcuna anomalia A1–A4.

## Backtest delle frequenze rolling

Un esperimento walk-forward predefinito ha verificato le finestre rolling delle
cifre più frequenti `3`, `6`, `8` e `12`. L’ipotesi primaria `N = 6` è stata
fissata prima della valutazione.

Ogni rosa è stata confrontata con rose uniformi casuali della stessa
dimensione. Il risultato più forte nel periodo di sviluppo, `N = 8` sugli ambi,
non si è replicato nel periodo held-out 2026. Anche `N = 6` è rimasta sotto la
media casuale held-out degli ambi.

Nessuna finestra mostra un vantaggio previsionale stabile. La contabilità di
posta virtuale, vincite e ritorno finanziario è stata deliberatamente esclusa
dallo scope implementato.

Vedere il
[report completo sulle frequenze rolling](docs/it/rolling-frequency-backtest.md).

## Interfaccia unificata da riga di comando

I 16 strumenti eseguibili restano utilizzabili autonomamente, mentre `lotto.py`
li espone attraverso un unico dispatcher facilmente esplorabile:

```bash
./lotto.py list
./lotto.py help current
./lotto.py current
./lotto.py current --to 2026-07-25
./lotto.py current --to-num 119
```

Gli argomenti successivi al sottocomando vengono inoltrati senza modifiche allo
strumento sottostante. Il wrapper restituisce lo stesso codice di uscita del
tool eseguito.

Il report `current` include una riga finale `TUTTE`. Considera soltanto le ruote
il cui ciclo naturale corrente ha età positiva e mostra:

- l’unione degli insiemi delle cifre più presenti su tutte le ruote attive;
- l’unione degli insiemi delle cifre mancanti soltanto sulle ruote attive a
  pari merito per la massima probabilità di completamento entro una estrazione;
- la loro intersezione `C`;
- tutti i numeri ordinati validi di due cifre formati dalle cifre di `C`, ammettendo le ripetizioni.

È una descrizione trasversale deterministica e, facoltativamente, un criterio di
gioco virtuale. Non modifica la probabilità di alcun numero del Lotto e non
costituisce prova di un vantaggio previsionale.

La lista completa è nella
[guida ai comandi](docs/it/cli-reference.md).

## Verifica rapida

Eseguire l’intera suite automatizzata:

```bash
python3 -m unittest discover -v
```

La suite corrente contiene 242 test.

Verificare indipendentemente il kernel esatto:

```bash
./lotto.py kernel \
    --output _work/transition-kernel-verification.json
```

Rigenerare l’atlante completo e l’analisi strutturale:

```bash
./lotto.py atlas
./lotto.py structure
```

Ricalcolare i confronti storici continui:

```bash
./lotto.py cycles
./lotto.py symmetry-history
./lotto.py anomalies
./lotto.py rolling-frequency
```

Esaminare lo stato corrente della copertura:

```bash
./lotto.py current
./lotto.py current --to 2026-07-25
./lotto.py current --to-num 119
```

`--to` applica un limite inclusivo basato sulla data ISO. `--to-num` applica un
limite inclusivo basato sul numero del concorso; `--to_num` resta disponibile
come grafia equivalente. Le due opzioni sono mutuamente esclusive.

Aggiornare ed esplorare il database annuale corrente:

```bash
./lotto.py update
./lotto.py db
./lotto.py db --digit 1,7,9
./lotto.py db --number 1,17,90
./lotto.py db --digit 7 --number 17,90
./lotto.py db --latest-occurrences
./lotto.py db --database data/lotto-2025.sqlite3 --latest-occurrences 100
```

`--digit` evidenzia ogni cifra selezionata ovunque compaia. `--number` evidenzia numeri del Lotto completi da `1` a `90`; l'opzione è ripetibile e accetta anche valori separati da virgola. Quando entrambi i selettori corrispondono, l'evidenziazione del numero completo prevale su quella delle singole cifre.

`--latest-occurrences [NUM_ESTRAZIONE]` attiva il tracciamento
retrospettivo sulla stessa ruota. Senza valore seleziona l'ultima estrazione
completa. Con un numero positivo usa quella estrazione come cutoff storico
inclusivo, esclude le estrazioni successive e mostra per prima la riga di
riferimento in ordine cronologico discendente. I cinque numeri di riferimento
usano colori posizionali distinti e le loro occorrenze precedenti vengono
evidenziate soltanto sulla stessa ruota.

La modalità è mutuamente esclusiva con `--digit` e `--number`. Per scegliere un
altro archivio usare la forma non ambigua
`--database PATH --latest-occurrences [NUM_ESTRAZIONE]`. La ripetizione storica
viene mostrata in modo descrittivo e non costituisce un segnale previsionale o
una raccomandazione di gioco.

## Struttura del repository

```text
.
├── data/                         archivi SQLite annuali
├── docs/                         documentazione del modello e della ricerca
│   └── it/                       documentazione italiana
├── generated/                    artefatti matematici deterministici
├── strategies/                   implementazioni di riferimento
├── tests/                        test matematici e dei dati
├── lotto.py                      dispatcher unico per tutti i 16 CLI
├── analyze_*.py                  analisi storiche e dello stato corrente
├── generate_state_atlas.py       atlante completo dei 1.023 stati
├── generate_structural_analysis.py
├── verify_transition_kernel.py   verifica indipendente esaustiva
├── import_lotto.py               importatore dell’archivio annuale
├── update_lotto_database.py      aggiornamento sicuro dell’archivio completo
└── view_lotto_database.sh        esploratore del database da terminale
```

## Documentazione

Iniziare dall’[indice italiano](docs/it/index.md).

L’interfaccia unificata è descritta nella
[guida italiana ai comandi](docs/it/cli-reference.md).

L’esperimento sulle frequenze rolling è documentato in
[`docs/it/rolling-frequency-backtest.md`](docs/it/rolling-frequency-backtest.md).

La specifica formale italiana è
[`docs/it/finite-state-model.md`](docs/it/finite-state-model.md).

Gli artefatti matematici machine-readable restano unici sotto `generated/`.

## Confine della ricerca

I precedenti esperimenti previsionali non hanno prodotto un vantaggio stabile
e indipendentemente utile dopo il condizionamento sullo stato esatto. Quella
linea di ricerca è chiusa e le implementazioni superate sono state eliminate.

La conclusione negativa è conservata in
[`docs/it/predictive-research-closure.md`](docs/it/predictive-research-closure.md).

L’archivio 2022 resta deliberatamente non importato e non ispezionato.
Ulteriori dati devono essere introdotti solo per una domanda matematica o di
validazione concreta e dichiarata in anticipo.

## Licenza

Distribuito secondo i termini della [licenza MIT](LICENSE).

Copyright © 2026 Giancarlo Cicellyn Comneno.
