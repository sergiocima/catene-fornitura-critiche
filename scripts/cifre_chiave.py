#!/usr/bin/env python3
"""
Stampa le cifre che nella pagina sono scritte a mano dentro il testo.

Serve a una cosa sola: quando la pipeline scarica dati nuovi, qualcuno deve
ricontrollare che le frasi che commentano quei numeri dicano ancora il vero.
Il testo d'autore non viene mai riscritto da uno script, quindi il controllo
e' umano, e questo elenco e' quello che l'umano deve confrontare con la pagina.

Il confronto e' sempre fra la media dei tre mesi precedenti la chiusura e
quella dei tre successivi: misurare da un mese preciso a un altro gonfia o
sgonfia il risultato a piacere.
"""

import csv
import os
import statistics

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRIMA = ("2025-12", "2026-01", "2026-02")
DOPO = ("2026-03", "2026-04", "2026-05")


def snapshot():
    with open(os.path.join(RADICE, "dati", "ULTIMO"), encoding="utf-8") as f:
        return f.read().strip()


def serie(file, codice):
    p = os.path.join(RADICE, "dati", snapshot(), file)
    with open(p, encoding="utf-8") as f:
        return {r["mese"]: (float(r["eur_per_kg"]), float(r["quantita_t"]))
                for r in csv.DictReader(f)
                if r["codice_cn8"] == codice and r["provvisorio"] == "no"}


def confronto(d):
    a = [d[m][0] for m in PRIMA if m in d]
    b = [d[m][0] for m in DOPO if m in d]
    if not a or not b:
        return None
    return statistics.mean(a), statistics.mean(b)


def main():
    print(f"Cifre citate nel testo, snapshot {snapshot()}")
    print("Confrontare con quanto scritto in sito/index.html prima di pubblicare.\n")

    print("Valori unitari all'import, media dic-feb contro media mar-mag")
    for nome, file, cod in (
        ("greggio", "greggio_italia_valore_unitario.csv", "27090090"),
        ("lubrificanti", "lubrificanti_italia_valore_unitario.csv", "LUBRIFICANTI"),
        ("elio", "elio_ue_valore_unitario.csv", "28042910"),
    ):
        d = serie(file, cod)
        c = confronto(d)
        if not c:
            print(f"  {nome:14} dati insufficienti")
            continue
        a, b = c
        print(f"  {nome:14} {a:8.3f} -> {b:8.3f} EUR/kg   {100 * (b / a - 1):+5.0f}%")

    lub = serie("lubrificanti_italia_valore_unitario.csv", "LUBRIFICANTI")
    if lub:
        ultimo = max(lub)
        print(f"\n  ultimo mese buono dei lubrificanti: {ultimo}, "
              f"{lub[ultimo][0]:.3f} EUR/kg su {lub[ultimo][1]:.0f} t")

    print("\nTransiti a Hormuz, media giornaliera per mese")
    p = os.path.join(RADICE, "dati", snapshot(), "hormuz_transiti_giornalieri.csv")
    per = {}
    with open(p, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["navi_totali"]:
                per.setdefault(r["data"][:7], []).append(float(r["navi_totali"]))
    storico = [v for m, vs in per.items() if m < "2026-01" for v in vs]
    print(f"  media 2019-2025: {statistics.mean(storico):.1f} navi al giorno")
    for m in sorted(per)[-8:]:
        print(f"  {m}: {statistics.mean(per[m]):5.1f}  ({len(per[m])} giorni)")


if __name__ == "__main__":
    main()
