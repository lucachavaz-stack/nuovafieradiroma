#!/usr/bin/env python3
"""Aggiorna data.json con gli eventi della Nuova Fiera di Roma. Solo libreria standard."""
import json, re, html, urllib.request, urllib.parse, datetime as dt
import xml.etree.ElementTree as ET

UA = {"User-Agent": "Mozilla/5.0 (compatible; FieraRomaBot/1.0)"}
TODAY = dt.date.today()
MESI = {m: i + 1 for i, m in enumerate("gennaio febbraio marzo aprile maggio giugno luglio agosto settembre ottobre novembre dicembre".split())}
HIGH = ("romics", "motodays", "abilmente", "hyrox", "casaidea")
QUERIES = [
    '"Nuova Fiera di Roma" prova scritta concorso',
    '"Fiera di Roma" preselezione concorso',
    '"Fiera di Roma" test ammissione università',
    '"Fiera Roma" via Portuense prove concorsuali',
]

def get(url, timeout=25):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
            return r.read().decode("utf-8", "ignore")
    except Exception as e:
        print("ERR", url[:80], e)
        return ""

def fiere():
    out, seen = [], set()
    for u in ("https://www.fieraroma.it/en/eventi/", "https://www.fieraroma.it/eventi/photo/", "https://www.fieraroma.it/luogo/fiera-di-roma/"):
        t = get(u)
        for n, s, e in re.findall(r'"name":"([^"]+)","startDate":"(\d{4}-\d{2}-\d{2})[^"]*","endDate":"(\d{4}-\d{2}-\d{2})', t):
            n = html.unescape(n).replace("\\/", "/")
            if (n, s) in seen or dt.date.fromisoformat(e) < TODAY:
                continue
            seen.add((n, s))
            out.append({"n": n, "s": s, "e": e, "k": "fiera", "i": "hi" if n.lower().startswith(HIGH) else "me",
                        "u": "https://www.fieraroma.it/en/eventi/", "src": "fieraroma.it"})
    return out

def dates_in(text):
    res = []
    rx = r"((?:\d{1,2}\s*(?:,|e|-|–|al)\s*)*\d{1,2})\s+(%s)\s+(\d{4})" % "|".join(MESI)
    for run, mese, anno in re.findall(rx, text.lower()):
        days = [int(x) for x in re.findall(r"\d+", run)]
        try:
            res.append((dt.date(int(anno), MESI[mese], min(days)), dt.date(int(anno), MESI[mese], max(days))))
        except ValueError:
            pass
    return res

def leads():
    out, seen = [], set()
    for q in QUERIES:
        url = "https://news.google.com/rss/search?" + urllib.parse.urlencode({"q": q + " when:30d", "hl": "it", "gl": "IT", "ceid": "IT:it"})
        try:
            items = ET.fromstring(get(url)).findall(".//item")
        except ET.ParseError:
            continue
        for it in items[:12]:
            title, link = it.findtext("title", ""), it.findtext("link", "")
            desc = re.sub(r"<[^>]+>", " ", html.unescape(it.findtext("description", "")))
            if link in seen:
                continue
            seen.add(link)
            body = re.sub(r"<[^>]+>", " ", get(link, 15)) if link else ""
            full = html.unescape(" ".join([title, desc, body]))
            low = full.lower()
            if "fiera di roma" not in low and "fiera roma" not in low:
                continue
            ds = []
            for m in re.finditer(r"fiera (?:di )?roma", low):
                ds += dates_in(full[max(0, m.start() - 400): m.end() + 400])
            ds = sorted({d for d in ds if d[1] >= TODAY})
            lead = {"t": title, "u": link, "k": "concorso" if re.search(r"concors|selezion|test|prov", low) else "evento"}
            if ds:
                lead["s"], lead["e"] = ds[0][0].isoformat(), max(d[1] for d in ds).isoformat()
            out.append(lead)
    return out

if __name__ == "__main__":
    try:
        manual = json.load(open("manual.json"))
    except Exception:
        manual = []
    data = {"updated": dt.datetime.now(dt.timezone.utc).isoformat(timespec="minutes"),
            "events": fiere() + manual, "leads": leads()}
    json.dump(data, open("data.json", "w"), ensure_ascii=False, indent=1)
    print(len(data["events"]), "eventi,", len(data["leads"]), "segnalazioni")
