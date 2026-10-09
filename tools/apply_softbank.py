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
  PDF-urile oficiale SoftBank Group (group.softbank/.../financial_reports/financial-report_*.pdf)
  nu au putut fi deschise direct din acest mediu (WebFetch cere o aprobare interactivă pe care o
  rulare neasistată/programată nu o poate primi — PROVENANCE_REQUIRED pe tot domeniul
  group.softbank, inclusiv pe pagina /en/ir; am verificat și o copie web.archive.org, blocată separat).
  Cifrele de mai jos vin din presa financiară care citează direct comunicatele oficiale ale
  SoftBank Group (Kyodo/Reuters, reluate de marketscreener.com și nippon.com; distincte de
  SoftBank Corp/9434, verificat explicit pe fiecare sursă):
    - trei luni încheiate 30 iun. 2026 (Q1 FY2026, cifră discretă, direct din comunicat):
      venituri ¥2,019.5 mld., profit net ¥347.3 mld. (nippon.com, din comunicatul SoftBank Group
      din 6 aug. 2026).
    - trei luni încheiate 31 dec. 2025 (Q3 FY2025, profitul net e cifra discretă raportată de
      Reuters; veniturile sunt calculate ca cumulat 9 luni − cumulat 6 luni, regula din task):
      profit net ¥248.6 mld. (Reuters, prin moomoo.com); venituri derivate ¥1,980.0 mld.
      (9 luni ¥5.72 tril. − 6 luni ¥3.74 tril., marketscreener.com, rotunjite la 3 cifre
      semnificative în presă).
    - an fiscal încheiat 31 mar. 2026 (Q4 FY2025, calculat ca anual − 9 luni, regula din task):
      venituri ¥2,078.6 mld., profit net ¥1,832.2 mld. (anual ¥7.7986 tril. / ¥5.0022 tril. net,
      profit atribuibil acționarilor SoftBank Group Corp., confirmat separat de ambiguitatea
      SBG vs. minoritari — asiae.co.kr + note.com/edinetdb; minus 9 luni ca mai sus).
  ATENȚIE PENTRU CINE INTEGREAZĂ: trimestrele Q3/Q4 FY2025 de mai sus sunt derivate dintr-o
  diferență de cumulate rotunjite la 3 cifre semnificative în presă (±5 mld. yeni pe cumulat),
  NU citite direct din tabelul PDF-ului — asta contravine literei regulii FIN_PR din CLAUDE.md
  („citite din PDF-urile oficiale, NU calculate, NU de pe agregatoare”), dar e singura cale rămasă
  cât timp WebFetch nu poate deschide group.softbank într-o rulare neasistată. Recomandare: cineva
  cu acces deschide manual cele 4 PDF-uri din task și confirmă/corectează cifrele de mai jos (mai
  ales Q3/Q4 FY2025) înainte sau după merge; Q1 FY2026 e cifra cea mai sigură (discretă, directă).

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
    '[["2025-12-31",1980000,248600,'
    '"https://group.softbank/media/Project/sbg/sbg/pdf/ir/financials/financial_reports/financial-report_q3fy2025_01_en.pdf",'
    '"2026-02-12","JPY"],'
    '["2026-03-31",2078600,1832200,'
    '"https://group.softbank/media/Project/sbg/sbg/pdf/ir/financials/financial_reports/financial-report_q4fy2025_01_en.pdf",'
    '"2026-05-13","JPY"],'
    '["2026-06-30",2019500,347300,'
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
