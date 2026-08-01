# Backtest walk-forward delle frequenze rolling

[English](../rolling-frequency-backtest.md) | **Italiano**

## Domanda di ricerca

L’esperimento verifica un’euristica definita in anticipo:

1. calcolare la cifra decimale più frequente nelle `N` estrazioni precedenti
   sulla stessa ruota;
2. conservare tutte le cifre a pari merito per la frequenza massima;
3. combinarle con le cifre ancora mancanti dal ciclo naturale di copertura
   attivo;
4. valutare i numeri generati sull’estrazione successiva.

La finestra primaria è `N = 6`, scelta prima della valutazione perché sei
estrazioni corrispondono approssimativamente al 95° percentile esatto della
durata dei cicli naturali.

Le finestre di confronto sono:

- `N = 3`;
- `N = 6`;
- `N = 8`;
- `N = 12`.

L’esperimento è descrittivo. Non presume che la frequenza storica delle cifre
modifichi la probabilità dell’estrazione successiva.

## Protocollo walk-forward

Per ogni ruota e ogni estrazione obiettivo ammissibile:

- vengono usate soltanto estrazioni strettamente precedenti all’obiettivo;
- la frequenza è calcolata sulle `N` estrazioni immediatamente precedenti;
- vengono conservati tutti i pari merito per la frequenza massima;
- lo stato del ciclo naturale deve essere già sincronizzato;
- gli stati di età zero subito dopo il completamento vengono esclusi;
- si generano numeri validi del Lotto `01`–`90` usando:
  - cifra frequente seguita da cifra mancante;
  - cifra mancante seguita da cifra frequente;
  - cifra frequente ripetuta, quando valida;
- i candidati duplicati vengono eliminati;
- i risultati vengono valutati soltanto dopo aver congelato la rosa.

L’implementazione usa una scansione incrementale lineare di ogni ruota.
Produce le stesse osservazioni della precedente ricostruzione completa dei
prefissi, riducendo il backtest reale quadriennale da `118,111` secondi a
`1,407` secondi sulla macchina di sviluppo: un’accelerazione di `83,95×`.

## Suddivisione temporale

La suddivisione è stata fissata prima della valutazione:

| Periodo | Date inclusive | Funzione |
|:---|:---|:---|
| Sviluppo | dal 2023-01-01 al 2025-12-31 | Confronto e diagnosi |
| Held-out | dal 2026-01-01 al 2026-12-31 | Valutazione fuori campione |

L’esecuzione di riferimento pubblicata usa l’archivio 2026 fino al
concorso 120 del 28 luglio 2026.

L’ipotesi primaria `N = 6` resta primaria indipendentemente dai risultati
comparativi delle altre finestre.

## Baseline casuale a parità di dimensione

Ogni osservazione viene confrontata con una rosa uniforme casuale avente la
stessa dimensione della rosa euristica.

L’esecuzione documentata usa:

- `1.000` repliche per ogni finestra e periodo;
- seed base deterministico `20260731`;
- un seed derivato distinto e deterministico per ogni confronto.

Il p-value empirico unilaterale è:

```text
(numero di repliche casuali almeno pari all’osservato + 1)
----------------------------------------------------------
                     numero di repliche + 1
```

La baseline ignora l’identità dei candidati. La simulazione dipende soltanto
dalla dimensione della rosa e dai cinque numeri obiettivo.

## Risultati

### Periodo di sviluppo, 2023–2025

| N | Numeri centrati | Media casuale | Rapporto | p-value | Ambi centrati | Media casuale | Rapporto | p-value |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 3 | 1.815 | 1.782,25 | 1,018 | 0,2058 | 428 | 409,07 | 1,046 | 0,2488 |
| 6 | 1.607 | 1.587,09 | 1,013 | 0,2967 | 322 | 299,18 | 1,076 | 0,1588 |
| 8 | 1.553 | 1.511,99 | 1,027 | 0,1359 | 299 | 263,95 | 1,133 | 0,0380 |
| 12 | 1.411 | 1.434,98 | 0,983 | 0,7542 | 236 | 234,37 | 1,007 | 0,4875 |

`N = 8` ha prodotto il risultato più forte sugli ambi nel periodo di sviluppo.
Il p-value empirico `0,0380` potrebbe sembrare interessante se gli stessi dati
fossero stati usati sia per individuare sia per validare la finestra.

Il risultato deve quindi essere giudicato sul periodo held-out.

### Periodo held-out, 2026

| N | Numeri centrati | Media casuale | Rapporto | p-value | Ambi centrati | Media casuale | Rapporto | p-value |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 3 | 367 | 350,69 | 1,047 | 0,1728 | 79 | 75,52 | 1,046 | 0,3916 |
| 6 | 320 | 324,82 | 0,985 | 0,6154 | 49 | 63,94 | 0,766 | 0,9391 |
| 8 | 305 | 307,54 | 0,992 | 0,5854 | 42 | 52,09 | 0,806 | 0,8991 |
| 12 | 292 | 290,02 | 1,007 | 0,4535 | 45 | 45,31 | 0,993 | 0,5145 |

L’apparente evidenza di `N = 8` nel periodo di sviluppo non si replica. Nel
periodo held-out il numero di ambi è inferiore alla media della baseline
casuale a parità di dimensione.

Anche la finestra primaria predefinita `N = 6` produce meno ambi della baseline
nel periodo held-out. `N = 12` è quasi perfettamente allineata all’attesa
casuale. `N = 3` è moderatamente sopra la media, ma resta pienamente dentro la
normale variabilità della baseline.

## Conclusione

Nessuna finestra rolling verificata mostra un vantaggio stabile rispetto a rose
casuali della stessa dimensione.

In particolare:

- il risultato più forte nello sviluppo fallisce fuori campione;
- l’ipotesi primaria predefinita non supera la baseline held-out;
- l’esposizione combinatoria spiega gran parte dei conteggi grezzi;
- nessuna finestra sostiene un’interpretazione previsionale o sfruttabile.

Le frequenze passate e le cifre mancanti dal ciclo naturale restano proprietà
descrittive valide dell’archivio. La loro combinazione non dimostra che un
numero candidato diventi più probabile nell’estrazione successiva.

## Contabilità economica esclusa

La contabilità di posta virtuale, vincite e ritorno economico è stata
deliberatamente esclusa dallo scope implementato.

Il report non formula quindi alcuna affermazione sulla redditività e non
converte i risultati storici in valori finanziari. Il numero dei candidati e
degli ambi coperti resta disponibile come misura esplicita dell’esposizione
combinatoria.

## Riproduzione

Eseguire l’esperimento predefinito:

```bash
./lotto.py rolling-frequency
```

L’alias equivalente è:

```bash
./lotto.py rolling
```

Gli output machine-readable predefiniti sono:

```text
_work/rolling-frequency-backtest.csv
_work/rolling-frequency-backtest.json
```

Esempio personalizzato:

```bash
./lotto.py rolling-frequency \
    --window-size 6 \
    --repetitions 1000 \
    --seed 20260731 \
    --csv-output _work/rolling-n6.csv \
    --json-output _work/rolling-n6.json
```

Le opzioni `--database` e `--window-size` possono essere ripetute.

Tutti gli archivi SQLite vengono aperti in sola lettura. Nell’esecuzione di
riferimento, il digest SHA-256 di ogni database annuale era identico prima e
dopo il backtest.

## Verifica

L’implementazione è coperta da test per:

- confini delle finestre rolling;
- zeri iniziali;
- pari merito per la frequenza massima;
- rifiuto di ruote mescolate;
- generazione e deduplicazione dei candidati;
- valori non validi superiori a `90`;
- assenza di look-ahead sull’estrazione obiettivo;
- gestione degli stati sincronizzati e di età zero;
- unione cronologica degli archivi;
- confini temporali inclusivi;
- baseline casuali deterministiche a parità di dimensione;
- output CSV e JSON deterministici;
- dispatch dalla CLI unificata.

A questo checkpoint la suite completa del repository contiene `242` test.
