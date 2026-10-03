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
import argparse, datetime as dt, glob, os, re, sys, time

try:
    import yfinance as yf
except ImportError:
    sys.exit("Lipsește yfinance. Rulează o dată:  pip install yfinance")

try:
    from zoneinfo import ZoneInfo
    NY = ZoneInfo("America/New_York")
except Exception:
    NY = None

YAHOO_SYMBOL = {"NDX": "^NDX", "VIX": "^VIX"}          # indici
NO_EARNINGS = {"NDX", "SPY", "QQQ", "IWM", "VIX", "SOXX", "IGV", "TLT", "GLD", "UUP",
               "SMH", "XLK", "IBIT", "HYG", "DIA"}       # ETF-uri / indici
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
    print(f"Scris: {os.path.basename(out)} + ai-stack-map-LATEST.html")


if __name__ == "__main__":
    main()
