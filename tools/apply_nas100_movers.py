#!/usr/bin/env python3
"""
apply_nas100_movers.py — aplică pe o versiune a paginii elementul "Winners & Losers NAS100":
  1. CSS: .movers-box / .mv-chip (chip-uri verzi/roșii, scroll orizontal), lângă .eth-tape existent;
  2. HTML: <div id="movers"> nou, imediat sub #tvTape — element SEPARAT de banda TV/ETH (widget-ul TradingView
     ticker-tape e un iframe închis, nu poate primi date proprii), deci vizibil ÎNTOTDEAUNA, nu doar PRE/POST/închis;
  3. JS: moversRow/moversOpen/moversChip/renderMovers, populate din quotes.json.movers (scris de live_quotes.py,
     vezi nas100_movers()); renderMovers() se apelează din ethFetch() existent — fără fetch nou, fără interval nou.
     Click pe un ticker deja urmărit în pagină deschide drawer-ul lui (rowul existent, .click()); altfel link spre
     TradingView, ca la butonul „Deschide în TradingView” din alte locuri. Fără `movers` în JSON (fetch eșuat sau
     cheie absentă): elementul rămâne ascuns (display:none), fără eroare.

Idempotent (regula 2: fără resturi) — fiecare modificare se sare dacă e deja aplicată. Dacă nu găsește nici forma
veche, nici pe cea nouă pentru un pas, se oprește fără să scrie nimic.
Scrie rezultatul ca ai-stack-map-mobile-(N+1).html + ai-stack-map-LATEST.html, în folderul fișierului.
Nu modifică fișierul de intrare (regula 1).

Rulare:  python3 tools/apply_nas100_movers.py ai-stack-map-mobile-N.html [--no-latest] [--check]
"""
import argparse, os, re, sys

OLD_CSS = r'''        .row-live.eth .eth-ses { display:inline-block; }
'''

NEW_CSS = r'''        .row-live.eth .eth-ses { display:inline-block; }
        /* Winners & Losers NAS100: chip-uri din quotes.json.movers (live_quotes.py, nas100_movers()) — element
           nou, separat de banda TV/ETH de mai sus (ticker-tape e iframe închis, nu poate primi date proprii),
           deci vizibil în ORICE sesiune, inclusiv 09:30–16:00 ET. */
        .movers-box { background:#070b16; border:1px solid #1a2840; border-radius:8px; padding:10px 12px; margin-bottom:14px; }
        .movers-head { display:flex; justify-content:space-between; align-items:baseline; gap:8px; margin-bottom:8px; }
        .movers-title { font-size:0.65rem; color:#4a5e7a; text-transform:uppercase; letter-spacing:0.1em; font-weight:bold; white-space:nowrap; }
        .movers-stamp { font-size:0.62rem; color:#4a5e7a; white-space:nowrap; }
        .movers-row { display:flex; gap:7px; overflow-x:auto; padding-bottom:2px; -webkit-overflow-scrolling:touch; }
        .movers-row + .movers-row { margin-top:6px; }
        .movers-row::-webkit-scrollbar { height:3px; }
        .mv-chip { flex-shrink:0; display:inline-flex; align-items:center; gap:4px; font-size:0.74rem; font-weight:bold; padding:5px 9px; border-radius:14px; border:1px solid currentColor; background:rgba(255,255,255,0.03); cursor:pointer; white-space:nowrap; text-decoration:none; }
        .mv-chip.up { color:#10b981; } .mv-chip.down { color:#ef4444; }
'''

OLD_MARKUP = r'''    <div id="tvTape"></div>
'''

NEW_MARKUP = r'''    <div id="tvTape"></div>
    <div class="movers-box" id="movers" style="display:none;">
        <div class="movers-head"><span class="movers-title">📊 Winners &amp; Losers NAS100</span><span class="movers-stamp" id="moversStamp"></span></div>
        <div class="movers-row" id="moversGainers"></div>
        <div class="movers-row" id="moversLosers"></div>
    </div>
'''

OLD_JS_ROW = r'''        function ethRow(box, t) {
            const x = ETH.q[t];
            if (!x) { box.remove(); return; }       // fără date ETH: rămâne prețul din fișier
            box.className = 'row-live eth on';
            box.innerHTML = `<span class="price-badge">${ethPrice(t, x.p)}</span><span class="change-badge" style="color:${ethCol(x.c)};">${ethPct(x.c)}</span>${ethTag(x)}`;
        }
'''

NEW_JS_ROW = r'''        function ethRow(box, t) {
            const x = ETH.q[t];
            if (!x) { box.remove(); return; }       // fără date ETH: rămâne prețul din fișier
            box.className = 'row-live eth on';
            box.innerHTML = `<span class="price-badge">${ethPrice(t, x.p)}</span><span class="change-badge" style="color:${ethCol(x.c)};">${ethPct(x.c)}</span>${ethTag(x)}`;
        }
        // ===== Winners & Losers NAS100: din quotes.json.movers, actualizat de fiecare dată când se termină un
        // ethFetch() (vezi mai jos) — nicio cerere de rețea nouă, niciun interval nou. Vizibil în orice sesiune.
        function moversRow(t) {
            for (const row of document.querySelectorAll('.ticker-row')) {
                if (row.querySelector('.ticker-symbol').innerText.trim() === t) return row;
            }
            return null;
        }
        function moversOpen(t) {
            const row = moversRow(t);
            if (row) { row.scrollIntoView({ behavior: 'smooth', block: 'center' }); row.click(); }
        }
        function moversChip(t, c) {
            const up = c > 0, cls = 'mv-chip ' + (up ? 'up' : 'down');
            const label = `${up ? '▲' : '▼'} ${t} ${up ? '+' : ''}${c.toFixed(1)}%`;
            return moversRow(t) ? `<span class="${cls}" onclick="moversOpen('${t}')">${label}</span>`
                : `<a class="${cls}" href="https://www.tradingview.com/chart/?symbol=${encodeURIComponent(tvSymbol(t))}" target="_blank" rel="noopener">${label}</a>`;
        }
        function renderMovers() {
            const box = document.getElementById('movers'), m = ETH && ETH.movers;
            if (!box) return;
            if (!m || !Array.isArray(m.gainers) || !Array.isArray(m.losers)) { box.style.display = 'none'; return; }  // fără date: ascuns, fără eroare
            box.style.display = '';
            document.getElementById('moversGainers').innerHTML = m.gainers.map(([t, c]) => moversChip(t, c)).join('');
            document.getElementById('moversLosers').innerHTML = m.losers.map(([t, c]) => moversChip(t, c)).join('');
            document.getElementById('moversStamp').innerText = ETH.generated ? ethAgeLabel(new Date(ETH.generated)) : '';
        }
'''

OLD_JS_FETCH = r'''        function ethFetch() {
            const ctl = new AbortController(), to = setTimeout(() => ctl.abort(), 10000);
            return fetch(`${ETH_URL}?ts=${Date.now()}`, { cache: 'no-store', signal: ctl.signal })
                .then(r => { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
                .then(j => { if (!j || !j.q) throw new Error('format'); ETH = j; ethErr = false; })
                .catch(() => { ethErr = true; })   // rămân ultimele cotații primite; fără ele, widget-urile TradingView ca până acum
                .finally(() => { clearTimeout(to); if (liveMode === 'ETH') liveRender(); else liveLabel(); });
        }
'''

NEW_JS_FETCH = r'''        function ethFetch() {
            const ctl = new AbortController(), to = setTimeout(() => ctl.abort(), 10000);
            return fetch(`${ETH_URL}?ts=${Date.now()}`, { cache: 'no-store', signal: ctl.signal })
                .then(r => { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
                .then(j => { if (!j || !j.q) throw new Error('format'); ETH = j; ethErr = false; })
                .catch(() => { ethErr = true; })   // rămân ultimele cotații primite; fără ele, widget-urile TradingView ca până acum
                .finally(() => { clearTimeout(to); if (liveMode === 'ETH') liveRender(); else liveLabel(); renderMovers(); });
        }
'''

# (nume, forma veche, forma nouă) — înlocuiri exacte, câte o singură apariție
EDITS = [
    ("CSS Winners & Losers", OLD_CSS, NEW_CSS),
    ("markup #movers (sub #tvTape)", OLD_MARKUP, NEW_MARKUP),
    ("JS moversRow/moversOpen/moversChip/renderMovers", OLD_JS_ROW, NEW_JS_ROW),
    ("JS ethFetch → renderMovers()", OLD_JS_FETCH, NEW_JS_FETCH),
]


def apply(html):
    """Întoarce (html_nou, listă_de_pași). Ridică ValueError dacă o modificare nu se poate aplica."""
    steps = []
    for name, old, new in EDITS:
        if html.count(new) == 1:
            steps.append(f"{name}: deja aplicat")
        elif html.count(old) == 1:
            html = html.replace(old, new)
            steps.append(f"{name}: aplicat")
        else:
            raise ValueError(f"{name}: nu găsesc (o singură dată) nici forma veche, nici pe cea nouă")
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
