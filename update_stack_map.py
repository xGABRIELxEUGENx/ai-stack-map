#!/usr/bin/env python3
"""
update_stack_map.py — actualizează singur AI Stack Map, fără cont, fără cheie API, fără Claude.

Ce face la fiecare rulare:
  1. Găsește ultima versiune ai-stack-map-mobile-N.html din folderul scriptului (sau --html).
  2. Pentru fiecare ticker din planșe citește datele publice Yahoo Finance (prin biblioteca yfinance):
     preț, variație %, market cap, volum, P/E, următoarea dată de earnings + dacă e estimată.
  3. Scrie o versiune NOUĂ (N+1) — cea veche rămâne neatinsă (metoda scriitorului) —
     plus o copie cu nume fix: ai-stack-map-LATEST.html (pe asta o deschizi / sincronizezi pe telefon).
  4. Scrie în update-log.txt tot ce s-a schimbat la earnings.

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
import argparse, datetime as dt, glob, json, os, re, sys, time

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


# ---------------------------------------------------------------- date trimestriale (secțiunea 📊 din drawer)
FIN_RE = re.compile(r"(// FIN-START[^\n]*\n\s*const FIN = )\{.*?\}(;\s*\n\s*// FIN-END)", re.S)
FIN_MAX_AGE_DAYS = 7      # reîmprospătare completă săptămânal + imediat după fiecare raport
FIN_SCHEMA = 2            # crește când se schimbă formatul → toate intrările se reîmprospătează

def _num(x):
    try:
        x = float(x)
        return None if x != x else x          # NaN → None
    except Exception:
        return None

def _row(df, names, col):
    for n in names:
        if n in df.index:
            return _num(df.loc[n, col])
    return None

def _col(df, *names):
    low = {str(c).lower(): c for c in df.columns}
    for n in names:
        if n.lower() in low:
            return low[n.lower()]
    return None

def fetch_fin(t, fcur=None):
    """Venituri/profit net pe 5 trimestre, EPS raportat vs estimat, consens trimestrul următor,
    reacția prețului după ultimele raportări. Întoarce dict (poate fi parțial) sau None."""
    tk = yf.Ticker(YAHOO_SYMBOL.get(t, t))
    out = {}
    # moneda în care raportează compania (TSM = TWD, ASML/SAP = EUR …); cifrele NU se convertesc
    if not fcur:
        try:
            fcur = (tk.info or {}).get("financialCurrency")
        except Exception:
            fcur = None
    out["cur"] = fcur or "USD"
    # 1) contul de profit și pierdere trimestrial
    try:
        q = tk.quarterly_income_stmt
        if q is not None and not q.empty:
            rows = []
            for c in sorted(q.columns)[-5:]:
                rev = _row(q, ["Total Revenue", "Operating Revenue"], c)
                ni = _row(q, ["Net Income", "Net Income Common Stockholders"], c)
                if rev is None:
                    continue
                rows.append([c.strftime("%Y-%m-%d"), round(rev / 1e6, 1), None if ni is None else round(ni / 1e6, 1)])
            if rows:
                out["q"] = rows
    except Exception as e:
        print(f"  ~ {t} fin/q: {e}")
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


def fin_needs_refresh(entry, earn_date, today):
    if not entry or not entry.get("upd") or entry.get("v") != FIN_SCHEMA:
        return True
    upd = dt.date.fromisoformat(entry["upd"])
    if (today - upd).days >= FIN_MAX_AGE_DAYS:
        return True
    # a avut loc un raport după ultima actualizare → reîmprospătează
    return bool(earn_date) and upd <= dt.date.fromisoformat(earn_date) <= today


def update_fin(html, tickers, today, data=None):
    m = FIN_RE.search(html)
    if not m:
        print("  ! blocul FIN lipsește din HTML — sar peste datele trimestriale")
        return html, 0, []
    block = html[m.start():m.end()]
    js = block[block.index("{"):block.rindex("}") + 1]
    fin = json.loads(js) if js.strip() != "{}" else {}
    earn_dates = {mm.group(2): mm.group(3) for mm in EARN_LINE_RE.finditer(html)}
    done, miss = 0, []
    for t in tickers:
        if t in NO_EARNINGS:
            fin.pop(t, None)
            continue
        if not fin_needs_refresh(fin.get(t), earn_dates.get(t), today):
            continue
        d = fetch_fin(t, ((data or {}).get(t) or {}).get("fcur"))
        if d:
            d["upd"], d["v"] = today.isoformat(), FIN_SCHEMA
            fin[t] = d                        # înlocuiește complet intrarea veche
            done += 1
        else:
            miss.append(t)                    # păstrează ce era, reîncearcă la rularea următoare
        time.sleep(0.4)
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
    html, fin_done, fin_miss = update_fin(html, tickers, today, data)
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
