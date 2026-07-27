
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

Conclusione

La copertura quasi completa delle cifre dopo poche estrazioni è un fenomeno
combinatorio reale.

Non è emersa evidenza replicabile che la cifra rimasta assente abbia una
probabilità superiore al caso di comparire nell'estrazione successiva.
