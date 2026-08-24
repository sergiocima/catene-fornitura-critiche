# Istruzioni per gli assistenti AI

Valgono per qualunque assistente lavori su questo progetto — Claude, Codex, Cursor, altri — su
qualunque macchina. Sono nel repo apposta: chi clona il progetto le eredita, senza configurare niente.

## La memoria di lavoro sta in `stato.md`

`stato.md`, nella radice, è la memoria di lavoro del progetto: **i ragionamenti, non i risultati**.
Serve perché chi ci lavora sopra cambia — persone diverse, macchine diverse, sessioni diverse — e
altrimenti ogni volta si riparte da zero e si rifanno gli stessi errori.

**All'inizio di una sessione**: leggilo prima di toccare qualsiasi cosa. Se contraddice quello che
trovi nel repo, vince il repo: segnalalo e correggi il file, non ignorarlo.

**Prima di chiudere una sessione** in cui hai preso decisioni, scartato una strada o lasciato qualcosa
in sospeso: aggiornalo e committalo insieme al lavoro. Non aspettare che te lo chiedano.

### Cosa ci va

- **Decisioni**, con la data in un marcatore riconoscibile `[✓ AAAA-MM-GG]`: cosa è stato deciso e in
  base a quale ragionamento o vincolo. Se una decisione ne annulla una precedente, dillo invece di
  riscrivere la vecchia: la sequenza dei ripensamenti è informazione.
- **Strade scartate, col perché.** È la parte che vale di più e quella che si perde per prima: una
  strada scartata senza motivazione viene ritentata dopo due mesi. Scrivi sia cosa è stato provato sia
  cosa è andato storto. Distingui lo scarto **definitivo** da quello **condizionato**: "non funziona" e
  "non funziona finché non abbiamo X" sono cose diverse, e il secondo è un punto aperto in attesa di X.
- **Punti aperti**: cosa resta da fare, cosa aspetta la decisione di qualcuno — col nome, se è una persona.
- **Trappole pagate sul campo**: un comportamento controintuitivo scoperto sbattendoci contro, che
  costerebbe di nuovo mezz'ora.

### Cosa NON ci va

Riassunti della conversazione, elenchi di comandi eseguiti, cronache passo passo, e tutto ciò che è già
evidente dal codice, dalla struttura delle cartelle o dal `git log`. Un `stato.md` che racconta la
sessione diventa illeggibile in tre sessioni e smette di essere aperto: meglio poche righe dense.

### Come si aggiorna

**In linea**, dentro le sezioni che ci sono già: se un punto aperto si è chiuso, chiudilo lì dov'è.
Non accodare un blocco datato in fondo a ogni sessione. Quando una decisione ne supera un'altra,
comprimi la vecchia in una riga invece di lasciarla per intero: il file deve restare un quadro, non
diventare una cronologia.

Non duplicare: quello che spiega **come si usa** il progetto sta nel README, le pendenze operative dove
il progetto le tiene già. Se un'informazione servirebbe in due posti, sta nel più specifico e l'altro ci
rimanda in una riga.

## Il file viaggia col progetto

`stato.md` è versionato e va **committato e pushato** come il resto: è il canale con cui le sessioni su
macchine diverse si parlano. Prima di leggerlo fai `git pull`, altrimenti leggi una versione vecchia e
riparti da decisioni già superate.

## Le convenzioni operative di questo repo

Stanno in [CLAUDE.md](CLAUDE.md), com`e fatta la pagina nel [README](README.md).
Questo file riguarda solo la memoria.
