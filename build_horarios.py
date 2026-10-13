#!/usr/bin/env python3
"""Gera horarios.json (Varziela <-> NorteShopping, Linha B) a partir do GTFS da Metro do Porto.

Uso:
  python build_horarios.py                 # descobre e descarrega o GTFS mais recente do site
  python build_horarios.py --zip ficheiro.zip   # usa um GTFS local

So usa a biblioteca standard do Python.
"""
import argparse, collections, csv, io, json, re, sys, urllib.request, zipfile

PAGE = "https://www.metrodoporto.pt/pages/337"
BASE = "https://www.metrodoporto.pt"
STOP_A = "Varziela"
STOP_B = "NorteShopping I Sete Bicas"
UA = {"User-Agent": "Mozilla/5.0 (horarios-metro-widget)"}


def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def find_gtfs_url():
    html = get(PAGE).decode("utf-8", "replace")
    m = re.search(r'href="([^"]*google_transit[^"]*\.zip)"', html, re.I)
    if not m:
        sys.exit("Nao encontrei o link do GTFS em " + PAGE)
    href = m.group(1)
    return href if href.startswith("http") else BASE + href


def table(z, name):
    with z.open(name) as fh:
        return list(csv.DictReader(io.TextIOWrapper(fh, encoding="utf-8-sig")))


def mins(t):
    h, m, _ = t.strip().split(":")
    return int(h) * 60 + int(m)


def build(zbytes, source):
    z = zipfile.ZipFile(io.BytesIO(zbytes))
    stops = {s["stop_name"].strip(): s["stop_id"] for s in table(z, "stops.txt")}
    if STOP_A not in stops or STOP_B not in stops:
        sys.exit("Paragens nao encontradas no GTFS: %s / %s" % (STOP_A, STOP_B))
    A, B = stops[STOP_A], stops[STOP_B]
    trips = {t["trip_id"]: t for t in table(z, "trips.txt")}
    seen = collections.defaultdict(dict)
    for r in table(z, "stop_times.txt"):
        if r["stop_id"] in (A, B):
            seen[r["trip_id"]][r["stop_id"]] = (int(r["stop_sequence"]), r["departure_time"])

    cal = table(z, "calendar.txt")
    kind = {}  # service_id -> util / sabado / domingo_feriado
    for c in cal:
        if c["saturday"] == "1":
            kind[c["service_id"]] = "sabado"
        elif c["sunday"] == "1":
            kind[c["service_id"]] = "domingo_feriado"
        else:
            kind[c["service_id"]] = "util"

    res = {"varziela_norteshopping": collections.defaultdict(list),
           "norteshopping_varziela": collections.defaultdict(list)}
    for tid, d in seen.items():
        if A in d and B in d and tid in trips:
            t = trips[tid]
            k = kind.get(t["service_id"])
            if not k:
                continue
            sa, sb = d[A], d[B]
            key = "varziela_norteshopping" if sa[0] < sb[0] else "norteshopping_varziela"
            dep, arr = (sa[1], sb[1]) if sa[0] < sb[0] else (sb[1], sa[1])
            res[key][k].append([mins(dep), mins(arr), "x" if t["route_id"].lower().startswith("bexp") else ""])

    nomes = {"varziela_norteshopping": "Varziela -> NorteShopping (sentido Porto)",
             "norteshopping_varziela": "NorteShopping -> Varziela (sentido Povoa)"}
    out = {"fonte": source,
           "valido_de": min(c["start_date"] for c in cal),
           "valido_ate": max(c["end_date"] for c in cal),
           "feriados_como_domingo": [], "sentidos": {}}
    out["valido_de"] = "%s-%s-%s" % (out["valido_de"][:4], out["valido_de"][4:6], out["valido_de"][6:])
    out["valido_ate"] = "%s-%s-%s" % (out["valido_ate"][:4], out["valido_ate"][4:6], out["valido_ate"][6:])

    if "calendar_dates.txt" in z.namelist():
        for cd in table(z, "calendar_dates.txt"):
            if cd["exception_type"] == "1" and kind.get(cd["service_id"]) == "domingo_feriado":
                dt = cd["date"]
                iso = "%s-%s-%s" % (dt[:4], dt[4:6], dt[6:])
                if iso not in out["feriados_como_domingo"]:
                    out["feriados_como_domingo"].append(iso)
        out["feriados_como_domingo"].sort()

    for key, byk in res.items():
        out["sentidos"][key] = {"nome": nomes[key]}
        for k in ("util", "sabado", "domingo_feriado"):
            out["sentidos"][key][k] = sorted(byk.get(k, []))
            if not out["sentidos"][key][k]:
                sys.exit("Sem horarios para %s/%s: algo mudou no GTFS" % (key, k))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip")
    ap.add_argument("--out", default="horarios.json")
    a = ap.parse_args()
    if a.zip:
        data, src = open(a.zip, "rb").read(), a.zip.split("/")[-1]
    else:
        url = find_gtfs_url()
        data, src = get(url), url.split("/")[-1]
    out = build(data, src)
    with open(a.out, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, separators=(",", ":"))
    print("OK", a.out, src, out["valido_de"], "->", out["valido_ate"])


if __name__ == "__main__":
    main()
