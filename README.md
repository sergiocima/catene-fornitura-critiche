# Catene di fornitura critiche

Pagina divulgativa su che cosa sia una catena di fornitura, perché alcune si
rompono e altre no, e che cosa si riesce davvero a misurare quando uno stretto
si chiude. Caso di studio: la chiusura di Hormuz del 2026.

Le decisioni editoriali, le strade scartate e i punti aperti stanno in
[`stato.md`](stato.md). Qui c'è solo come è fatta e come si rimette in moto.

---

## Com'è fatta

Sito statico. Nessun framework, nessuna libreria lato browser, nessuna chiamata
a servizi esterni mentre la pagina è aperta. La prima visita pesa **172 KB**
compresa la geometria del mappamondo.

```
scripts/aggiorna_dati.py     scarica e congela i dati in uno snapshot datato
scripts/genera_grafici.py    disegna gli SVG e copia i dati dentro il sito
dati/AAAA-MM-GG/             lo snapshot, con manifest.json (URL, ora, checksum)
dati/ULTIMO                  quale snapshot usare
sito/                        quello che va in produzione
fonti/                       materiali di lavoro, non pubblicati
```

Il mappamondo è un canvas con proiezione ortografica scritta a mano, meno di
dieci kilobyte. Le rotte sono interpolazioni su grande cerchio. I grafici sono
SVG generati in build: il browser riceve tracciati già disegnati, e ogni SVG
si porta dentro la propria palette perché caricato via `<img>` non vedrebbe il
CSS della pagina.

## Rimettere in moto

```bash
python3 scripts/aggiorna_dati.py      # scarica tutto, snapshot con la data di oggi
python3 scripts/genera_grafici.py     # ridisegna i grafici e aggiorna sito/dati/
cd sito && python3 -m http.server 8099
```

Solo libreria standard, nessun `pip install`. Serve rete: PortWatch, Eurostat
Comext e Natural Earth.

Per riscrivere uno snapshot preciso invece di crearne uno nuovo:
`python3 scripts/aggiorna_dati.py 2026-08-16`.

## Deploy

```bash
docker compose up -d --build     # espone la porta 8081
```

Il container è `nginx:alpine` con dentro la cartella `sito/`. Nessun processo
applicativo, nessun database. Gli asset e i dati hanno cache lunga, l'HTML no,
così una correzione di refuso arriva subito.

---

## Trappole tecniche, pagate sul campo

**Comext non sta sull'API di disseminazione normale di Eurostat.** Il dataflow
`DS-045409` risponde «is not available for dissemination» su
`api/dissemination/statistics/1.0/`. Ha un endpoint SDMX suo, ed è quello che
usa il provider `comext` di `opensdmx`. Anche i bulk file
(`files?file=comext/COMEXT_DATA/PRODUCTS/fullAAAAMM.7z`) rispondono 404: non è
una fonte morta, è il canale sbagliato.

**L'indicatore quantità è `QUANTITY_IN_100KG`, non `QUANTITY_100KG`.** La
codelist del dataflow elenca entrambi perché è condivisa con Prodcom, ma il
secondo dà HTTP 400. Il modo affidabile di scoprire quali indicatori esistano
davvero per una chiave è interrogare l'endpoint lasciando vuota l'ultima
dimensione e guardare cosa torna.

**Come dichiarante Comext accetta i codici paese, non gli aggregati.**
`EU27_2020` torna vuoto senza dare errore, il che è peggio di un errore. Gli
aggregati esistono nella codelist ma non sono serviti da questo dataflow.

**PortWatch: due servizi diversi.** `Daily_Chokepoint_Data` è una tabella senza
geometria; le coordinate stanno in `PortWatch_chokepoints_database`. Il primo
pagina a mille record per volta, quindi la serie giornaliera va sfogliata con
`resultOffset`.

**`timeout` non esiste su macOS** senza coreutils.

**Chrome headless da riga di comando va in stallo con `--virtual-time-budget`
su una pagina che ha un ciclo `requestAnimationFrame`**: il tempo virtuale
continua ad avanzare fotogrammi e lo screenshot non arriva mai. Serve
`--headless=new` senza budget, oppure Playwright.

---

## Due difetti dei dati che il codice corregge, e perché

Sono documentati per esteso nel codice e nella pagina del metodo, perché sono
il genere di errore che si pubblica senza accorgersene.

**Mesi incompleti.** Comext pubblica con ritardo e non tutti gli stati
dichiarano entro lo stesso mese. Senza controllo, giugno 2026 mostrava l'Italia
importare quaranta tonnellate di olio motore invece di seimila, con il valore
unitario a 7,65 euro al chilo. Il controllo confronta la copertura e il volume
con la mediana dei dodici mesi precedenti. Il test sul volume si applica **solo
agli ultimi tre mesi**: applicato a tutta la serie cancellerebbe in silenzio i
crolli veri, che sono esattamente ciò che il progetto cerca.

**Dichiarazioni fuori scala.** Il codice CN 2804.29.10 contiene solo elio, e
l'elio vero viaggia fra 74 e 98 euro al chilo. Ma i Paesi Bassi vi dichiarano
quasi dodicimila tonnellate di origine cinese a 3,75 euro al chilo: aggregando,
quella riga produceva un calo dell'ottanta per cento del prezzo che non è mai
avvenuto. Il primo rimedio tentato era una soglia automatica sulla mediana delle
celle, ed è stato scartato perché escludeva anche Qatar e Stati Uniti, cioè
l'elio vero: le migliaia di celle minuscole hanno valori unitari selvaggi e
spostavano la mediana. Ora c'è una banda dichiarata a mano in `BANDE`, visibile
e contestabile. Peggiore in teoria, molto migliore in pratica.

Lo script stampa sempre le celle più grosse della serie con il loro valore
unitario: serve ad accorgersi di una contaminazione nuova senza doverla
sospettare in anticipo.

---

## Regole editoriali da non rompere

Ogni numero in pagina porta uno dei quattro statuti: misurato, modellato,
dichiarazione di parte, non verificabile. Se una cifra non rientra in nessuno,
non si pubblica.

Il valore unitario doganale non è un prezzo e non va mai chiamato così.

Testo d'autore e dati vivi restano separati. I numeri citati nella prosa sono
scritti a mano e riferiti allo snapshot dichiarato in fondo alla pagina: se si
rigenera lo snapshot vanno ricontrollati a mano, perché uno script che riscrive
i numeri sotto le frasi che li commentano fa mentire il testo senza che nessuno
se ne accorga.

Nei titoli maiuscola solo sulla prima parola e sui nomi propri. Niente trattino
lungo. Poca elencazione, si scrive in prosa.
