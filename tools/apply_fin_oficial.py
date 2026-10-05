#!/usr/bin/env python3
"""
apply_fin_oficial.py — aplică pe o versiune a paginii modificările pentru sursele veniturilor/profitului:
  1. blocul gol FIN_PR imediat după // FIN-END (dacă lipsește);
  2. JS: graficul de venituri marchează trimestrele după sursă (SEC fără marcaj · * comunicatul companiei ·
     † TradingView, provizoriu); sub grafic apare sursa pe trimestre (comunicatele cu link);
     rândul final de sursă: SEC + comunicate + TradingView provizoriu pentru venituri/profit, Yahoo pentru EPS/consens/prețuri;
  3. CSS pentru linkurile din rândul de sursă.

Idempotent: fiecare modificare se sare dacă e deja aplicată; acceptă ca „formă veche” atât codul de pe main (v26),
cât și formele intermediare de pe ramura fin-oficial (v27–v31). Dacă nu găsește nici forma veche, nici pe cea nouă,
se oprește fără să scrie nimic. Scrie rezultatul ca ai-stack-map-mobile-(N+1).html + ai-stack-map-LATEST.html,
în folderul fișierului. Nu modifică fișierul de intrare (regula 1) și nu atinge conținutul FIN / FIN_PR existent.

Rulare:  python3 tools/apply_fin_oficial.py ai-stack-map-mobile-N.html [--no-latest] [--check]
"""
import argparse, os, re, sys

FINPR_BLOCK = '        // FINPR-START (cifre din comunicatele oficiale ale companiilor; scris DOAR de Claude, nu de script)\n        const FIN_PR = {};\n        // FINPR-END\n'

# (nume, forma nouă) — înlocuiri exacte; forma veche e ștearsă complet (regula 2: fără resturi)
EDITS = [
    ('CSS fin-qsrc',
     '        .fin-src { font-size:0.66rem; color:#4a5e7a; margin:-2px 0 15px; }\n        .fin-qsrc { margin:6px 0 0; line-height:1.45; }\n        .fin-qsrc a { color:#7a90aa; }\n'),
    ('grafic venituri: tooltip + marcaj sursă',
     "                const cx = i * gw + gw / 2, [d, rev, ni, src] = r, mg = (ni != null && rev) ? ni / rev * 100 : null, fs = FIN_SRC[src], mk = fs ? fs.mk : '';\n                g += `<g><title>${finQ(d)}${mk} · Venituri ${finMoney(rev)} · Profit net ${finMoney(ni)}${mg!=null?' · Marjă '+mg.toFixed(1)+'%':''}${fs ? ' · sursă: ' + fs.name : ''}</title>"),
    ('grafic venituri: eticheta trimestrului',
     '                    <text x="${cx}" y="${bot + 16}" text-anchor="middle" font-size="10" fill="${FIN_C.ink2}">${finQ(d)}${mk}</text>\n                    <text x="${cx}" y="${bot + 30}" text-anchor="middle" font-size="9.5" fill="${FIN_C.mute}">${mg != null ? \'marjă \''),
    ('funcția finSrcLine',
     '        // Sursa veniturilor/profitului pe trimestre: "SEC" = raportul 10-Q/10-K (XBRL) · "C" = comunicatul de rezultate (FIN_PR, cu link)\n        // · "TV" = TradingView, provizoriu: trimestrul abia raportat, până apare în 10-Q / FIN_PR\n        const FIN_SRC = { SEC: { mk: \'\', name: \'SEC 10-Q/10-K\' }, C: { mk: \'*\', name: \'comunicatul companiei\' }, TV: { mk: \'†\', name: \'TradingView, provizoriu\' } };\n        function finSrcLine(ticker, q) {\n            const pr = (typeof FIN_PR !== \'undefined\' && FIN_PR[ticker]) || [], day = iso => Date.parse(iso + \'T00:00:00Z\');\n            const lab = (src, fn) => q.filter(r => r[3] === src).reverse().map(fn || (r => finQ(r[0]) + FIN_SRC[src].mk));\n            const com = lab(\'C\', r => {\n                const p = pr.find(x => Math.abs(day(x[0]) - day(r[0])) <= 12 * 864e5);\n                return p && p[3] ? `<a href="${finEsc(p[3]).replace(/"/g, \'&quot;\')}" target="_blank" rel="noopener">${finQ(r[0])}*</a>` : finQ(r[0]) + \'*\';\n            });\n            const parts = [[lab(\'SEC\'), \'SEC 10-Q/10-K\'], [com, \'comunicat companie\'], [lab(\'TV\'), \'TradingView, provizoriu\']]\n                .filter(([l]) => l.length).map(([l, n]) => `${n} (${l.join(\', \')})`);\n            return parts.length ? `<div class="fin-note fin-qsrc">Venituri/profit: ${parts.join(\' · \')}</div>` : \'\';\n        }\n\n        // 2) EPS raportat (punct plin) vs estimat (cerc gol) + trimestrul următor (doar consens)\n'),
    ('renderFin: legendă marcaje + sursa pe trimestre',
     '                    <div class="fin-legend"><span><i style="background:${FIN_C.rev}"></i>Venituri</span><span><i style="background:${FIN_C.ni}"></i>Profit net</span>${f.q.some(r => r[3] === \'C\') ? \'<span>* comunicat</span>\' : \'\'}${f.q.some(r => r[3] === \'TV\') ? \'<span>† provizoriu</span>\' : \'\'}</div>\n                    ${finChartRev(f.q)}${finSrcLine(ticker, f.q)}</div>`;'),
    ('rândul final de sursă',
     '            h += `<div class="fin-src">Venituri/profit: SEC, comunicatele companiei; trimestrul abia raportat: TradingView (provizoriu) · EPS, consens, prețuri: Yahoo Finance · actualizat ${f.upd ? fmtIsoDate(f.upd) : \'—\'}</div>`;'),
]

# formele vechi acceptate pentru fiecare modificare (main v26, apoi ramura fin-oficial v27–v31)
OLD_FORMS = {
    'CSS fin-qsrc': [
        '        .fin-src { font-size:0.66rem; color:#4a5e7a; margin:-2px 0 15px; }\n',
    ],
    'grafic venituri: tooltip + marcaj sursă': [
        "                const cx = i * gw + gw / 2, [d, rev, ni] = r, mg = (ni != null && rev) ? ni / rev * 100 : null;\n                g += `<g><title>${finQ(d)} · Venituri ${finMoney(rev)} · Profit net ${finMoney(ni)}${mg!=null?' · Marjă '+mg.toFixed(1)+'%':''}</title>",
        "                const cx = i * gw + gw / 2, [d, rev, ni, src] = r, mg = (ni != null && rev) ? ni / rev * 100 : null, pr = src === 'C';\n                g += `<g><title>${finQ(d)}${pr ? '*' : ''} · Venituri ${finMoney(rev)} · Profit net ${finMoney(ni)}${mg!=null?' · Marjă '+mg.toFixed(1)+'%':''} · sursă: ${pr ? 'comunicatul companiei' : 'SEC 10-Q/10-K'}</title>",
        "                const cx = i * gw + gw / 2, [d, rev, ni, src] = r, mg = (ni != null && rev) ? ni / rev * 100 : null, pr = src === 'C';\n                g += `<g><title>${finQ(d)}${pr ? '*' : ''} · Venituri ${finMoney(rev)} · Profit net ${finMoney(ni)}${mg!=null?' · Marjă '+mg.toFixed(1)+'%':''}${src ? ' · sursă: ' + (pr ? 'comunicatul companiei' : 'SEC 10-Q/10-K') : ''}</title>",
    ],
    'grafic venituri: eticheta trimestrului': [
        '                    <text x="${cx}" y="${bot + 16}" text-anchor="middle" font-size="10" fill="${FIN_C.ink2}">${finQ(d)}</text>\n                    <text x="${cx}" y="${bot + 30}" text-anchor="middle" font-size="9.5" fill="${FIN_C.mute}">${mg != null ? \'marjă \'',
        '                    <text x="${cx}" y="${bot + 16}" text-anchor="middle" font-size="10" fill="${FIN_C.ink2}">${finQ(d)}${pr ? \'*\' : \'\'}</text>\n                    <text x="${cx}" y="${bot + 30}" text-anchor="middle" font-size="9.5" fill="${FIN_C.mute}">${mg != null ? \'marjă \'',
    ],
    'funcția finSrcLine': [
        '        // 2) EPS raportat (punct plin) vs estimat (cerc gol) + trimestrul următor (doar consens)\n',
        '        // Sursa veniturilor/profitului pe trimestre: "SEC" = raportul 10-Q/10-K (XBRL) · "C" = comunicatul de rezultate (FIN_PR, cu link)\n        function finSrcLine(ticker, q) {\n            const pr = (typeof FIN_PR !== \'undefined\' && FIN_PR[ticker]) || [], day = iso => Date.parse(iso + \'T00:00:00Z\');\n            const sec = q.filter(r => r[3] === \'SEC\').reverse().map(r => finQ(r[0]));\n            const com = q.filter(r => r[3] === \'C\').reverse().map(r => {\n                const p = pr.find(x => Math.abs(day(x[0]) - day(r[0])) <= 12 * 864e5);\n                return p && p[3] ? `<a href="${finEsc(p[3]).replace(/"/g, \'&quot;\')}" target="_blank" rel="noopener">${finQ(r[0])}*</a>` : finQ(r[0]) + \'*\';\n            });\n            const parts = [];\n            if (sec.length) parts.push(`SEC 10-Q/10-K (${sec.join(\', \')})`);\n            if (com.length) parts.push(`comunicat companie (${com.join(\', \')})`);\n            return parts.length ? `<div class="fin-note fin-qsrc">Venituri/profit: ${parts.join(\' · \')}</div>` : \'\';\n        }\n\n        // 2) EPS raportat (punct plin) vs estimat (cerc gol) + trimestrul următor (doar consens)\n',
    ],
    'renderFin: legendă marcaje + sursa pe trimestre': [
        '                    <div class="fin-legend"><span><i style="background:${FIN_C.rev}"></i>Venituri</span><span><i style="background:${FIN_C.ni}"></i>Profit net</span></div>\n                    ${finChartRev(f.q)}</div>`;',
        '                    <div class="fin-legend"><span><i style="background:${FIN_C.rev}"></i>Venituri</span><span><i style="background:${FIN_C.ni}"></i>Profit net</span>${f.q.some(r => r[3] === \'C\') ? \'<span>* = comunicatul companiei</span>\' : \'\'}</div>\n                    ${finChartRev(f.q)}${finSrcLine(ticker, f.q)}</div>`;',
    ],
    'rândul final de sursă': [
        '            h += `<div class="fin-src">Sursă: Yahoo Finance (rapoarte trimestriale, estimări consens, istoric prețuri) · actualizat ${f.upd ? fmtIsoDate(f.upd) : \'—\'}</div>`;',
        '            h += `<div class="fin-src">Venituri/profit: rapoarte oficiale (SEC, comunicatele companiei) · EPS, consens, prețuri: Yahoo Finance · actualizat ${f.upd ? fmtIsoDate(f.upd) : \'—\'}</div>`;',
    ],
}



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
    for name, new in EDITS:
        olds = OLD_FORMS[name]
        if new in html:
            steps.append(f"{name}: deja aplicat")
        elif any(html.count(o) == 1 for o in olds):         # cea mai lungă formă găsită (una veche o poate conține pe alta)
            html = html.replace(max((o for o in olds if html.count(o) == 1), key=len), new)
            steps.append(f"{name}: aplicat")
        else:
            raise ValueError(f"{name}: nu găsesc forma veche și nici pe cea nouă")
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
