# Glossario

[English](../glossary.md) | **Italiano**

## Assorbimento

Primo ingresso nello stato vuoto, cioè il completamento del ciclo.

## Atlante degli stati

Tabella completa delle metriche teoriche per tutti i 1.023 stati non vuoti.

## Autotransizione

Transizione \(S\rightarrow S\), nella quale l’estrazione non contiene nessuna
delle cifre ancora mancanti.

## Catena assorbente

Catena di Markov con almeno uno stato che, una volta raggiunto, non viene più
abbandonato. Nel modello, tale stato è \(\varnothing\).

## Censura a destra

Situazione del ciclo ancora aperto alla fine dell’archivio. La sua durata
completa non è osservabile.

## Censura a sinistra

Situazione del primo ciclo osservato, il cui vero inizio può precedere la prima
estrazione disponibile.

## Cifra mancante

Cifra decimale non ancora comparsa nel ciclo naturale corrente.

## Classe strutturale

Insieme di stati equivalenti sotto le rietichettature delle cifre ammesse dalla
struttura di `01–90`.

## Completamento

Transizione verso lo stato vuoto.

## Copertura

Insieme delle cifre presenti nei cinque numeri di una estrazione.

## Ciclo naturale

Sequenza che inizia con tutte le dieci cifre mancanti e termina quando tutte
sono state osservate almeno una volta.

## Distribuzione cumulativa

Funzione

\[
q_h(S)=P(\tau_S\leq h)
\]

che misura la probabilità di completare entro \(h\) estrazioni.

## Distribuzione geometrica

Distribuzione del numero di prove necessarie al primo successo con probabilità
costante. Descrive esattamente il tempo residuo degli stati singoletti.

## Età del ciclo

Numero di estrazioni trascorse dall’inizio del ciclo naturale corrente.

Nel modello non modifica la legge futura quando lo stato esatto è già noto.

## Funzione di massa

Probabilità che il tempo di assorbimento sia esattamente \(h\):

\[
P(\tau_S=h)=q_h(S)-q_{h-1}(S).
\]

## Insieme delle parti

\[
\mathcal{P}(D)
\]

è l’insieme di tutti i sottoinsiemi di \(D\). Costituisce lo spazio dei 1.024
stati.

## Kernel di transizione

Funzione

\[
K(S,T)=P(S_{n+1}=T\mid S_n=S)
\]

che assegna la probabilità di passare dallo stato \(S\) allo stato \(T\).

## Maschera di cifre

Rappresentazione binaria a dieci bit dell’insieme delle cifre presenti in un
numero o in una estrazione.

## Monotonia per inclusione

Proprietà secondo la quale uno stato con meno cifre mancanti non può risultare
più difficile, nel senso dell’ordinamento stocastico, di uno stato che lo
contiene.

## Osservazione a un passo

Coppia formata da uno stato prima di una estrazione e dall’indicatore che il
ciclo si completi alla estrazione successiva.

## Processo naturale con riavvio

Sequenza storica nella quale, dopo ogni completamento, un nuovo ciclo riparte
con tutte le cifre mancanti.

## Quantile del tempo di assorbimento

Minimo orizzonte \(h\) per il quale la probabilità cumulativa raggiunge una
soglia prefissata.

## Residuo

Differenza tra una quantità osservata e il valore previsto dal modello.

## Stato

Insieme esatto delle cifre ancora mancanti.

## Stato completo

Lo stato iniziale

\[
\{0,1,2,3,4,5,6,7,8,9\}.
\]

## Stato singoletto

Stato che contiene una sola cifra mancante, per esempio `{9}`.

## Stato vuoto

\[
\varnothing
\]

Rappresenta il ciclo completato ed è assorbente nella catena matematica.

## Tempo di assorbimento

Numero di estrazioni necessario per raggiungere lo stato vuoto:

\[
\tau_S=\inf\{n\geq0:S_n=\varnothing\}.
\]

## Transizione non terminale

Transizione di progresso che rimuove almeno una cifra ma non completa il ciclo.

## Vantaggio previsionale

Miglioramento stabile e verificabile rispetto al modello di riferimento su dati
non usati per formulare o selezionare l’ipotesi.

Il progetto non ha trovato un vantaggio previsionale difendibile.
