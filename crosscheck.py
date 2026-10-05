#!/usr/bin/env python3
"""
crosscheck.py — METODA B de verificare a AI Stack Map: cod automat, pe TOȚI tickerii,
cu alte surse și alt traseu de date decât update_stack_map.py (nu importă nimic din el).

Surse de control (fără cont, fără cheie API):
  - Prețuri, %, market cap, volum, P/E: TradingView scanner (scanner.tradingview.com) — nu Yahoo.
  - Venituri și profit net trimestriale: SEC EDGAR XBRL (data.sec.gov) — raportările oficiale 10-Q/10-K.
Verificări interne (nu depind de nicio sursă):
  - JS-ul paginii e valid; LATEST e identic cu ultima versiune; contoarele straturilor = rândurile;
  - fiecare rând are linie în EARNINGS și invers; culoarea % se potrivește cu semnul;
  - market cap / preț (acțiuni) stabil față de versiunea anterioară;
  - nicio dată de earnings trecută afișată ca viitoare; niciun 'confirmat' fără sursă oficială;
  - datele trimestriale (FIN) recente și plauzibile.

Scrie crosscheck-report.md (raportul ultimei rulări) și adaugă un rând în crosscheck-history.csv.
Nu modifică niciodată fișierele HTML.
"""
import csv, datetime as dt, glob, gzip, json, os, re, subprocess, sys, tempfile, time
import urllib.request

UA = "AI Stack Map crosscheck stack-map-bot@users.noreply.github.com"
HERE = os.path.dirname(os.path.abspath(__file__))
NON_STOCK = {"NDX", "VIX", "SPY", "QQQ", "IWM", "SOXX", "IGV", "TLT", "GLD", "UUP", "SMH", "XLK",
             "IBIT", "HYG", "DIA", "WTI", "BRENT"}
TV_NON_STOCK = {"VIX": ["TVC:VIX", "CBOE:VIX"], "NDX": ["NASDAQ:NDX"], "WTI": ["NYMEX:CL1!", "TVC:USOIL"],
                "BRENT": ["ICEEUR:BRN1!", "ICE:BRN1!", "TVC:UKOIL"]}
H24 = {"WTI", "BRENT", "VIX"}      # se tranzacționează aproape non-stop → prețul depinde de momentul citirii

# toleranțe → (eroare, diferență)
TOL = {"price": (1.0, 0.3), "chg_pp": (0.30, 0.10), "mcap": (8.0, 3.0), "vol": (40.0, 15.0),
       "pe": (1e9, 15.0),            # P/E: definiții diferite între surse → niciodată „eroare”, doar diferență
       "mcap_adr": (1e9, 3.0),       # ADR: prima față de bursa locală → doar diferență
       "price_24h": (3.0, 1.0), "chg_24h": (2.0, 0.5),
       "fin": (2.0, 0.5), "shares": (5.0, 2.0)}
# SEC cere un email real de contact în User-Agent. Se ține în secretul GitHub SEC_USER_AGENT (nu în cod — repo-ul e public).
SEC_UAS = ([os.environ["SEC_USER_AGENT"]] if os.environ.get("SEC_USER_AGENT") else []) + [
           "AI Stack Map crosscheck stack-map-bot@users.noreply.github.com",
           "AIStackMap/1.0 (+https://github.com/xGABRIELxEUGENx/ai-stack-map; stack-map-bot@users.noreply.github.com)"]


# ------------------------------------------------------------------ rețea
def http(url, data=None, headers=None, tries=3):
    h = {"User-Agent": UA, "Accept": "application/json,*/*"}
    h.update(headers or {})
    body = json.dumps(data).encode() if data is not None else None
    if body: h["Content-Type"] = "application/json"
    err = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, data=body, headers=h)
            with urllib.request.urlopen(req, timeout=30) as r:
                raw = r.read()
                if r.headers.get("Content-Encoding") == "gzip": raw = gzip.decompress(raw)
                return json.loads(raw.decode("utf-8"))
        except Exception as e:
            err = e
            time.sleep(1.5 * (i + 1))
    raise RuntimeError(f"{url}: {err}")


# ------------------------------------------------------------------ parsare independentă a paginii
def js_args(s, i):
    """Citește argumentele unui apel JS începând după '(' — șiruri '…', liste […], numere."""
    out, cur, depth, q = [], "", 0, None
    while i < len(s):
        c = s[i]
        if q:
            if c == "\\": cur += s[i + 1]; i += 2; continue
            if c == q: q = None
            else: cur += c
        elif c in "'\"": q = c
        elif c == "[": depth += 1; cur += c
        elif c == "]": depth -= 1; cur += c
        elif c == "," and depth == 0: out.append(cur.strip()); cur = ""
        elif c == ")" and depth == 0: out.append(cur.strip()); return out
        else: cur += c
        i += 1
    return out

def num(s):
    s = (s or "").replace("$", "").replace(",", "").replace("%", "").replace("−", "-").strip()
    if s in ("", "—", "-"): return None
    mult = {"T": 1e12, "B": 1e9, "M": 1e6, "K": 1e3}.get(s[-1:], 1)
    try: return float(s[:-1] if mult != 1 else s) * mult
    except ValueError: return None

def parse_page(html):
    rows = []
    for m in re.finditer(r'<div class="ticker-row" onclick="openDetails\(', html):
        a = js_args(html, m.end())
        tail = html[m.end(): m.end() + 3000]
        badge = re.search(r'price-badge">([^<]*)</span><span class="change-badge" style="color:([^;]*);">([^<]*)<', tail)
        layer = re.findall(r'<div class="layer-box" id="(box-[^"]+)">', html[:m.start()])
        rows.append({"t": a[0], "layer": layer[-1] if layer else "", "price": num(a[2]), "chg": num(a[3]), "col": a[4], "mcap": num(a[5]),
                     "vol": num(a[6]), "pe": num(a[7]), "pos": m.start(),
                     "badge": badge.groups() if badge else None})
    layers = []
    boxes = [(m.start(), m.group(1)) for m in re.finditer(r'<div class="layer-box" id="(box-[^"]+)">', html)]
    for k, (pos, bid) in enumerate(boxes):
        end = boxes[k + 1][0] if k + 1 < len(boxes) else len(html)
        seg = html[pos:end]
        cnt = re.search(r'class="layer-count">\((\d+)\)', seg)
        n = len(re.findall(r'<div class="ticker-row"', seg))
        if cnt: layers.append((bid, int(cnt.group(1)), n))
    earn = {m.group(1): dict(zip(("date", "session", "status", "time", "src"), m.groups()[1:]))
            for m in re.finditer(r"'([A-Z.]+)': \{ date:'([^']*)', session:'([^']*)', status:'([^']*)', time:'([^']*)', src:'((?:[^'\\]|\\.)*)' \}", html)}
    fm = re.search(r"// FIN-START[^\n]*\n\s*const FIN = (\{.*?\});\s*\n\s*// FIN-END", html, re.S)
    fin = json.loads(fm.group(1)) if fm else None
    tvex = {}
    tm = re.search(r"const TV_EX = \{(.*?)\};", html, re.S)
    if tm:
        for ex, lst in re.findall(r"(\w+): '([^']*)'", tm.group(1)):
            for t in lst.split(): tvex[t] = ex
    irl = set(re.findall(r"^\s*'([A-Z.]+)':'https?://", html, re.M))
    return rows, layers, earn, fin, tvex, irl


# ------------------------------------------------------------------ surse de control
def tv_quotes(tickers, tvex):
    """Întoarce ({ticker: cotație}, {ticker: simbolul TV care a mers}). Bursa din TV_EX are prioritate;
    dacă nu răspunde, se încearcă celelalte burse (și se raportează nepotrivirea)."""
    cands, back = {}, {}
    for t in dict.fromkeys(tickers):
        if t in TV_NON_STOCK: c = TV_NON_STOCK[t]
        else:
            first = [f"{tvex[t]}:{t}"] if t in tvex else []
            c = first + [f"{ex}:{t}" for ex in ("NASDAQ", "NYSE", "AMEX", "CBOE") if f"{ex}:{t}" not in first]
        cands[t] = c
        for s in c: back[s] = t
    cols = ["close", "change", "market_cap_basic", "volume", "price_earnings_ttm"]
    got = {}
    for market in ("america", "futures", "cfd", "global"):
        need = [s for s, t in back.items() if s not in got and not any(x in got for x in cands[t])]
        if not need: break
        try:
            r = http(f"https://scanner.tradingview.com/{market}/scan",
                     {"symbols": {"tickers": need, "query": {"types": []}}, "columns": cols},
                     {"Origin": "https://www.tradingview.com", "Referer": "https://www.tradingview.com/"})
        except Exception as e:
            print(f"  ! TradingView {market}: {e}"); continue
        for row in r.get("data", []):
            if row.get("s") in back and row.get("d") and row["d"][0] is not None:
                got[row["s"]] = dict(zip(cols, row["d"]))
    out, used = {}, {}
    for t, c in cands.items():
        for s in c:                                   # primul candidat (în ordinea priorității) care a răspuns
            if s in got: out[t], used[t] = got[s], s; break
    return out, used

SEC_REV = ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax", "SalesRevenueNet",
           "RevenueFromContractWithCustomerIncludingAssessedTax", "RevenuesNetOfInterestExpense"]

def sec_quarters(cik):
    """{tag: {end_date: valoare_trimestrială_USD}} din XBRL; Q4 = an − 9 luni când lipsește."""
    j = http(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json", headers={"Accept-Encoding": "gzip"})
    g = j.get("facts", {}).get("us-gaap", {})
    def series(tag):
        items = (g.get(tag, {}).get("units", {}) or {}).get("USD", [])
        q, ann, ytd9 = {}, {}, {}
        for it in items:
            if "start" not in it: continue
            s, e = dt.date.fromisoformat(it["start"]), dt.date.fromisoformat(it["end"])
            d = (e - s).days
            if 80 <= d <= 100: q[e] = it["val"]
            elif 350 <= d <= 380: ann[(s, e)] = it["val"]
            elif 260 <= d <= 285: ytd9[(s, e)] = it["val"]
        for (s, e), v in ann.items():
            if e not in q:
                nine = [val for (s9, e9), val in ytd9.items() if s9 == s and 0 < (e - e9).days < 110]
                if nine: q[e] = v - nine[0]
        return q
    rev = {}
    for tag in SEC_REV:                       # primul tag care are date recente câștigă per trimestru
        for e, v in series(tag).items():
            rev.setdefault(e, v)
    return rev, series("NetIncomeLoss")

def nearest(d, series, days=12):
    best = None
    for e, v in series.items():
        k = abs((e - d).days)
        if k <= days and (best is None or k < best[0]): best = (k, e, v)
    return best


# ------------------------------------------------------------------ verificare
class Report:
    def __init__(self): self.items, self.checked = [], 0
    def ok(self, n=1): self.checked += n
    def add(self, level, t, field, file_v, ctrl_v, src, note=""):
        self.checked += 1
        self.items.append((level, t, field, file_v, ctrl_v, src, note))

def pdiff(a, b):
    return abs(a - b) / abs(b) * 100 if b else (0 if a == b else 100)

def grade(r, kind, t, field, fv, cv, src, note=""):
    if fv is None or cv is None: return
    pp = kind.startswith("chg")                      # variația % se compară în puncte procentuale
    d = abs(fv - cv) if pp else pdiff(fv, cv)
    err, warn = TOL[kind]
    unit = "pp" if pp else "%"
    if d >= err: r.add("EROARE", t, field, fv, cv, src, f"{d:.2f}{unit} {note}".strip())
    elif d >= warn: r.add("DIFERENȚĂ", t, field, fv, cv, src, f"{d:.2f}{unit} {note}".strip())
    else: r.ok()

def src_tv_name(): return "TradingView scanner"

def latest_versions():
    files = []
    for f in glob.glob(os.path.join(HERE, "ai-stack-map-mobile-*.html")):
        m = re.search(r"-(\d+)\.html$", f)
        if m: files.append((int(m.group(1)), f))
    return sorted(files)

def main():
    today = dt.datetime.utcnow().date()
    vers = latest_versions()
    n, path = vers[-1]
    html = open(path, encoding="utf-8").read()
    rows, layers, earn, fin, tvex, irl = parse_page(html)
    r, notes = Report(), []
    tick = [x["t"] for x in rows]
    stocks = [t for t in tick if t not in NON_STOCK]

    # ---- 1. integritate internă
    latest = os.path.join(HERE, "ai-stack-map-LATEST.html")
    if os.path.exists(latest) and open(latest, encoding="utf-8").read() == html: r.ok()
    else: r.add("EROARE", "—", "LATEST", "diferit", f"v{n}", "intern", "ai-stack-map-LATEST.html nu e identic cu ultima versiune")
    js = "\n".join(re.findall(r"<script>(.*?)</script>", html, re.S))
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as fh: fh.write(js)
    try:
        p = subprocess.run(["node", "--check", fh.name], capture_output=True, text=True, timeout=60)
        if p.returncode == 0: r.ok()
        else: r.add("EROARE", "—", "JavaScript", "invalid", "valid", "node --check", p.stderr.strip()[:200])
    except FileNotFoundError:
        notes.append("node indisponibil — JS neverificat")
    for bid, cnt, nrows in layers:
        if cnt == nrows: r.ok()
        else: r.add("EROARE", bid, "contor strat", cnt, nrows, "intern", "contorul (N) ≠ numărul de rânduri")
    pairs = [(x["t"], x["layer"]) for x in rows]          # același ticker în straturi diferite e permis (ex. CEG: AI L3 + Energy L2)
    for t, lay in sorted({p for p in pairs if pairs.count(p) > 1}):
        r.add("EROARE", t, "rând duplicat în același strat", pairs.count((t, lay)), 1, "intern", lay)
    for x in rows:
        t = x["t"]
        if t not in earn: r.add("EROARE", t, "EARNINGS", "lipsă", "linie", "intern")
        else: r.ok()
        if t not in NON_STOCK and t not in irl: r.add("DIFERENȚĂ", t, "IR_LINKS", "lipsă", "link oficial", "intern")
        if x["price"] is None or x["price"] <= 0: r.add("EROARE", t, "preț", x["price"], "> 0", "intern")
        if x["chg"] is not None:
            want = "#ef4444" if x["chg"] < 0 else "#10b981"
            if x["col"].lower() == want: r.ok()
            else: r.add("EROARE", t, "culoare %", x["col"], want, "intern")
        if x["badge"]:
            bp, bc, bchg = x["badge"]
            if num(bp) == x["price"] and num(bchg) == x["chg"]: r.ok()
            else: r.add("EROARE", t, "badge ≠ drawer", f"{bp} {bchg}", f"{x['price']} {x['chg']}", "intern")
    for t, e in earn.items():
        if t not in tick: r.add("DIFERENȚĂ", t, "EARNINGS fără rând", e["date"], "—", "intern")
        if e["status"] in ("n/a", "delistat"): continue
        if e["date"]:
            d = dt.date.fromisoformat(e["date"])
            if d < today - dt.timedelta(days=3):
                r.add("EROARE", t, "earnings trecut", e["date"], f"după {today}", "intern", "raportul a trecut, data nu s-a mutat la următorul")
            else: r.ok()
        if e["status"] == "confirmat":
            if not e["src"] or e["src"].lower().startswith("yahoo"):
                r.add("EROARE", t, "confirmat fără sursă oficială", e["src"] or "—", "comunicat oficial", "intern")
            else: r.ok()
    # acțiuni = mcap/preț stabile față de versiunea anterioară
    if len(vers) > 1:
        prev = {x["t"]: x for x in parse_page(open(vers[-2][1], encoding="utf-8").read())[0]}
        for x in rows:
            p0 = prev.get(x["t"])
            if p0 and x["mcap"] and p0["mcap"] and x["price"] and p0["price"]:
                grade(r, "shares", x["t"], "acțiuni (mcap/preț)", x["mcap"] / x["price"], p0["mcap"] / p0["price"],
                      f"v{vers[-2][0]}", "număr de acțiuni schimbat brusc")
    # FIN — plauzibilitate
    if fin is None: r.add("EROARE", "—", "FIN", "lipsă", "bloc", "intern")
    else:
        for t in stocks:
            f = fin.get(t)
            if not f: r.add("DIFERENȚĂ", t, "FIN", "lipsă", "date trimestriale", "intern"); continue
            age = (today - dt.date.fromisoformat(f.get("upd", "2000-01-01"))).days
            if age > 10: r.add("DIFERENȚĂ", t, "FIN vechime", f"{age} zile", "≤ 10", "intern")
            else: r.ok()
            q = f.get("q") or []
            if [x[0] for x in q] != sorted(x[0] for x in q): r.add("EROARE", t, "FIN ordine", "nesortat", "cronologic", "intern")
            for d, ses, pct in f.get("rx") or []:
                if abs(pct) > 60: r.add("DIFERENȚĂ", t, f"reacție {d}", f"{pct}%", "< 60%", "intern", "mișcare extremă — verifică")

    # ---- 2. TradingView: preț, %, market cap, volum, P/E
    tvq, used = tv_quotes(tick, tvex)
    for t, s in used.items():
        if t in tvex and s != f"{tvex[t]}:{t}":
            r.add("EROARE", t, "bursa în TV_EX", tvex[t], s.split(":")[0], src_tv_name(),
                  "widget-ul live din pagină caută pe bursa greșită")
    src_tv = "TradingView scanner"
    if not tvq: notes.append("TradingView scanner indisponibil — prețurile nu au fost verificate extern")
    for x in rows:
        q, t = tvq.get(x["t"]), x["t"]
        if not q:
            if tvq: notes.append(f"{t}: fără cotație TradingView")
            continue
        h24 = t in H24
        note24 = "(se tranzacționează ~24h; momentul citirii diferă)" if h24 else ""
        grade(r, "price_24h" if h24 else "price", t, "preț", x["price"], q["close"], src_tv, note24)
        grade(r, "chg_24h" if h24 else "chg_pp", t, "% zi", x["chg"], q["change"], src_tv, note24)
        if t not in NON_STOCK:
            adr = ((fin or {}).get(t) or {}).get("cur", "USD") != "USD"
            grade(r, "mcap_adr" if adr else "mcap", t, "market cap", x["mcap"], q["market_cap_basic"], src_tv,
                  "(ADR: prima față de bursa locală)" if adr else "")
            grade(r, "vol", t, "volum", x["vol"], q["volume"], src_tv, "(metode de agregare diferite)")
            if x["pe"] and q["price_earnings_ttm"] and q["price_earnings_ttm"] > 0:
                grade(r, "pe", t, "P/E", x["pe"], q["price_earnings_ttm"], src_tv, "(TTM calculat diferit)")

    # ---- 3. SEC EDGAR: venituri și profit net pe trimestru
    global UA
    cmap, sec_err = {}, []
    for ua in SEC_UAS:
        UA = ua
        try:
            cmap = {v["ticker"].upper(): int(v["cik_str"]) for v in
                    http("https://www.sec.gov/files/company_tickers.json", headers={"Accept-Encoding": "gzip"}).values()}
            notes.append("SEC EDGAR acceptat" + (" (contact din secretul SEC_USER_AGENT)" if ua == os.environ.get("SEC_USER_AGENT") else f" cu User-Agent: {ua}"))
            break
        except Exception as e:
            sec_err.append(str(e)[-60:])
    if not cmap:                                   # a doua sursă pentru lista ticker → CIK
        for ua in SEC_UAS:
            UA = ua
            try:
                raw = urllib.request.urlopen(urllib.request.Request("https://www.sec.gov/include/ticker.txt",
                                             headers={"User-Agent": ua}), timeout=30).read().decode()
                cmap = {a.upper(): int(b) for a, b in (ln.split("\t") for ln in raw.splitlines() if "\t" in ln)}
                notes.append("SEC: lista CIK din ticker.txt"); break
            except Exception as e:
                sec_err.append("ticker.txt " + str(e)[-40:])
    if not cmap:                                   # diagnostic: e blocat doar www.sec.gov sau și data.sec.gov?
        diag = []
        for ua in SEC_UAS:
            UA = ua
            try:
                http("https://data.sec.gov/api/xbrl/companyfacts/CIK0001045810.json", headers={"Accept-Encoding": "gzip"}, tries=1)
                diag.append(f"data.sec.gov OK cu UA #{SEC_UAS.index(ua) + 1}")
            except Exception as e:
                diag.append(f"data.sec.gov UA #{SEC_UAS.index(ua) + 1}: {str(e)[-30:]}")
        secret = "secret SEC_USER_AGENT prezent" if os.environ.get("SEC_USER_AGENT") else "secret SEC_USER_AGENT LIPSĂ"
        fmt = ""
        if os.environ.get("SEC_USER_AGENT"):
            v = os.environ["SEC_USER_AGENT"]
            quoted = v.strip()[:1] in ("'", '"')
            fmt = (f", format: {'conține @' if '@' in v else 'FĂRĂ @'}, "
                   f"{'are nume + spațiu' if ' ' in v.strip() else 'FĂRĂ spațiu'}, ghilimele: {'DA' if quoted else 'nu'}")
        notes.append(f"SEC EDGAR indisponibil — financiarele neverificate ({secret}{fmt}; {'; '.join(sec_err)}; {'; '.join(diag)})")
    sec_ok, sec_skip = 0, []
    for t in stocks:
        f = (fin or {}).get(t)
        if not f or not f.get("q") or t not in cmap: sec_skip.append(t); continue
        if f.get("cur", "USD") != "USD": sec_skip.append(t); continue
        try:
            rev_s, ni_s = sec_quarters(cmap[t]); time.sleep(0.15)   # limita SEC: max 10 cereri/secundă
        except Exception as e:
            sec_skip.append(t); continue
        hit = False
        for d, rev, ni in f["q"][-3:]:
            dd = dt.date.fromisoformat(d)
            a = nearest(dd, rev_s)
            if a and rev is not None:
                grade(r, "fin", t, f"venituri {d}", rev, a[2] / 1e6, f"SEC 10-Q/10-K ({a[1]})"); hit = True
            b = nearest(dd, ni_s)
            if b and ni is not None:
                grade(r, "fin", t, f"profit net {d}", ni, b[2] / 1e6, f"SEC 10-Q/10-K ({b[1]})"); hit = True
        if hit: sec_ok += 1
        else: sec_skip.append(t)

    # ---- raport
    errs = [i for i in r.items if i[0] == "EROARE"]
    diffs = [i for i in r.items if i[0] == "DIFERENȚĂ"]
    okn = r.checked - len(r.items)
    stamp = dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    L = [f"# Cross-check metoda B — v{n}", "",
         f"Rulat: {stamp} · fișier: `{os.path.basename(path)}` · tickeri: {len(rows)}", "",
         f"**{r.checked} verificări · {okn} OK · {len(errs)} erori · {len(diffs)} diferențe**", "",
         f"Surse: TradingView scanner ({len(tvq)}/{len(rows)} tickeri cotați) · SEC EDGAR XBRL ({sec_ok} companii verificate; "
         f"fără date SEC trimestriale: {len(sec_skip)} — ADR/IFRS, ETF sau tag-uri lipsă)", ""]
    for title, lst in (("Erori", errs), ("Diferențe", diffs)):
        L += [f"## {title} ({len(lst)})", ""]
        if lst:
            L += ["| Ticker | Câmp | Fișier | Control | Sursă | Notă |", "|---|---|---|---|---|---|"]
            fmt = lambda v: f"{v:,.4g}" if isinstance(v, float) else str(v)
            L += [f"| {t} | {fld} | {fmt(fv)} | {fmt(cv)} | {s} | {nt} |" for _, t, fld, fv, cv, s, nt in lst]
        else:
            L.append("—")
        L.append("")
    if notes: L += ["## Note", ""] + [f"- {x}" for x in sorted(set(notes))] + [""]
    if sec_skip and cmap: L += [f"Fără verificare SEC: {', '.join(sorted(set(sec_skip)))}", ""]
    open(os.path.join(HERE, "crosscheck-report.md"), "w", encoding="utf-8").write("\n".join(L))
    hist = os.path.join(HERE, "crosscheck-history.csv")
    new = not os.path.exists(hist)
    with open(hist, "a", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        if new: w.writerow(["data_utc", "versiune", "verificari", "ok", "erori", "diferente", "tv_cotati", "sec_companii"])
        w.writerow([stamp, n, r.checked, okn, len(errs), len(diffs), len(tvq), sec_ok])
    print("\n".join(L[:8]))


if __name__ == "__main__":
    main()
