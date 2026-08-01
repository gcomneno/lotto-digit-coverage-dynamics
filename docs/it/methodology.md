# Metodologia

[English](../methodology.md) | **Italiano**

## Obiettivo della ricerca

Il progetto domanda se la copertura delle cifre decimali su una ruota del Lotto
italiano possa essere rappresentata esattamente come un processo stocastico
assorbente a stati finiti e quanto le proprietà derivate siano compatibili con
le osservazioni storiche.

L’obiettivo è spiegare e verificare, non selezionare numeri.

## Rappresentazione decimale

Ogni numero è rappresentato con due posizioni decimali:

```text
1  -> 01 -> {0,1}
9  -> 09 -> {0,9}
40 -> 40 -> {0,4}
77 -> 77 -> {7}
90 -> 90 -> {0,9}
```

Lo zero iniziale contribuisce quindi alla copertura delle cifre.

## Definizione dello stato

Sia \(D=\{0,1,\ldots,9\}\). Uno stato \(S\subseteq D\) è l’insieme delle cifre
ancora mancanti nel ciclo corrente.

Esistono \(2^{10}=1.024\) stati. L’insieme vuoto è assorbente nella catena
matematica. Il processo storico naturale riparte da \(D\) dopo il completamento.

## Costruzione esatta delle transizioni

Un’estrazione su una ruota è un sottoinsieme non ordinato di cinque elementi
scelti fra `01–90`, quindi esistono

\[
\binom{90}{5}=43.949.268
\]

estrazioni possibili.

Ogni numero viene trasformato in una maschera di dieci bit. Una programmazione
dinamica intera conta quanti sottoinsiemi di cinque numeri producono ciascuna
maschera di unione. La distribuzione esatta delle maschere induce il kernel

\[
K(S,T)=P(S\setminus G(\omega)=T).
\]

Una transizione può soltanto rimuovere cifre mancanti, quindi \(T\subseteq S\).

## Verifica indipendente

Il kernel di riferimento viene confrontato con una costruzione intera
concettualmente indipendente su:

- tutti i 1.024 stati;
- tutte le celle di transizione raggiungibili;
- l’intero spazio campionario delle estrazioni di cinque numeri.

Al checkpoint di luglio 2026:

- sono state osservate 968 maschere di unione delle cifre;
- sono state confrontate 58.848 celle di transizione;
- la massima discrepanza assoluta è stata
  `2.289401307420391 × 10⁻¹⁵`.

La tolleranza del verificatore è `1 × 10⁻¹²`.

## Quantità derivate

Per ogni stato non vuoto, l’implementazione calcola:

- probabilità di completamento in una estrazione;
- funzione di distribuzione cumulativa su orizzonti arbitrari;
- funzione di massa;
- numero medio di estrazioni residue;
- varianza e deviazione standard;
- quantili selezionati del tempo di assorbimento;
- classifica stabile della difficoltà degli stati.

Le ricorrenze di Bellman sfruttano il fatto che ogni successore proprio
contiene meno cifre mancanti.

## Analisi strutturale

Il progetto verifica:

- monotonia dell’aggiornamento deterministico dello stato;
- ordinamento stocastico rispetto all’inclusione insiemistica;
- simmetrie decimali esatte;
- perdita di informazione quando uno stato viene ridotto alla sola cardinalità.

I 1.023 stati non vuoti collassano in 27 classi strutturali esatte:

- senza la cifra `9`, le cifre `0–8` sono intercambiabili;
- quando manca anche `9`, la cifra `0` diventa distinta mentre `1–8` restano
  intercambiabili.

## Protocollo di osservazione storica

Gli archivi SQLite annuali vengono uniti per data separatamente per ogni ruota.

Al checkpoint pubblicato, l’archivio primario è continuo dal 2023 al
concorso 120 del 2026.

Per i cicli naturali:

1. il ciclo iniziale censurato a sinistra di ogni ruota viene escluso;
2. i cicli completati vengono conservati;
3. il ciclo terminale incompleto viene registrato ma escluso dalle sintesi
   delle durate complete;
4. i confini fra anni continui non azzerano il ciclo.

Le ruote condividono il calendario delle estrazioni. Le osservazioni aggregate
non vengono quindi trattate come repliche indipendenti.

## Confronti storici basati sullo stato esatto

Le analisi storiche comprendono:

- distribuzione aggregata dei tempi di assorbimento;
- calibrazione a un passo per classe strutturale esatta;
- completamenti attesi e osservati;
- durata residua attesa e osservata;
- etichette retrospettive A1–A4;
- maturità dello stato esatto corrente.

La proprietà di Markov viene interpretata in modo condizionato: noto l’insieme
esatto delle cifre mancanti, l’età del ciclo e il percorso precedente non
modificano la legge teorica delle transizioni.

## Confine della riproducibilità

Gli artefatti matematici deterministici sono tracciati sotto `generated/`.
I rapporti transitori e i controlli di pubblicazione appartengono a `_work/`.

Gli archivi esterni all’ambito pubblicato 2023–2026 sono esclusi dalle
analisi tracciate. Devono entrare in un’analisi pubblicata soltanto per una
domanda dichiarata prima di valutare i dati pertinenti.
