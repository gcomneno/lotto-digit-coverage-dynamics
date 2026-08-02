# Limitazioni

[English](../limitations.md) | **Italiano**

## Assunzioni del modello

Il kernel esatto descrive l’estrazione su una ruota come una selezione non
ordinata di cinque numeri distinti fra `01–90`.

Tutte le probabilità teoriche sono condizionate a questo spazio campionario
idealizzato. Il progetto non verifica in modo indipendente gli apparati fisici,
le procedure operative o i processi istituzionali che generano i dati.

## Dipendenza storica

Le undici ruote condividono il calendario delle estrazioni. Le osservazioni sono
aggregate per le sintesi descrittive, ma il progetto non assume che siano
repliche sperimentali indipendenti.

Le differenze aggregate rispetto alla teoria non vengono quindi trasformate
direttamente in p-value classici o in dichiarazioni di accettazione formale del
modello.

## Ampiezza dell’archivio

Il repository pubblica database annuali dal 1871 al 2025 e un consolidato
storico complessivo contenente 10.779 estrazioni dal 1871-01-07 al 2025-12-30.

La disponibilità del dataset più ampio non trasforma ogni rapporto esistente in
un’analisi di 155 anni. Il checkpoint originario dello stato esatto dal
3 gennaio 2023 al 28 luglio 2026, per esempio, contiene ancora 2.253 cicli
completi e resta il campione dichiarato per i risultati che lo citano.

La copertura storica estesa introduce ulteriori limitazioni:

- la disponibilità delle ruote cambia nel tempo;
- la frequenza delle estrazioni varia sensibilmente;
- le numerosità differiscono fra le ruote;
- alcune estrazioni del 1943–1946 contengono soltanto una parte delle ruote
  regolari;
- non si può assumere l’invarianza delle procedure operative lungo l’intero
  periodo.

Stati e transizioni rare possono comunque avere campioni piccoli all’interno
di una specifica ruota, regime o confronto dichiarato in anticipo.

Vedere il
[rapporto sull’archivio storico del Lotto](historical-lotto-archive.md).

## Censura

Il primo ciclo osservato di ogni ruota è censurato a sinistra e viene escluso.
L’ultimo ciclo aperto è censurato a destra e viene escluso dalle sintesi delle
durate complete.

Queste regole riducono le distorsioni ma scartano una parte delle osservazioni.

## Etichette di anomalia

Gli eventi A1–A4 sono etichette descrittive retrospettive.

Le soglie non costituiscono una procedura completa per confronti multipli e A4
usa un limite superiore conservativo di Bonferroni condizionato a una precedente
anomalia primaria.

Un’anomalia non implica:

- manipolazione;
- dipendenza nelle estrazioni future;
- comportamento compensativo;
- una regola di selezione redditizia.

## Rappresentazione numerica

I conteggi combinatori sottostanti sono interi, ma le probabilità riportate e
le metriche di Bellman usano l’aritmetica in virgola mobile.

La verifica indipendente mostra attualmente una differenza massima assoluta di
circa `2,29 × 10⁻¹⁵`, molto inferiore alla tolleranza configurata di
`1 × 10⁻¹²`.

## Output dello stato corrente

Gli stati correnti delle ruote cambiano ogni volta che l’archivio annuale viene
aggiornato. Sono fotografie operative, non conclusioni scientifiche stabili.

La documentazione specifica quindi la data di arresto dell’archivio e invita a
rigenerare il rapporto corrente.

## Disponibilità dei dati esterni

Gli aggiornamenti annuali dipendono dalla struttura e dalla disponibilità della
pagina archivio a monte. L’importatore verifica la completezza e scrive i
database in modo atomico, ma un cambiamento del formato esterno può richiedere
manutenzione.

## Nessuna affermazione previsionale

Il progetto non afferma che:

- le cifre in ritardo diventino più probabili;
- l’età del ciclo modifichi le probabilità dello stato esatto;
- i residui storici creino un vantaggio sfruttabile;
- le transizioni rare passate prevedano transizioni rare future.

I precedenti esperimenti previsionali sono stati chiusi dopo non aver prodotto
un risultato stabile oltre il modello dello stato esatto.
