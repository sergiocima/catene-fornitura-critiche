#!/usr/bin/env python3
"""
Scarica i dati del progetto e li congela in uno snapshot datato.

Nessuna dipendenza esterna: solo libreria standard, perche' questo script deve
continuare a funzionare fra tre anni senza che nessuno lo mantenga.

Uso:
    python3 scripts/aggiorna_dati.py            # snapshot con la data di oggi
    python3 scripts/aggiorna_dati.py 2026-08-16 # riscrive uno snapshot preciso

Ogni file prodotto e' registrato in manifest.json con l'URL da cui viene, il
momento dello scaricamento e il checksum, cosi' chi legge la pagina fra due anni
puo' sapere esattamente cosa aveva sotto gli occhi.
"""

import csv
import datetime as dt
import hashlib
import io
import json
import os
import sys
import time
import urllib.parse
import urllib.request

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = "catene-fornitura-critiche/1.0 (progetto editoriale; contatto via zadig.it)"

PORTWATCH = ("https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services"
             "/Daily_Chokepoints_Data/FeatureServer/0/query")
PORTWATCH_ANAGRAFICA = ("https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services"
                        "/PortWatch_chokepoints_database/FeatureServer/0/query")
COMEXT = "https://ec.europa.eu/eurostat/api/comext/dissemination/sdmx/2.1/data/DS-045409/"
TERRE = ("https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master"
         "/geojson/ne_110m_land.geojson")

# Stati membri UE al 2026. Serve a separare l'import extra-UE dalle
# riesportazioni interne, che altrimenti gonfiano i volumi e sporcano i
# valori unitari: i Paesi Bassi sono un hub e rispedirebbero due volte lo
# stesso elio.
UE27 = {"AT", "BE", "BG", "CY", "CZ", "DE", "DK", "EE", "ES", "FI", "FR", "GR",
        "HR", "HU", "IE", "IT", "LT", "LU", "LV", "MT", "NL", "PL", "PT", "RO",
        "SE", "SI", "SK"}

# Codici a due lettere che in Comext non sono paesi ma aggregati.
NON_PAESI = {"EU", "EA"}

MANIFEST = []


# --------------------------------------------------------------------------- rete

def scarica(url, tentativi=4, attesa=3):
    """GET con qualche tentativo. Restituisce i byte grezzi."""
    ultimo = None
    for n in range(tentativi):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=180) as r:
                return r.read()
        except Exception as e:          # noqa: BLE001 - vogliamo davvero riprovare su tutto
            ultimo = e
            if n < tentativi - 1:
                time.sleep(attesa * (n + 1))
    raise RuntimeError(f"scaricamento fallito dopo {tentativi} tentativi: {url}\n  {ultimo}")


def json_da(url):
    return json.loads(scarica(url).decode("utf-8"))


# ----------------------------------------------------------------------- scrittura

def scrivi_csv(cartella, nome, intestazione, righe, fonte, nota=""):
    """Scrive un CSV e lo registra nel manifest con checksum e provenienza."""
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(intestazione)
    w.writerows(righe)
    testo = buf.getvalue()

    percorso = os.path.join(cartella, nome)
    with open(percorso, "w", encoding="utf-8") as f:
        f.write(testo)

    MANIFEST.append({
        "file": nome,
        "righe": len(righe),
        "fonte": fonte,
        "nota": nota,
        "scaricato": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "sha256": hashlib.sha256(testo.encode("utf-8")).hexdigest(),
    })
    print(f"  {nome}: {len(righe)} righe")


# ---------------------------------------------------------------------- portwatch

def pw_query(base, **params):
    params.setdefault("f", "json")
    return json_da(base + "?" + urllib.parse.urlencode(params))


def anagrafica_chokepoint(cartella):
    """I 28 chokepoint con coordinate e traffico annuo. Servono al mappamondo."""
    d = pw_query(PORTWATCH_ANAGRAFICA, where="1=1", outFields="*", returnGeometry="false")
    righe = []
    for f in d["features"]:
        a = f["attributes"]
        righe.append([
            a.get("portid"), a.get("portname"), a.get("country"),
            a.get("lat"), a.get("lon"),
            a.get("vessel_count_total"), a.get("vessel_count_tanker"),
            a.get("industry_top1"), a.get("industry_top2"), a.get("industry_top3"),
        ])
    righe.sort(key=lambda r: int(str(r[0]).replace("chokepoint", "") or 0))
    scrivi_csv(
        cartella, "chokepoint_anagrafica.csv",
        ["id", "nome", "paese", "lat", "lon", "navi_anno", "petroliere_anno",
         "industria_1", "industria_2", "industria_3"],
        righe, PORTWATCH_ANAGRAFICA,
        "Coordinate e traffico annuo dei 28 chokepoint monitorati da IMF PortWatch.")


def transiti_giornalieri(cartella, portid="chokepoint6", nome="hormuz"):
    """Serie giornaliera completa di un chokepoint, con paginazione."""
    righe, offset = [], 0
    while True:
        d = pw_query(PORTWATCH,
                     where=f"portid='{portid}'",
                     outFields="date,n_total,n_tanker,n_cargo,capacity_tanker,capacity",
                     returnGeometry="false", orderByFields="date",
                     resultRecordCount=1000, resultOffset=offset)
        f = d.get("features", [])
        if not f:
            break
        for x in f:
            a = x["attributes"]
            righe.append([a["date"], a["n_total"], a["n_tanker"], a["n_cargo"],
                          a["capacity_tanker"], a["capacity"]])
        if not d.get("exceededTransferLimit"):
            break
        offset += len(f)

    scrivi_csv(
        cartella, f"{nome}_transiti_giornalieri.csv",
        ["data", "navi_totali", "petroliere", "cargo",
         "capacita_petroliere_dwt", "capacita_totale_dwt"],
        righe, PORTWATCH,
        "Transiti giornalieri stimati da dati AIS satellitari. "
        "Nelle aree di conflitto jamming, spoofing e transponder spenti fanno "
        "sottostimare i transiti reali.")


def transiti_mensili_tutti(cartella):
    """Medie mensili per tutti i 28 chokepoint: serve al confronto."""
    anagrafica = pw_query(PORTWATCH_ANAGRAFICA, where="1=1",
                          outFields="portid,portname", returnGeometry="false")
    ids = sorted({f["attributes"]["portid"] for f in anagrafica["features"]},
                 key=lambda s: int(s.replace("chokepoint", "")))
    stats = json.dumps([
        {"statisticType": "avg", "onStatisticField": "n_total",
         "outStatisticFieldName": "navi"},
        {"statisticType": "avg", "onStatisticField": "n_tanker",
         "outStatisticFieldName": "petroliere"},
    ])
    righe = []
    for pid in ids:
        d = pw_query(PORTWATCH, where=f"portid='{pid}' AND year>=2019",
                     outStatistics=stats,
                     groupByFieldsForStatistics="portname,year,month",
                     returnGeometry="false", resultRecordCount=1000)
        for f in d.get("features", []):
            a = f["attributes"]
            righe.append([pid, a["portname"], f"{a['year']}-{a['month']:02d}",
                          round(a["navi"] or 0, 2), round(a["petroliere"] or 0, 2)])
    righe.sort(key=lambda r: (int(r[0].replace("chokepoint", "")), r[2]))
    scrivi_csv(
        cartella, "chokepoint_transiti_mensili.csv",
        ["id", "nome", "mese", "navi_giorno_media", "petroliere_giorno_media"],
        righe, PORTWATCH,
        "Media giornaliera dei transiti, per mese, su tutti i chokepoint.")


# ------------------------------------------------------------------------- comext

def comext(chiave, dal="2019-01"):
    """
    Interroga Comext e restituisce righe gia' spacchettate.

    La chiave e' posizionale: freq.dichiarante.partner.prodotto.flusso.indicatore
    Una dimensione lasciata vuota vale 'tutti i valori'.

    Attenzione, due trappole pagate sul campo:
      - l'indicatore quantita' si chiama QUANTITY_IN_100KG. La codelist del
        dataflow elenca anche QUANTITY_100KG perche' e' condivisa con Prodcom,
        ma quello restituisce HTTP 400.
      - come dichiarante Comext accetta i codici paese, non gli aggregati tipo
        EU27_2020: quelli tornano vuoti senza dare errore, ed e' peggio.
    """
    url = COMEXT + chiave + "?" + urllib.parse.urlencode(
        {"format": "SDMX-CSV", "startPeriod": dal})
    testo = scarica(url).decode("utf-8")
    return list(csv.DictReader(io.StringIO(testo))), url


def mesi_provvisori(coppie_per_mese, volume_per_mese, finestra=12, coda=3):
    """
    Individua i mesi in cui Comext non ha ancora ricevuto tutte le dichiarazioni.

    Due segnali, con ambiti diversi di proposito.

    Il primo e' la copertura: quante coppie dichiarante-origine sono presenti
    rispetto alla mediana dei dodici mesi precedenti. Sotto il 60 per cento
    mancano dichiarazioni, e vale su tutta la serie perche' un buco di
    copertura e' sempre un difetto del dato, mai un fatto economico.

    Il secondo e' il volume, e vale SOLO sugli ultimi mesi della serie. Qui sta
    il punto delicato: un volume dimezzato puo' benissimo essere un crollo
    vero, ed e' esattamente il genere di notizia che questo progetto cerca.
    Applicare il test del volume a tutta la serie significherebbe cancellare
    in silenzio i crolli reali, cioe' il difetto peggiore che una pipeline
    editoriale possa avere. Sugli ultimi mesi invece la causa nota e'
    un'altra, il ritardo di pubblicazione, e li' il test e' legittimo.

    Senza questo controllo a giugno 2026 l'Italia risultava importare 40
    tonnellate di olio motore invece di seimila, con il valore unitario a 7,65
    euro al chilo: un artefatto di pubblicazione travestito da notizia.
    """
    mesi = sorted(coppie_per_mese)
    provvisori = set()

    def mediana_precedente(serie, i):
        p = sorted(serie[x] for x in mesi[max(0, i - finestra):i])
        return p[len(p) // 2] if len(p) >= 6 else None

    for i, m in enumerate(mesi):
        med_c = mediana_precedente(coppie_per_mese, i)
        if med_c and coppie_per_mese[m] < 0.6 * med_c:
            provvisori.add(m)
            continue
        if i >= len(mesi) - coda:
            med_v = mediana_precedente(volume_per_mese, i)
            if med_v and volume_per_mese[m] < 0.5 * med_v:
                provvisori.add(m)
    return provvisori


def mediana(v):
    s = sorted(v)
    return s[len(s) // 2] if s else None


# Bande di plausibilita' dichiarate a mano, per codice doganale, in euro al
# chilo. Sono un giudizio editoriale esplicito, non una soglia statistica, e
# stanno qui in chiaro perche' chi rifa' i conti possa contestarle.
#
# Perche' servono, e perche' NON sono automatiche. Il codice CN 2804.29.10
# contiene solo elio, quindi il suo valore unitario sembrava un proxy di
# prezzo affidabile. L'elio vero, importato da Qatar, Algeria e Stati Uniti,
# sta fra 74 e 98 euro al chilo. Ma i Paesi Bassi dichiarano sotto lo stesso
# codice quasi dodicimila tonnellate di origine cinese a 3,75 euro al chilo,
# un ventesimo: qualunque cosa sia, elio non e'. Aggregando, quella singola
# riga schiacciava la media e produceva un calo dell'ottanta per cento che non
# e' mai avvenuto.
#
# Il primo tentativo di rimedio era una soglia automatica calcolata sulla
# mediana delle celle, ed e' stato scartato: escludeva anche il Qatar e gli
# Stati Uniti, cioe' l'elio vero, perche' le migliaia di celle minuscole da
# pochi chili hanno valori unitari selvaggi e spostavano la mediana. Un filtro
# statistico che rimodella i dati in silenzio e' esattamente il difetto contro
# cui questa pagina mette in guardia. Meglio una soglia dichiarata, discutibile
# e visibile, che una automatica e invisibile.
BANDE = {
    "28042910": (20.0, 300.0),   # elio: sotto i 20 EUR/kg non e' elio industriale
}


def celle_implausibili(celle, prodotto):
    """
    Applica la banda dichiarata per quel codice, se ce n'e' una.

    Le celle escluse restano nel CSV di dettaglio con la loro etichetta e
    vengono stampate a schermo: niente sparisce, si dichiara soltanto che non
    entra nell'aggregato.
    """
    banda = BANDE.get(prodotto)
    if not banda:
        return set(), None
    lo, hi = banda
    return {k for k, u in celle if u < lo or u > hi}, banda


def valore_unitario(cartella, nome, dichiaranti, prodotti, etichette,
                    solo_extra_ue=False, dal="2019-01",
                    aggrega=None):
    """
    Valore unitario implicito: valore diviso quantita'.

    NON e' un prezzo e non va mai chiamato cosi' in pagina. Su un codice
    doganale che contiene merci eterogenee un cambio di composizione si legge
    come un cambio di prezzo. E anche su un codice puro, come si scopre qui
    sotto, una dichiarazione anomala basta a rovinare l'aggregato.

    Produce due file: il dettaglio per origine, che e' il dato grezzo su cui
    chiunque puo' rifare i conti, e l'aggregato mensile, che e' quello che
    finisce in pagina.
    """
    chiave = (f"M.{'+'.join(dichiaranti)}..{'+'.join(prodotti)}.1."
              "QUANTITY_IN_100KG+VALUE_IN_EUROS")
    dati, url = comext(chiave, dal)

    celle = {}
    for r in dati:
        p = r["partner"]
        if len(p) != 2 or not p.isalpha() or p in NON_PAESI:
            continue                      # scarta gli aggregati, evita il doppio conteggio
        if solo_extra_ue and p in UE27:
            continue
        k = (r["TIME_PERIOD"][:7], r["product"], r["reporter"], p)
        v = celle.setdefault(k, [0.0, 0.0])
        v[0 if r["indicators"] == "VALUE_IN_EUROS" else 1] += float(r["OBS_VALUE"])

    unitari = [(k, v / (q * 100)) for k, (v, q) in celle.items() if q > 0]

    fuori = set()
    for prod in prodotti:
        f, banda = celle_implausibili([(k, u) for k, u in unitari if k[1] == prod],
                                      prod)
        fuori |= f
        if f:
            tonnellate = sum(celle[k][1] * 100 / 1000 for k in f)
            quali = sorted({f"{k[2]}<-{k[3]}" for k in f})
            print(f"    {prod}: fuori dalla banda {banda[0]:.0f}-{banda[1]:.0f} "
                  f"EUR/kg, {tonnellate:.0f} t escluse dall'aggregato "
                  f"({len(f)} celle: {', '.join(quali[:8])}"
                  f"{' e altre' if len(quali) > 8 else ''})")

    # Diagnostica: le celle piu' grosse dell'intera serie, per accorgersi di
    # una contaminazione nuova senza doverla sospettare in anticipo.
    grosse = sorted(unitari, key=lambda x: -celle[x[0]][1])[:4]
    for k, u in grosse:
        print(f"      cella maggiore {k[2]}<-{k[3]} {k[0]}: "
              f"{celle[k][1] * 100 / 1000:.0f} t a {u:.2f} EUR/kg"
              f"{'  ESCLUSA' if k in fuori else ''}")

    # dettaglio per origine, con l'etichetta di chi e' stato escluso e perche'
    dettaglio = []
    for k, u in sorted(unitari):
        mese, prod, rep, org = k
        val, q100 = celle[k]
        dettaglio.append([mese, prod, rep, org, round(val, 0),
                          round(q100 * 100 / 1000, 3), round(u, 4),
                          "si" if k in fuori else "no"])
    scrivi_csv(
        cartella, f"{nome}_valore_unitario_per_origine.csv",
        ["mese", "codice_cn8", "dichiarante", "origine", "valore_eur",
         "quantita_t", "eur_per_kg", "fuori_banda"],
        dettaglio, url,
        "Dettaglio per dichiarante e origine. La colonna fuori_scala segnala "
        "le celle escluse dall'aggregato perche' il valore unitario e' oltre "
        "quattro volte distante dalla mediana: non sono state cancellate, "
        "solo tenute fuori dalla media.")

    # Con `aggrega` i codici vengono sommati in una serie sola, ponderata per
    # le quantita'. Serve quando una merce e' sparsa su piu' codici doganali di
    # peso molto diverso: guardarne uno solo da' una risposta sbagliata, e
    # sceglierlo male la da' clamorosamente sbagliata. Sui lubrificanti
    # italiani il 2710.19.99 vale quarantottomila tonnellate al mese e il
    # 2710.19.81 seimila: leggere solo il secondo faceva sembrare fermo un
    # mercato che si stava muovendo di un quinto.
    agg, coppie = {}, {}
    for k, (val, q100) in celle.items():
        if k in fuori or q100 <= 0:
            continue
        mese, prod, rep, org = k
        chiave = (aggrega, mese) if aggrega else (prod, mese)
        a = agg.setdefault(chiave, [0.0, 0.0])
        a[0] += val
        a[1] += q100
        coppie.setdefault(mese, set()).add((rep, org))

    volumi = {}
    for (prod, mese), (val, q100) in agg.items():
        volumi[mese] = volumi.get(mese, 0.0) + q100 * 100
    provvisori = mesi_provvisori({m: len(s) for m, s in coppie.items()}, volumi)

    righe = []
    for (prod, mese) in sorted(agg):
        val, q100 = agg[(prod, mese)]
        kg = q100 * 100
        if kg <= 0:
            continue                      # il dato assente si dichiara, non si riempie
        righe.append([mese, prod, etichette.get(prod, prod),
                      round(val, 0), round(kg / 1000, 1), round(val / kg, 4),
                      "si" if mese in provvisori else "no"])

    if provvisori:
        print(f"    mesi incompleti esclusi dai grafici: {', '.join(sorted(provvisori))}")

    ambito = "solo origini extra-UE" if solo_extra_ue else "tutte le origini"
    scrivi_csv(
        cartella, f"{nome}_valore_unitario.csv",
        ["mese", "codice_cn8", "descrizione", "valore_eur", "quantita_t",
         "eur_per_kg", "provvisorio"],
        righe, url,
        f"Import di {'+'.join(dichiaranti)}, {ambito}. Valore unitario implicito "
        "(valore diviso quantita'), non un indice di prezzo. Esclude le celle "
        "fuori scala elencate nel file per origine e i mesi ancora incompleti.")


def origine(cartella, nome, dichiaranti, prodotti, dal="2019-01"):
    """Quantita' importata per paese di origine."""
    chiave = f"M.{'+'.join(dichiaranti)}..{'+'.join(prodotti)}.1.QUANTITY_IN_100KG"
    dati, url = comext(chiave, dal)

    agg = {}
    for r in dati:
        p = r["partner"]
        if len(p) != 2 or not p.isalpha() or p in NON_PAESI:
            continue
        k = (r["TIME_PERIOD"][:7], p)
        agg[k] = agg.get(k, 0.0) + float(r["OBS_VALUE"]) * 100 / 1000

    righe = [[m, p, round(t, 1), "si" if p in UE27 else "no"]
             for (m, p), t in sorted(agg.items()) if t > 0]
    scrivi_csv(
        cartella, f"{nome}_origine.csv",
        ["mese", "origine", "tonnellate", "intra_ue"],
        righe, url,
        f"Import di {'+'.join(dichiaranti)} per paese di origine.")


# ------------------------------------------------------------------- geografia

def terre_emerse():
    """
    Contorni delle terre emerse per il mappamondo, alleggeriti.

    Natural Earth 110m, dominio pubblico. Le coordinate vengono arrotondate a
    due decimali (circa un chilometro) e i poligoni con meno di cinque vertici
    scartati: a schermo non si vedono e pesano.
    """
    d = json.loads(scarica(TERRE).decode("utf-8"))
    poligoni = []

    def aggiungi(anello):
        if len(anello) < 5:
            return
        p = [[round(x, 2), round(y, 2)] for x, y in anello]
        compatto = [p[0]]
        for punto in p[1:]:
            if punto != compatto[-1]:
                compatto.append(punto)
        if len(compatto) >= 5:
            poligoni.append(compatto)

    for f in d["features"]:
        g = f["geometry"]
        if g["type"] == "Polygon":
            aggiungi(g["coordinates"][0])
        elif g["type"] == "MultiPolygon":
            for parte in g["coordinates"]:
                aggiungi(parte[0])

    percorso = os.path.join(RADICE, "sito", "assets", "terre.json")
    testo = json.dumps(poligoni, separators=(",", ":"))
    with open(percorso, "w", encoding="utf-8") as f:
        f.write(testo)
    MANIFEST.append({
        "file": "sito/assets/terre.json",
        "righe": len(poligoni),
        "fonte": TERRE,
        "nota": "Natural Earth 110m, dominio pubblico. Coordinate arrotondate a 2 decimali.",
        "scaricato": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "sha256": hashlib.sha256(testo.encode("utf-8")).hexdigest(),
    })
    print(f"  sito/assets/terre.json: {len(poligoni)} poligoni, "
          f"{len(testo) // 1024} KB")


# ---------------------------------------------------------------------- principale

# Tutti i codici a otto cifre in cui l'Unione europea classifica gli oli
# lubrificanti. Vanno presi tutti e sommati: presi uno alla volta danno
# risposte contraddittorie, perche' pesano in modo molto diverso e ciascuno
# contiene un pezzo del mercato. A maggio 2026, sull'import italiano, il
# 2710.19.99 vale 48.144 tonnellate e il 2710.19.81 ne vale 6.399.
LUBRIFICANTI = {
    "27101971": "Oli lubrificanti destinati a un processo specifico",
    "27101981": "Oli motore, oli per compressori e turbine",
    "27101983": "Oli idraulici",
    "27101985": "Oli bianchi e paraffina liquida",
    "27101987": "Oli per ingranaggi e riduttori",
    "27101991": "Oli per lavorazione metalli, distacco stampi, anticorrosione",
    "27101993": "Oli isolanti per uso elettrico",
    "27101999": "Altri oli lubrificanti (qui rientra la base GTL)",
}
ELIO = {"28042910": "Elio"}
GREGGIO = {"27090090": "Oli greggi di petrolio"}


def main():
    data = sys.argv[1] if len(sys.argv) > 1 else dt.date.today().isoformat()
    cartella = os.path.join(RADICE, "dati", data)
    os.makedirs(cartella, exist_ok=True)
    print(f"snapshot {data} in dati/{data}/\n")

    print("PortWatch")
    anagrafica_chokepoint(cartella)
    transiti_giornalieri(cartella)
    transiti_mensili_tutti(cartella)

    print("\nComext, lubrificanti")
    valore_unitario(cartella, "lubrificanti_italia", ["IT"],
                    list(LUBRIFICANTI),
                    {"LUBRIFICANTI": "Oli lubrificanti, tutti i codici 2710.19"},
                    aggrega="LUBRIFICANTI")
    # La stessa cosa spacchettata per codice, perche' l'aggregato nasconde
    # che i singoli codici si muovono in direzioni diverse.
    valore_unitario(cartella, "lubrificanti_italia_per_codice", ["IT"],
                    list(LUBRIFICANTI), LUBRIFICANTI)
    origine(cartella, "lubrificanti_italia", ["IT"], list(LUBRIFICANTI))

    # Il greggio serve come termine di paragone, ed e' preso con lo stesso
    # metodo e dalla stessa fonte dei lubrificanti: due valori unitari
    # doganali si possono confrontare fra loro, un valore unitario doganale
    # e una quotazione Brent no.
    print("\nComext, greggio")
    valore_unitario(cartella, "greggio_italia", ["IT"],
                    list(GREGGIO), GREGGIO)

    print("\nComext, elio")
    valore_unitario(cartella, "elio_ue", ["IT", "DE", "FR", "NL", "ES"],
                    list(ELIO), ELIO, solo_extra_ue=True)
    origine(cartella, "elio_ue", ["IT", "DE", "FR", "NL", "ES"], list(ELIO))

    print("\nGeografia")
    terre_emerse()

    manifest = {
        "snapshot": data,
        "generato": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "avvertenza": ("I dati piu' recenti di Comext sono incompleti: non tutti "
                       "gli stati dichiarano entro lo stesso mese. Verificare "
                       "sempre la copertura per dichiarante prima di leggere "
                       "l'ultimo mese come un fatto."),
        "file": MANIFEST,
    }
    with open(os.path.join(cartella, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    with open(os.path.join(RADICE, "dati", "ULTIMO"), "w", encoding="utf-8") as f:
        f.write(data + "\n")

    print(f"\nfatto. manifest in dati/{data}/manifest.json")


if __name__ == "__main__":
    main()
