# Anomalie della copertura

[English](../coverage-anomalies.md) | **Italiano**

## Scopo

Il rilevatore identifica eventi storici rari rispetto al modello esatto dello
stato corrente.

Le categorie A1–A4 sono descrittive e retrospettive. Non alterano il kernel di
transizione e non costituiscono segnali di gioco.

## Protocollo di osservazione

L’analisi usa la sequenza cronologica continua degli archivi 2023–2026.

Per ogni ruota:

- il ciclo iniziale censurato a sinistra viene escluso;
- le transizioni dei cicli osservabili vengono registrate;
- un ciclo completato non viene trattato come censurato;
- il ciclo terminale aperto non produce una falsa anomalia A1;
- le date e l’ordine delle ruote sono conservati.

Le undici ruote condividono il calendario e non sono considerate repliche
indipendenti.

## Soglie predefinite

La soglia primaria è

\[
\alpha=0,01.
\]

La finestra di ricorrenza A4 è di 10 transizioni valide sulla stessa ruota.

La soglia di ricorrenza è anch’essa `0,01`.

Le soglie sono convenzioni descrittive, non una procedura inferenziale completa
per confronti multipli.

## A1 — Anomalia di persistenza

A1 viene registrata quando un ciclo rimane aperto per \(h\) ulteriori
estrazioni a partire da uno stato sorgente \(S\) e

\[
P(\tau_S>h)\leq\alpha.
\]

Per evitare duplicati, viene emesso soltanto il primo attraversamento della
soglia all’interno dello stesso ciclo.

Esempio per lo stato completo:

\[
P(\tau_D>8)=0,895955\%.
\]

Poiché il valore scende sotto l’`1%` per la prima volta a \(h=8\), un ciclo
completo ancora aperto dopo otto estrazioni genera A1.

La persistenza non significa che la chiusura sia “dovuta”.

## A2 — Anomalia di chiusura immediata

A2 descrive una transizione

\[
S\rightarrow\varnothing
\]

la cui probabilità esatta soddisfa

\[
K(S,\varnothing)\leq\alpha.
\]

La chiusura immediata dello stato completo ha probabilità

\[
0,038226\%
\]

ed è quindi classificata come evento estremo con la soglia predefinita.

Una chiusura rara non cambia la distribuzione della estrazione successiva.

## A3 — Anomalia di transizione non terminale

A3 riguarda una transizione di progresso

\[
S\rightarrow T,
\qquad
\varnothing\neq T\subsetneq S.
\]

Il punteggio primario non usa soltanto la probabilità atomica
\(K(S,T)\).

Viene calcolata la massa complessiva delle transizioni non terminali dallo stesso
stato sorgente che non sono più probabili dell’esito osservato.

Questo evita di classificare meccanicamente ogni singola cella piccola senza
considerare la distribuzione discreta degli esiti comparabili.

Il rapporto conserva comunque anche la probabilità atomica della transizione.

## A4 — Anomalia di ricorrenza

A4 viene considerata quando, sulla stessa ruota, la medesima chiave primaria di
anomalia ricompare entro la finestra configurata.

La probabilità riportata è un limite superiore conservativo di Bonferroni:

\[
p_{\text{A4}}
=
\min(1,w\,p),
\]

dove \(w\) è la finestra e \(p\) il punteggio primario dell’evento corrente.

Il calcolo è condizionato al fatto che una prima anomalia sia già stata
osservata.

Il prodotto dei due punteggi primari viene conservato separatamente come misura
descrittiva, ma non è interpretato come p-value della finestra.

## Severità

Le etichette di severità dipendono dalla probabilità condizionale:

- `rare`: evento sotto la soglia primaria;
- `extreme`: evento sostanzialmente più raro della soglia primaria.

La severità non misura conseguenze pratiche e non implica irregolarità del
processo reale.

## Regole contro i duplicati

Il validatore garantisce che:

- la stessa firma esatta non venga emessa due volte;
- A1 compaia una sola volta per il primo attraversamento del ciclo;
- A2 e A3 non descrivano la stessa transizione;
- A4 resti separata dall’anomalia primaria;
- un ciclo terminale censurato non generi A1;
- un ciclo completato venga valutato normalmente.

## Risultati 2023–2026

Con la soglia primaria dell’`1%`:

| Categoria | Eventi |
|:---|---:|
| A1 | 21 |
| A2 | 3 |
| A3 | 12 |
| A4 | 0 |
| Totale | 36 |

Ulteriori proprietà del rapporto:

```text
Firme uniche:                    20
Eventi duplicati:               0
Sovrapposizioni A2/A3:          0
A1 censurate a destra:          0
Eventi rari:                    33
Eventi estremi:                 3
```

Nel solo archivio 2026 fino al concorso 120 sono stati osservati:

```text
A1=5
A2=1
A3=0
A4=0
```

Al concorso 120 del 28 luglio 2026 non era attiva alcuna anomalia.

## Output

Il comando predefinito è:

```bash
python3 analyze_coverage_anomalies.py
```

Gli output sono:

```text
_work/coverage-anomalies-2023-2026.csv
_work/coverage-anomalies-2023-2026.json
```

È possibile specificare più database ripetendo `--database`.

## Confine interpretativo

Una anomalia descrive un evento raro rispetto al modello condizionato sullo
stato sorgente.

Non dimostra:

- manipolazione;
- memoria del sistema;
- ritorno alla media nelle estrazioni successive;
- compensazione delle cifre;
- vantaggio economico;
- ripetibilità futura dell’evento.
