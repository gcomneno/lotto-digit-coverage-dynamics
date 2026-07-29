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

La finestra storica corrente va dal 3 gennaio 2023 al 28 luglio 2026.

Pur contenendo 2.253 cicli completi, resta una finestra finita. Gli stati e le
transizioni rare possono avere campioni empirici piccoli.

L’archivio 2022 è deliberatamente escluso e non è stato ispezionato.

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
