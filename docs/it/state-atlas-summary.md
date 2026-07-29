# Sintesi dell’atlante degli stati di copertura

[English](../state-atlas-summary.md) | **Italiano**

## Stato

L’atlante matematico completo è stato generato e verificato.

Gli artefatti machine-readable restano unici:

```text
generated/coverage-state-atlas.csv
generated/coverage-state-atlas.json
```

La versione italiana documenta gli stessi valori senza duplicare i dati.

## Ambito

L’atlante contiene tutti i 1.023 stati non vuoti.

Per ogni stato registra:

- insieme esatto delle cifre mancanti;
- cardinalità;
- probabilità di completamento in una estrazione;
- probabilità di completamento entro 2, 3, 5 e 10 estrazioni;
- media residua;
- varianza;
- deviazione standard;
- quantili 50%, 90%, 95% e 99%;
- rango stabile di difficoltà;
- classe strutturale.

## Sintesi per cardinalità

La cardinalità fornisce una tendenza generale:

- meno cifre mancano, minore è normalmente il tempo residuo;
- più cifre mancano, maggiore è normalmente il tempo residuo.

Non è però una statistica sufficiente.

Stati della stessa cardinalità possono avere metriche diverse perché l’identità
delle cifre modifica la distribuzione.

La presenza della cifra `9` è il caso strutturale più evidente.

## Stati più facili

Gli stati singoletti `{0}`–`{8}` sono equivalenti.

Per ciascuno:

```text
Completamento in 1:  68,1643%
Completamento in 2:  89,86%
Completamento in 3:  96,77%
Completamento in 5:  99,67%
Media residua:        1,467
```

Sono gli stati non vuoti con minore attesa residua.

## Stato singoletto `{9}`

Lo stato `{9}` è più difficile degli altri singoletti:

```text
Completamento in 1:  45,3005%
Completamento in 2:  70,08%
Completamento in 3:  83,63%
Completamento in 5:  95,10%
Media residua:        2,207
```

La differenza è interamente strutturale: la cifra `9` compare in meno numeri
dell’universo `01–90`.

## Stato iniziale completo

Lo stato

\[
\{0,1,2,3,4,5,6,7,8,9\}
\]

è il più difficile secondo l’ordinamento per inclusione.

Le metriche principali sono:

| Metrica | Valore |
|:---|---:|
| Completamento in 1 | 0,038226% |
| Completamento entro 2 | 21,26% |
| Completamento entro 3 | 60,47% |
| Completamento entro 5 | 92,28% |
| Media residua | 3,506190 |
| Varianza | 1,924821 |
| Mediana | 3 |
| 95º percentile | 6 |
| 99º percentile | 8 |

## Ordinamento

Il rango è contiguo e deterministico.

L’ordinamento principale usa l’attesa residua crescente, con criteri stabili per
risolvere eventuali uguaglianze strutturali.

Il rango non rappresenta una raccomandazione di gioco.

## Monotonia

Se \(A\subseteq B\), allora:

\[
E(A)\leq E(B)
\]

e

\[
P(\tau_A\leq h)
\geq
P(\tau_B\leq h)
\]

per ogni orizzonte \(h\).

L’atlante verifica esaustivamente questa proprietà su tutte le coppie
confrontabili.

## Riproduzione

```bash
python3 generate_state_atlas.py
```

Per verificare senza modificare gli artefatti tracciati:

```bash
python3 generate_state_atlas.py \
    --csv-output _work/atlas/coverage-state-atlas.csv \
    --json-output _work/atlas/coverage-state-atlas.json \
    --summary-output _work/atlas/state-atlas-summary.md

cmp generated/coverage-state-atlas.csv \
    _work/atlas/coverage-state-atlas.csv

cmp generated/coverage-state-atlas.json \
    _work/atlas/coverage-state-atlas.json
```

Al checkpoint di luglio 2026, gli artefatti rigenerati coincidono byte per byte
con quelli tracciati.
