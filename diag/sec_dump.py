# TEMPORAR (ramura sec-anomalii): descarcă faptele SEC relevante pentru toți tickerii → diag/sec-facts.json.gz
import gzip, json, re, sys, time, os
sys.path.insert(0, ".")
import update_stack_map as u
n, src = u.latest_html(".")
html = open(src, encoding="utf-8").read()
tickers = sorted(set(re.findall(r"openDetails\('([A-Z.]+)'", html)) - u.NO_EARNINGS)
pat = re.compile(r"Revenue|Sales|NetIncome|ProfitLoss|IncomeLoss")
out = {}
for t in tickers:
    try:
        cik = u._sec_cik(t)
    except Exception as e:
        print("CIK err", t, e); continue
    if not cik:
        out[t] = None; continue
    try:
        j = u._sec_get(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json")
    except Exception as e:
        print("facts err", t, e); out[t] = {"_err": str(e)}; continue
    g = j.get("facts", {}).get("us-gaap", {})
    keep = {}
    for tag, v in g.items():
        if not pat.search(tag): continue
        units = {}
        for un, lst in (v.get("units") or {}).items():
            l = [x for x in lst if x.get("end", "") >= "2022-01-01"]
            if l: units[un] = l
        if units: keep[tag] = {"units": units}
    out[t] = {"cik": cik, "name": j.get("entityName"), "us-gaap": keep}
    print(t, cik, len(keep)); time.sleep(0.15)
os.makedirs("diag", exist_ok=True)
with gzip.open("diag/sec-facts.json.gz", "wt", encoding="utf-8") as f:
    json.dump(out, f)
print("gata", len(out))
