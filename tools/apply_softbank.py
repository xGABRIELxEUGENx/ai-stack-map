#!/usr/bin/env python3
"""
apply_softbank.py — adaugă SoftBank Group Corp (ticker intern „SFTBY”) ca ticker nou în planșa M1
(Indici, ETF-uri & Giganți Financiari): holding-ul japonez (TSE: 9984), cel mai mare backer extern
al OpenAI — semnal de finanțare pentru ecosistemul AI, nu producător (regula din CLAUDE.md „Când
adaugi un ticker nou”).

IMPORTANT — nu se confundă cu SoftBank Corp (TSE: 9434), filiala de telecom japoneză: e o companie
diferită, cu CIK/ADR diferit. Compania-holding (9984) NU depune nimic la SEC: CIK0001764097 e
„SoftBank Corp./ADR” și are doar F-6/F-6EF/424B3 (înregistrare ADR), niciun 6-K/20-F financiar —
deci NO_EDGAR obligatoriu. Nu are ADR pe NYSE/Nasdaq, doar OTC ilichid (SFTBY) → TV_SPECIAL cu
listarea principală TSE:9984, nu TV_EX.

Ce aplică (idempotent — sare peste tot ce e deja aplicat):
  1. rândul SFTBY în grid-mf-l1 + contorul stratului M1 (+1);
  2. linia SFTBY în EARNINGS (confirmat, din notificarea oficială SoftBank Group IR);
  3. SFTBY în IR_LINKS;
  4. SFTBY în NO_EDGAR;
  5. SFTBY în TV_SPECIAL → TSE:9984;
  6. FIN_PR — 3 trimestre reale (vezi mai jos).

FIN_PR — sursă și metodă (an fiscal aprilie–martie, cifre în JPY, milioane):
  CORECTAT la integrare (Claude, coordonator) — varianta inițială a acestui script folosea cifre din
  presă (agentul care a construit branch-ul a raportat explicit că WebFetch n-a putut deschide
  group.softbank din mediul lui). La verificare, din mediul de integrare PDF-urile oficiale S-AU
  putut deschide direct — cifrele de mai jos sunt citite efectiv din cele 4 PDF-uri (nu din presă),
  cu scădere de cumulate, exact ca derivarea T4 din SEC în update_stack_map.py:
    - cumulat 3 luni (Q1 FY2026, 1 apr.–30 iun. 2026), direct din statement, discret prin definiție:
      venituri ¥2,019,591M, profit net atribuibil ¥347,330M
      (financial-report_q1fy2026_01_en.pdf, „Tokyo, August 6, 2026”)
    - cumulat 6 luni (H1 FY2025, 1 apr.–30 sep. 2025): venituri ¥3,736,843M, profit net ¥2,924,066M
      (financial-report_q2fy2025_01_en.pdf)
    - cumulat 9 luni (FY2025, 1 apr.–31 dec. 2025): venituri ¥5,719,247M, profit net ¥3,172,653M
      (financial-report_q3fy2025_01_en.pdf, „Tokyo, February 12, 2026”)
    - cumulat 12 luni (FY2025, 1 apr. 2025–31 mar. 2026): venituri ¥7,798,650M, profit net ¥5,002,271M
      (financial-report_q4fy2025_01_en.pdf, „Tokyo, May 13, 2026”) — niciunul din cele 4 PDF-uri nu are
      tabel separat cu trimestrul discret, deci Q3/Q4 FY2025 se derivă prin scădere:
    - Q3 FY2025 (31 dec. 2025) = 9 luni − 6 luni: venituri 5,719,247−3,736,843=¥1,982,404M;
      profit net 3,172,653−2,924,066=¥248,587M
    - Q4 FY2025 (31 mar. 2026) = 12 luni − 9 luni: venituri 7,798,650−5,719,247=¥2,079,403M;
      profit net 5,002,271−3,172,653=¥1,829,618M
  Profitul net e cel atribuibil acționarilor SoftBank Group Corp. (nu include minoritarii), conform
  regulii FIN_PR.

Rulare:  python3 tools/apply_softbank.py ai-stack-map-mobile-N.html [--no-latest] [--check]
"""
import argparse, os, re, sys

MS_ROW_RE = re.compile(
    r"            <div class=\"ticker-row\" onclick=\"openDetails\('MS',.*?\n            </div>\n",
    re.S)

SFTBY_ROW = """
            <div class="ticker-row" onclick="openDetails('SFTBY','SoftBank Group (ADR)','$18.04','+1.18%','#10b981','206.08B','2.5M','—',['macro'],'Holding japonez (TSE: 9984) — NU SoftBank Corp/9434 (telecom). Cel mai mare backer extern al OpenAI (SVF2 + participație directă). Semnal de finanțare AI, nu producător. ADR OTC (SFTBY), ilichid.')">
                <div class="ticker-meta"><span class="ticker-symbol" style="color:#ec4899;">SFTBY</span><span class="ticker-company">SoftBank Group (ADR)</span><div class="tag-container"><span class="strategy-tag">OpenAI Backer</span><span class="strategy-tag">AI Funding Proxy</span></div></div>
                <div class="ticker-perf"><span class="price-badge">$18.04</span><span class="change-badge" style="color:#10b981;">+1.18%</span></div>
            </div>
"""

LAYER_COUNT_RE = re.compile(
    r"(<span class=\"layer-id\" style=\"color:#ec4899;\">M1</span><span class=\"layer-name\">"
    r"· Indici, ETF-uri & Giganți Financiari<span class=\"layer-count\">\()(\d+)(\)</span></span>)")

MA_EARN_RE = re.compile(r"\n            'MA': \{ date:'[^']*', session:'[^']*', status:'[^']*', time:'[^']*', src:'[^']*' \},\n")
SFTBY_EARN_LINE = "            'SFTBY': { date:'2026-11-10', session:'BMO', status:'confirmat', time:'01:30', src:'SoftBank Group IR 2 Oct 2026 – briefing 16:30 JST (01:30 ET)' },\n"

MS_IR_RE = re.compile(r"            'MS':'[^']*',\n")
SFTBY_IR_LINE = "            'SFTBY':'https://group.softbank/en/ir',\n"

NO_EDGAR_RE = re.compile(r'(const NO_EDGAR = \[)(.*?)(\];)')
TV_SPECIAL_RE = re.compile(r"(const TV_SPECIAL = \{ )(.*?)( \}; //[^\n]*\n)")
SAP_FINPR_RE = re.compile(r'            "SAP": \[.*?\],\n')
SFTBY_FINPR_LINE = (
    '            "SFTBY": '
    '[["2025-12-31",1982404,248587,'
    '"https://group.softbank/media/Project/sbg/sbg/pdf/ir/financials/financial_reports/financial-report_q3fy2025_01_en.pdf",'
    '"2026-02-12","JPY"],'
    '["2026-03-31",2079403,1829618,'
    '"https://group.softbank/media/Project/sbg/sbg/pdf/ir/financials/financial_reports/financial-report_q4fy2025_01_en.pdf",'
    '"2026-05-13","JPY"],'
    '["2026-06-30",2019591,347330,'
    '"https://group.softbank/media/Project/sbg/sbg/pdf/ir/financials/financial_reports/financial-report_q1fy2026_01_en.pdf",'
    '"2026-08-06","JPY"]],\n'
)


def apply(html):
    steps = []
    already = "openDetails('SFTBY'," in html

    if already:
        steps.append("rând SFTBY + contor M1: deja aplicat")
    else:
        m = MS_ROW_RE.search(html)
        if not m:
            raise ValueError("nu găsesc rândul MS în grid-mf-l1 (ancoră pentru inserare)")
        html = html[:m.end()] + SFTBY_ROW + html[m.end():]
        cm = LAYER_COUNT_RE.search(html)
        if not cm:
            raise ValueError("nu găsesc contorul stratului M1 (layer-count)")
        html = html[:cm.start()] + cm.group(1) + str(int(cm.group(2)) + 1) + cm.group(3) + html[cm.end():]
        steps.append("rând SFTBY: adăugat + contor M1 incrementat")

    if "'SFTBY': { date:" in html:
        steps.append("EARNINGS SFTBY: deja aplicat")
    else:
        m = MA_EARN_RE.search(html)
        if not m:
            raise ValueError("nu găsesc linia EARNINGS pentru MA (ancoră pentru inserare)")
        html = html[:m.end()] + SFTBY_EARN_LINE + html[m.end():]
        steps.append("EARNINGS SFTBY: adăugat")

    if "'SFTBY':'https://" in html:
        steps.append("IR_LINKS SFTBY: deja aplicat")
    else:
        m = MS_IR_RE.search(html)
        if not m:
            raise ValueError("nu găsesc linia IR_LINKS pentru MS (ancoră pentru inserare)")
        html = html[:m.end()] + SFTBY_IR_LINE + html[m.end():]
        steps.append("IR_LINKS SFTBY: adăugat")

    m = NO_EDGAR_RE.search(html)
    if not m:
        raise ValueError("nu găsesc NO_EDGAR")
    if '"SFTBY"' in m.group(2):
        steps.append("NO_EDGAR SFTBY: deja aplicat")
    else:
        html = html[:m.start()] + m.group(1) + m.group(2) + ', "SFTBY"' + m.group(3) + html[m.end():]
        steps.append("NO_EDGAR SFTBY: adăugat")

    m = TV_SPECIAL_RE.search(html)
    if not m:
        raise ValueError("nu găsesc TV_SPECIAL")
    if "SFTBY:" in m.group(2):
        steps.append("TV_SPECIAL SFTBY: deja aplicat")
    else:
        html = html[:m.start()] + m.group(1) + m.group(2) + ", SFTBY:'TSE:9984'" + m.group(3) + html[m.end():]
        steps.append("TV_SPECIAL SFTBY → TSE:9984: adăugat")

    if '"SFTBY": [' in html:
        steps.append("FIN_PR SFTBY: deja aplicat")
    else:
        m = SAP_FINPR_RE.search(html)
        if not m:
            raise ValueError("nu găsesc intrarea FIN_PR pentru SAP (ancoră pentru inserare)")
        html = html[:m.end()] + SFTBY_FINPR_LINE + html[m.end():]
        steps.append("FIN_PR SFTBY: adăugat (3 trimestre — vezi notele din capul fișierului)")

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
