# Distribuzione storica dei cicli di copertura

[English](../historical-cycle-distribution.md) | **Italiano**

## Scopo

Il rapporto confronta le durate dei cicli storici completi con la distribuzione
esatta del tempo di assorbimento generata dal modello a stati finiti.

Il confronto è descrittivo. Non è un test inferenziale di indipendenza e non è
una regola per selezionare numeri.

## Oggetto teorico

Un ciclo naturale inizia con tutte le dieci cifre mancanti. Ogni estrazione
rimuove le cifre osservate nei cinque numeri della ruota, rappresentati come
`01–90`. Il ciclo termina quando l’insieme delle cifre mancanti diventa vuoto.

Per lo stato iniziale completo, la distribuzione esatta ha:

| Metrica | Valore esatto |
|:---|---:|
| Media | 3,506190 |
| Varianza | 1,924821 |
| Deviazione standard | 1,387379 |
| Mediana | 3 |
| 90º percentile | 5 |
| 95º percentile | 6 |
| 99º percentile | 8 |

## Archivi storici

Il segmento primario è continuo:

| Anno | Primo concorso | Ultimo concorso | Prima data | Ultima data |
|:---|---:|---:|:---|:---|
| 2023 | 1 | 182 | 2023-01-03 | 2023-12-30 |
| 2024 | 1 | 209 | 2024-01-02 | 2024-12-31 |
| 2025 | 1 | 208 | 2025-01-02 | 2025-12-30 |
| 2026 | 1 | 120 | 2026-01-02 | 2026-07-28 |

I quattro database contengono 719 date di estrazione e vengono uniti
cronologicamente per ciascuna ruota.

Non esiste un segmento secondario predefinito.

## Regole di continuità e censura

Per ogni ruota:

1. il primo ciclo osservato viene escluso perché il suo vero inizio potrebbe
   precedere l’archivio;
2. i cicli completi successivi al primo completamento osservato vengono
   conservati;
3. il ciclo finale incompleto viene registrato come censurato a destra ma
   escluso dal campione delle durate complete;
4. i confini annuali non interrompono un ciclo quando gli archivi sono
   cronologicamente continui.

Le undici ruote condividono il calendario. I loro cicli vengono aggregati per il
confronto descrittivo, ma non sono considerati statisticamente indipendenti.

## Risultati fino al 28 luglio 2026

Il segmento continuo contiene 2.253 cicli completi.

| Metrica | Osservata | Esatta | Differenza |
|:---|---:|---:|---:|
| Media | 3,481580 | 3,506190 | -0,024610 |
| Varianza | 1,938964 | 1,924821 | +0,014142 |
| Deviazione standard | 1,392467 | 1,387379 | +0,005087 |
| Mediana | 3 | 3 | 0 |
| 90º percentile | 5 | 5 | 0 |
| 95º percentile | 6 | 6 | 0 |
| 99º percentile | 8 | 8 | 0 |

L’intervallo delle durate osservate è 1–18 estrazioni.

Sulla distribuzione cumulativa fino all’estrazione 18:

- differenza CDF assoluta massima: `0.0131885`;
- differenza CDF assoluta media: `0.00186675`;
- probabilità teorica oltre l’estrazione 18: `0.00001923`.

Centro, dispersione e quantili empirici selezionati sono vicini al riferimento
esatto. Si tratta di compatibilità descrittiva, non della prova che tutte le
osservazioni storiche siano campioni indipendenti del modello.

## Interpretazione

Il confronto sostiene l’utilità del modello esatto come descrizione della
durata aggregata dei cicli nell’archivio disponibile.

Non dimostra:

- indipendenza fra le ruote;
- assenza di ogni possibile irregolarità storica;
- vantaggio previsionale derivante dall’età del ciclo o dagli scarti passati;
- esistenza di una strategia di gioco redditizia.

## Riproduzione

Dalla radice del repository:

```bash
python3 analyze_historical_cycle_distribution.py
```

Gli output predefiniti sono:

```text
_work/historical-cycle-comparison.txt
_work/historical-cycle-comparison.json
```

I database primari predefiniti sono gli archivi annuali completi dal 2023 al
2026. Archivi discontinui opzionali possono essere forniti esplicitamente come
segmento secondario separato.

## Mappa dell’implementazione

- ricostruzione dei cicli: `strategies/coverage_cycle_history.py`;
- metriche esatte di assorbimento: `strategies/coverage_markov.py`;
- rapporto storico: `analyze_historical_cycle_distribution.py`;
- test automatici:
  `tests/test_analyze_historical_cycle_distribution.py` e
  `tests/test_coverage_cycle_history.py`.
