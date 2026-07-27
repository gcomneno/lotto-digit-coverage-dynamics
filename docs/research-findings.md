
Research findings
Copertura delle cifre 0–9

Ogni numero viene rappresentato con due cifre:

1 -> 01
9 -> 09
90 -> 90

Le cifre 0–8 e la cifra 9 non hanno la stessa distribuzione nei numeri
01–90. La cifra 9 compare in un insieme più piccolo di numeri e tende
quindi a essere assente più frequentemente.

Sulle 60 estrazioni 2026 inizialmente importate, considerando tutte le undici
ruote:

Finestra	Finestre	Copertura completa	Una mancante	Due mancanti	Tre o più
1	660	0,15%	2,42%	13,03%	84,39%
2	649	21,57%	44,22%	27,43%	6,78%
3	638	60,03%	32,76%	7,05%	0,16%

Dopo tre estrazioni, nel 92,79% delle finestre risultavano assenti al massimo
una cifra.

Questa è una proprietà descrittiva della copertura, non una prova che la cifra
residua abbia memoria o probabilità aumentata nella quarta estrazione.

Regola congelata

Regola analizzata:

prendere tre estrazioni consecutive della stessa ruota;
verificare che manchi esattamente una cifra tra 0–9;
controllare se la cifra compare nell'estrazione immediatamente successiva.
Piccolo campione 2026

Nel segmento bersaglio 100–119:

segnali: 71;
hit: 48;
osservato: 67,61%;
atteso ponderato: 58,83%;
delta: +8,78%.

Il risultato è stato trattato come anomalia da replicare, non come regola
predittiva acquisita.

Replica indipendente 2025

Sull'intero archivio 2025:

segnali: 775;
hit: 459;
osservato: 59,23%;
atteso ponderato: 59,82%;
delta: −0,59%;
intervallo Wilson 95%: 55,73%–62,63%.

Suddivisione cronologica:

Periodo	Segnali	Osservato	Atteso	Delta
Concorsi 4–104	379	59,10%	60,14%	−1,04%
Concorsi 105–208	396	59,34%	59,50%	−0,16%

La replica indipendente ha confutato l'ipotesi di un vantaggio predittivo
generalizzabile.

Permutazioni rimosse

Una prima implementazione applicava spostamenti circolari alle estrazioni
bersaglio.

Il procedimento poteva riallineare un segnale alle stesse estrazioni usate per
definirne la cifra mancante. In tali casi l'insuccesso era garantito per
costruzione, abbassando artificialmente la distribuzione nulla.

Gli script, i test e i rapporti basati su quella permutazione sono stati
rimossi.

Momentum residuo

Gli esperimenti momentum lavorano sui residui prequentiali:

- esito osservato della chiusura al concorso successivo, espresso come 0 o 1;
- meno la probabilità di chiusura prevista dal modello Markov per lo stato
  esatto delle cifre mancanti.

Un residuo positivo indica quindi una chiusura avvenuta oltre quanto previsto
dal modello. Le strategie verificano se una concentrazione recente di residui
positivi anticipi un'altra chiusura.

MOMENTUM-1 — sovraperformance accumulata

Regola congelata:

- finestra di dieci osservazioni precedenti sulla stessa ruota;
- ingresso quando il residuo standardizzato raggiunge `z >= 1,50`;
- durata di un solo concorso;
- disarmo immediato dopo il segnale;
- riarmo soltanto quando `z < 0,50`.

Il concorso bersaglio non partecipa mai al calcolo del segnale.

Risultati sui segmenti inizialmente analizzati:

Periodo	Segnali	Attese	Osservate	Tasso atteso	Tasso osservato	Delta
2025, concorsi 20–100	16	2,753	1	17,20%	6,25%	−10,95%
2025, concorsi 101–208	15	1,707	1	11,38%	6,67%	−4,71%
2026, concorsi 100–119	3	0,566	0	18,87%	0,00%	−18,87%
Totale iniziale	34	5,025	2	14,78%	5,88%	−8,90%

Nel campione storico 2024, non usato per definire la regola:

- segnali: 41;
- chiusure attese: 4,951;
- chiusure osservate: 7;
- tasso atteso: 12,08%;
- tasso osservato: 17,07%;
- delta: +5,00%;
- p nominale unilaterale: 0,1944;
- p nominale bilaterale: 0,2768.

Combinando descrittivamente tutti i segmenti:

- segnali: 75;
- chiusure attese: 9,976;
- chiusure osservate: 9;
- tasso atteso: circa 13,30%;
- tasso osservato: 12,00%;
- delta: circa −1,30%.

La direzione del risultato cambia tra gli anni e il vantaggio osservato nel
2024 non è statisticamente convincente. MOMENTUM-1 è quindi classificato come
risultato instabile e non replicato.

MOMENTUM-2 — calma e take-off

La seconda strategia tenta di riconoscere la nascita dell'onda anziché una
sovraperformance già matura.

Macchina a stati congelata:

1. attendere una finestra calma di cinque osservazioni con `|z5| <= 0,50`;
2. dopo la calma, attendere un'accelerazione sulle ultime due osservazioni con
   `z2 >= 1,00`;
3. emettere un segnale soltanto sul concorso immediatamente successivo;
4. disarmarsi dopo il colpo;
5. richiedere una nuova finestra completa di cinque osservazioni successive
   al colpo prima di potersi ritarare.

La finestra di calma e l'onda non possono coincidere. Anche in questo caso il
concorso bersaglio non partecipa al calcolo del segnale.

Risultati:

Periodo	Segnali	Attese	Osservate	Tasso atteso	Tasso osservato	Delta
2024, concorsi 20–209	155	24,630	23	15,89%	14,84%	−1,05%
2025, concorsi 20–100	54	6,897	4	12,77%	7,41%	−5,37%
2025, concorsi 101–208	83	12,838	11	15,47%	13,25%	−2,21%
2026, concorsi 100–119	12	1,162	1	9,68%	8,33%	−1,35%
Totale	304	45,527	39	14,98%	12,83%	−2,15%

Sul totale:

- Brier score: 0,1022;
- z medio della calma: 0,032;
- z medio del take-off: 1,352;
- p nominale unilaterale: 0,8956;
- p nominale bilaterale: 0,2863.

I p-value sono nominali perché segnali appartenenti a ruote diverse possono
condividere lo stesso concorso e non sono necessariamente indipendenti.

Tutti i segmenti hanno comunque prodotto meno chiusure di quelle previste dal
modello. MOMENTUM-2 non mostra quindi alcun vantaggio predittivo replicabile.

Il segno negativo non autorizza a trasformare retroattivamente il risultato
in una strategia di mean reversion. Una simile ipotesi dovrebbe essere
congelata separatamente e verificata soltanto su dati non ancora osservati.

Conclusione

La copertura quasi completa delle cifre dopo poche estrazioni è un fenomeno
combinatorio reale.

Non è emersa evidenza replicabile che:

- la cifra rimasta assente abbia una probabilità superiore al caso di comparire
  nell'estrazione successiva;
- una recente sovraperformance rispetto al modello Markov continui nel concorso
  successivo;
- una fase calma seguita da un'accelerazione positiva produca un take-off
  predittivamente sfruttabile.

Le sequenze possono assumere forme visivamente ondulate, ma i due esperimenti
momentum non hanno dimostrato memoria residua oltre la probabilità già spiegata
dallo stato esatto delle cifre mancanti.
