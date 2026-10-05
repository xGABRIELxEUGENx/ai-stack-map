#!/usr/bin/env python3
"""
apply_fin_oficial.py — aplică pe o versiune a paginii modificările „financiare oficiale” (fără Yahoo la venituri/profit):
  1. blocul gol FIN_PR imediat după // FIN-END (dacă lipsește);
  2. JS: graficul de venituri marchează cu * trimestrele din comunicatul companiei ("C");
     sub grafic apare sursa pe trimestre (SEC 10-Q/10-K · comunicat companie, cu link);
     rândul final de sursă: rapoarte oficiale pentru venituri/profit, Yahoo pentru EPS/consens/prețuri;
  3. CSS pentru linkurile din rândul de sursă.

Idempotent: fiecare modificare se sare dacă e deja aplicată; dacă nu găsește nici forma veche, nici pe cea nouă, se oprește
fără să scrie nimic. Scrie rezultatul ca ai-stack-map-mobile-(N+1).html + ai-stack-map-LATEST.html, în folderul fișierului.
Nu modifică fișierul de intrare (regula 1: versiunile se păstrează) și nu atinge conținutul FIN / FIN_PR existent.

Rulare:  python3 tools/apply_fin_oficial.py ai-stack-map-mobile-N.html [--no-latest] [--check]
"""
import argparse, os, re, sys

FINPR_BLOCK = """        // FINPR-START (cifre din comunicatele oficiale ale companiilor; scris DOAR de Claude, nu de script)
        const FIN_PR = {};
        // FINPR-END
"""

# (nume, forma veche, forma nouă) — înlocuiri exacte; forma veche e ștearsă complet (regula 2: fără resturi)
EDITS = [
    ("CSS fin-qsrc",
     """        .fin-src { font-size:0.66rem; color:#4a5e7a; margin:-2px 0 15px; }
""",
     """        .fin-src { font-size:0.66rem; color:#4a5e7a; margin:-2px 0 15px; }
        .fin-qsrc { margin:6px 0 0; line-height:1.45; }
        .fin-qsrc a { color:#7a90aa; }
"""),
    ("grafic venituri: tooltip + * pe trimestrele din comunicat",
     """                const cx = i * gw + gw / 2, [d, rev, ni] = r, mg = (ni != null && rev) ? ni / rev * 100 : null;
                g += `<g><title>${finQ(d)} · Venituri ${finMoney(rev)} · Profit net ${finMoney(ni)}${mg!=null?' · Marjă '+mg.toFixed(1)+'%':''}</title>""",
     """                const cx = i * gw + gw / 2, [d, rev, ni, src] = r, mg = (ni != null && rev) ? ni / rev * 100 : null, pr = src === 'C';
                g += `<g><title>${finQ(d)}${pr ? '*' : ''} · Venituri ${finMoney(rev)} · Profit net ${finMoney(ni)}${mg!=null?' · Marjă '+mg.toFixed(1)+'%':''} · sursă: ${pr ? 'comunicatul companiei' : 'SEC 10-Q/10-K'}</title>"""),
    ("grafic venituri: eticheta trimestrului",
     """                    <text x="${cx}" y="${bot + 16}" text-anchor="middle" font-size="10" fill="${FIN_C.ink2}">${finQ(d)}</text>
                    <text x="${cx}" y="${bot + 30}" text-anchor="middle" font-size="9.5" fill="${FIN_C.mute}">${mg != null ? 'marjă '""",
     """                    <text x="${cx}" y="${bot + 16}" text-anchor="middle" font-size="10" fill="${FIN_C.ink2}">${finQ(d)}${pr ? '*' : ''}</text>
                    <text x="${cx}" y="${bot + 30}" text-anchor="middle" font-size="9.5" fill="${FIN_C.mute}">${mg != null ? 'marjă '"""),
    ("funcția finSrcLine",
     """        // 2) EPS raportat (punct plin) vs estimat (cerc gol) + trimestrul următor (doar consens)
""",
     """        // Sursa veniturilor/profitului pe trimestre: "SEC" = raportul 10-Q/10-K (XBRL) · "C" = comunicatul de rezultate (FIN_PR, cu link)
        function finSrcLine(ticker, q) {
            const pr = (typeof FIN_PR !== 'undefined' && FIN_PR[ticker]) || [], day = iso => Date.parse(iso + 'T00:00:00Z');
            const sec = q.filter(r => r[3] === 'SEC').reverse().map(r => finQ(r[0]));
            const com = q.filter(r => r[3] === 'C').reverse().map(r => {
                const p = pr.find(x => Math.abs(day(x[0]) - day(r[0])) <= 12 * 864e5);
                return p && p[3] ? `<a href="${finEsc(p[3]).replace(/"/g, '&quot;')}" target="_blank" rel="noopener">${finQ(r[0])}*</a>` : finQ(r[0]) + '*';
            });
            const parts = [];
            if (sec.length) parts.push(`SEC 10-Q/10-K (${sec.join(', ')})`);
            if (com.length) parts.push(`comunicat companie (${com.join(', ')})`);
            return parts.length ? `<div class="fin-note fin-qsrc">Venituri/profit: ${parts.join(' · ')}</div>` : '';
        }

        // 2) EPS raportat (punct plin) vs estimat (cerc gol) + trimestrul următor (doar consens)
"""),
    ("renderFin: legendă * + sursa pe trimestre",
     """                    <div class="fin-legend"><span><i style="background:${FIN_C.rev}"></i>Venituri</span><span><i style="background:${FIN_C.ni}"></i>Profit net</span></div>
                    ${finChartRev(f.q)}</div>`;""",
     """                    <div class="fin-legend"><span><i style="background:${FIN_C.rev}"></i>Venituri</span><span><i style="background:${FIN_C.ni}"></i>Profit net</span>${f.q.some(r => r[3] === 'C') ? '<span>* = comunicatul companiei</span>' : ''}</div>
                    ${finChartRev(f.q)}${finSrcLine(ticker, f.q)}</div>`;"""),
    ("rândul final de sursă",
     """            h += `<div class="fin-src">Sursă: Yahoo Finance (rapoarte trimestriale, estimări consens, istoric prețuri) · actualizat ${f.upd ? fmtIsoDate(f.upd) : '—'}</div>`;""",
     """            h += `<div class="fin-src">Venituri/profit: rapoarte oficiale (SEC, comunicatele companiei) · EPS, consens, prețuri: Yahoo Finance · actualizat ${f.upd ? fmtIsoDate(f.upd) : '—'}</div>`;"""),
]


def apply(html):
    """Întoarce (html_nou, listă_de_pași). Ridică ValueError dacă o modificare nu se poate aplica."""
    steps = []
    if "// FINPR-START" in html:
        steps.append("bloc FIN_PR: există deja")
    else:
        m = re.search(r"^[ \t]*// FIN-END[^\n]*\n", html, re.M)
        if not m:
            raise ValueError("nu găsesc linia // FIN-END")
        html = html[:m.end()] + FINPR_BLOCK + html[m.end():]
        steps.append("bloc FIN_PR: adăugat (gol)")
    for name, old, new in EDITS:
        if new in html:
            steps.append(f"{name}: deja aplicat")
        elif html.count(old) == 1:
            html = html.replace(old, new)
            steps.append(f"{name}: aplicat")
        else:
            raise ValueError(f"{name}: nu găsesc forma veche (de {html.count(old)} ori) și nici pe cea nouă")
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
