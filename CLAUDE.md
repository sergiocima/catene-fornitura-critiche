# Istruzioni per lavorare su questo progetto

Leggere `stato.md` prima di toccare qualsiasi cosa: decisioni, strade scartate e punti
aperti stanno lì. Il `README.md` dice come si rimette in moto.

## Regole redazionali, da non rompere

**Ogni numero in pagina porta uno dei quattro statuti**: misurato, modellato, dichiarazione di
parte, non verificabile da noi. Se una cifra non rientra in nessuno dei quattro, non si
pubblica. È la regola fondante del progetto, non una convenzione grafica.

**Il valore unitario doganale non è un prezzo e non va mai chiamato così.** È valore diviso
quantità su un codice che contiene merci diverse: un cambio di composizione si legge come un
cambio di prezzo.

**Testo d'autore e dati vivi restano separati.** I numeri citati nella prosa sono scritti a
mano di proposito e riferiti allo scatto dichiarato in fondo alla pagina. Nessuno script deve
mai riscriverli: se lo facesse, il testo comincerebbe a mentire sotto frasi che li commentano,
che è esattamente il difetto che la pagina denuncia. Quando si rigenera lo scatto, girare
`python3 scripts/cifre_chiave.py` e ricontrollare a mano.

**Gli errori commessi restano scritti in pagina.** Ce ne sono due nel riquadro della sezione
dati. Non vanno tolti quando si corregge qualcos'altro: una pagina che spiega come si sbaglia a
leggere i dati doganali è più credibile se dichiara di averlo fatto.

## Scrittura

Italiano. Nei titoli maiuscola solo sulla prima parola e sui nomi propri. Niente trattino lungo.
Poca elencazione, si scrive in prosa.

## Stato attuale

La pagina è una **bozza**: fascia in cima, `noindex` in entrambe le pagine, e una sezione in
`metodo.html#bozza` che elenca cosa manca. Quando le verifiche elencate lì sono fatte, togliere
il `noindex`, la fascia e l'avviso in linea sulla sezione delle catene critiche.
