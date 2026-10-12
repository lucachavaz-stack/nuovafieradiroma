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
    def add(n, s, e, u):
        n = html.unescape(n).replace("\\/", "/").strip()
        if not n or (n, s) in seen or dt.date.fromisoformat(e) < TODAY:
            return
        seen.add((n, s))
        out.append({"n": n, "s": s, "e": e, "k": "fiera", "i": "hi" if n.lower().startswith(HIGH) else "me", "u": u, "src": "fieraroma.it"})
    api = "https://www.fieraroma.it/wp-json/tribe/events/v1/events?per_page=50&start_date=" + TODAY.isoformat()
    try:
        for ev in json.loads(get(api) or "{}").get("events", []):
            add(ev["title"], ev["start_date"][:10], ev["end_date"][:10], ev.get("url", "https://www.fieraroma.it/en/eventi/"))
    except Exception as e:
        print("API ERR", e)
    if not out:
        for u in ("https://www.fieraroma.it/en/eventi/", "https://www.fieraroma.it/eventi/photo/"):
            t = get(u)
            print("pagina", u, len(t), "caratteri")
            rx = r'"name":"([^"]+)"[^{}]*?"startDate":"(\d{4}-\d{2}-\d{2})[^"]*"[^{}]*?"endDate":"(\d{4}-\d{2}-\d{2})'
            for n, s_, e in re.findall(rx, t):
                add(n, s_, e, u)
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

FEEDS = ["https://www.concorsando.it/blog/feed/", "https://simoneconcorsi.it/feed/", "https://www.ticonsiglio.com/feed/",
         "https://corriereuniv.it/feed/", "https://www.newsistruzione.it/feed/", "https://www.leggioggi.it/feed/",
         "https://lentepubblica.it/feed/", "https://www.concorsipubblici.com/feed/"]
CE = "{http://purl.org/rss/1.0/modules/content/}encoded"

def leads():
    out, seen = [], set()
    urls = list(FEEDS)
    for q in QUERIES:
        urls.append("https://news.google.com/rss/search?" + urllib.parse.urlencode({"q": q + " when:30d", "hl": "it", "gl": "IT", "ceid": "IT:it"}))
    for url in urls:
        try:
            items = ET.fromstring(get(url)).findall(".//item")
        except ET.ParseError:
            items = []
        print(len(items), "articoli da", url[:60])
        for it in items[:25]:
            title, link = it.findtext("title", ""), it.findtext("link", "")
            if link in seen:
                continue
            raw = " ".join([title, it.findtext("description", ""), it.findtext(CE, "")])
            full = html.unescape(re.sub(r"<[^>]+>", " ", raw))
            low = full.lower()
            if "fiera di roma" not in low and "fiera roma" not in low:
                continue
            seen.add(link)
            alld = []
            for m in re.finditer(r"fiera (?:di )?roma", low):
                alld += dates_in(full[max(0, m.start() - 400): m.end() + 400])
            ds = sorted({d for d in alld if d[1] >= TODAY})
            if alld and not ds:
                continue
            if re.search(r"esiti|graduatoria|punteggi|risultati|ammessi", title.lower()):
                continue
            lead = {"t": html.unescape(title), "u": link, "k": "concorso" if re.search(r"concors|selezion|test|prov", low) else "evento"}
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
