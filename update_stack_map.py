#!/usr/bin/env python3
"""
update_stack_map.py — actualizează singur AI Stack Map, fără cont, fără cheie API, fără Claude.

Ce face la fiecare rulare:
  1. Găsește ultima versiune ai-stack-map-mobile-N.html din folderul scriptului (sau --html).
  2. Pentru fiecare ticker din planșe citește datele publice Yahoo Finance (prin biblioteca yfinance):
     preț, variație %, market cap, volum, P/E, următoarea dată de earnings + dacă e estimată.
     Venituri și profit net trimestrial, fără Yahoo:
       - rapoartele depuse la SEC (10-Q/10-K, XBRL), marcate "SEC" — istoricul, automat;
       - comunicatele de rezultate (blocul FIN_PR din pagină, scris de Claude), marcate "C" — pentru companiile
         străine care nu depun trimestrial XBRL la SEC;
       - TradingView scanner, marcat "TV" (provizoriu) — trimestrul abia raportat, din seara publicării, până
         apare în 10-Q / FIN_PR; doar cifre în USD (TradingView convertește companiile străine → acolo nu se folosește).
     Yahoo rămâne doar pentru EPS raportat vs estimat, consensul trimestrului următor și reacția prețului.
  3. Scrie o versiune NOUĂ (N+1) — versiunile vechi rămân neatinse, pentru urmărirea bug-urilor —
     plus o copie cu nume fix: ai-stack-map-LATEST.html (pe asta o deschizi / sincronizezi pe telefon).
  4. Scrie în update-log.txt tot ce s-a schimbat la earnings și diferențele comunicat vs SEC.

Reguli pentru earnings (ca să nu strice ce e verificat):
  - O dată 'confirmat' din fișier NU e suprascrisă cât timp e în viitor; dacă Yahoo arată altă dată,
    doar se notează în log ca AVERTISMENT, ca s-o verifici.
  - După ce data a trecut (compania a raportat), se ia următoarea dată de la Yahoo.
  - Tickerii 'estimat' / 'neverificat' primesc data Yahoo, MEREU cu status 'estimat'.
    'confirmat' se pune doar manual, după anunțul oficial al companiei (IR / comunicat).
    Un 'confirmat' care provine de la Yahoo (src începe cu 'Yahoo Finance') e retrogradat la 'estimat'.
  - Sesiunea BMO/AMC se ia din Yahoo doar dacă lipsește ('?') sau data s-a schimbat; altfel rămâne cea existentă.

Instalare (o singură dată):   pip install yfinance
Rulare manuală:               python update_stack_map.py
Programare zilnică: vezi README din răspunsul Claude (Task Scheduler pe Windows / cron pe Mac-Linux).
"""
import argparse, datetime as dt, glob, gzip, json, os, re, sys, time
import urllib.request

try:
    import yfinance as yf
except ImportError:
    sys.exit("Lipsește yfinance. Rulează o dată:  pip install yfinance")

try:
    from zoneinfo import ZoneInfo
    NY = ZoneInfo("America/New_York")
except Exception:
    NY = None

YAHOO_SYMBOL = {"NDX": "^NDX", "VIX": "^VIX",          # indici
                "WTI": "CL=F", "BRENT": "BZ=F"}        # petrol: futures, luna activă
NO_EARNINGS = {"NDX", "SPY", "QQQ", "IWM", "VIX", "SOXX", "IGV", "TLT", "GLD", "UUP",
               "SMH", "XLK", "IBIT", "HYG", "DIA",
               "WTI", "BRENT"}                            # ETF-uri / indici / mărfuri
INDEX_NO_DOLLAR = {"NDX", "VIX"}
GREEN, RED = "#10b981", "#ef4444"

ROW_RE = re.compile(
    r"(<div class=\"ticker-row\" onclick=\"openDetails\('([A-Z.]+)','(?:[^'\\]|\\.)*',)"
    r"'[^']*','[^']*','[^']*','[^']*','[^']*','[^']*'"
    r"(.*?<span class=\"price-badge\">)[^<]*(</span><span class=\"change-badge\" style=\"color:)[^;]*(;\">)[^<]*(</span>)",
    re.S)
EARN_LINE_RE = re.compile(
    r"^(\s*)'([A-Z.]+)': \{ date:'([^']*)', session:'([^']*)', status:'([^']*)', time:'([^']*)', src:'([^']*)' \},$",
    re.M)


# ---------------------------------------------------------------- utilitare de format
def fmt_big(n):
    if n is None: return "—"
    n = float(n)
    for div, suf in ((1e12, "T"), (1e9, "B"), (1e6, "M")):
        if abs(n) >= div: return f"{n/div:.2f}{suf}"
    return f"{n:,.0f}"

def fmt_vol(n):
    if not n: return "—"
    n = float(n)
    return f"{n/1e6:.1f}M" if n >= 1e6 else f"{round(n/1e3)}K"

def fmt_price(t, p):
    s = f"{p:,.2f}"
    return s if t in INDEX_NO_DOLLAR else "$" + s

def fmt_chg(c):
    s = f"{c:+.2f}%"
    return "+0.00%" if s == "-0.00%" else s

def js_str(s):
    return str(s).replace("\\", "\\\\").replace("'", "\\'")


# ---------------------------------------------------------------- citire date Yahoo
def fetch(t):
    """Întoarce dict cu datele Yahoo pentru ticker, sau None dacă eșuează."""
    sym = YAHOO_SYMBOL.get(t, t)
    for attempt in range(3):
        try:
            info = yf.Ticker(sym).info or {}
            price = info.get("regularMarketPrice") or info.get("currentPrice")
            if price is None:
                raise ValueError("fără preț")
            chg = info.get("regularMarketChangePercent")
            if chg is None and info.get("regularMarketPreviousClose"):
                chg = (price / info["regularMarketPreviousClose"] - 1) * 100
            return {
                "price": float(price),
                "chg": float(chg or 0.0),
                "mcap": info.get("marketCap"),
                "vol": info.get("regularMarketVolume") or info.get("volume"),
                "pe": info.get("trailingPE"),
                "earn_ts": info.get("earningsTimestampStart") or info.get("earningsTimestamp"),
                "earn_est": info.get("isEarningsDateEstimate"),
                "fcur": info.get("financialCurrency"),
            }
        except Exception as e:
            err = e
            time.sleep(1.5 * (attempt + 1))
    print(f"  ! {t}: {err}")
    return None


def earnings_from_yahoo(d, today):
    """(date_iso, session, is_estimate) pentru următorul raport, sau None."""
    ts = d.get("earn_ts") if d else None
    if not ts:
        return None
    when = dt.datetime.fromtimestamp(int(ts), tz=dt.timezone.utc)
    when_ny = when.astimezone(NY) if NY else when - dt.timedelta(hours=4)
    if when_ny.date() < today:
        return None
    est = d.get("earn_est")
    est = True if est is None else bool(est)
    session = "?"
    if not est:
        h = when_ny.hour + when_ny.minute / 60
        session = "BMO" if h < 9.5 else ("AMC" if h >= 16 else "?")
    return when_ny.date().isoformat(), session, est


# ---------------------------------------------------------------- SEC EDGAR (sursa oficială pentru venituri / profit net)
# SEC cere un „Nume email” de contact în User-Agent → secretul GitHub SEC_USER_AGENT (nu în cod: repo-ul e public).
SEC_UA = os.environ.get("SEC_USER_AGENT", "").strip()
SEC_REV_TAGS = ["RevenuesNetOfInterestExpense",          # bănci: venitul net total, cum îl raportează banca
                "Revenues",                              # venitul total raportat (include ex. derivatele la energie)
                "RevenueFromContractWithCustomerExcludingAssessedTax", "SalesRevenueNet",
                "RevenueFromContractWithCustomerIncludingAssessedTax"]
SEC_NI_TAGS = ["NetIncomeLoss", "ProfitLoss"]           # profitul net atribuibil companiei; altfel profitul total
_SEC_CIK = None
_SEC_CIK_ERR = None                                      # motivul pentru care lista CIK nu s-a putut citi

class SecUnavailable(Exception):
    """SEC nu a răspuns (rețea, secret lipsă) — diferit de „compania nu are CIK”."""

def _sec_get(url):
    req = urllib.request.Request(url, headers={"User-Agent": SEC_UA, "Accept-Encoding": "gzip"})
    with urllib.request.urlopen(req, timeout=40) as r:
        raw = r.read()
        if r.headers.get("Content-Encoding") == "gzip":
            raw = gzip.decompress(raw)
    return json.loads(raw.decode("utf-8"))

def _sec_cik(t):
    global _SEC_CIK, _SEC_CIK_ERR
    if _SEC_CIK is None:
        _SEC_CIK = {}
        if not SEC_UA:
            _SEC_CIK_ERR = "SEC_USER_AGENT lipsește"
        else:
            try:
                _SEC_CIK = {v["ticker"].upper(): int(v["cik_str"])
                            for v in _sec_get("https://www.sec.gov/files/company_tickers.json").values()}
            except Exception as e:
                _SEC_CIK_ERR = f"lista CIK: {e}"
        if _SEC_CIK_ERR:
            print(f"  ! SEC indisponibil ({_SEC_CIK_ERR}) — venituri/profit rămân cele din versiunea anterioară")
    if _SEC_CIK_ERR:
        raise SecUnavailable(_SEC_CIK_ERR)
    return _SEC_CIK.get(t)

def _sec_series(g, tag):
    """{data_sfârșit: valoare trimestrială}; fiecare perioadă din raportarea cea mai recentă.
    T4 lipsește ca trimestru în 10-K → an − 9 luni, verificat cu an − (T1+T2+T3); dacă nu se potrivesc, T4 se omite."""
    latest = {}
    for it in (g.get(tag, {}).get("units", {}) or {}).get("USD", []):
        if "start" not in it:
            continue
        k = (it["start"], it["end"])
        if k not in latest or it.get("filed", "") > latest[k].get("filed", ""):
            latest[k] = it
    q, ann, ytd9 = {}, {}, {}
    for (st, en), it in latest.items():
        sd, ed = dt.date.fromisoformat(st), dt.date.fromisoformat(en)
        d = (ed - sd).days
        if 80 <= d <= 100: q[ed] = (sd, it["val"])
        elif 350 <= d <= 380: ann[(sd, ed)] = it["val"]
        elif 260 <= d <= 285: ytd9[(sd, ed)] = it["val"]
    out = {e: v for e, (sd, v) in q.items()}
    for (sd, ed), v in ann.items():
        if ed in out:
            continue
        est = []
        nine = [val for (s9, e9), val in ytd9.items() if s9 == sd and 60 < (ed - e9).days < 110]
        if nine: est.append(v - nine[0])
        three = [val for e3, (s3, val) in q.items() if sd <= s3 and e3 < ed - dt.timedelta(days=60)]
        if len(three) == 3: est.append(v - sum(three))
        if len(est) == 2 and abs(est[0] - est[1]) > 0.01 * max(abs(est[0]), abs(est[1]), 1):
            continue
        if est: out[ed] = est[0]
    return out

def sec_quarters(t):
    """Ultimele 5 trimestre [data, venituri M$, profit net M$, "SEC"] din raportările oficiale,
    None dacă firma nu are CIK / date trimestriale; SecUnavailable dacă SEC nu răspunde."""
    cik = _sec_cik(t)
    if not cik:
        return None
    try:
        g = _sec_get(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json").get("facts", {}).get("us-gaap", {})
        time.sleep(0.15)                                   # limita SEC: max 10 cereri/secundă
    except Exception as e:
        if getattr(e, "code", None) == 404:                # CIK fără date XBRL
            return None
        raise SecUnavailable(f"{t}: {e}")
    rev, ni = {}, {}
    for tag in SEC_REV_TAGS:                               # pe fiecare trimestru: prima definiție din listă care are valoare
        for e, v in _sec_series(g, tag).items(): rev.setdefault(e, v)
    for tag in SEC_NI_TAGS:
        for e, v in _sec_series(g, tag).items(): ni.setdefault(e, v)
    ends = sorted(e for e in rev if e > dt.date.today() - dt.timedelta(days=550))[-5:]
    rows = [[e.isoformat(), round(rev[e] / 1e6, 2), None if e not in ni else round(ni[e] / 1e6, 2), "SEC"] for e in ends]
    return rows or None


# ---------------------------------------------------------------- date trimestriale (secțiunea 📊 din drawer)
FIN_RE = re.compile(r"(// FIN-START[^\n]*\n\s*const FIN = )\{.*?\}(;\s*\n\s*// FIN-END)", re.S)
# FIN_PR: cifrele din comunicatele oficiale, scrise DOAR de Claude; scriptul doar le citește, nu scrie niciodată aici.
FINPR_RE = re.compile(r"// FINPR-START[^\n]*\n\s*const FIN_PR = (\{.*?\});\s*\n\s*// FINPR-END", re.S)
FIN_MAX_AGE_DAYS = 7      # reîmprospătare completă săptămânal + imediat după fiecare raport
FIN_SCHEMA = 5            # crește când se schimbă formatul → toate intrările se reîmprospătează
PR_GAP_DAYS = 45          # un trimestru din comunicat intră doar dacă e la > 45 zile după ultimul trimestru SEC
PR_MATCH_DAYS = 12        # același trimestru: sfârșit la ±12 zile (SEC folosește data exactă, comunicatul uneori sfârșit de lună)
PR_DIFF_PCT = 0.5         # prag pentru „DIFERENȚĂ comunicat vs SEC” / „TradingView vs oficial” în update-log.txt
TV_SCAN_URL = "https://scanner.tradingview.com/america/scan"
# revenue_fq: la NEE a dat venitul raportat (total_revenue_fq nu); la celelalte cele două coincid → revenue_fq întâi
TV_COLS = ["revenue_fq", "total_revenue_fq", "net_income_fq", "fiscal_period_end_fq", "fundamental_currency_code"]

def _num(x):
    try:
        x = float(x)
        return None if x != x else x          # NaN → None
    except Exception:
        return None

def _col(df, *names):
    low = {str(c).lower(): c for c in df.columns}
    for n in names:
        if n.lower() in low:
            return low[n.lower()]
    return None

def _d(iso):
    return dt.date.fromisoformat(iso)

def read_fin_pr(html):
    """{ticker: [[sfârșit_trim, venituri_M, profit_M, url, data_comunicat, moneda], ...]} din blocul FIN_PR al paginii."""
    m = FINPR_RE.search(html)
    if not m:
        return {}
    try:
        pr = json.loads(m.group(1))
    except ValueError as e:
        print(f"  ! FIN_PR nu e JSON valid ({e}) — ignorat")
        return {}
    return {t: sorted(rows, key=lambda r: r[0]) for t, rows in pr.items() if rows}

def read_tv_ex(html):
    """{ticker: bursa} din TV_EX al paginii (NASDAQ/NYSE/AMEX)."""
    m = re.search(r"const TV_EX = \{(.*?)\};", html, re.S)
    return {t: ex for ex, lst in re.findall(r"(\w+): '([^']*)'", m.group(1)) for t in lst.split()} if m else {}

def tv_latest(tickers, tv_ex):
    """{ticker: [sfârșit_trim, venituri_M, profit_M]} = ultimul trimestru raportat, din TradingView scanner
    (o singură cerere pentru toți tickerii). Doar cifre în USD. None dacă scanner-ul nu răspunde."""
    back = {}
    for t in tickers:
        for ex in ([tv_ex[t]] if t in tv_ex else ["NASDAQ", "NYSE", "AMEX"]):
            back[f"{ex}:{t}"] = t
    body = json.dumps({"symbols": {"tickers": list(back), "query": {"types": []}}, "columns": TV_COLS}).encode()
    req = urllib.request.Request(TV_SCAN_URL, data=body, headers={
        "Content-Type": "application/json", "Origin": "https://www.tradingview.com",
        "Referer": "https://www.tradingview.com/", "User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            rows = json.loads(r.read().decode("utf-8")).get("data", [])
    except Exception as e:
        print(f"  ! TradingView scanner: {e} — trimestrele provizorii rămân cele din versiunea anterioară")
        return None
    out = {}
    for row in rows:
        t, d = back.get(row.get("s")), dict(zip(TV_COLS, row.get("d") or []))
        rev = _num(d.get("revenue_fq"))
        rev = rev if rev is not None else _num(d.get("total_revenue_fq"))
        end = d.get("fiscal_period_end_fq")
        if not t or t in out or rev is None or not end or d.get("fundamental_currency_code") != "USD":
            continue
        ni = _num(d.get("net_income_fq"))
        out[t] = [dt.datetime.fromtimestamp(int(end), dt.timezone.utc).date().isoformat(),
                  round(rev / 1e6, 2), None if ni is None else round(ni / 1e6, 2)]
    return out

def build_quarters(t, srows, pr, tvq, log):
    """Rândurile q [data, venituri, profit, "SEC"|"C"|"TV"] + moneda lor (sau None dacă moneda vine din Yahoo).
    SEC are prioritate; comunicatul („C”) doar pentru trimestrele de după ultimul raport SEC (> 45 zile)
    sau pentru companiile fără SEC; TradingView („TV”, provizoriu) doar pentru un trimestru și mai nou (> 45 zile),
    și doar în USD. Ultimele 5."""
    pr = pr or []
    for p in pr:                                           # comunicat vs SEC pe același trimestru → log la diferențe
        s = next((r for r in srows or [] if abs((_d(r[0]) - _d(p[0])).days) <= PR_MATCH_DAYS), None)
        if not s:
            continue
        diffs = [f"{lab} comunicat {pv} vs SEC {sv}" for lab, pv, sv in (("venituri", p[1], s[1]), ("profit", p[2], s[2]))
                 if pv is not None and sv is not None and abs(pv - sv) > PR_DIFF_PCT / 100 * max(abs(sv), 1e-9)]
        if diffs:
            log.append(f"DIFERENȚĂ comunicat vs SEC {t} {p[0]}: " + "; ".join(diffs) + f" (sursă comunicat: {p[3]})")
    if srows:
        last = _d(srows[-1][0])
        q, cur = srows + [[p[0], p[1], p[2], "C"] for p in pr
                          if p[5] == "USD" and _d(p[0]) > last + dt.timedelta(days=PR_GAP_DAYS)], None
    elif pr:
        cur = pr[-1][5]                                    # moneda ultimului comunicat; rânduri în altă monedă nu se amestecă
        q = [[p[0], p[1], p[2], "C"] for p in pr if p[5] == cur]
    else:
        q, cur = [], None
    if tvq and cur in (None, "USD") and (not q or _d(tvq[0]) > _d(q[-1][0]) + dt.timedelta(days=PR_GAP_DAYS)):
        q = q + [[tvq[0], tvq[1], tvq[2], "TV"]]
    return (q[-5:] or None), cur

def fetch_fin(t, fcur=None, pr=None, log=None, tvq=None):
    """Venituri/profit net pe 5 trimestre (SEC + comunicate + TradingView provizoriu), EPS raportat vs estimat, consens trimestrul
    următor, reacția prețului după ultimele raportări. Întoarce dict (poate fi parțial) sau None.
    Cheia temporară "_secerr" = SEC n-a răspuns → update_fin păstrează veniturile/profitul vechi."""
    tk = yf.Ticker(YAHOO_SYMBOL.get(t, t))
    out = {}
    # moneda în care raportează compania (TSM = TWD, ASML/SAP = EUR …); cifrele NU se convertesc
    if not fcur:
        try:
            fcur = (tk.info or {}).get("financialCurrency")
        except Exception:
            fcur = None
    out["cur"] = fcur or "USD"
    # 1) venituri și profit net trimestrial: SEC (10-Q/10-K XBRL) pentru companiile americane, comunicatele din
    #    FIN_PR („C”) pentru companiile străine, TradingView („TV”, provizoriu) pentru trimestrul abia raportat.
    srows = None
    if out["cur"] == "USD":
        try:
            srows = sec_quarters(t)
        except SecUnavailable as e:
            print(f"  ~ {t} SEC: {e}")
            out["_secerr"] = True
    if "_secerr" not in out:
        q, qcur = build_quarters(t, srows, pr, tvq, log if log is not None else [])
        if q:
            out["q"] = q
            if qcur:
                out["cur"] = qcur                          # moneda din comunicat (documentul oficial) are prioritate
    # 2) EPS raportat vs estimare (ultimele 4 trimestre)
    try:
        eh = tk.earnings_history
        if eh is not None and not eh.empty:
            ca, ce = _col(eh, "epsActual", "Reported EPS"), _col(eh, "epsEstimate", "EPS Estimate")
            rows = []
            for idx in sorted(eh.index):
                a, e = _num(eh.loc[idx, ca]) if ca else None, _num(eh.loc[idx, ce]) if ce else None
                if a is None:
                    continue
                # estimare în altă unitate/monedă decât raportatul (ex. ADR vs acțiunea locală) → o respingem
                if e is not None and a and e and (abs(a / e) > 8 or abs(e / a) > 8):
                    e = None
                d = idx.strftime("%Y-%m-%d") if hasattr(idx, "strftime") else str(idx)[:10]
                rows.append([d, round(a, 3), None if e is None else round(e, 3)])
            if rows:
                out["eps"] = rows[-5:]
    except Exception as e:
        print(f"  ~ {t} fin/eps: {e}")
    # 3) consensul pentru trimestrul care urmează să fie raportat
    try:
        nx = {}
        ee = tk.earnings_estimate
        if ee is not None and not ee.empty and "0q" in ee.index:
            v = _num(ee.loc["0q", _col(ee, "avg")])
            if v is not None: nx["eps"] = round(v, 3)
        re_ = tk.revenue_estimate
        if re_ is not None and not re_.empty and "0q" in re_.index:
            v = _num(re_.loc["0q", _col(re_, "avg")])
            if v is not None: nx["rev"] = round(v / 1e6, 1)
        if nx:
            out["nx"] = nx
    except Exception as e:
        print(f"  ~ {t} fin/nx: {e}")
    # 4) reacția prețului: AMC → închiderea zilei următoare vs ziua raportului; BMO → ziua raportului vs ziua anterioară
    try:
        ed = tk.get_earnings_dates(limit=12)
        hist = tk.history(period="2y", interval="1d", auto_adjust=False)
        if ed is not None and not ed.empty and hist is not None and not hist.empty:
            closes = hist["Close"]
            days = [d.date() for d in closes.index]
            cr = _col(ed, "Reported EPS")
            rx = []
            now = dt.datetime.now(dt.timezone.utc)
            for ts in sorted(ed.index):
                if ts.to_pydatetime() > now or (cr and _num(ed.loc[ts, cr]) is None):
                    continue
                ts_ny = ts.tz_convert("America/New_York") if ts.tzinfo else ts
                d = ts_ny.date()
                amc = ts_ny.hour >= 16
                if amc:
                    i0 = max((i for i, x in enumerate(days) if x <= d), default=None)
                    i1 = None if i0 is None or i0 + 1 >= len(days) else i0 + 1
                else:
                    i1 = min((i for i, x in enumerate(days) if x >= d), default=None)
                    i0 = None if i1 is None or i1 == 0 else i1 - 1
                if i0 is None or i1 is None:
                    continue
                pct = (float(closes.iloc[i1]) / float(closes.iloc[i0]) - 1) * 100
                rx.append([d.isoformat(), "AMC" if amc else "BMO", round(pct, 2)])
            if rx:
                out["rx"] = rx[-6:]
    except Exception as e:
        print(f"  ~ {t} fin/rx: {e}")
    return out if len(out) > 1 else None


def fin_needs_refresh(entry, earn_date, today, pr=None, tvq=None):
    if not entry or not entry.get("upd") or entry.get("v") != FIN_SCHEMA:
        return True
    # Claude a adăugat / corectat un trimestru în FIN_PR care nu se vede încă în q → reîmprospătează
    q = entry.get("q") or []
    if pr and (not q or _d(pr[-1][0]) > _d(q[-1][0]) + dt.timedelta(days=PR_MATCH_DAYS)):
        return True
    if pr and any(r[3] == "TV" and any(abs((_d(p[0]) - _d(r[0])).days) <= PR_MATCH_DAYS for p in pr) for r in q):
        return True                                        # comunicatul a sosit pentru trimestrul provizoriu
    # TradingView are un trimestru nou (sau alte cifre pentru cel provizoriu) → reîmprospătează imediat (doar USD)
    if tvq and entry.get("cur", "USD") == "USD":
        if not q or _d(tvq[0]) > _d(q[-1][0]) + dt.timedelta(days=PR_GAP_DAYS):
            return True
        if q[-1][3] == "TV" and q[-1][:3] != tvq:
            return True
    prd = {p[0]: p for p in pr or []}
    if any(r[3] == "C" and (r[0] not in prd or [prd[r[0]][1], prd[r[0]][2]] != r[1:3]) for r in q):
        return True
    upd = dt.date.fromisoformat(entry["upd"])
    if (today - upd).days >= FIN_MAX_AGE_DAYS:
        return True
    # a avut loc un raport după ultima actualizare → reîmprospătează
    return bool(earn_date) and upd <= dt.date.fromisoformat(earn_date) <= today


def update_fin(html, tickers, today, data=None, log=None):
    m = FIN_RE.search(html)
    if not m:
        print("  ! blocul FIN lipsește din HTML — sar peste datele trimestriale")
        return html, 0, []
    block = html[m.start():m.end()]
    js = block[block.index("{"):block.rindex("}") + 1]
    fin = json.loads(js) if js.strip() != "{}" else {}
    fin_pr = read_fin_pr(html)
    earn_dates = {mm.group(2): mm.group(3) for mm in EARN_LINE_RE.finditer(html)}
    tv = tv_latest([t for t in tickers if t not in NO_EARNINGS], read_tv_ex(html))
    done, miss, secdown = 0, [], []
    for t in tickers:
        if t in NO_EARNINGS:
            fin.pop(t, None)
            continue
        old_q = (fin.get(t) or {}).get("q") or []
        if tv is not None:
            tvq = tv.get(t)
        else:                                              # scanner indisponibil → păstrează rândul provizoriu vechi
            tvq = next((r[:3] for r in old_q if len(r) > 3 and r[3] == "TV"), None)
        if not fin_needs_refresh(fin.get(t), earn_dates.get(t), today, fin_pr.get(t), tvq):
            continue
        d = fetch_fin(t, ((data or {}).get(t) or {}).get("fcur"), fin_pr.get(t), log, tvq)
        if d and d.pop("_secerr", False):
            old = fin.get(t) or {}
            if old.get("v") == FIN_SCHEMA and old.get("q"):
                d["q"], d["cur"] = old["q"], old.get("cur", d["cur"])   # SEC n-a răspuns → păstrează rândurile oficiale vechi
            secdown.append(t)
        if d and log is not None:                          # provizoriul TV înlocuit de cifra oficială → cât de bun a fost?
            for r in old_q:
                if len(r) < 4 or r[3] != "TV":
                    continue
                o = next((x for x in d.get("q") or [] if x[3] != "TV" and abs((_d(x[0]) - _d(r[0])).days) <= PR_MATCH_DAYS), None)
                if not o:
                    continue
                diffs = [f"{lab} TV {tv_v} vs {o[3]} {ov}" for lab, tv_v, ov in (("venituri", r[1], o[1]), ("profit", r[2], o[2]))
                         if tv_v is not None and ov is not None and abs(tv_v - ov) > PR_DIFF_PCT / 100 * max(abs(ov), 1e-9)]
                log.append(f"{'DIFERENȚĂ' if diffs else 'OK'} TradingView vs {o[3]} {t} {o[0]}" + (": " + "; ".join(diffs) if diffs else ""))
        if d:
            d["upd"], d["v"] = today.isoformat(), FIN_SCHEMA
            fin[t] = d                        # înlocuiește complet intrarea veche
            done += 1
        else:
            miss.append(t)                    # păstrează ce era, reîncearcă la rularea următoare
        time.sleep(0.4)
    if secdown and log is not None:
        log.append(f"SEC indisponibil — venituri/profit păstrate din versiunea anterioară (unde existau) pentru: {', '.join(secdown)}")
    body = "{\n" + ",\n".join(f'            "{k}":{json.dumps(fin[k], separators=(",", ":"))}' for k in sorted(fin)) + "\n        }"
    html = html[:m.start()] + m.group(1) + body + m.group(2) + html[m.end():]
    return html, done, miss


# ---------------------------------------------------------------- main
def latest_html(folder):
    files = glob.glob(os.path.join(folder, "ai-stack-map-mobile-*.html"))
    files = [(int(re.search(r"-(\d+)\.html$", f).group(1)), f) for f in files if re.search(r"-(\d+)\.html$", f)]
    if not files:
        sys.exit(f"Nu găsesc niciun ai-stack-map-mobile-N.html în {folder}")
    return max(files)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--html", help="fișierul de pornire (implicit: ultima versiune din folderul scriptului)")
    ap.add_argument("--dir", default=os.path.dirname(os.path.abspath(__file__)), help="folderul cu versiunile")
    ap.add_argument("--dry-run", action="store_true", help="arată ce s-ar schimba, fără să scrie fișiere")
    args = ap.parse_args()

    if args.html:
        m = re.search(r"-(\d+)\.html$", args.html)
        n, src = (int(m.group(1)) if m else 0), args.html
    else:
        n, src = latest_html(args.dir)
    html = open(src, encoding="utf-8").read()
    today = (dt.datetime.now(NY) if NY else dt.datetime.utcnow()).date()
    stamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f"Pornesc de la: {os.path.basename(src)}")

    tickers = sorted(set(re.findall(r"openDetails\('([A-Z.]+)'", html)))
    data, failed = {}, []
    for i, t in enumerate(tickers, 1):
        d = fetch(t)
        if d: data[t] = d
        else: failed.append(t)
        print(f"\r  {i}/{len(tickers)} {t:6}", end="", flush=True)
        time.sleep(0.25)
    print()

    # 1) rândurile din planșe
    def upd_row(m):
        t = m.group(2); d = data.get(t)
        if not d: return m.group(0)
        price, chg = fmt_price(t, d["price"]), fmt_chg(d["chg"])
        col = RED if chg.startswith("-") else GREEN
        etf = t in NO_EARNINGS
        mcap = "—" if etf else fmt_big(d["mcap"])
        vol = "—" if t in INDEX_NO_DOLLAR else fmt_vol(d["vol"])
        pe = "—" if (etf or not d["pe"] or d["pe"] <= 0) else f"{d['pe']:,.2f}"
        return (m.group(1) + f"'{price}','{chg}','{col}','{mcap}','{vol}','{pe}'" + m.group(3) + price
                + m.group(4) + col + m.group(5) + chg + m.group(6))
    html = ROW_RE.sub(upd_row, html)
    nrows = sum(1 for m in ROW_RE.finditer(html) if m.group(2) in data)

    # 2) calendarul de earnings
    log = []
    def upd_earn(m):
        ind, t, date, ses, st, tm, srcx = m.groups()
        if t in NO_EARNINGS or st in ("n/a", "delistat"):
            return m.group(0)
        y = earnings_from_yahoo(data.get(t), today)
        if not y:
            return m.group(0)
        ydate, yses, yest = y
        upcoming = bool(date) and date >= today.isoformat()
        if st == "confirmat" and srcx.startswith("Yahoo Finance"):
            st = "yahoo-confirmat"          # nu e anunț oficial → îl tratăm ca estimat
        if st == "confirmat" and upcoming:
            if ydate != date:
                log.append(f"AVERTISMENT {t}: confirmat {date} în fișier, Yahoo arată {ydate} — verifică pe IR")
            return m.group(0)
        new_st = "estimat"                 # Yahoo nu e sursă oficială
        new_ses = yses if (ses == "?" or ydate != date) and yses != "?" else ses   # nu suprascrie o sesiune deja știută
        new_tm = "" if (ydate != date) else tm
        new_src = f"Yahoo Finance {today.isoformat()}" + ("" if yest else " (Yahoo: dată neestimată — verifică IR)")
        if (ydate, new_ses, new_st) == (date, ses, st):
            return m.group(0)
        st = "confirmat(Yahoo)" if st == "yahoo-confirmat" else st
        log.append(f"{t}: {date or '—'} {ses} {st}  →  {ydate} {new_ses} {new_st}")
        return f"{ind}'{t}': {{ date:'{ydate}', session:'{new_ses}', status:'{new_st}', time:'{new_tm}', src:'{js_str(new_src)}' }},"
    html = EARN_LINE_RE.sub(upd_earn, html)

    # 3) date trimestriale (doar unde e nevoie: lipsă, mai vechi de 7 zile sau după un raport)
    html, fin_done, fin_miss = update_fin(html, tickers, today, data, log)
    print(f"Trimestriale: {fin_done} tickeri reîmprospătați | fără date: {', '.join(fin_miss) or 'niciunul'}")

    print(f"Rânduri actualizate: {nrows} | tickeri fără date: {', '.join(failed) or 'niciunul'}")
    print("Earnings:\n  " + ("\n  ".join(log) if log else "nicio schimbare"))
    if args.dry_run:
        return
    if len(failed) > len(tickers) / 2:
        sys.exit(f"Prea mulți tickeri fără date ({len(failed)}/{len(tickers)}) — probabil fără internet sau Yahoo indisponibil. Nu scriu nimic.")
    if html == open(src, encoding="utf-8").read():
        print("Nicio schimbare față de ultima versiune — nu scriu fișier nou.")
        return

    out = os.path.join(args.dir, f"ai-stack-map-mobile-{n+1}.html")
    open(out, "w", encoding="utf-8").write(html)
    open(os.path.join(args.dir, "ai-stack-map-LATEST.html"), "w", encoding="utf-8").write(html)
    with open(os.path.join(args.dir, "update-log.txt"), "a", encoding="utf-8") as f:
        f.write(f"\n=== {stamp} | {os.path.basename(src)} → {os.path.basename(out)} | rânduri {nrows} | fără date: {', '.join(failed) or '-'}\n")
        for line in log: f.write("  " + line + "\n")
        f.write(f"  trimestriale: {fin_done} reîmprospătate | fără date: {', '.join(fin_miss) or '-'}\n")
    print(f"Scris: {os.path.basename(out)} + ai-stack-map-LATEST.html")


if __name__ == "__main__":
    main()
