import json, os, sys, datetime as dt, urllib.request
sys.path.insert(0, ".")
import update_stack_map as u

KEYS = ("Noncontrolling", "Redeemable", "Preferred", "Dividend", "Attributable", "Available", "ProfitLoss", "NetIncome", "MinorityInterest", "Accretion")
ENDS = {"2025-08-31", "2025-11-30", "2026-02-28", "2026-05-31", "2026-08-31"}
cik = u._sec_cik("APLD")
facts = u._sec_get(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json")["facts"]
print("=== APLD CIK", cik, "namespaces", list(facts))
for ns, g in facts.items():
    for tag, d in sorted(g.items()):
        if not any(k in tag for k in KEYS): continue
        for unit, arr in d.get("units", {}).items():
            for it in arr:
                if it.get("end") in ENDS and "start" in it:
                    days = (dt.date.fromisoformat(it["end"]) - dt.date.fromisoformat(it["start"])).days
                    print(f"{ns}:{tag} [{unit}] {it['start']}..{it['end']} ({days}d) val={it['val']} form={it.get('form')} filed={it.get('filed')}")
g = facts.get("us-gaap", {})
print("=== sec_quarters(APLD)", u.sec_quarters("APLD"))
for tag in u.SEC_NI_TAGS + [u.SEC_NI_FALLBACK, u.SEC_NCI_TAG] + u.SEC_NCI_PARTS:
    print("series", tag, {str(k): v for k, v in sorted(u._sec_series(g, tag).items())[-6:]})

print("=== SOUN dei")
c2 = u._sec_cik("SOUN")
f2 = u._sec_get(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{c2:010d}.json")["facts"]
for it in f2.get("dei", {}).get("EntityCommonStockSharesOutstanding", {}).get("units", {}).get("shares", [])[-8:]:
    print(it)
import yfinance as yf
for t in ("SOUN", "NBIS", "APLD", "GOOGL", "META"):
    i = yf.Ticker(t).info
    print("=== yahoo", t, {k: i.get(k) for k in ("currentPrice", "regularMarketPrice", "marketCap", "sharesOutstanding", "impliedSharesOutstanding", "floatShares", "financialCurrency")})
req = urllib.request.Request("https://scanner.tradingview.com/america/scan", data=json.dumps({"symbols": {"tickers": ["NASDAQ:SOUN", "NASDAQ:NBIS"]}, "columns": ["close", "market_cap_basic", "total_shares_outstanding", "total_shares_outstanding_fundamental", "float_shares_outstanding"]}).encode(), headers={"Content-Type": "application/json"})
print("=== TV", urllib.request.urlopen(req, timeout=30).read().decode())
