# Modello a stati finiti della copertura delle cifre decimali

[English](../finite-state-model.md) | **Italiano**

## Scopo

Questo documento definisce il modello matematico canonico della copertura delle
cifre decimali nelle estrazioni del Lotto italiano.

Il modello descrive una singola ruota e risponde a tre domande:

1. qual è lo stato esatto del ciclo di copertura;
2. con quali probabilità lo stato può cambiare alla prossima estrazione;
3. quanto tempo occorre, in distribuzione, per completare il ciclo.

Il modello non seleziona numeri e non attribuisce alle estrazioni passate un
effetto causale sulle probabilità future.

## 1. Universo decimale

L’insieme delle cifre è

\[
D=\{0,1,2,3,4,5,6,7,8,9\}.
\]

L’insieme dei numeri del Lotto è

\[
N=\{1,2,\ldots,90\}.
\]

Ogni numero viene rappresentato con esattamente due posizioni decimali:

```text
1  -> 01
6  -> 06
9  -> 09
40 -> 40
77 -> 77
90 -> 90
```

Lo zero iniziale appartiene quindi alla rappresentazione matematica.

Definiamo la funzione delle cifre

\[
g:N\rightarrow\mathcal{P}(D)
\]

che associa a ciascun numero l’insieme delle cifre presenti nella sua
rappresentazione a due posizioni.

Esempi:

\[
g(1)=\{0,1\},
\qquad
g(40)=\{0,4\},
\qquad
g(77)=\{7\},
\qquad
g(90)=\{0,9\}.
\]

Le ripetizioni interne a un numero non aumentano la copertura: `77` copre la
cifra `7` una sola volta.

## 2. Spazio campionario di una estrazione

Su una ruota vengono estratti cinque numeri distinti, senza ordine rilevante.

Lo spazio campionario è

\[
\Omega=
\left\{
\omega\subseteq N:\lvert\omega\rvert=5
\right\}.
\]

La sua cardinalità è

\[
\lvert\Omega\rvert
=
\binom{90}{5}
=
43.949.268.
\]

Nel modello ideale, ogni elemento di \(\Omega\) ha la stessa probabilità.

Per una estrazione \(\omega\), definiamo l’insieme delle cifre osservate:

\[
G(\omega)=\bigcup_{n\in\omega}g(n).
\]

## 3. Cicli naturali di copertura

Un ciclo naturale inizia quando tutte le dieci cifre sono ancora mancanti.

Dopo ogni estrazione, le cifre osservate vengono eliminate dall’insieme delle
cifre mancanti.

Il ciclo termina quando non manca più alcuna cifra.

Nella sequenza storica naturale, dopo il completamento inizia immediatamente un
nuovo ciclo con tutte le dieci cifre nuovamente mancanti.

La catena matematica assorbente e il processo storico con riavvio sono quindi
due oggetti collegati ma distinti:

- la catena assorbente si arresta nello stato vuoto;
- il processo naturale riavvia il ciclo dopo lo stato vuoto.

## 4. Spazio degli stati

Uno stato è un sottoinsieme di \(D\):

\[
\mathcal{S}=\mathcal{P}(D).
\]

La cardinalità dello spazio è

\[
\lvert\mathcal{S}\rvert=2^{10}=1.024.
\]

Uno stato \(S\) rappresenta le cifre ancora mancanti.

Esempi:

```text
{9}                    manca soltanto 9
{3,9}                  mancano 3 e 9
{0,1,2,3,4,5,6,7,8,9} stato iniziale completo
{}                     ciclo completato
```

Lo stato vuoto \(\varnothing\) è lo stato assorbente.

Gli stati non vuoti sono 1.023 e costituiscono le righe dell’atlante completo.

## 5. Aggiornamento deterministico

Dato uno stato corrente \(S\) e una estrazione \(\omega\), lo stato successivo è

\[
F(S,\omega)=S\setminus G(\omega).
\]

La regola implica:

\[
F(S,\omega)\subseteq S.
\]

Una transizione può quindi soltanto rimuovere cifre mancanti. Non può aggiungerne
all’interno dello stesso ciclo.

Per lo stato vuoto:

\[
F(\varnothing,\omega)=\varnothing.
\]

## 6. Kernel di transizione esatto

Il kernel di transizione è

\[
K(S,T)
=
P(F(S,\omega)=T),
\qquad S,T\in\mathcal{S}.
\]

Poiché ogni estrazione è equiprobabile:

\[
K(S,T)
=
\frac{
\left|
\left\{
\omega\in\Omega:
S\setminus G(\omega)=T
\right\}
\right|
}{
\binom{90}{5}
}.
\]

Una transizione è impossibile quando \(T\not\subseteq S\), quindi:

\[
K(S,T)=0
\quad\text{se}\quad
T\not\subseteq S.
\]

Per ogni stato:

\[
\sum_{T\in\mathcal{S}}K(S,T)=1.
\]

Per lo stato assorbente:

\[
K(\varnothing,\varnothing)=1.
\]

## 7. Costruzione mediante inclusione-esclusione

Per calcolare la probabilità che una estrazione copra tutte le cifre di un
insieme richiesto \(R\), si può usare il principio di inclusione-esclusione.

Per \(A\subseteq R\), sia \(c(A)\) il numero di numeri fra `01–90` che non
contengono nessuna cifra di \(A\).

Il numero di estrazioni che contengono tutte le cifre richieste è

\[
\sum_{A\subseteq R}
(-1)^{\lvert A\rvert}
\binom{c(A)}{5}.
\]

Dividendo per \(\binom{90}{5}\) si ottiene la probabilità esatta di
completamento in una estrazione.

Questa costruzione è usata anche come controllo indipendente per le probabilità
di completamento.

## 8. Costruzione indipendente con conteggi interi

Ogni numero viene rappresentato da una maschera di dieci bit.

Una programmazione dinamica intera conta, senza enumerare esplicitamente tutte
le 43.949.268 cinquine, quanti sottoinsiemi di cinque numeri producono ciascuna
maschera di unione.

La distribuzione finale comprende 968 maschere osservabili.

Per ogni maschera \(M\) e stato \(S\), lo stato successivo è determinato da

\[
T=S\setminus M.
\]

Aggregando i conteggi per \(T\) si ottiene un kernel costruito in modo
concettualmente indipendente dall’implementazione combinatoria principale.

## 9. Verifica esaustiva del kernel

Il verificatore confronta le due costruzioni su:

- tutti i 1.024 stati;
- tutte le 58.848 celle raggiungibili;
- tutte le 968 classi di maschere osservate.

Al checkpoint di luglio 2026:

```text
Spazio campionario:        43.949.268
Maschere osservate:        968
Stati verificati:          1.024
Celle verificate:          58.848
Errore assoluto massimo:   2,289401307420391 × 10⁻¹⁵
Tolleranza:                1 × 10⁻¹²
```

Il caso di massima discrepanza riguarda la chiusura dello stato

\[
\{0,1,2,3,4,5,6,7,8\}
\]

e resta molti ordini di grandezza sotto la tolleranza.

## 10. Interpretazione come catena assorbente

Sia

\[
\tau_S
=
\inf\{n\geq 0:S_n=\varnothing\}
\]

il tempo di assorbimento a partire dallo stato \(S\).

Per lo stato vuoto:

\[
\tau_{\varnothing}=0.
\]

Per ogni stato non vuoto, la probabilità di raggiungere lo stato vuoto tende a
uno all’aumentare dell’orizzonte.

Ogni stato non vuoto ha quindi tempo medio di assorbimento finito.

### Modello di assorbimento

Nella catena matematica, raggiunto lo stato vuoto, il processo vi rimane.

### Processo storico naturale

Nell’osservazione storica, la chiusura termina un ciclo e la successiva
estrazione viene valutata a partire dallo stato completo \(D\).

Questa distinzione evita di confondere:

- il tempo residuo di un ciclo aperto;
- la sequenza indefinita dei cicli naturali.

## 11. Probabilità di completamento entro un orizzonte

Definiamo

\[
q_h(S)=P(\tau_S\leq h).
\]

Le condizioni iniziali sono:

\[
q_0(\varnothing)=1,
\]

\[
q_0(S)=0
\quad\text{per}\quad
S\neq\varnothing.
\]

Per \(h\geq1\):

\[
q_h(S)
=
\sum_{T\subseteq S}
K(S,T)q_{h-1}(T).
\]

Per ogni stato, \(q_h(S)\) è non decrescente rispetto a \(h\) e converge a uno.

La probabilità puntuale del tempo di assorbimento è

\[
P(\tau_S=h)
=
q_h(S)-q_{h-1}(S).
\]

## 12. Numero medio di estrazioni residue

Sia

\[
E(S)=\mathbb{E}[\tau_S].
\]

Per lo stato vuoto:

\[
E(\varnothing)=0.
\]

Per uno stato non vuoto:

\[
E(S)
=
1+\sum_{T\subseteq S}K(S,T)E(T).
\]

Separando l’autotransizione:

\[
E(S)
=
\frac{
1+
\sum_{T\subsetneq S}K(S,T)E(T)
}{
1-K(S,S)
}.
\]

Poiché ogni successore proprio contiene meno cifre, i valori possono essere
calcolati ricorsivamente in ordine di cardinalità.

La varianza viene ricavata mediante la corrispondente equazione di Bellman per
il secondo momento.

## 13. Stati con una sola cifra mancante

Quando manca una sola cifra \(d\), il completamento a ogni estrazione è un
evento di Bernoulli con probabilità costante \(p_d\).

Il tempo di assorbimento è quindi geometrico:

\[
P(\tau_{\{d\}}=h)
=
(1-p_d)^{h-1}p_d.
\]

Per le cifre `0–8`:

\[
p_d
=
0,681643\ldots
\]

e

\[
E(\{d\})
=
\frac{1}{p_d}
\approx1,467.
\]

Per la cifra `9`:

\[
p_9
=
0,453005\ldots
\]

e

\[
E(\{9\})
=
\frac{1}{p_9}
\approx2,207.
\]

La differenza deriva dal fatto che `9` compare in un numero minore di elementi
dell’universo `01–90`.

Non dipende da quanto a lungo la cifra è rimasta assente.

## 14. Ordine parziale e monotonia

Lo spazio degli stati è ordinato per inclusione.

Se

\[
A\subseteq B,
\]

allora per ogni estrazione \(\omega\):

\[
F(A,\omega)\subseteq F(B,\omega).
\]

Questa proprietà produce un accoppiamento naturale: iniziando da uno stato con
meno cifre mancanti, il completamento non può avvenire più tardi rispetto allo
stesso percorso di estrazioni iniziato da uno stato che lo contiene.

Ne seguono:

\[
q_h(A)\geq q_h(B)
\]

per ogni \(h\), e

\[
E(A)\leq E(B).
\]

La varianza non è invece monotona per semplice conseguenza dell’inclusione.

## 15. Simmetrie decimali

La struttura dei numeri `01–90` non rende tutte le cifre intercambiabili.

Le simmetrie esatte sono:

1. negli stati che non contengono `9`, le cifre `0–8` sono intercambiabili;
2. negli stati che contengono `9`, la cifra `0` è distinta e le cifre `1–8`
   sono intercambiabili.

I 1.023 stati non vuoti si raggruppano quindi in 27 classi strutturali esatte.

Stati appartenenti alla stessa classe hanno:

- kernel equivalenti sotto una rietichettatura ammessa;
- identiche probabilità di assorbimento;
- stessa media e varianza residue;
- stessi quantili.

La sola cardinalità dello stato non conserva tutta l’informazione.

## 16. Stato iniziale completo

Per

\[
D=\{0,1,2,3,4,5,6,7,8,9\},
\]

le metriche esatte sono:

| Metrica | Valore |
|:---|---:|
| Completamento in 1 estrazione | 0,038226% |
| Completamento entro 2 estrazioni | 21,26% |
| Completamento entro 3 estrazioni | 60,47% |
| Completamento entro 5 estrazioni | 92,28% |
| Media | 3,506190 |
| Varianza | 1,924821 |
| Deviazione standard | 1,387379 |
| Mediana | 3 |
| 90º percentile | 5 |
| 95º percentile | 6 |
| 99º percentile | 8 |
| Probabilità ancora aperto dopo 8 estrazioni | 0,895955% |

La soglia A1 predefinita dell’`1%` viene quindi attraversata per la prima volta
a \(h=8\) nello stato completo.

## 17. Cosa stabilisce il modello

Il modello stabilisce esattamente:

- lo spazio degli stati;
- la legge delle transizioni;
- le probabilità di completamento;
- i tempi medi e la dispersione;
- i quantili del tempo residuo;
- le simmetrie decimali;
- le relazioni di monotonia;
- il riferimento teorico per le osservazioni storiche.

Conosciuto lo stato corrente, la legge futura non dipende da:

- età del ciclo;
- ordine delle apparizioni precedenti;
- numero di estrazioni consecutive di assenza;
- scarti storici accumulati.

## 18. Cosa non stabilisce il modello

Il modello non dimostra:

- indipendenza empirica fra le ruote;
- correttezza fisica o istituzionale del processo reale;
- assenza di ogni anomalia storica;
- possibilità di ottenere un vantaggio economico;
- aumento della probabilità di una cifra perché “in ritardo”;
- compensazione dopo un evento raro.

Le anomalie storiche sono etichette retrospettive, non modificatori del kernel.

## 19. Mappa dell’implementazione

| Oggetto | Implementazione |
|:---|:---|
| Kernel e metriche di assorbimento | `strategies/coverage_markov.py` |
| Completamento esatto | `strategies/coverage_completion.py` |
| Enumeratore indipendente | `strategies/coverage_transition_enumerator.py` |
| Verifica esaustiva | `verify_transition_kernel.py` |
| Monotonia | `strategies/coverage_monotonicity.py` |
| Simmetrie | `strategies/coverage_structure.py` |
| Atlante degli stati | `generate_state_atlas.py` |
| Analisi strutturale | `generate_structural_analysis.py` |
| Ricostruzione storica | `strategies/coverage_cycle_history.py` |

## 20. Stato attuale della verifica

La suite potata contiene 153 test automatici.

Gli artefatti teorici rigenerati al checkpoint di luglio 2026 coincidono byte per
byte con quelli tracciati sotto `generated/`.

Il confronto storico continuo 2023–2026 contiene 2.253 cicli completi e mostra:

- media osservata `3,481580`;
- media teorica `3,506190`;
- differenza CDF assoluta massima `0,0131885`;
- quantili osservati 50%, 90%, 95% e 99% identici a quelli teorici.

Questi risultati sostengono l’utilità descrittiva del modello senza trasformarlo
in una regola previsionale.
