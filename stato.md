# Catene di fornitura critiche — stato del progetto

Caso di studio sulle basi lubrificanti di Gruppo III dopo la chiusura dello stretto di Hormuz,
usato per spiegare il meccanismo degli input critici non sostituibili.

---

## Decisioni prese

**[✓ 2026-08-16] Architettura: pagina unica narrativa, più una pagina di metodo, più i dati
scaricabili.** Sergio ha chiesto una pagina che spieghi cos'è una catena di fornitura con
movimenti su un mappamondo, poi le catene critiche, poi i dati: la struttura in quattro atti
segue quella richiesta. La pagina di metodo esiste separata perché l'apparato sullo statuto delle
fonti, che è il cuore redazionale, renderebbe illeggibile la narrazione se stesse in linea.

**[✓ 2026-08-16] Grafici statici generati in build, nessuna libreria lato browser.** SVG disegnati
da uno script Python. Prima visita a 172 KB compresa la geometria del mappamondo. L'interattività
scartata di proposito: un grafico interattivo di solito è il sintomo di non aver deciso cosa si
vuole dire, e qui lo sappiamo.

**[✓ 2026-08-16] Scatto datato, non dashboard.** I dati si scaricano in build, si congelano in
`dati/AAAA-MM-GG/` con un manifest che registra URL, ora e checksum, e la pagina legge quelli.
Una dashboard che si aggiorna da sola sotto un testo scritto in una certa data mente due volte,
quando smette di aggiornarsi e quando ci riesce.

**[✓ 2026-08-16] Taglio: divulgativo sul meccanismo, non sul caso.** È il cambiamento più
importante rispetto al briefing iniziale, ed è imposto dai dati, non da una preferenza. Vedi la
sezione sul ribaltamento della tesi.

**[✓ 2026-08-16] Pubblicazione su GitHub Pages, non sulla VPS.** Repo personale
`sergiocima/catene-fornitura-critiche`, online su
<https://sergiocima.github.io/catene-fornitura-critiche/>. Sergio ha scelto di tenerlo per conto
suo e non sotto una testata Zadig, quindi Pages invece di Cloudflare. Tre ragioni: l'archivio
datato che il progetto produce è già di forma git, e committarlo dà gratis storia e diff; la VPS
è la macchina che da Starlink non si raggiunge senza VPN; e qui non serve un server.

**[✓ 2026-08-16] L'aggiornamento mensile apre una pull request, non pubblica.** È la decisione
che protegge la regola editoriale: nella pagina i numeri sono scritti a mano dentro le frasi che
li commentano, quindi un aggiornamento automatico del testo lo farebbe mentire. La pull request
porta il diff dei CSV e l'elenco delle cifre da ricontrollare, prodotto da
`scripts/cifre_chiave.py`.

**[✓ 2026-08-16] Pubblicata come bozza dichiarata.** Fascia appiccicata in cima a entrambe le
pagine, titolo che lo dice nella linguetta, `noindex` sui motori di ricerca, sezione
`metodo.html#bozza` che elenca cosa manca, e un avviso in linea sulla sezione delle catene
critiche, che è la meno solida. La fascia è appiccicata e non fissa perché il testo va a capo a
larghezze diverse e l'altezza non è nota in anticipo: fissa richiedeva un padding sul body pari a
un'altezza che non si può sapere.

**[✓ 2026-08-16] I dati statistici si prendono via SDMX**, non dai bulk file di Eurostat. Provider
`comext`, dataflow `DS-045409`. La pipeline definitiva (`scripts/aggiorna_dati.py`) chiama
l'endpoint SDMX direttamente con la sola libreria standard, senza `opensdmx`, per non dipendere da
una CLI installata a mano: `opensdmx` resta utilissimo per esplorare e trovare i codici.
Le trappole sono nel `README.md`.

---

## Cosa dice il test di fattibilità sui cinque anelli

L'impianto è una catena di cinque anelli verificabili separatamente: transiti nello stretto, export
di basi dal Golfo, prezzi delle basi, annunci dei produttori, prezzo finale in Italia.

**Anello 1, transiti: solido, gratuito, spettacolare.** IMF PortWatch espone i transiti giornalieri
per 28 chokepoint via ArcGIS REST, senza chiave. Hormuz è `chokepoint6`. Serie giornaliera continua
dal 2019-01-01, quindi con sette anni di linea di base. Media giornaliera delle navi in transito:
69,9 a febbraio 2026, **2,8 a marzo**, 5,0 ad aprile, 3,2 a maggio, 10,7 a giugno (riapertura
parziale), 8,4 a luglio, 4,0 nei primi nove giorni di agosto. La cronologia del briefing è
confermata dai dati. Endpoint e campi in `dati/2026-08-16/portwatch_hormuz_giornaliero_*.json`.

**Anello 2, export di basi dal Golfo: misurabile solo in forma degradata.** Il Gruppo III è definito
per specifica (indice di viscosità ≥120, saturi ≥90%, zolfo ≤0,03%), non per capitolo doganale. La
sorpresa è che una definizione doganale esiste eccome, alla decima cifra TARIC, e ricalca la
specifica API alla lettera: **2710 19 81 40** e **2710 19 99 60** sono letteralmente basi con
indice di viscosità ≥120, ≥90% di saturi e ≤0,03% di zolfo, e **2710 19 99 20** è la base GTL
sintetizzata da idrocarburi gassosi, cioè il prodotto di Ras Laffan. Ma Comext **dissemina solo fino
a CN8**: il dataflow si autodescrive come "EU trade since 1988 by HS2-4-6 and CN8". Quindi si
arriva a 2710.19.81 (oli motore, compressori, turbine) e 2710.19.99 (altri oli lubrificanti), che
sono secchi più larghi. BACI, essendo HS6, è inutilizzabile qui: 2710.19 contiene anche gasolio e
oli combustibili.

Vale la pena scriverlo in pagina così com'è: **l'Unione europea sa definire il Gruppo III e lo fa
nel proprio tariffario, ma non pubblica il commercio a quella granularità.** È un fatto sullo
statuto dei dati, non un limite da nascondere in nota.

**Anello 3, prezzi delle basi: parzialmente riempibile, e il risultato contraddice la tesi.**
Comext dà valore e quantità per lo stesso codice, quindi il rapporto è un valore unitario implicito,
gratuito, mensile, per paese dichiarante e paese partner. Non è la quotazione Argus, ma è un proxy
di prezzo pubblico e verificabile. Sull'import italiano il valore unitario **non mostra alcuna
rottura dopo la chiusura**: 2710.19.81 sta a 3,24 EUR/kg a gennaio 2026, 3,09 a febbraio, 3,11 a
marzo, 2,95 ad aprile, 3,30 a maggio, tutti dentro la banda 2,46-3,50 del 2022-2025. Il 2710.19.99
sale a 1,52 a maggio 2026, ma nella stessa serie agosto 2025 faceva 1,94 e agosto 2022 faceva 1,82,
ed era sceso a 0,86 a gennaio 2026: è rumore ordinario, non un salto di regime.

**Anello 5, prezzo al dettaglio in Italia: fattibile, a pagamento, e ricostruibile all'indietro.**
Non esiste una serie pubblica isolabile (l'indice Istat annega i lubrificanti dentro "carburanti e
lubrificanti", dominato dal carburante). La via praticabile è un paniere fisso di 20-30 SKU seguito
su Amazon.it tramite Keepa: copre il marketplace italiano, l'API costa da 49 euro al mese, e una
richiesta prodotto vale un token e restituisce la serie storica completa. Un mese di abbonamento
basta a tirare giù tutta la storia del paniere. camelcamelcamel ha il dominio italiano ma risponde
403 alle richieste automatiche.

---

## Il ribaltamento della tesi, e perché il pezzo ora è un altro

**[✓ 2026-08-16]** Il briefing partiva dall'idea che il prezzo dell'olio motore si fosse scollato
verso l'alto da quello del greggio. Costruendo il confronto con un metodo unico su una fonte unica,
i valori unitari doganali di Comext, viene fuori il contrario, ed è più interessante.

**Corretto il 16/8 dopo un'obiezione di Sergio, che aveva ragione.** La prima versione misurava i
lubrificanti sul solo codice 2710.19.81, che sono gli oli motore già confezionati e valgono
seimila tonnellate al mese, ignorando il 2710.19.99 che ne vale quarantottomila ed è dove entrano
le basi. Su un ottavo del mercato il mercato sembrava fermo (più 1,7 per cento). Sommando tutti e
otto i codici 2710.19.71-99 ponderati per le quantità, il quadro è un altro.

Confrontando la media di dicembre-febbraio con quella di marzo-maggio, cioè la stessa finestra
usata per gli stretti: **greggio più 66 per cento, lubrificanti più 20 per cento, elio fermo.**
I lubrificanti hanno recuperato circa **un terzo** del movimento del greggio. Il picco di maggio,
1,756 euro al chilo, è il più alto degli ultimi due anni fra i mesi a volume pieno.

La precisazione sul volume è essenziale e va tenuta: agosto 2025 segnava 2,085 euro al chilo, di
più, ma su 26.985 tonnellate contro le 58.968 di maggio 2026. In un mese sottile una partita
anomala sposta la media: quel picco è composizione, non prezzo. I mesi del 2026 stanno tutti sopra
le 45.000 tonnellate e la salita è progressiva su quattro mesi consecutivi.

**Non misurare mai da punto a punto.** Da gennaio a maggio i lubrificanti farebbero più 56 per
cento, ma gennaio 2026 è il minimo degli ultimi due anni: da un minimo si sale sempre. Il confronto
fra finestre è l'unico onesto.

Quindi la conclusione non è né lo scollamento verso l'alto della stampa di settore, né
l'immobilità: è un **adeguamento parziale e ritardato**, che è poi esattamente ciò che il lucchetto
della certificazione produce. Chi non può cambiare fornitore paga il prezzo del contratto finché
dura, e lo rinnova a condizioni peggiori. Lo shock non sparisce, slitta. Ragione in più per
rileggere la serie a settembre.

Aggiunta decisiva del 16/8, sull'elio: **la quota del Qatar sull'elio extra-UE scende dal 66 per
cento di gennaio al 32 di maggio, e l'Algeria diventa primo fornitore a volumi quasi invariati.**
L'origine si è sostituita in due mesi senza che il prezzo di frontiera si muovesse. È il
controesempio che rende il pezzo onesto: un input critico non è un input che viene da un posto
solo, è un input che non si riesce a ricomprare altrove abbastanza in fretta. L'elio, alla dogana
europea, ci è riuscito.

Il pezzo pubblicabile è quindi sul **meccanismo**: cosa rende una filiera fragile, perché il collo
di bottiglia è il certificato e non la molecola, e cosa si riesce e non si riesce a misurare. Il
caso Hormuz è l'esempio, non la tesi.

## Il problema di merito, non tecnico

La tesi del briefing è che il prezzo dei lubrificanti si è scollato dal greggio e non è più tornato
indietro. Gli anelli misurabili gratuitamente sono l'1 e, in forma degradata, il 2 e il 3. **Lo
scollamento sta nell'anello 3 e nell'anello 5, cioè esattamente dove i dati pubblici mancano o
dicono altro.**

Due riscontri che vanno affrontati e non aggirati:

**Il valore unitario all'import non si muove** fino a maggio 2026 (ultimo mese disponibile). Le
attenuanti sono reali e vanno dichiarate tutte: è un aggregato CN8 eterogeneo, quindi un
cambiamento di mix può mascherare un movimento di prezzo; è un valore unitario doganale, non un
indice di prezzo; è il prezzo alla frontiera, non al dettaglio; e non copre il secondo blocco di
luglio. Ma resta che la sola serie pubblica vicina a un prezzo non mostra quello che la tesi
richiede.

**L'Italia non importa lubrificanti dal Golfo.** Nel 2025-2026 gli arrivi diretti da Qatar e Bahrain
sui due codici sono nulli, quelli da Emirati e Arabia Saudita sono decine o poche centinaia di
tonnellate al mese, mentre gli Stati Uniti sono il primo fornitore extra-UE e nel 2026 sono
**cresciuti** (1.972 t ad aprile, 1.575 a giugno, contro una media 2025 sotto le 400). Se una
trasmissione c'è, non passa dal commercio diretto ma dal mercato europeo e mondiale delle basi.

C'è anche una ragione strutturale che rafforza il pezzo invece di indebolirlo: il grosso della
capacità mondiale di Gruppo III è coreano (S-Oil a Onsan, SK, GS Caltex) e non transita da Hormuz.
Nel Golfo ci sono il GTL di Ras Laffan e gli impianti di Bahrain e Ruwais. Quindi il collo di
bottiglia, se esiste, **non è il volume ma l'omologazione**: un formulatore non può sostituire uno
slate qatarino con uno coreano senza rifare la qualifica presso il costruttore, e quella richiede
mesi. È esattamente la specificità dell'input di Barrot e Sauvagnat, ed è un argomento più forte e
più difendibile del "manca il prodotto". Da verificare con una fonte sulle quote di capacità.

---

## Strade scartate

**BACI del CEPII per l'anello 2.** Scartata in via definitiva: è HS6, e 2710.19 a sei cifre contiene
gasolio, oli combustibili e lubrificanti nello stesso secchio. Nessuna elaborazione la salva.

**Bulk download di Comext.** Scartata a favore di SDMX. Gli indirizzi
`api/dissemination/files?file=comext/COMEXT_DATA/PRODUCTS/fullAAAAMM.7z` restituiscono 404 (provati
202603, 202604, 202605), e gli endpoint di listing del catalogo pure. Non è una fonte morta, è il
canale sbagliato: via SDMX gli stessi dati escono senza attrito.

**API di disseminazione standard di Eurostat per Comext.** Scartata: `DS-045409` non è servito da
`api/dissemination/statistics/1.0/data/`, che risponde "is not available for dissemination". Comext
ha il suo endpoint SDMX separato, ed è quello che usa il provider `comext` di `opensdmx`.

**camelcamelcamel per l'anello 5.** Scartata in via condizionata: il dominio italiano esiste ma
risponde 403 dietro Cloudflare alle richieste automatiche. Riapribile solo se si accetta di
raccogliere a mano o di forzare, e non ne vale la pena avendo Keepa.

**Il valore unitario dell'elio aggregato su tutte le origini.** Costruito, pubblicato in bozza,
e buttato via lo stesso giorno. Mostrava un calo dell'ottanta per cento che non è mai avvenuto:
i Paesi Bassi dichiarano sotto il codice dell'elio quasi dodicimila tonnellate di origine cinese
a 3,75 euro al chilo contro i 74-98 dell'elio vero, e quella sola riga schiacciava la media.
Ce ne siamo accorti solo perché il numero era implausibile rispetto alla produzione mondiale.
Vale come lezione generale: su una serie doganale il controllo di plausibilità fisica va fatto
prima di guardare la forma della curva.

**Il filtro statistico automatico sulle celle fuori scala.** Scritto, provato e scartato in
mezz'ora. Calcolava la mediana dei valori unitari di tutte le celle ed escludeva quelle oltre un
fattore quattro. Escludeva anche Qatar e Stati Uniti, cioè l'elio vero, perché le migliaia di
celle minuscole da pochi chili hanno valori unitari selvaggi e spostavano la mediana. Sostituito
da una banda dichiarata a mano nel dizionario `BANDE` di `aggiorna_dati.py`. È peggiore in teoria
e migliore in pratica, e soprattutto è visibile e contestabile: un filtro che rimodella i dati in
silenzio è esattamente il difetto contro cui questo progetto mette in guardia.

**Misurare i lubrificanti su un solo codice doganale.** Scartato dopo l'obiezione di Sergio del
16/8. Non è un errore di calcolo ma di scelta della grandezza, ed è il più insidioso dei due:
il numero era pulito, riproducibile e riferito a un codice reale. Semplicemente misurava un
ottavo del mercato. Regola generale che ne esce: prima di leggere la forma di una curva doganale,
controllare quanto pesa il codice rispetto agli altri della stessa famiglia. La stessa trappola
vale per qualunque merce sparsa su più voci.

**Il test sul volume applicato a tutta la serie** per individuare i mesi incompleti. Scartato
subito: avrebbe cancellato in silenzio i crolli veri, che sono la notizia che cerchiamo. Il test
sul volume vale solo sugli ultimi tre mesi, dove la causa nota è il ritardo di pubblicazione.
Sulla copertura invece il test vale su tutta la serie, perché un buco di copertura è sempre un
difetto del dato e mai un fatto economico.

---

## Sul Kiel Policy Brief 206

Il brief esiste, ma **non parla di lubrificanti.** Titolo reale: *The Cost of Closing the Strait of
Hormuz: Energy Bottlenecks and Global Food Security*, Hinz, Mahlkow, Sogalla, Willmann, marzo 2026.
La catena che modella è energia → chimica → fertilizzanti → cibo, e i paesi al centro dei risultati
sono Zambia (+30,7% sui prezzi alimentari), Sri Lanka, Taiwan, Pakistan. Citarlo a sostegno del caso
Gruppo III sarebbe una attribuzione falsa.

Cosa si può prendere legittimamente: il meccanismo dell'estensione bottleneck, e i risultati
settoriali della figura 5, dove "Petroleum products" fa +7,42% e "Chemicals" +5,75% contro +11,94%
del greggio. I lubrificanti non compaiono come settore: in GTAP stanno dentro "petroleum products"
insieme ai carburanti.

I limiti dichiarati dagli autori confermano il briefing alla lettera: il modello coglie il solo
canale commerciale e non include dinamiche speculative, accaparramento, rilasci di riserve
strategiche o prezzi dei futures. Testo estratto in `fonti/kiel-policy-brief-206.txt`, così le
citazioni si controllano senza riaprire il PDF.

Segnalato anche, da leggere: *A Critical-Inputs Playbook: What the Strait of Hormuz Tells Europe*,
Intereconomics 2026 n. 3.

---

## Punti aperti

Da decidere, in attesa di Sergio:

- **Rilevazione originale sui prezzi al dettaglio: si fa o no.** Costo 49 euro per un mese di API
  Keepa, che basta a tirare giù la storia completa di un paniere di 20-30 SKU su Amazon.it. Ora è
  meno decisiva di prima, perché il taglio metodologico regge senza; resta l'unico modo di
  documentare l'anello che nessuno ha documentato.
- **Chi legge**: pubblico di Scienza in rete o lettore generalista. La pagina com'è sta nel mezzo.
- Cosa intendeva Sergio con "owd" nel messaggio del 16/8 sugli accessi disponibili.

Da verificare prima di pubblicare, tutte affermazioni che in pagina sono scritte come fatti:

- **Le quote di capacità mondiale di Gruppo III per area (Corea contro Golfo).** Su questo numero
  poggia l'intero argomento dell'omologazione, ed è citato a memoria. Serve una fonte citabile.
- **Che sia davvero l'omologazione a bloccare la sostituzione**, e in quanti mesi. In pagina è
  affermato con sicurezza. Serve o una fonte tecnica o una intervista a un formulatore.
- I nodi elencati nella sezione sulle catene critiche (mezzi di contrasto 2022, neon ucraino,
  quarzo di Spruce Pine, nitrocellulosa, trasformatori): sono a memoria e vanno controllati uno
  per uno o attenuati.
- Che a Ras Laffan si produca sia la base GTL sia circa un terzo dell'elio mondiale, e l'entità
  del danno agli impianti dopo il 2 marzo.

Quando le verifiche qui sopra sono fatte, **togliere le marcature di bozza**: il `noindex` in
entrambe le pagine, la fascia in cima, l'avviso in linea sulla sezione delle catene critiche e la
sezione `metodo.html#bozza`. Finché restano, la pagina non è indicizzata dai motori di ricerca.

Da fare comunque:

- **Rileggere i valori unitari a settembre**, quando Comext pubblicherà giugno e luglio. Il secondo
  blocco di inizio luglio è fuori dai dati attuali, e se una rottura c'è si vedrà lì. È il
  controllo che può ribaltare di nuovo la conclusione.
- Controllare l'import **intra-UE**, non solo extra-UE: l'Italia prende l'84 per cento dei
  lubrificanti da altri paesi europei, e il Golfo può stare a monte di quel flusso senza comparire.
- Verificare se l'aumento dell'import dagli Stati Uniti nel 2026 è sostituzione di origine o
  rumore stagionale.
- Provare `docker compose up` sulla VPS: in locale il demone non era attivo, quindi il Dockerfile
  non è mai stato costruito davvero.
- Se si rigenera lo snapshot, **ricontrollare a mano i numeri citati nella prosa**: sono scritti a
  mano di proposito, e uno script che li riscrivesse farebbe mentire il testo.

---

## Materiali bloccanti

Nessuno, al momento: tutte le fonti gratuite necessarie sono raggiungibili e provate. L'unico
sblocco a pagamento è Keepa, e dipende da una decisione, non da una indisponibilità.

Restano fuori portata e vanno dichiarati come tali in pagina: Argus, ICIS e S&P Global Platts per
le quotazioni delle basi, Datalastic per il tracciamento navale usato dal Kiel Institute.

---

## Trappole tecniche

Stanno nel [`README.md`](README.md), che è il posto giusto: riguardano come si rimette in moto il
progetto, non le decisioni editoriali. In sintesi, Comext ha un endpoint SDMX suo e non risponde
sull'API di disseminazione normale, l'indicatore quantità si chiama `QUANTITY_IN_100KG`, come
dichiarante non accetta gli aggregati tipo `EU27_2020` e li restituisce vuoti senza errore, e
Chrome headless va in stallo con `--virtual-time-budget` su una pagina che anima.

## Avvertenze da riportare in pagina

Sui dati AIS: nelle aree di conflitto ci sono jamming del GPS, spoofing e navi con il transponder
spento, quindi i transiti visibili sottostimano quelli reali. Vale per tutta la serie PortWatch.

Sui valori unitari doganali: sono valore diviso quantità su un aggregato eterogeneo, quindi un
cambiamento di composizione si legge come un cambiamento di prezzo. Non vanno mai chiamati prezzi.
