# Analisi delle simmetrie strutturali

[English](../structural-symmetry-analysis.md) | **Italiano**

## Scopo

L’analisi identifica quali stati hanno comportamento matematicamente identico
sotto rietichettature delle cifre compatibili con la struttura di `01–90`.

Non si tratta di una approssimazione empirica: le classi sono conseguenze esatte
del conteggio dei numeri ammessi.

## Teorema di conteggio dei numeri ammessi

Per un insieme di cifre proibite \(A\), sia

\[
c(A)
\]

il numero di elementi di `01–90` che non contengono alcuna cifra di \(A\).

Il valore di \(c(A)\) dipende da tre quantità:

1. se `9` appartiene ad \(A\);
2. se `0` appartiene ad \(A\);
3. quante cifre fra `1–8` appartengono ad \(A\).

Non dipende dall’identità specifica delle cifre selezionate all’interno di
`1–8`.

Questa proprietà determina il gruppo di simmetria del kernel.

## Classi esatte

Gli stati non vuoti si dividono in tre famiglie.

### Famiglia senza `9`

Quando `9` non è nello stato, le cifre `0–8` sono intercambiabili.

La classe dipende soltanto dal numero di cifre mancanti fra `0–8`.

### Famiglia con `9` ma senza `0`

Quando `9` è mancante e `0` non lo è, la classe dipende dal numero di cifre
mancanti fra `1–8`.

### Famiglia con `0` e `9`

Quando mancano sia `0` sia `9`, la classe dipende ancora dal numero di cifre
mancanti fra `1–8`, ma appartiene a una famiglia distinta.

Il totale è:

\[
9+9+9=27
\]

classi strutturali non vuote.

## Molteplicità

Le molteplicità derivano dai coefficienti binomiali.

Per la famiglia senza `9`, con \(k\) cifre mancanti fra `0–8`:

\[
\binom{9}{k}.
\]

Per le due famiglie contenenti `9`, con \(k\) cifre mancanti fra `1–8`:

\[
\binom{8}{k}.
\]

La somma delle molteplicità è 1.023.

## Equivarianza del kernel

Sia \(\pi\) una permutazione ammessa delle cifre.

Per ogni stato \(S\) e successore \(T\):

\[
K(\pi(S),\pi(T))=K(S,T).
\]

Il progetto verifica esaustivamente questa proprietà sull’intero kernel.

Ne segue che gli stati nella stessa classe condividono:

- probabilità di transizione equivalenti;
- distribuzione del tempo di assorbimento;
- media;
- varianza;
- quantili;
- rango di difficoltà a parità di criteri strutturali.

## Perdita di informazione dalla sola cardinalità

La cardinalità

\[
\lvert S\rvert
\]

non identifica la classe.

Esempio:

```text
{1} e {9}
```

hanno entrambi cardinalità uno, ma:

```text
P(chiusura di {1} in una estrazione) = 68,1643%
P(chiusura di {9} in una estrazione) = 45,3005%
```

La media residua è rispettivamente circa:

```text
1,467
2,207
```

Una sintesi basata soltanto sul numero di cifre mancanti perde quindi
informazione strutturale essenziale.

## Il ruolo distinto dello zero

Quando `9` non è proibito, `0` appartiene alla stessa orbita delle cifre `1–8`.

Quando `9` è proibito, `0` diventa distinto.

La ragione è il numero `90`, che collega in modo particolare le cifre `9` e `0`
nella struttura `01–90`.

Questa asimmetria è verificata sia nel conteggio chiuso dei numeri ammessi sia
nel kernel completo.

## Confronto storico per classe

L’archivio continuo 2023–2026 produce:

```text
Classi:       27
Osservazioni: 7.869
Intervallo:   2023-01-10 -> 2026-07-28
```

Le frequenze empiriche di completamento a un passo vengono confrontate con la
probabilità esatta della classe.

Il confronto è aggregato e descrittivo; le ruote condividono il calendario e
non sono trattate come indipendenti.

## Artefatti

```text
generated/coverage-symmetry-classes.csv
generated/coverage-cardinality-loss.csv
generated/coverage-structural-analysis.json
```

Gli artefatti restano indipendenti dalla lingua e rappresentano la fonte di
verità machine-readable.

## Riproduzione

```bash
python3 generate_structural_analysis.py
```

Per l’analisi storica:

```bash
python3 analyze_historical_symmetry_classes.py
```

Al checkpoint di luglio 2026, gli artefatti teorici rigenerati coincidevano byte
per byte con quelli tracciati.

## Confine

Le simmetrie descrivono equivalenze matematiche del modello.

Non implicano:

- equivalenza economica di giocate;
- vantaggio di una classe rispetto a un’altra;
- effetto compensativo;
- capacità previsionale derivante dalle frequenze storiche.
