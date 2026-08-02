# Archivio storico del Lotto, 1871–2025

[English](../historical-lotto-archive.md) | **Italiano**

## Scopo

Questo documento descrive l’archivio SQLite storico pubblicato dal repository
e ciò che abbiamo imparato durante la sua costruzione.

L’archivio è una risorsa per analisi storiche riproducibili. Non dimostra che
le estrazioni passate possano prevedere quelle future e non modifica la
probabilità di alcun numero valido del Lotto nel modello casuale ideale.

## Archivio pubblicato

Il database storico completo è:

```text
data/lotto-1871-2025.sqlite3
```

Contiene:

| Proprietà | Valore |
|:---|---:|
| Prima data di estrazione | 1871-01-07 |
| Ultima data di estrazione | 2025-12-30 |
| Estrazioni | 10.779 |
| Righe in `draw_numbers` | 518.410 |
| Presenze di ruota | 103.682 |
| Intervallo della numerazione globale | 1–10.779 |
| Minimo di ruote in una estrazione | 6 |
| Massimo di ruote in una estrazione | 11 |

Il `draw_number` globale è una sequenza cronologica definita dal repository.
Non coincide con il numero annuale originale del concorso.

Ogni archivio annuale originale resta disponibile separatamente e ogni
estrazione consolidata conserva data originale, URL sorgente, timestamp di
importazione, ruote, posizioni e valori.

## Blocchi consolidati sorgente

L’archivio complessivo deriva da cinque database verificati separatamente:

| Database | Periodo | Estrazioni |
|:---|:---|---:|
| `data/lotto-1871-1900.sqlite3` | 1871-01-07 – 1900-12-29 | 1.565 |
| `data/lotto-1901-1950.sqlite3` | 1901-01-05 – 1950-12-30 | 2.609 |
| `data/lotto-1951-2000.sqlite3` | 1951-01-06 – 2000-12-30 | 2.807 |
| `data/lotto-2001-2020.sqlite3` | 2001-01-03 – 2020-12-31 | 2.886 |
| `data/lotto-2021-2025.sqlite3` | 2021-01-02 – 2025-12-30 | 912 |

La somma dei loro conteggi coincide esattamente con le 10.779 estrazioni del
database complessivo.

## Costruzione e verifiche

I database consolidati sono stati costruiti cronologicamente dagli archivi
SQLite annuali.

Per ogni database sorgente e destinazione sono stati verificati:

1. `PRAGMA integrity_check`;
2. `PRAGMA foreign_key_check`;
3. unicità delle date nel periodo consolidato;
4. esattamente cinque posizioni per ogni ruota presente;
5. posizioni esattamente uguali a `1, 2, 3, 4, 5`;
6. cinque valori distinti su ciascuna ruota;
7. uguaglianza fra conteggi delle estrazioni sorgente e destinazione;
8. uguaglianza fra conteggi delle righe `draw_numbers`;
9. numerazione globale cronologica a partire da uno;
10. conservazione delle configurazioni storiche variabili delle ruote.

Ogni destinazione è stata prima costruita in un file SQLite temporaneo,
verificata e poi installata atomicamente.

## Configurazioni storiche delle ruote

Il numero di ruote operative non è costante nell’intero archivio.

| Numeri nell’estrazione | Ruote operative | Estrazioni |
|---:|---:|---:|
| 30 | 6 | 3 |
| 35 | 7 | 177 |
| 40 | 8 | 3.424 |
| 45 | 9 | 57 |
| 50 | 10 | 3.778 |
| 55 | 11 | 3.340 |

Ogni estrazione contiene cinque valori per ciascuna ruota effettivamente
presente.

La tabella di riferimento `wheels` può elencare una ruota anche quando quella
ruota non ha un risultato in una determinata estrazione storica. La completezza
storica deve quindi essere ricavata da `draw_numbers`, non dalla sola presenza
in `wheels`.

## Cronologia delle ruote

### Configurazione originaria a sette ruote

La prima estrazione archiviata, datata 1871-01-07, contiene:

- Firenze;
- Milano;
- Napoli;
- Palermo;
- Roma;
- Torino;
- Venezia.

Queste sette ruote costituiscono l’intera configurazione osservata fino al
1874-04-25.

### Bari

Bari compare per la prima volta il 1874-05-02, al numero globale 174.

Da quella data fino al 1939-07-01 la configurazione regolare contiene otto
ruote.

### Cagliari e Genova

Cagliari e Genova compaiono insieme per la prima volta il 1939-07-08, al numero
globale 3.575.

La configurazione regolare raggiunge così dieci ruote.

### Variabilità del periodo 1943–1946

Fra il 1943 e il 1946 la disponibilità delle ruote cambia da una estrazione
all’altra.

L’archivio contiene configurazioni con:

- 6 ruote;
- 7 ruote;
- 8 ruote;
- 9 ruote;
- 10 ruote.

I dati mostrano risultati di ruota assenti in questo periodo, ma l’archivio da
solo non dimostra la causa amministrativa o storica di ciascuna assenza. Il
repository registra quindi le configurazioni osservate senza inventare valori
mancanti né attribuire spiegazioni non supportate.

Dal 1946-11-30 la configurazione regolare a dieci ruote torna a essere presente
con continuità nei dati archiviati, fino all’introduzione della ruota Nazionale.

### Nazionale

La Nazionale compare per la prima volta il 2005-05-04.

Il blocco consolidato 2001–2020 contiene:

- 458 estrazioni senza Nazionale;
- 2.428 estrazioni con Nazionale.

L’archivio complessivo contiene 3.340 estrazioni con Nazionale fino al
2025-12-30.

## Presenze delle ruote

Il numero di estrazioni archiviate in cui compare ciascuna ruota è:

| Ruota | Prima presenza archiviata | Estrazioni presenti |
|:---|:---|---:|
| Bari | 1874-05-02 | 10.606 |
| Cagliari | 1939-07-08 | 7.131 |
| Firenze | 1871-01-07 | 10.772 |
| Genova | 1939-07-08 | 7.203 |
| Milano | 1871-01-07 | 10.777 |
| Napoli | 1871-01-07 | 10.774 |
| Palermo | 1871-01-07 | 10.752 |
| Roma | 1871-01-07 | 10.777 |
| Torino | 1871-01-07 | 10.775 |
| Venezia | 1871-01-07 | 10.775 |
| Nazionale | 2005-05-04 | 3.340 |

Le differenze di conteggio fra ruote attive da lungo tempo sono proprietà reali
dell’archivio importato. Non devono essere sostituite silenziosamente con
risultati sintetici.

## Evoluzione della frequenza delle estrazioni

Il numero annuale di estrazioni archiviate cambia sensibilmente nel tempo.

### Periodo prevalentemente settimanale

Dal 1871 al 1996 quasi ogni anno contiene 52 o 53 estrazioni.

Fra le eccezioni osservate:

- 1961: 51 estrazioni.

Lo schema 52/53 è compatibile con un calendario prevalentemente settimanale,
ma il database registra le date, non la norma giuridica o amministrativa che
stabiliva la frequenza.

### Transizione fra il 1997 e il 2005

I conteggi annuali aumentano:

| Anno | Estrazioni |
|---:|---:|
| 1997 | 95 |
| 1998 | 104 |
| 1999 | 104 |
| 2000 | 105 |
| 2001 | 105 |
| 2002 | 109 |
| 2003 | 105 |
| 2004 | 104 |
| 2005 | 133 |

Questi conteggi dimostrano un cambiamento nella frequenza osservata delle
estrazioni. Non documentano, da soli, le modifiche ufficiali che lo hanno
prodotto.

### Periodo a frequenza più elevata

Dal 2006 al 2019 i totali annuali sono normalmente 156 o 157 estrazioni.

I conteggi successivi sono:

| Anno | Estrazioni |
|---:|---:|
| 2020 | 139 |
| 2021 | 156 |
| 2022 | 157 |
| 2023 | 182 |
| 2024 | 209 |
| 2025 | 208 |

Le variazioni nette sono osservazioni storiche ricavate dall’archivio. Per
attribuire loro una causa servono fonti ufficiali esterne.

## Cosa abbiamo imparato sulla gestione dei dati storici

### I numeri annuali dei concorsi non possono essere uniti direttamente

I database annuali ricominciano la numerazione dei concorsi. Un archivio
pluriennale non può quindi usare il numero annuale originale come chiave
globalmente univoca.

I database consolidati assegnano una nuova sequenza cronologica, conservando
data e provenienza.

### Un numero fisso di ruote è storicamente errato

Pretendere undici ruote in ogni estrazione storica scarterebbe erroneamente
tutti i dati validi precedenti al 2005.

Pretendere dieci ruote scarterebbe anche:

- il periodo a sette ruote precedente a Bari;
- il periodo a otto ruote precedente a Cagliari e Genova;
- le configurazioni variabili osservate fra il 1943 e il 1946.

La validazione deve richiedere cinque valori per ogni ruota effettivamente
presente e considerare esplicitamente le transizioni storiche documentate.

### Tabelle di riferimento e osservazioni hanno ruoli differenti

La tabella `wheels` è un dizionario stabile dei possibili identificatori di
ruota.

La tabella `draw_numbers` registra quali ruote hanno effettivamente partecipato
a ciascuna estrazione. Le analisi storiche devono usare quest’ultima per
determinare la configurazione operativa.

### Una ruota assente non equivale a un valore zero

Una ruota assente non possiede un’osservazione per quella data. Non deve essere
rappresentata con zero, con una riga vuota di cinque numeri o copiando dati da
un’altra estrazione.

### Il consolidamento deve conservare la provenienza

L’archivio complessivo conserva:

- data originale dell’estrazione;
- URL sorgente originale;
- timestamp originale di importazione;
- righe esatte di ruota, posizione e valore;
- metadata sui database sorgente e sulla politica di numerazione globale.

## Uso analitico appropriato

L’archivio complessivo consente:

- studi di copertura delle cifre sul lungo periodo;
- studi delle durate dei cicli nei diversi regimi storici;
- confronti per ruota e periodo;
- analisi dei cambiamenti nella frequenza delle estrazioni;
- verifiche di robustezza su blocchi storici definiti indipendentemente;
- esclusione o trattamento separato delle configurazioni variabili.

Le analisi aggregate sulle ruote devono ricordare che tutte le ruote di una
estrazione condividono la stessa data e non costituiscono repliche temporali
indipendenti.

Le analisi estese su periodi lunghi devono inoltre considerare:

- variazione della disponibilità delle ruote;
- variazione della frequenza delle estrazioni;
- numerosità differenti fra le ruote;
- configurazioni temporaneamente parziali;
- date di introduzione di Bari, Cagliari, Genova e Nazionale.

## Cosa l’archivio non dimostra

Il database non stabilisce da solo:

- perché manchi uno specifico risultato storico di ruota;
- il fondamento giuridico di una variazione di calendario;
- che un’apparente regolarità abbia valore predittivo;
- l’indipendenza fra ruote osservate nella stessa data;
- l’invarianza delle procedure operative lungo 155 anni;
- l’esistenza di una strategia di gioco redditizia.

Queste domande richiedono fonti primarie esterne oppure un disegno statistico
dichiarato separatamente.

## Confine della riproducibilità

L’intero archivio annuale dal 1871 al 2025 e i sei database SQLite consolidati
sono tracciati nel repository.

Il database mutabile dell’anno corrente resta locale:

```text
data/lotto-current.sqlite3
```

I rapporti transitori, i download intermedi e i controlli di pubblicazione
appartengono a `_work/` e non fanno parte del dataset storico durevole.
