import re, json, time, urllib.request, sys
sys.path.insert(0, ".")
import old_usm as o, new_usm as n
html = open("page.html", encoding="utf-8").read()
tickers = sorted(set(re.findall(r"openDetails\('([A-Z.]+)'", html)))
changed = 0
for t in tickers:
    try:
        a = o.sec_quarters(t); b = n.sec_quarters(t)
    except Exception as e:
        print("ERR", t, e); continue
    if a != b:
        changed += 1
        print("DIFF", t, "\n  old", a, "\n  new", b)
print("tickers", len(tickers), "changed", changed)
# SOUN: coperta ultimului 10-Q (clase de acțiuni)
UA = n.SEC_UA
def get(url):
    r = urllib.request.Request(url, headers={"User-Agent": UA}); return urllib.request.urlopen(r, timeout=40).read().decode("utf-8", "replace")
for t, cik in (("SOUN", 1840856), ("NBIS", 1513845)):
    sub = json.loads(get(f"https://data.sec.gov/submissions/CIK{cik:010d}.json"))["filings"]["recent"]
    for i, f in enumerate(sub["form"]):
        if f in ("10-Q", "10-K", "6-K", "20-F"):
            acc = sub["accessionNumber"][i].replace("-", ""); doc = sub["primaryDocument"][i]
            url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/{doc}"
            txt = re.sub(r"<[^>]+>", " ", get(url)); txt = re.sub(r"&#160;|&nbsp;|\s+", " ", txt)
            print("===", t, f, sub["filingDate"][i], url)
            for m in re.finditer(r"[^.]{0,200}(Class A|Class B)[^.]{0,250}outstanding[^.]{0,120}", txt[:60000]):
                print("  ", m.group(0)[:500])
            break
