#!/usr/bin/env python3
"""
Genera i grafici del sito come SVG, in fase di build.

Niente libreria di grafici spedita al browser: il lettore riceve dei tracciati
gia' disegnati, che pesano qualche kilobyte e funzionano anche senza
JavaScript. I colori sono variabili CSS, cosi' il tema chiaro e quello scuro
usano lo stesso file.

Legge lo snapshot indicato in dati/ULTIMO e scrive in sito/assets/grafici/.
"""

import csv
import json
import os
from xml.sax.saxutils import escape

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
USCITA = os.path.join(RADICE, "sito", "assets", "grafici")

L, R, T, B = 62, 18, 26, 46          # margini interni
W, H = 720, 330                       # area di disegno nominale

MESI = ["gen", "feb", "mar", "apr", "mag", "giu",
        "lug", "ago", "set", "ott", "nov", "dic"]


# ------------------------------------------------------------------- lettura

def snapshot():
    with open(os.path.join(RADICE, "dati", "ULTIMO"), encoding="utf-8") as f:
        return f.read().strip()


def leggi(nome):
    p = os.path.join(RADICE, "dati", snapshot(), nome)
    with open(p, encoding="utf-8") as f:
        return list(csv.DictReader(f))


# -------------------------------------------------------------------- disegno

def scala(vmin, vmax, p0, p1):
    if vmax == vmin:
        vmax = vmin + 1
    return lambda v: p0 + (v - vmin) * (p1 - p0) / (vmax - vmin)


def tacche(vmin, vmax, quante=5):
    """Tacche su valori tondi, senza inventare precisione."""
    grezzo = (vmax - vmin) / max(quante, 1)
    if grezzo <= 0:
        return [vmin]
    import math
    mag = 10 ** math.floor(math.log10(grezzo))
    for m in (1, 2, 2.5, 5, 10):
        if grezzo / mag <= m:
            passo = m * mag
            break
    inizio = math.floor(vmin / passo) * passo
    out, v = [], inizio
    while v <= vmax + passo * 0.001:
        if v >= vmin - passo * 0.001:
            out.append(round(v, 10))
        v += passo
    return out


def formatta(v):
    if v == 0:
        return "0"
    if abs(v) >= 1000:
        return f"{v:,.0f}".replace(",", ".")
    if abs(v) >= 10:
        return f"{v:.0f}"
    if abs(v) >= 1:
        return f"{v:.1f}".replace(".", ",")
    return f"{v:.2f}".replace(".", ",")


# I grafici sono caricati con <img>, e un SVG dentro un <img> e' un documento
# separato: non vede il CSS della pagina e non eredita le variabili del tema.
# Quindi ogni file si porta dentro la propria palette, tema scuro compreso.
# Costa duecento byte a grafico e in cambio i file restano cacheabili,
# apribili da soli e leggibili anche fuori dal sito.
STILE = """<style>
  .griglia{stroke:#d5cec0;stroke-width:1}
  .base{stroke:#55514a;stroke-width:1;stroke-dasharray:3 3}
  .tacca,.unita,.etichetta-riga,.valore-riga,.evento-testo{
    font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;
    font-size:11px;fill:#55514a}
  .unita{font-size:10px;letter-spacing:.06em;text-transform:uppercase}
  .valore-riga{font-size:10.5px}
  polyline{fill:none;stroke-width:2;stroke-linejoin:round;stroke-linecap:round}
  .banda{fill:#55514a;opacity:.18}
  .serie-1{stroke:#c1452b}.serie-2{stroke:#1f6f6b}.serie-3{stroke:#7a5ea8}
  .punto-1{fill:#c1452b}.punto-2{fill:#1f6f6b}.punto-3{fill:#7a5ea8}
  .sottile-1,.sottile-2,.sottile-3{fill:#f6f3ec;stroke-width:1.5}
  .sottile-1{stroke:#c1452b}.sottile-2{stroke:#1f6f6b}.sottile-3{stroke:#7a5ea8}
  .barra{fill:#55514a;opacity:.5}.barra-evidenza{fill:#c1452b}
  .evento{stroke:#1d1c1a;stroke-width:1;stroke-dasharray:2 3;opacity:.6}
  @media (prefers-color-scheme:dark){
    .griglia{stroke:#33363a}
    .base{stroke:#a8a49c}
    .tacca,.unita,.etichetta-riga,.valore-riga,.evento-testo{fill:#a8a49c}
    .banda{fill:#a8a49c;opacity:.2}
    .serie-1{stroke:#ff6b4a}.serie-2{stroke:#4fbdb6}.serie-3{stroke:#b295e0}
    .punto-1{fill:#ff6b4a}.punto-2{fill:#4fbdb6}.punto-3{fill:#b295e0}
    .sottile-1,.sottile-2,.sottile-3{fill:#17181a}
    .sottile-1{stroke:#ff6b4a}.sottile-2{stroke:#4fbdb6}.sottile-3{stroke:#b295e0}
    .barra{fill:#a8a49c;opacity:.45}.barra-evidenza{fill:#ff6b4a}
    .evento{stroke:#ece8e1}
  }
</style>"""


def intestazione(titolo, descrizione, altezza=None):
    idt = "t-" + str(abs(hash(titolo)) % 99999)
    h = altezza or H
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {h}" '
            f'class="grafico" role="img" aria-labelledby="{idt}">'
            f'<title id="{idt}">{escape(titolo)}</title>'
            f'<desc>{escape(descrizione)}</desc>{STILE}')


def assi(ymin, ymax, sy, etichette_x, sx, unita=""):
    """Griglia orizzontale, etichette degli assi. La griglia verticale non
    serve: aggiunge inchiostro e non aggiunge lettura."""
    out = []
    for v in tacche(ymin, ymax):
        y = sy(v)
        out.append(f'<line class="griglia" x1="{L}" y1="{y:.1f}" '
                   f'x2="{W - R}" y2="{y:.1f}"/>')
        out.append(f'<text class="tacca" x="{L - 8}" y="{y + 4:.1f}" '
                   f'text-anchor="end">{formatta(v)}</text>')
    if unita:
        # ancorata a sinistra dal bordo: con text-anchor="end" sul margine
        # interno il testo usciva dal riquadro e veniva tagliato.
        out.append(f'<text class="unita" x="4" y="{T - 10}" '
                   f'text-anchor="start">{escape(unita)}</text>')
    for pos, testo in etichette_x:
        out.append(f'<text class="tacca" x="{sx(pos):.1f}" y="{H - B + 20}" '
                   f'text-anchor="middle">{escape(testo)}</text>')
    return "".join(out)


def salva(nome, contenuto):
    os.makedirs(USCITA, exist_ok=True)
    with open(os.path.join(USCITA, nome), "w", encoding="utf-8") as f:
        f.write(contenuto + "</svg>")
    kb = os.path.getsize(os.path.join(USCITA, nome)) / 1024
    print(f"  {nome}  {kb:.1f} KB")


# --------------------------------------------------------------------- grafici

def transiti_hormuz():
    """La serie giornaliera, con la media mobile a sette giorni in evidenza."""
    righe = [r for r in leggi("hormuz_transiti_giornalieri.csv") if r["navi_totali"]]
    dati = [(r["data"], float(r["navi_totali"])) for r in righe]
    dati.sort()

    finestra, mobile = 7, []
    for i in range(len(dati)):
        f = [v for _, v in dati[max(0, i - finestra + 1):i + 1]]
        mobile.append(sum(f) / len(f))

    n = len(dati)
    vmax = max(max(v for _, v in dati), 1) * 1.05
    sx = scala(0, n - 1, L, W - R)
    sy = scala(0, vmax, H - B, T)

    anni = {}
    for i, (d, _) in enumerate(dati):
        anni.setdefault(d[:4], i)
    etichette = [(i, a) for a, i in sorted(anni.items())]

    # Con 2778 giorni su 720 pixel ci sono quasi quattro punti per pixel: una
    # polilinea giornaliera sarebbe cinquanta kilobyte di dettaglio invisibile.
    # Al suo posto una banda fra il minimo e il massimo di ogni colonna, che
    # mostra la stessa volatilita' e pesa un quarto.
    colonne = {}
    for i, (_, v) in enumerate(dati):
        c = int(sx(i))
        lo, hi = colonne.get(c, (v, v))
        colonne[c] = (min(lo, v), max(hi, v))
    ordinate = sorted(colonne)
    sopra = " ".join(f"{c},{sy(colonne[c][1]):.0f}" for c in ordinate)
    sotto = " ".join(f"{c},{sy(colonne[c][0]):.0f}" for c in reversed(ordinate))
    banda = f'<polygon class="banda" points="{sopra} {sotto}"/>'

    punti_m = " ".join(f"{sx(i):.0f},{sy(v):.1f}" for i, v in enumerate(mobile)
                       if i % 3 == 0 or i == len(mobile) - 1)

    # la chiusura del 28 febbraio 2026
    chiusura = next((i for i, (d, _) in enumerate(dati) if d >= "2026-02-28"), None)
    ann = ""
    if chiusura is not None:
        x = sx(chiusura)
        ann = (f'<line class="evento" x1="{x:.1f}" y1="{T}" x2="{x:.1f}" y2="{H - B}"/>'
               f'<text class="evento-testo" x="{x - 6:.1f}" y="{T + 14}" '
               f'text-anchor="end">chiusura, 28 febbraio 2026</text>')

    svg = (intestazione(
        "Transiti giornalieri nello stretto di Hormuz, 2019-2026",
        "Numero di navi al giorno rilevate da dati AIS satellitari. Dopo la "
        "chiusura del 28 febbraio 2026 la media scende da circa settanta navi "
        "al giorno a meno di cinque.")
        + assi(0, vmax, sy, etichette, sx, "navi al giorno")
        + banda
        + f'<polyline class="serie-1" points="{punti_m}"/>'
        + ann)
    salva("transiti-hormuz.svg", svg)


def valori_unitari_confronto():
    """
    Greggio, lubrificanti ed elio sullo stesso grafico, indicizzati.

    Indicizzare a gennaio 2024 e' l'unico modo di mettere sullo stesso asse
    merci che costano 0,4 e 85 euro al chilo. Il confronto regge perche' i tre
    valori sono calcolati con lo stesso metodo sulla stessa fonte: sono tre
    valori unitari doganali, non una quotazione di mercato contro una statistica.
    """
    serie, volumi = {}, {}

    def carica(file, codice, etichetta):
        righe = [r for r in leggi(file)
                 if r["codice_cn8"] == codice and r["provvisorio"] == "no"]
        serie[etichetta] = {r["mese"]: float(r["eur_per_kg"]) for r in righe}
        volumi[etichetta] = {r["mese"]: float(r["quantita_t"]) for r in righe}

    def mesi_sottili(vol, finestra=12, soglia=0.6):
        """
        Mesi in cui e' passata molta meno merce del solito.

        Non vanno nascosti, vanno marcati. In un mese sottile una singola
        partita anomala sposta la media, quindi il valore unitario dice piu'
        sulla composizione che sul prezzo: nell'agosto 2025 i lubrificanti
        segnano il valore piu' alto di tutta la serie su meno di meta' del
        volume normale, e senza un segno a schermo quel picco sembra l'evento
        principale del grafico invece che un artefatto.
        """
        mesi = sorted(vol)
        fuori = set()
        for i, m in enumerate(mesi):
            p = sorted(vol[x] for x in mesi[max(0, i - finestra):i])
            if len(p) < 6:
                continue
            med = p[len(p) // 2]
            if med and vol[m] < soglia * med:
                fuori.add(m)
        return fuori

    carica("greggio_italia_valore_unitario.csv", "27090090", "Greggio")
    carica("lubrificanti_italia_valore_unitario.csv", "LUBRIFICANTI",
           "Oli lubrificanti")
    carica("elio_ue_valore_unitario.csv", "28042910", "Elio")

    base_mese = "2024-01"
    mesi = sorted(set.intersection(*(set(v) for v in serie.values())))
    mesi = [m for m in mesi if m >= base_mese]

    ind = {}
    for et, v in serie.items():
        b = v.get(base_mese)
        if not b:
            continue
        ind[et] = [(m, 100 * v[m] / b) for m in mesi if m in v]

    tutti = [y for s in ind.values() for _, y in s]
    ymin, ymax = min(min(tutti), 0), max(tutti) * 1.08
    sx = scala(0, len(mesi) - 1, L, W - R)
    sy = scala(ymin, ymax, H - B, T)
    pos = {m: i for i, m in enumerate(mesi)}

    etichette = []
    for m in mesi:
        a, mm = m.split("-")
        if mm in ("01", "07"):
            etichette.append((pos[m], f"{MESI[int(mm) - 1]} {a[2:]}"))

    corpo = []
    for i, (et, s) in enumerate(ind.items(), start=1):
        p = " ".join(f"{sx(pos[m]):.1f},{sy(y):.1f}" for m, y in s)
        corpo.append(f'<polyline class="serie-{i}" points="{p}"/>')
        # i mesi a volume ridotto vengono cerchiati: il valore c'e' ancora,
        # ma il lettore sa che quel punto e' meno affidabile degli altri
        sottili = mesi_sottili(volumi[et])
        for m, y in s:
            if m in sottili:
                corpo.append(f'<circle class="sottile-{i}" cx="{sx(pos[m]):.1f}" '
                             f'cy="{sy(y):.1f}" r="4"/>')
        mfin, yfin = s[-1]
        corpo.append(f'<circle class="punto-{i}" cx="{sx(pos[mfin]):.1f}" '
                     f'cy="{sy(yfin):.1f}" r="3.5"/>')

    y100 = sy(100)
    corpo.insert(0, f'<line class="base" x1="{L}" y1="{y100:.1f}" '
                    f'x2="{W - R}" y2="{y100:.1f}"/>')

    chiusura = pos.get("2026-02")
    if chiusura is not None:
        x = sx(chiusura)
        corpo.append(f'<line class="evento" x1="{x:.1f}" y1="{T}" '
                     f'x2="{x:.1f}" y2="{H - B}"/>')
        corpo.append(f'<text class="evento-testo" x="{x - 6:.1f}" y="{T + 14}" '
                     f'text-anchor="end">chiusura di Hormuz</text>')

    svg = (intestazione(
        "Valore unitario all'import, gennaio 2024 uguale a 100",
        "Confronto fra il valore unitario doganale del greggio, degli oli "
        "lubrificanti e dell'elio importati. Dopo la chiusura di Hormuz il "
        "greggio sale con decisione, gli altri due no.")
        + assi(ymin, ymax, sy, etichette, sx, "gen 2024 = 100")
        + "".join(corpo))
    salva("valori-unitari.svg", svg)

    return {et: (s[0][1], s[-1][1], s[-1][0]) for et, s in ind.items()}


def elio_origine():
    """Da dove arriva l'elio extra-UE, e quanto pesa il Qatar."""
    # Si legge il dettaglio per origine e si tengono solo le celle dentro la
    # banda dichiarata: il file delle origini grezze contiene anche le
    # dichiarazioni olandesi di merce cinese a tre euro al chilo, che elio non
    # e' e che da sola varrebbe il settanta per cento del totale.
    righe = [r for r in leggi("elio_ue_valore_unitario_per_origine.csv")
             if r["fuori_banda"] == "no"]
    per_mese = {}
    for r in righe:
        m = r["mese"]
        if m < "2023-01":
            continue
        d = per_mese.setdefault(m, {})
        d[r["origine"]] = d.get(r["origine"], 0.0) + float(r["quantita_t"])

    provvisori = {r["mese"] for r in leggi("elio_ue_valore_unitario.csv")
                  if r["provvisorio"] == "si"}
    mesi = [m for m in sorted(per_mese) if m not in provvisori]

    totali = {m: sum(per_mese[m].values()) for m in mesi}
    quota_qa = [(m, 100 * per_mese[m].get("QA", 0) / totali[m])
                for m in mesi if totali[m] > 0]

    sx = scala(0, len(quota_qa) - 1, L, W - R)
    ymax = max(y for _, y in quota_qa) * 1.15
    sy = scala(0, ymax, H - B, T)

    etichette = []
    for i, (m, _) in enumerate(quota_qa):
        a, mm = m.split("-")
        if mm in ("01", "07"):
            etichette.append((i, f"{MESI[int(mm) - 1]} {a[2:]}"))

    barre = []
    larghezza = max(2.0, (W - R - L) / len(quota_qa) * 0.7)
    for i, (m, y) in enumerate(quota_qa):
        x = sx(i) - larghezza / 2
        alt = (H - B) - sy(y)
        cls = "barra-evidenza" if m >= "2026-03" else "barra"
        barre.append(f'<rect class="{cls}" x="{x:.1f}" y="{sy(y):.1f}" '
                     f'width="{larghezza:.1f}" height="{max(alt, 0):.1f}"/>')

    svg = (intestazione(
        "Quota del Qatar sull'elio importato da fuori Unione europea",
        "Percentuale delle tonnellate di elio extra-UE di origine qatarina, "
        "importate da Italia, Germania, Francia, Paesi Bassi e Spagna.")
        + assi(0, ymax, sy, etichette, sx, "% delle tonnellate")
        + "".join(barre))
    salva("elio-origine.svg", svg)


def chokepoint_confronto():
    """
    Quanto e' caduto ciascun chokepoint fra febbraio e maggio 2026.

    Serve a mostrare che quello di Hormuz non e' un calo fra tanti: e' fuori
    scala rispetto a tutti gli altri, che nello stesso periodo si muovono poco.
    """
    righe = leggi("chokepoint_transiti_mensili.csv")
    val = {}
    for r in righe:
        val.setdefault(r["nome"], {})[r["mese"]] = float(r["navi_giorno_media"])

    var = []
    for nome, s in val.items():
        prima = [s[m] for m in ("2025-12", "2026-01", "2026-02") if m in s]
        dopo = [s[m] for m in ("2026-03", "2026-04", "2026-05") if m in s]
        if len(prima) < 2 or len(dopo) < 2:
            continue
        p, d = sum(prima) / len(prima), sum(dopo) / len(dopo)
        if p < 3:
            continue                       # sotto le tre navi al giorno il rapporto e' rumore
        var.append((nome, 100 * (d - p) / p, p))
    var.sort(key=lambda x: x[1])

    n = len(var)
    alt_riga = 15
    h = T + n * alt_riga + B
    vmin = min(v for _, v, _ in var) * 1.05
    vmax = max(max(v for _, v, _ in var), 5) * 1.15
    sx = scala(vmin, vmax, 168, W - R)
    zero = sx(0)

    corpo = [f'<line class="griglia" x1="{zero:.1f}" y1="{T - 6}" '
             f'x2="{zero:.1f}" y2="{T + n * alt_riga:.1f}"/>']
    for i, (nome, v, _) in enumerate(var):
        y = T + i * alt_riga + alt_riga / 2
        x0, x1 = (sx(v), zero) if v < 0 else (zero, sx(v))
        cls = "barra-evidenza" if "Hormuz" in nome else "barra"
        corpo.append(f'<rect class="{cls}" x="{x0:.1f}" y="{y - 5:.1f}" '
                     f'width="{max(x1 - x0, 0.8):.1f}" height="9"/>')
        corpo.append(f'<text class="etichetta-riga" x="160" y="{y + 3.5:.1f}" '
                     f'text-anchor="end">{escape(nome)}</text>')
        corpo.append(f'<text class="valore-riga" x="{(x0 - 6) if v < 0 else (x1 + 6):.1f}" '
                     f'y="{y + 3.5:.1f}" text-anchor="{"end" if v < 0 else "start"}">'
                     f'{v:+.0f}%</text>')

    svg = (intestazione(
        "Variazione dei transiti nei chokepoint marittimi",
        "Confronto fra la media giornaliera di dicembre 2025 - febbraio 2026 "
        "e quella di marzo - maggio 2026 per ciascuno stretto monitorato.",
        altezza=h)
        + "".join(corpo))
    salva("chokepoint-confronto.svg", svg)


def dati_mappamondo():
    """Prepara per il mappamondo i chokepoint con il loro calo, in JSON compatto."""
    ana = leggi("chokepoint_anagrafica.csv")
    mens = leggi("chokepoint_transiti_mensili.csv")
    per_id = {}
    for r in mens:
        per_id.setdefault(r["id"], {})[r["mese"]] = float(r["navi_giorno_media"])

    out = []
    for r in ana:
        s = per_id.get(r["id"], {})
        prima = [s[m] for m in ("2025-12", "2026-01", "2026-02") if m in s]
        dopo = [s[m] for m in ("2026-03", "2026-04", "2026-05") if m in s]
        calo = None
        if len(prima) >= 2 and len(dopo) >= 2:
            p = sum(prima) / len(prima)
            if p >= 3:
                calo = round(100 * (sum(dopo) / len(dopo) - p) / p, 1)
        out.append({
            "id": r["id"], "nome": r["nome"],
            "lat": round(float(r["lat"]), 3), "lon": round(float(r["lon"]), 3),
            "navi": int(float(r["navi_anno"] or 0)),
            "calo": calo,
        })
    percorso = os.path.join(RADICE, "sito", "assets", "chokepoint.json")
    with open(percorso, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    print(f"  ../chokepoint.json  {os.path.getsize(percorso) / 1024:.1f} KB")


def pubblica_dati():
    """
    Copia lo snapshot dentro il sito, perche' ogni grafico deve avere il suo
    dato scaricabile accanto. Si copia invece di collegare con un link
    simbolico: il sito deve restare una cartella autonoma, servibile da
    qualunque server statico e archiviabile cosi' com'e'.
    """
    import shutil
    sorgente = os.path.join(RADICE, "dati", snapshot())
    destinazione = os.path.join(RADICE, "sito", "dati")
    if os.path.isdir(destinazione):
        shutil.rmtree(destinazione)
    shutil.copytree(sorgente, destinazione)
    peso = sum(os.path.getsize(os.path.join(destinazione, f))
               for f in os.listdir(destinazione))
    print(f"  sito/dati/  {len(os.listdir(destinazione))} file, {peso / 1024:.0f} KB")


def main():
    print(f"snapshot {snapshot()}\n")
    transiti_hormuz()
    cifre = valori_unitari_confronto()
    elio_origine()
    chokepoint_confronto()
    dati_mappamondo()
    pubblica_dati()

    print("\nvariazioni rispetto a gennaio 2024:")
    for et, (primo, ultimo, mese) in cifre.items():
        print(f"  {et:32} {ultimo:6.1f}  (al {mese})")


if __name__ == "__main__":
    main()
