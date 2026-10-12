#!/usr/bin/env python3
"""
apply_tv_live.py — feed-ul live vine din TradingView; unde TradingView e deschis, e deschis și în pagină.

Înlocuiește calendarul propriu al paginii (sesiune calculată pe ceasul ET, 09:30–16:00 = TradingView, restul = quotes.json)
cu o împărțire pe tipul instrumentului:
  1. Banda de sus: widget-ul TradingView `ticker-tape` în ORICE moment (nu mai există banda proprie ETH). Indicii, futures,
     VIX, DXY, US10Y, petrol, BTC sunt cotați de TradingView aproape 24h (de duminică 18:00 ET, inclusiv în zile de sărbătoare
     bancară) — deschiderea o decide TradingView, nu un calendar din pagină.
  2. Rândurile din TV_SPECIAL (NDX, VIX, WTI, BRENT, SFTBY): widget-ul TradingView `single-quote` în orice moment.
  3. Acțiunile și ETF-urile: tot TradingView în sesiunea regulată; în PRE / POST / închis rămâne fluxul ETH din quotes.json,
     pentru că widget-urile gratuite TradingView nu arată la acțiuni decât sesiunea regulată.
Șterge întâi ce înlocuiește (banda ETH: CSS, ETH_TAPE_KEY, ETH_NO_DOLLAR, ethTape()), apoi scrie codul nou (regula 2).

Idempotent — fiecare modificare se sare dacă e deja aplicată. Dacă nu găsește nici forma veche, nici pe cea nouă pentru un pas,
se oprește fără să scrie nimic. Scrie rezultatul ca ai-stack-map-mobile-(N+1).html + ai-stack-map-LATEST.html. Nu modifică
fișierul de intrare (regula 1).

Rulare:  python3 tools/apply_tv_live.py ai-stack-map-mobile-N.html [--no-latest] [--check]
"""
import argparse, os, re, sys

EDITS = []


def edit(name, old, new):
    EDITS.append((name, old, new))


edit("CSS banda ETH → șters", r'''        /* flux ETH (PRE / POST / închis): banda proprie și prețul pe rând, din quotes.json */
        .eth-tape { display:flex; overflow:hidden; height:46px; align-items:center; }
        .eth-track { display:flex; flex-shrink:0; align-items:center; gap:22px; padding-right:22px; white-space:nowrap; animation:ethScroll 50s linear infinite; }
        .eth-tape:hover .eth-track { animation-play-state:paused; }
        @keyframes ethScroll { from { transform:translateX(0); } to { transform:translateX(-100%); } }
        @media (prefers-reduced-motion: reduce) { .eth-tape { overflow-x:auto; } .eth-track { animation:none; } }
        .eth-item { font-size:0.78rem; font-weight:bold; color:#d8e4f0; }
        .eth-item b { color:#7a90aa; margin-right:6px; }
        .eth-item i { font-style:normal; margin-left:6px; }
''', r'''        /* flux ETH (doar acțiuni, în PRE / POST / închis): prețul pe rând, din quotes.json */
''')

edit("loadTape: întotdeauna TradingView", r'''            if (ethOn()) { ethTape(box); return; }
            tvEmbed(box, 'ticker-tape', {''', r'''            tvEmbed(box, 'ticker-tape', {''')

edit("refreshLive: reîncarcă banda", r'''            if (liveMode === 'TV') liveRender();
            ethFetch();                       // în PRE/POST/închis, banda și rândurile se redesenează după răspuns
''', r'''            loadTape();
            if (liveMode === 'TV') liveRender();
            ethFetch();                       // în PRE/POST/închis, rândurile de acțiuni se redesenează după răspuns
''')

edit("comentariu flux ETH", r'''        // ===== Flux ETH: în afara sesiunii regulate (PRE, POST, închis), prețurile vin din quotes.json
        // (Yahoo, ~15 min întârziere), generat la 15 minute de .github/workflows/live.yml pe ramura `live`.
        // În sesiunea regulată (09:30–16:00 ET, luni–vineri) rămân widget-urile TradingView.
''', r'''        // ===== Flux ETH, doar pentru ACȚIUNI și ETF-uri: widget-urile gratuite TradingView le arată numai în sesiunea regulată,
        // deci în PRE, POST și închis prețurile lor vin din quotes.json (Yahoo, generat de .github/workflows/live.yml pe ramura `live`).
        // Banda de sus și rândurile din TV_SPECIAL (indici, futures, VIX, petrol, SFTBY) sunt TradingView în orice moment:
        // TradingView decide când sunt deschise (de duminică 18:00 ET, inclusiv în sărbători bancare), nu un calendar din pagină.
''')

edit("ETH_TAPE_KEY + ETH_NO_DOLLAR → șterse", r'''        const ETH_TAPE_KEY = { NAS100: 'NQ' };          // NAS100 din bandă → contractul futures Nasdaq (NQ=F), care se mișcă în ETH
        const ETH_NO_DOLLAR = ['NDX', 'VIX', 'NQ', 'DXY', 'US10Y'];
''', '')

edit("ethPrice fără ETH_NO_DOLLAR", r'''            return (ETH_NO_DOLLAR.includes(k) ? '' : '$') + p.toLocaleString(''', r'''            return '$' + p.toLocaleString(''')

edit("ethTape() → șters", r'''        function ethTape(box) {
            const items = TAPE.map(([, title]) => {
                const k = ETH_TAPE_KEY[title] || title, x = ETH.q[k];
                return x ? `<span class="eth-item"><b>${k}</b>${ethPrice(k, x.p)}<i style="color:${ethCol(x.c)}">${ethPct(x.c)}</i><span class="eth-ses s-${x.s}">${ETH_SES[x.s] || x.s}</span></span>` : '';
            }).join('');
            box.className = '';
            box.innerHTML = items ? `<div class="eth-tape"><div class="eth-track">${items}</div><div class="eth-track" aria-hidden="true">${items}</div></div>`
                                  : '<div class="tv-fail">Flux ETH fără date pentru bandă</div>';
        }
''', '')

edit("liveLabel: acțiuni ETH, restul TradingView", r'''                    txt = (liveSes === 'CLOSED' ? 'Închis · ultimele cotații ETH' : 'ETH') + ' (' + ethAgeLabel(g) + ')';
                    col = stale ? '#ef4444' : (liveSes === 'CLOSED' ? '#7a90aa' : '#f59e0b');
                    stamp = stale ? 'flux neactualizat de mult — posibil blocat' : '';''',
     r'''                    txt = (liveSes === 'CLOSED' ? 'Acțiuni închise · ultimele cotații ETH' : 'Acțiuni ETH') + ' (' + ethAgeLabel(g) + ')';
                    col = stale ? '#ef4444' : (liveSes === 'CLOSED' ? '#7a90aa' : '#f59e0b');
                    stamp = stale ? 'flux neactualizat de mult — posibil blocat' : 'bandă, indici, futures: TradingView live';''')

edit("liveRender: banda nu se mai reconstruiește la schimbarea sesiunii", r'''        function liveRender() { loadTape(); rowLiveReset(); liveLabel(); }''',
     r'''        function liveRender() { rowLiveReset(); liveLabel(); }''')

edit("liveTick: fără placeholder de bandă", r'''            else {                                             // încărcare sau 16:00: banda și rândurile se desenează după răspuns
                if (was === null) { document.getElementById('tvTape').innerHTML = '<div class="tv-fail">Se încarcă cotațiile ETH…</div>'; liveLabel(); }
                ethFetch();
            }
''', r'''            else ethFetch();                                   // încărcare sau 16:00: rândurile de acțiuni se desenează după răspuns
''')

edit("rowLiveLoad: TV_SPECIAL mereu TradingView", r'''            if (ethOn()) { ethRow(box, t); return; }
            box.className = 'row-live';''', r'''            if (ethOn() && !TV_SPECIAL[t]) { ethRow(box, t); return; }   // TV_SPECIAL (indici, futures, VIX, petrol, SFTBY): mereu TradingView
            box.className = 'row-live';''')

edit("comentariu rânduri", r'''        // ===== Preț live pe fiecare rând (widget TradingView sau, în afara sesiunii regulate, flux ETH; doar rândurile vizibile) =====''',
     r'''        // ===== Preț live pe fiecare rând (widget TradingView; la acțiuni, în afara sesiunii regulate, flux ETH; doar rândurile vizibile) =====''')

edit("inițializare: banda se încarcă o dată", r'''        tvStamp = 'încărcat ' + fmtLocalTime(new Date());
        liveTick();''', r'''        tvStamp = 'încărcat ' + fmtLocalTime(new Date());
        loadTape();
        liveTick();''')


def apply(html):
    steps = []
    for name, old, new in EDITS:
        if new and html.count(new) == 1 and html.count(old) == 0:
            steps.append(f"{name}: deja aplicat")
        elif not new and html.count(old) == 0:
            steps.append(f"{name}: deja aplicat")
        elif html.count(old) == 1:
            html = html.replace(old, new)
            steps.append(f"{name}: aplicat")
        else:
            raise ValueError(f"{name}: nu găsesc (o singură dată) forma veche")
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
