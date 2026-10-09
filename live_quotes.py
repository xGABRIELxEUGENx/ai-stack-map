#!/usr/bin/env python3
"""
live_quotes.py — fluxul ETH (pre-market / after-hours) al paginii: scrie quotes.json din Yahoo Finance (yfinance).

Independent de update_stack_map.py (nu importă nimic din el). Rulează din .github/workflows/live.yml,
la 15 minute, luni–vineri; rezultatul se publică pe ramura orfană `live` (un singur commit, force push),
nu în main. Pagina îl citește în afara sesiunii regulate (PRE, POST, închis).

Ieșire:
  {"generated": "2026-10-05T12:45:00Z",
   "q": {"NVDA": {"p": 183.2, "c": 0.84, "ref": 181.67, "s": "PRE", "t": "2026-10-05T12:40:00Z"}, ...},
   "missing": ["XYZ", ...]}
  p = ultimul preț (bara de 5 min, inclusiv pre/post) · t = ora barei (ISO UTC) · s = sesiunea după ora în ET
  (PRE 04:00–09:30, REG 09:30–16:00, POST 16:00–20:00, altfel CLOSED) · ref = închiderea regulată de referință
  (în PRE/REG cea anterioară, în POST cea de azi; la crypto: închiderea zilei UTC anterioare) · c = % față de ref.

Reguli:
  - iese cu 0, fără să scrie, în weekend (ET) și în afara intervalului 04:00–20:15 ET (--force sare peste filtru);
  - tickerii fără date se omit și se listează în `missing`;
  - dacă lipsesc peste jumătate dintre tickeri, NU scrie fișierul și iese cu 1.

Pe lângă fluxul ETH de mai sus, scriptul mai calculează la fiecare rulare (orice sesiune, nu doar PRE/POST/închis)
top 5 gainers și top 5 losers ai componentelor Nasdaq-100 ("Winners & Losers NAS100"), scrise sub cheia `movers`:
  "movers": {"gainers": [["NVDA", 3.21], ...5], "losers": [["INTC", -2.14], ...5]}  (variația zilnică %, din coloana
  `change` a TradingView scanner — același tipar ca în crosscheck.py / update_stack_map.py: scanner.tradingview.com,
  fără cont, fără cheie API — vezi `nas100_movers()`). Motivul elementului separat de bandă: widget-ul gratuit
  TradingView `ticker-tape` (folosit în sesiunea regulată) e un iframe închis, nu poate primi date proprii, deci
  movers trebuie să vină dintr-o sursă interogabilă direct (scanner), nu din widget.
  Lista celor ~101 componente (NAS100_CONSTITUENTS mai jos) e statică, nu vine dintr-un filtru "apartenență la
  index" al scanner-ului TradingView: nu există unul documentat/public, fără cont (biblioteca de referință pentru
  interogarea scanner-ului, github.com/shner-elmo/TradingView-Screener, nu listează un filtru de tip index
  membership/constituents; pagina proprie TradingView pentru componente, tradingview.com/symbols/NASDAQ-NDX/components,
  arată tabelul doar cu autentificare — ceea ce ar încălca regula 6 din CLAUDE.md). `movers` lipsește din JSON dacă
  scanner-ul nu răspunde pentru cel puțin jumătate din componente — pagina trebuie să trateze absența ei fără eroare.

Rulare:  python3 live_quotes.py [--out quotes.json] [--html ai-stack-map-mobile-N.html] [--force]
"""
import argparse, glob, gzip, json, math, os, re, sys, time as time_module
import urllib.request
from datetime import datetime, time, timezone
from zoneinfo import ZoneInfo

NY = ZoneInfo("America/New_York")
# simbolurile paginii care nu sunt acțiuni → simbolul Yahoo
YAHOO_SYMBOL = {"NDX": "^NDX", "VIX": "^VIX", "WTI": "CL=F", "BRENT": "BZ=F"}
# doar pentru banda proprie a paginii (cheia din quotes.json → simbolul Yahoo)
TAPE_EXTRA = {"NQ": "NQ=F", "BTC": "BTC-USD", "DXY": "DX-Y.NYB", "US10Y": "^TNX"}
WINDOW = (time(4, 0), time(20, 15))

# ------------------------------------------------------------------------------------------------------------------
# NAS100_CONSTITUENTS — componentele Nasdaq-100 (101 titluri, incl. GOOGL/GOOG separat, cum le dă Nasdaq).
# Sursă: tabelul "Components" de pe https://en.wikipedia.org/wiki/Nasdaq-100 (citează indexul oficial Nasdaq),
# citit la 2026-10-09, „101 components (June 5, 2026)”. Listă statică (vezi nota de mai sus) — Nasdaq rebalansează
# trimestrial/anual; la rebalansare lista de mai jos trebuie actualizată manual din aceeași sursă.
NAS100_CONSTITUENTS = [
    "ADBE", "AMD", "ABNB", "ALNY", "GOOGL", "GOOG", "AMZN", "AEP", "AMGN", "ADI",
    "AAPL", "AMAT", "APP", "ARM", "ASML", "ALAB", "ADSK", "ADP", "AXON", "BKR",
    "BKNG", "AVGO", "CDNS", "CTAS", "CSCO", "CCEP", "CMCSA", "CEG", "CPRT", "CRWV",
    "COST", "CRWD", "CSX", "DDOG", "DXCM", "FANG", "DASH", "EA", "EXC", "FAST",
    "FER", "FTNT", "GEHC", "GILD", "HON", "IDXX", "INTC", "INTU", "ISRG", "KDP",
    "KLAC", "KHC", "LRCX", "LIN", "LITE", "MAR", "MRVL", "MELI", "META", "MCHP",
    "MU", "MSFT", "MSTR", "MDLZ", "MPWR", "MNST", "NBIS", "NFLX", "NVDA", "NXPI",
    "ORLY", "ODFL", "PCAR", "PLTR", "PANW", "PAYX", "PYPL", "PDD", "PEP", "QCOM",
    "REGN", "RKLB", "ROP", "ROST", "SNDK", "STX", "SHOP", "SBUX", "SNPS", "TMUS",
    "TTWO", "TER", "TSLA", "TXN", "TRI", "VRTX", "WMT", "WBD", "WDC", "WDAY", "XEL",
]
TV_SCAN_URL = "https://scanner.tradingview.com/{market}/scan"
TV_UA = "AI Stack Map live-quotes-bot@users.noreply.github.com"


def latest_html(folder):
    files = glob.glob(os.path.join(folder, "ai-stack-map-mobile-*.html"))
    if not files:
        sys.exit("Nu găsesc niciun ai-stack-map-mobile-N.html")
    return max(files, key=lambda f: int(re.search(r"-(\d+)\.html$", f).group(1)))


def page_tickers(html):
    seen = []
    for t in re.findall(r"openDetails\('([A-Z][A-Z0-9.\-]*)'", html):
        if t not in seen:
            seen.append(t)
    return seen


def session_of(dt_utc):
    et = dt_utc.astimezone(NY)
    if et.weekday() >= 5:
        return "CLOSED"
    hm = et.time()
    if time(4, 0) <= hm < time(9, 30):
        return "PRE"
    if time(9, 30) <= hm < time(16, 0):
        return "REG"
    if time(16, 0) <= hm < time(20, 0):
        return "POST"
    return "CLOSED"


def rnd(x):
    return round(x, 4) if abs(x) < 10 else round(x, 2)


def column(df, field, sym, n_syms):
    """Coloana `field` pentru `sym` dintr-un yf.download (MultiIndex la mai multe simboluri)."""
    if df is None or df.empty:
        return None
    try:
        if n_syms == 1 and not hasattr(df.columns, "levels"):
            s = df[field]
        else:
            s = df[field][sym] if field in df.columns.get_level_values(0) else df[sym][field]
    except KeyError:
        return None
    s = s.dropna()
    return s if len(s) else None


def to_utc(ts):
    ts = ts.to_pydatetime()
    return ts.replace(tzinfo=timezone.utc) if ts.tzinfo is None else ts.astimezone(timezone.utc)


def reference_close(daily, t_utc, crypto):
    """Ultima închidere regulată deja încheiată la momentul t_utc."""
    best = None
    for idx, val in daily.items():
        d = idx.date() if hasattr(idx, "date") else idx
        if crypto:                         # bara zilnică crypto = ziua UTC; referința = ziua UTC anterioară
            done = d < t_utc.date()
        else:                              # închiderea regulată a zilei d are loc la 16:00 ET
            done = datetime.combine(d, time(16, 0), NY) <= t_utc
        if done:
            best = float(val)
    return best


def _tv_scan(symbols, columns, market="america", tries=3, timeout=20):
    """POST către scanner.tradingview.com/{market}/scan — același tipar (fără cont, fără cheie API) ca
    `tv_quotes()` din crosscheck.py și TV_SCAN_URL din update_stack_map.py. Întoarce {simbol_TV: [coloane]}."""
    body = json.dumps({"symbols": {"tickers": symbols, "query": {"types": []}}, "columns": columns}).encode()
    headers = {"User-Agent": TV_UA, "Accept": "application/json,*/*", "Content-Type": "application/json",
               "Origin": "https://www.tradingview.com", "Referer": "https://www.tradingview.com/"}
    err = None
    for i in range(tries):
        try:
            req = urllib.request.Request(TV_SCAN_URL.format(market=market), data=body, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                raw = r.read()
                if r.headers.get("Content-Encoding") == "gzip":
                    raw = gzip.decompress(raw)
                data = json.loads(raw.decode("utf-8"))
            return {row["s"]: row["d"] for row in data.get("data", []) if row.get("d") is not None}
        except Exception as e:
            err = e
            time_module.sleep(1.5 * (i + 1))
    raise RuntimeError(f"scanner TradingView ({market}): {err}")


def nas100_movers(tickers=NAS100_CONSTITUENTS, chunk=50):
    """Top 5 gainers și top 5 losers (după `change`, variația zilnică %) din componentele NAS100_CONSTITUENTS,
    citite prin scanner-ul TradingView (toate pe NASDAQ — condiție de membru al indexului). Întoarce None la
    eroare de rețea sau dacă lipsesc date pentru peste jumătate din tickeri (nu blochează restul scriptului:
    e un calcul suplimentar, nu sursa principală de date)."""
    uniq = list(dict.fromkeys(tickers))
    changes = {}
    try:
        for i in range(0, len(uniq), chunk):
            batch = [f"NASDAQ:{t}" for t in uniq[i:i + chunk]]
            got = _tv_scan(batch, ["change"])
            for sym, d in got.items():
                t = sym.split(":", 1)[-1]
                if d and d[0] is not None:
                    changes[t] = float(d[0])
    except Exception as e:
        print(f"  ! NAS100 movers: scanner TradingView indisponibil ({e}) — omit `movers`.")
        return None
    missing = [t for t in uniq if t not in changes]
    if missing:
        print(f"  NAS100 movers: lipsă {len(missing)}/{len(uniq)} tickeri: {', '.join(missing)}")
    if len(changes) < len(uniq) / 2:
        print(f"  ! NAS100 movers: date insuficiente ({len(changes)}/{len(uniq)}) — omit `movers`.")
        return None
    ranked = sorted(changes.items(), key=lambda kv: kv[1], reverse=True)
    gainers = [[t, round(c, 2)] for t, c in ranked[:5]]
    losers = [[t, round(c, 2)] for t, c in ranked[-5:][::-1]]
    return {"gainers": gainers, "losers": losers}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="quotes.json")
    ap.add_argument("--html", help="pagina din care se citesc tickerii (implicit ultima versiune)")
    ap.add_argument("--force", action="store_true", help="ignoră filtrul de weekend / interval orar (teste)")
    a = ap.parse_args()

    now = datetime.now(timezone.utc)
    et = now.astimezone(NY)
    if not a.force and (et.weekday() >= 5 or not (WINDOW[0] <= et.time() <= WINDOW[1])):
        print(f"În afara programului ETH ({et:%a %H:%M} ET) — nu scriu nimic.")
        return 0

    html_path = a.html or latest_html(os.path.dirname(os.path.abspath(__file__)))
    tickers = page_tickers(open(html_path, encoding="utf-8").read())
    keys = {t: YAHOO_SYMBOL.get(t, t.replace(".", "-")) for t in tickers}
    for k, y in TAPE_EXTRA.items():
        keys.setdefault(k, y)
    syms = sorted(set(keys.values()))
    print(f"{os.path.basename(html_path)}: {len(tickers)} tickeri + {len(TAPE_EXTRA)} pentru bandă → {len(syms)} simboluri Yahoo")

    import yfinance as yf
    common = dict(group_by="column", auto_adjust=False, progress=False, threads=True)
    intra = yf.download(syms, period="2d", interval="5m", prepost=True, **common)
    daily = yf.download(syms, period="7d", interval="1d", **common)

    q, missing = {}, []
    for key, sym in keys.items():
        last = column(intra, "Close", sym, len(syms))
        closes = column(daily, "Close", sym, len(syms))
        if last is None or closes is None:
            missing.append(key)
            continue
        t_utc = to_utc(last.index[-1])
        p = float(last.iloc[-1])
        ref = reference_close(closes, t_utc, sym.endswith("-USD"))
        if ref is None or not ref or math.isnan(p) or math.isnan(ref):
            missing.append(key)
            continue
        q[key] = {"p": rnd(p), "c": round((p / ref - 1) * 100, 2) + 0.0,  # + 0.0: fără „-0.0”
                  "ref": rnd(ref),
                  "s": session_of(t_utc), "t": t_utc.strftime("%Y-%m-%dT%H:%M:%SZ")}

    total = len(keys)
    print(f"Cu date: {len(q)}/{total} · lipsă: {', '.join(missing) or '—'}")
    by_s = {}
    for v in q.values():
        by_s[v["s"]] = by_s.get(v["s"], 0) + 1
    print("Pe sesiuni: " + ", ".join(f"{k} {v}" for k, v in sorted(by_s.items())))
    if len(missing) > total / 2:
        print(f"EROARE: lipsesc {len(missing)} din {total} tickeri (> jumătate) — nu scriu {a.out}.", file=sys.stderr)
        return 1

    print("Winners & Losers NAS100:")
    movers = nas100_movers()
    out = {"generated": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "q": q, "missing": missing}
    if movers is not None:
        out["movers"] = movers
        print(f"  gainers: {', '.join(f'{t} {c:+.2f}%' for t, c in movers['gainers'])}")
        print(f"  losers:  {', '.join(f'{t} {c:+.2f}%' for t, c in movers['losers'])}")
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(out, f, separators=(",", ":"), ensure_ascii=False)
    print(f"Scris: {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
