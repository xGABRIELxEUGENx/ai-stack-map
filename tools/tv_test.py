# Test temporar: cât de repede are TradingView (scanner) veniturile/profitul trimestrului abia raportat?
import json, urllib.request, datetime as dt
H = {"Content-Type": "application/json", "Origin": "https://www.tradingview.com", "Referer": "https://www.tradingview.com/", "User-Agent": "Mozilla/5.0"}
def scan(market, tickers, cols):
    req = urllib.request.Request(f"https://scanner.tradingview.com/{market}/scan",
        data=json.dumps({"symbols": {"tickers": tickers, "query": {"types": []}}, "columns": cols}).encode(), headers=H)
    try:
        return json.loads(urllib.request.urlopen(req, timeout=30).read())
    except urllib.error.HTTPError as e:
        return {"error": e.code, "body": e.read()[:200].decode(errors="ignore")}
CAND = ["total_revenue_fq", "revenue_fq", "total_revenue", "net_income_fq", "net_income", "fiscal_period_end_fq",
        "fiscal_period_current", "fiscal_period_end", "earnings_release_date", "earnings_release_next_date",
        "earnings_per_share_fq", "earnings_per_share_basic_fq", "fundamental_currency_code", "currency",
        "last_annual_revenue", "revenue_ttm", "total_revenue_ttm", "net_income_ttm", "fiscal_period_end_fh",
        "total_revenue_fh", "net_income_fh"]
ok = []
for c in CAND:
    r = scan("america", ["NASDAQ:AAPL"], [c])
    good = "data" in r and r["data"]
    print("COL", c, "OK" if good else "X", (r["data"][0]["d"] if good else r.get("body", "")))
    if good: ok.append(c)
T = ["NASDAQ:MU", "NYSE:NKE", "NYSE:ACN", "NYSE:FDX", "NASDAQ:PAYX", "NASDAQ:CTAS", "NYSE:CCL", "NYSE:STZ", "NYSE:GIS",
     "NYSE:KMX", "NASDAQ:COST", "NYSE:CAG", "NASDAQ:CTAS", "NYSE:LEVI", "NYSE:UNF",
     "NYSE:TSM", "NASDAQ:ASML", "NYSE:SAP", "NYSE:CCJ", "NASDAQ:GFS", "NASDAQ:NBIS", "NASDAQ:SKHY", "NYSE:SKHY",
     "NASDAQ:AMKR", "NYSE:BE", "NASDAQ:CDNS", "NYSE:DLR", "NYSE:NEE", "NYSE:V", "NYSE:WOLF", "NASDAQ:WOLF", "NASDAQ:APLD", "NASDAQ:NVDA"]
r = scan("america", list(dict.fromkeys(T)), ok)
print("RUN_UTC", dt.datetime.utcnow().isoformat())
for row in r.get("data", []):
    d = dict(zip(ok, row["d"]))
    for k in ("earnings_release_date", "earnings_release_next_date"):
        if isinstance(d.get(k), (int, float)): d[k] = dt.datetime.utcfromtimestamp(d[k]).strftime("%Y-%m-%d %H:%M")
    for k in list(d):
        if isinstance(d[k], float) and abs(d[k]) > 1e5: d[k] = round(d[k] / 1e6, 3)
    print("ROW", row["s"], json.dumps(d, ensure_ascii=False))
if "error" in r: print("ERR", r)
