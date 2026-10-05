# TEMPORAR (ramura sec-anomalii): descarcă documentele oficiale pentru cazurile investigate → diag/docs/
import json, os, re, sys, time, html as H
sys.path.insert(0, ".")
import update_stack_map as u
CASES = {"ANET": ["0001596532-26-000013"], "NEE": ["0000753308-26-000015", "0000753308-26-000031"],
         "NTAP": ["0001193125-26-380207", "0001193125-26-259683"], "TLN": ["0001622536-26-000066"],
         "XE": ["0001193125-26-347752"], "APLD": ["0001144879-26-000006", "0001144879-26-000030"],
         "BE": ["0001628280-26-006516", "0001628280-26-028021"], "GTLB": ["0001628280-26-018731"],
         "SOUN": ["0001840856-26-000006"]}
def get(url, raw=False):
    import urllib.request, gzip
    req = urllib.request.Request(url, headers={"User-Agent": u.SEC_UA, "Accept-Encoding": "gzip"})
    with urllib.request.urlopen(req, timeout=40) as r:
        b = r.read()
        if r.headers.get("Content-Encoding") == "gzip": b = gzip.decompress(b)
    time.sleep(0.2)
    return b.decode("utf-8", "replace")
def text(h):
    h = re.sub(r"(?is)<(script|style).*?</\1>", " ", h)
    h = re.sub(r"(?i)</(tr|p|div|br|h\d)>", "\n", h)
    h = re.sub(r"(?i)</t[dh]>", " | ", h)
    h = H.unescape(re.sub(r"<[^>]+>", " ", h))
    return "\n".join(re.sub(r"[ \t\xa0]+", " ", l).strip() for l in h.splitlines() if l.strip())
os.makedirs("diag/docs", exist_ok=True)
idx = {}
for t, accns in CASES.items():
    cik = u._sec_cik(t)
    sub = json.loads(get(f"https://data.sec.gov/submissions/CIK{cik:010d}.json"))["filings"]["recent"]
    rows = [dict(zip(sub, v)) for v in zip(*sub.values())]
    eks = [r["accessionNumber"] for r in rows if r["form"] == "8-K" and "2.02" in r.get("items", "") and r["filingDate"] >= "2026-01-15"]
    idx[t] = [{k: r[k] for k in ("form", "filingDate", "reportDate", "accessionNumber", "primaryDocument", "items")}
              for r in rows if r["filingDate"] >= "2025-09-01" and r["form"] in ("10-Q", "10-K", "8-K", "10-Q/A", "10-K/A")]
    for a in accns + eks:
        base = f"https://www.sec.gov/Archives/edgar/data/{cik}/{a.replace('-', '')}/"
        try:
            items = json.loads(get(base + "index.json"))["directory"]["item"]
        except Exception as e:
            print("idx err", t, a, e); continue
        names = [i["name"] for i in items]
        if a in eks:
            want = [n for n in names if re.search(r"(?i)ex-?99|ex991|exhibit99|dex99", n) and n.lower().endswith((".htm", ".html"))][:1]
        else:
            want = [f"R{k}.htm" for k in range(2, 9) if f"R{k}.htm" in names]
        out = []
        for n in want:
            try: out.append(f"##### {n}\n" + text(get(base + n)))
            except Exception as e: out.append(f"##### {n} ERR {e}")
        open(f"diag/docs/{t}_{a}.txt", "w").write(f"{base}\n" + "\n".join(out))
        print(t, a, want)
json.dump(idx, open("diag/docs/_filings.json", "w"), indent=1)
