# Analisi statistica dei numeri gemelli

Questa analisi studia i numeri `11`, `22`, `33`, `44`, `55`, `66`, `77` e `88` come famiglia prefissata di eventi del Lotto.

L'obiettivo non è costruire una strategia di gioco, ma verificare una domanda falsificabile: **le informazioni sullo stato di copertura disponibili prima di un'estrazione modificano in modo riproducibile la frequenza del gemello corrispondente?**

## Null model

Per un gemello prefissato `dd` su una ruota prefissata, cinque numeri distinti vengono estratti da `1..90`. La probabilità che `dd` appartenga alla cinquina è quindi esattamente:

```text
P(dd) = 5 / 90 = 1 / 18 = 5,555...%
```

Il confronto principale è sempre contro questo null. La semplice presenza di un gemello in un concorso non costituisce un'anomalia.

## Costruzione ex ante

La cronologia di ogni ruota viene sincronizzata alla prima copertura completa osservata. Per ogni estrazione successiva, lo stato viene fotografato **prima** di leggere i cinque numeri target.

Per ogni cifra `d` fra `1` e `8` vengono registrate condizioni prefissate:

- `baseline`: tutte le estrazioni target sincronizzate;
- `missing`: `d` è ancora mancante nel ciclo naturale attivo;
- `top`: `d` appartiene alle cifre con massimo numero di occorrenze nel ciclo attivo;
- `last-missing`: `{d}` è l'insieme completo delle cifre ancora mancanti;
- `missing-age>=3`: `d` è mancante e il ciclo attivo contiene almeno tre estrazioni;
- `return-gap:1-4`, `5-9`, `10-19`, `20+`: classi prefissate del numero di estrazioni trascorse dall'ultima apparizione dello stesso gemello sulla stessa ruota.

Lo stato vuoto immediatamente successivo alla chiusura di un ciclo non genera condizioni `missing` o `top`: in quel punto tutte le cifre risultano banalmente mancanti e non forniscono informazione trasversale.

## Statistiche riportate

Per ogni coppia condizione/gemello il report include:

- numero di casi;
- hit osservati;
- hit attesi sotto `1/18`;
- frequenza osservata;
- lift assoluto rispetto al null;
- intervallo Wilson al 95%;
- p-value binomiale esatto two-sided;
- q-value Benjamini-Hochberg sulle condizioni esplorative.

Una riga viene etichettata `CANDIDATO` soltanto se soddisfa contemporaneamente:

1. almeno 200 casi;
2. `q < 0,05` dopo correzione Benjamini-Hochberg;
3. intervallo Wilson al 95% che esclude `1/18`.

Questa etichetta è deliberatamente più debole di "segnale" o "trigger".

## Limite inferenziale

Le ruote condividono il calendario delle estrazioni e le condizioni sullo stesso gemello si sovrappongono. Il pooling serve quindi come **screen esplorativo**, non come insieme di repliche indipendenti.

Un candidato storico deve essere congelato come ipotesi e verificato su dati cronologicamente successivi non utilizzati nella scoperta, oppure in forward test. Senza questa validazione il risultato resta descrittivo.

Se nessuna condizione supera il gate, il risultato corretto è esplicito:

```text
Nessun trigger sui numeri gemelli statisticamente supportato.
```

## CLI

```bash
./lotto.py twins
./lotto.py gemelli
```

Il database predefinito è `data/lotto-1871-2025.sqlite3`. È possibile limitare periodo e ruote:

```bash
./lotto.py twins --from-date 2001-01-01 --to-date 2025-12-31
./lotto.py twins --wheel Milano
```

Il comando scrive anche report riproducibili in `_work/twin-number-statistics.csv` e `_work/twin-number-statistics.json`.
