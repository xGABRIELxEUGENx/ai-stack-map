#!/usr/bin/env python3
"""
apply_bac.py — adaugă BAC (Bank of America) ca ticker nou în planșa M1 (Indici, ETF-uri & Giganți
Financiari), lângă JPM/GS/V/MA/MS: bancă money-center, proxy pentru finanțarea prin credit
sindicalizat/corporativ a capex-ului AI al hyperscalerilor (regula din CLAUDE.md „Când adaugi un
ticker nou”). Companie americană SEC-reporting normală (10-Q/10-K) → `q` din FIN vine automat din
SEC la rularea update_stack_map.py; nu are nevoie de FIN_PR manual, de YAHOO_SYMBOL special (BAC e
simbol Yahoo direct) sau de NO_EDGAR/TV_SPECIAL.

Ce aplică (idempotent — sare peste tot ce e deja aplicat):
  1. rândul BAC în grid-mf-l1 + contorul stratului M1 (+1);
  2. linia BAC în EARNINGS (confirmat, din comunicatul oficial BofA Newsroom);
  3. BAC în IR_LINKS;
  4. BAC în TV_EX['NYSE'].

Date reale la data scrierii (vor fi reîmprospătate automat de update_stack_map.py la următoarea
rulare pe main): preț/mcap/volum/P-E din StockAnalysis + public.com + fullratio.com, închiderea de
pe 8 oct. 2026 ($53.61, +0.17%, mcap $374.88B, volum 28.71M, P/E trailing 12.21).

Earnings Q3 2026: confirmat oficial — Bank of America Newsroom, comunicat 30 sep. 2026:
"Bank of America to Report Third Quarter 2026 Financial Results and Host Investor Conference Call
on October 14" — rezultate 14 oct. 2026, ~06:45 ET, call 08:30 ET.
(https://newsroom.bankofamerica.com/content/newsroom/press-releases/2026/09/bank-of-america-to-report-third-quarter-2026-financial-results-a.html)

Rulare:  python3 tools/apply_bac.py ai-stack-map-mobile-N.html [--no-latest] [--check]
"""
import argparse, os, re, sys

MS_ROW_RE = re.compile(
    r"            <div class=\"ticker-row\" onclick=\"openDetails\('MS',.*?\n            </div>\n",
    re.S)

BAC_ROW = """
            <div class="ticker-row" onclick="openDetails('BAC','Bank of America','$53.61','+0.17%','#10b981','374.88B','28.7M','12.21',['macro'],'A doua bancă US ca active. Barometru pentru consum/credit și pentru finanțarea prin credit sindicalizat/corporativ a capex-ului AI al hyperscalerilor.')">
                <div class="ticker-meta"><span class="ticker-symbol" style="color:#ec4899;">BAC</span><span class="ticker-company">Bank of America</span><div class="tag-container"><span class="strategy-tag">Money Center Bank</span><span class="strategy-tag">AI Capex Financing</span></div></div>
                <div class="ticker-perf"><span class="price-badge">$53.61</span><span class="change-badge" style="color:#10b981;">+0.17%</span></div>
            </div>
"""

LAYER_COUNT_RE = re.compile(
    r"(<span class=\"layer-id\" style=\"color:#ec4899;\">M1</span><span class=\"layer-name\">"
    r"· Indici, ETF-uri & Giganți Financiari<span class=\"layer-count\">\()(\d+)(\)</span></span>)")

MA_EARN_RE = re.compile(r"\n            'MA': \{ date:'[^']*', session:'[^']*', status:'[^']*', time:'[^']*', src:'[^']*' \},\n")
BAC_EARN_LINE = "            'BAC': { date:'2026-10-14', session:'BMO', status:'confirmat', time:'06:45', src:'Bank of America Newsroom 30 Sep 2026 – call 08:30 ET' },\n"

MS_IR_RE = re.compile(r"            'MS':'[^']*',\n")
BAC_IR_LINE = "            'BAC':'https://investor.bankofamerica.com/',\n"

TV_EX_NYSE_RE = re.compile(r"(NYSE: ')([^']*)(')")


def apply(html):
    steps = []
    already = "openDetails('BAC'," in html

    if already:
        steps.append("rând BAC + contor M1: deja aplicat")
    else:
        m = MS_ROW_RE.search(html)
        if not m:
            raise ValueError("nu găsesc rândul MS în grid-mf-l1 (ancoră pentru inserare)")
        html = html[:m.end()] + BAC_ROW + html[m.end():]
        cm = LAYER_COUNT_RE.search(html)
        if not cm:
            raise ValueError("nu găsesc contorul stratului M1 (layer-count)")
        html = html[:cm.start()] + cm.group(1) + str(int(cm.group(2)) + 1) + cm.group(3) + html[cm.end():]
        steps.append("rând BAC: adăugat + contor M1 incrementat")

    if "'BAC': { date:" in html:
        steps.append("EARNINGS BAC: deja aplicat")
    else:
        m = MA_EARN_RE.search(html)
        if not m:
            raise ValueError("nu găsesc linia EARNINGS pentru MA (ancoră pentru inserare)")
        html = html[:m.end()] + BAC_EARN_LINE + html[m.end():]
        steps.append("EARNINGS BAC: adăugat")

    if "'BAC':'https://" in html:
        steps.append("IR_LINKS BAC: deja aplicat")
    else:
        m = MS_IR_RE.search(html)
        if not m:
            raise ValueError("nu găsesc linia IR_LINKS pentru MS (ancoră pentru inserare)")
        html = html[:m.end()] + BAC_IR_LINE + html[m.end():]
        steps.append("IR_LINKS BAC: adăugat")

    m = TV_EX_NYSE_RE.search(html)
    if not m:
        raise ValueError("nu găsesc TV_EX['NYSE']")
    tickers = m.group(2).split()
    if "BAC" in tickers:
        steps.append("TV_EX NYSE BAC: deja aplicat")
    else:
        html = html[:m.start()] + m.group(1) + (m.group(2) + " BAC") + m.group(3) + html[m.end():]
        steps.append("TV_EX NYSE BAC: adăugat")

    return html, steps


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("html", help="ai-stack-map-mobile-N.html")
    ap.add_argument("--no-latest", action="store_true", help="nu copia rezultatul în ai-stack-map-LATEST.html")
    ap.add_argument("--check", action="store_true", help="doar arată ce s-ar aplica, fără să scrie")
    a = ap.parse_args()
    m = re.search(r"ai-stack-map-mobile-(\d+)\.html$", a.html)
    if not m:
        sys.exit("Fișierul trebuie să se numească ai-stack-map-mobile-N.html")
    src = open(a.html, encoding="utf-8").read()
    try:
        out, steps = apply(src)
    except ValueError as e:
        sys.exit(f"OPRIT, nimic scris: {e}")
    print("\n".join("  " + s for s in steps))
    if out == src:
        print("Totul era deja aplicat — nu scriu versiune nouă.")
        return
    if a.check:
        return
    folder = os.path.dirname(os.path.abspath(a.html))
    dst = os.path.join(folder, f"ai-stack-map-mobile-{int(m.group(1)) + 1}.html")
    if os.path.exists(dst):
        sys.exit(f"OPRIT: {os.path.basename(dst)} există deja (regula 1: nu se rescrie o versiune). Rulează pe ultima versiune.")
    open(dst, "w", encoding="utf-8").write(out)
    if not a.no_latest:
        open(os.path.join(folder, "ai-stack-map-LATEST.html"), "w", encoding="utf-8").write(out)
    print(f"Scris: {os.path.basename(dst)}" + ("" if a.no_latest else " + ai-stack-map-LATEST.html"))


if __name__ == "__main__":
    main()
