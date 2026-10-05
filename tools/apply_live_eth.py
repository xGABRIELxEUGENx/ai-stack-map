#!/usr/bin/env python3
"""
apply_live_eth.py — aplică pe o versiune a paginii modificările pentru fluxul ETH (pre-market / after-hours / închis):
  1. CSS: banda proprie ETH (derulare CSS, fără biblioteci) și prețul ETH pe rând, cu badge de sesiune;
  2. HTML: eticheta barei live primește <span id="liveSrc"> (textul se schimbă după sesiune);
  3. JS: comportamentul hibrid —
       sesiunea regulată (09:30–16:00 ET, luni–vineri): banda TV și widget-urile TV pe rânduri, exact ca înainte;
       PRE / POST / închis: banda proprie și prețurile pe rânduri din quotes.json (ramura `live`, ~15 min întârziere),
       citit la încărcare, la Refresh și automat la 5 minute; sesiunea (America/New_York) se reverifică la fiecare minut,
       iar trecerea la 09:30 / 16:00 reconstruiește banda și rândurile fără reîncărcare;
       dacă fetch-ul eșuează și nu există date ETH, rămân widget-urile TV, iar eticheta spune „flux ETH indisponibil”.
     Drawer-ul (graficul mini TV) rămâne neschimbat.

Idempotent: fiecare modificare se sare dacă e deja aplicată; forma veche (main v16–v30) e înlocuită complet
(regula 2: fără resturi). Dacă nu găsește nici forma veche, nici pe cea nouă, se oprește fără să scrie nimic.
Scrie rezultatul ca ai-stack-map-mobile-(N+1).html + ai-stack-map-LATEST.html, în folderul fișierului.
Nu modifică fișierul de intrare (regula 1).

Rulare:  python3 tools/apply_live_eth.py ai-stack-map-mobile-N.html [--no-latest] [--check]
"""
import argparse, os, re, sys

OLD_CSS = r'''        .tv-fail { padding:14px; font-size:0.78rem; color:#7a90aa; line-height:1.5; }
'''

NEW_CSS = r'''        .tv-fail { padding:14px; font-size:0.78rem; color:#7a90aa; line-height:1.5; }
        /* flux ETH (PRE / POST / închis): banda proprie și prețul pe rând, din quotes.json */
        .eth-tape { display:flex; overflow:hidden; height:46px; align-items:center; }
        .eth-track { display:flex; flex-shrink:0; align-items:center; gap:22px; padding-right:22px; white-space:nowrap; animation:ethScroll 50s linear infinite; }
        .eth-tape:hover .eth-track { animation-play-state:paused; }
        @keyframes ethScroll { from { transform:translateX(0); } to { transform:translateX(-100%); } }
        @media (prefers-reduced-motion: reduce) { .eth-tape { overflow-x:auto; } .eth-track { animation:none; } }
        .eth-item { font-size:0.78rem; font-weight:bold; color:#d8e4f0; }
        .eth-item b { color:#7a90aa; margin-right:6px; }
        .eth-item i { font-style:normal; margin-left:6px; }
        .eth-ses { font-size:0.58rem; font-weight:bold; letter-spacing:0.04em; color:#7a90aa; border:1px solid currentColor; border-radius:3px; padding:0 4px; margin-left:6px; white-space:nowrap; }
        .eth-ses.s-PRE { color:#f59e0b; } .eth-ses.s-POST { color:#818cf8; } .eth-ses.s-REG { color:#10b981; }
        .row-live.eth { text-align:right; }
        .row-live.eth .eth-ses { display:inline-block; margin:3px 0 0; }
'''

OLD_LABEL = r'''    <div class="live-bar"><span class="live-lbl">● Live · TradingView <span id="liveStamp" style="color:#4a5e7a;font-weight:normal;"></span></span><button class="live-btn" onclick="refreshLive()">🔄 Refresh</button></div>
'''

NEW_LABEL = r'''    <div class="live-bar"><span class="live-lbl">● <span id="liveSrc">Live · TradingView</span> <span id="liveStamp" style="color:#4a5e7a;font-weight:normal;"></span></span><button class="live-btn" onclick="refreshLive()">🔄 Refresh</button></div>
'''

OLD_JS = r'''        function loadTape() {
            const box = document.getElementById('tvTape');
            if (!box || !navigator.onLine) { if (box) box.innerHTML = '<div class="tv-fail">Offline — prețuri live indisponibile</div>'; return; }
            tvEmbed(box, 'ticker-tape', {
                symbols: TAPE.map(([proName, title]) => ({ proName, title })),
                showSymbolLogo: false, isTransparent: true, displayMode: 'compact', colorTheme: 'dark', locale: 'en'
            }, () => { box.innerHTML = '<div class="tv-fail">Banda TradingView nu s-a încărcat (conexiune / blocată de browser)</div>'; });
        }

        function loadDrawerLive(ticker) {
            const box = document.getElementById('tvLive');
            const tv = tvSymbol(ticker);
            document.getElementById('tvLiveSym').innerText = tv;
            const fail = () => { box.innerHTML = `<div class="tv-fail">Widget-ul live nu s-a încărcat. <a href="https://www.tradingview.com/chart/?symbol=${encodeURIComponent(tv)}" target="_blank" rel="noopener" style="color:#00c8f0;">Deschide ${ticker} în TradingView ↗</a></div>`; };
            if (!navigator.onLine) { fail(); return; }
            tvEmbed(box, 'mini-symbol-overview', {
                symbol: tv, width: '100%', height: 190, locale: 'en', dateRange: '1D',
                colorTheme: 'dark', isTransparent: true, autosize: false, largeChartUrl: ''
            }, fail);
        }

        function refreshLive() {
            loadTape();
            rowLiveReset();
            const open = document.getElementById('detailsDrawer').classList.contains('open');
            if (open) loadDrawerLive(document.getElementById('drawSymbol').innerText.trim());
            const s = document.getElementById('liveStamp');
            if (s) s.innerText = 'actualizat ' + new Date().toLocaleTimeString('ro-RO', { hour:'2-digit', minute:'2-digit' });
        }

        // ===== Preț live pe fiecare rând (widget TradingView, încărcat doar pentru rândurile vizibile) =====
        function rowLiveLoad(row) {
            if (row.dataset.live) return;
            row.dataset.live = '1';
            const t = row.querySelector('.ticker-symbol').innerText.trim();
            const perf = row.querySelector('.ticker-perf');
            let box = row.querySelector('.row-live');
            if (!box) { box = document.createElement('div'); perf.parentNode.insertBefore(box, perf); }
            box.className = 'row-live';
            tvEmbed(box, 'single-quote', { symbol: tvSymbol(t), width: '100%', isTransparent: true, colorTheme: 'dark', locale: 'en' },
                () => { box.className = 'row-live'; box.innerHTML = ''; });   // rezervă: rămâne prețul din fișier
            box.classList.add('row-live');
            const iv = setInterval(() => { if (box.querySelector('iframe')) { box.classList.add('on'); clearInterval(iv); } }, 300);
            setTimeout(() => clearInterval(iv), 10500);
        }
        const rowLiveIO = ('IntersectionObserver' in window) ? new IntersectionObserver(entries => {
            entries.forEach(e => { if (e.isIntersecting && navigator.onLine) { rowLiveLoad(e.target); rowLiveIO.unobserve(e.target); } });
        }, { rootMargin: '200px' }) : null;
        function rowLiveObserve(row) { if (rowLiveIO) rowLiveIO.observe(row); }
        function rowLiveReset() {
            document.querySelectorAll('.ticker-row').forEach(row => {
                delete row.dataset.live;
                const box = row.querySelector('.row-live'); if (box) box.remove();
                rowLiveObserve(row);
            });
        }
        document.querySelectorAll('.ticker-row').forEach(rowLiveObserve);
        loadTape();
        document.getElementById('liveStamp').innerText = 'încărcat ' + new Date().toLocaleTimeString('ro-RO', { hour:'2-digit', minute:'2-digit' });
'''

NEW_JS = r'''        function loadTape() {
            const box = document.getElementById('tvTape');
            if (!box || !navigator.onLine) { if (box) box.innerHTML = '<div class="tv-fail">Offline — prețuri live indisponibile</div>'; return; }
            if (ethOn()) { ethTape(box); return; }
            tvEmbed(box, 'ticker-tape', {
                symbols: TAPE.map(([proName, title]) => ({ proName, title })),
                showSymbolLogo: false, isTransparent: true, displayMode: 'compact', colorTheme: 'dark', locale: 'en'
            }, () => { box.innerHTML = '<div class="tv-fail">Banda TradingView nu s-a încărcat (conexiune / blocată de browser)</div>'; });
        }

        function loadDrawerLive(ticker) {
            const box = document.getElementById('tvLive');
            const tv = tvSymbol(ticker);
            document.getElementById('tvLiveSym').innerText = tv;
            const fail = () => { box.innerHTML = `<div class="tv-fail">Widget-ul live nu s-a încărcat. <a href="https://www.tradingview.com/chart/?symbol=${encodeURIComponent(tv)}" target="_blank" rel="noopener" style="color:#00c8f0;">Deschide ${ticker} în TradingView ↗</a></div>`; };
            if (!navigator.onLine) { fail(); return; }
            tvEmbed(box, 'mini-symbol-overview', {
                symbol: tv, width: '100%', height: 190, locale: 'en', dateRange: '1D',
                colorTheme: 'dark', isTransparent: true, autosize: false, largeChartUrl: ''
            }, fail);
        }

        function refreshLive() {
            const open = document.getElementById('detailsDrawer').classList.contains('open');
            if (open) loadDrawerLive(document.getElementById('drawSymbol').innerText.trim());
            tvStamp = 'actualizat ' + fmtLocalTime(new Date());
            if (liveMode === 'TV') liveRender();
            ethFetch();                       // în PRE/POST/închis, banda și rândurile se redesenează după răspuns
        }

        // ===== Flux ETH: în afara sesiunii regulate (PRE, POST, închis), prețurile vin din quotes.json
        // (Yahoo, ~15 min întârziere), generat la 15 minute de .github/workflows/live.yml pe ramura `live`.
        // În sesiunea regulată (09:30–16:00 ET, luni–vineri) rămân widget-urile TradingView.
        const ETH_URL = 'https://raw.githubusercontent.com/xGABRIELxEUGENx/ai-stack-map/live/quotes.json';
        const ETH_TAPE_KEY = { NAS100: 'NQ' };          // NAS100 din bandă → contractul futures Nasdaq (NQ=F), care se mișcă în ETH
        const ETH_NO_DOLLAR = ['NDX', 'VIX', 'NQ', 'DXY', 'US10Y'];
        const ETH_SES = { PRE: 'PRE', REG: 'REG', POST: 'POST', CLOSED: 'ÎNCHIS' };
        let ETH = null, ethErr = false, liveMode = null, liveSes = null, tvStamp = '';
        function nySession(d) {
            const p = nyParts(d), m = p.h * 60 + p.mi;
            if (['Sat', 'Sun'].includes(p.wd)) return 'CLOSED';
            return m >= 240 && m < 570 ? 'PRE' : m >= 570 && m < 960 ? 'REG' : m >= 960 && m < 1200 ? 'POST' : 'CLOSED';
        }
        const ethOn = () => liveMode === 'ETH' && !!ETH;
        const ethCol = c => c > 0 ? '#10b981' : c < 0 ? '#ef4444' : '#7a90aa';
        const ethPct = c => (c > 0 ? '+' : '') + c.toFixed(2) + '%';
        function ethPrice(k, p) {
            const d = Math.abs(p) < 1 ? 4 : 2;
            return (ETH_NO_DOLLAR.includes(k) ? '' : '$') + p.toLocaleString('en-US', { minimumFractionDigits: d, maximumFractionDigits: d });
        }
        // badge de sesiune: „PRE 08:45 ET”; cu piața închisă: „ÎNCHIS · POST 19:55 ET”; din altă zi (ET): cu ziua
        function ethTag(x) {
            const d = new Date(x.t), p = nyParts(d), n = nyParts(new Date());
            const day = (p.d !== n.d || p.m !== n.m) ? d.toLocaleDateString('ro-RO', { weekday: 'short', timeZone: NY_TZ }) + ' ' : '';
            const tag = `${ETH_SES[x.s] || x.s} ${day}${pad(p.h)}:${pad(p.mi)} ET`;
            return `<span class="eth-ses s-${x.s}">${liveSes === 'CLOSED' && x.s !== 'CLOSED' ? 'ÎNCHIS · ' + tag : tag}</span>`;
        }
        function ethTape(box) {
            const items = TAPE.map(([, title]) => {
                const k = ETH_TAPE_KEY[title] || title, x = ETH.q[k];
                return x ? `<span class="eth-item"><b>${k}</b>${ethPrice(k, x.p)}<i style="color:${ethCol(x.c)}">${ethPct(x.c)}</i><span class="eth-ses s-${x.s}">${ETH_SES[x.s] || x.s}</span></span>` : '';
            }).join('');
            box.className = '';
            box.innerHTML = items ? `<div class="eth-tape"><div class="eth-track">${items}</div><div class="eth-track" aria-hidden="true">${items}</div></div>`
                                  : '<div class="tv-fail">Flux ETH fără date pentru bandă</div>';
        }
        function ethRow(box, t) {
            const x = ETH.q[t];
            if (!x) { box.remove(); return; }       // fără date ETH: rămâne prețul din fișier
            box.className = 'row-live eth on';
            box.innerHTML = `<span class="price-badge">${ethPrice(t, x.p)}</span><span class="change-badge" style="color:${ethCol(x.c)};">${ethPct(x.c)}</span>${ethTag(x)}`;
        }
        function liveLabel() {
            const src = document.getElementById('liveSrc'), st = document.getElementById('liveStamp');
            let txt = 'Live · TradingView', stamp = tvStamp, col = '';
            if (liveMode === 'ETH') {
                if (ETH) {
                    const g = new Date(ETH.generated), today = g.toDateString() === new Date().toDateString();
                    txt = liveSes === 'CLOSED' ? 'Închis · ultimele cotații ETH' : 'Live · ETH (PRE/POST, ~15 min întârziere)';
                    col = liveSes === 'CLOSED' ? '#7a90aa' : '#f59e0b';
                    stamp = 'generat ' + (today ? '' : fmtLocalDate(g) + ' ') + fmtLocalTime(g);
                }
                if (ethErr) stamp += (stamp ? ' · ' : '') + 'flux ETH indisponibil';
            }
            src.innerText = txt; st.innerText = stamp; src.parentNode.style.color = col;
        }
        function liveRender() { loadTape(); rowLiveReset(); liveLabel(); }
        function ethFetch() {
            const ctl = new AbortController(), to = setTimeout(() => ctl.abort(), 10000);
            return fetch(`${ETH_URL}?ts=${Date.now()}`, { cache: 'no-store', signal: ctl.signal })
                .then(r => { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
                .then(j => { if (!j || !j.q) throw new Error('format'); ETH = j; ethErr = false; })
                .catch(() => { ethErr = true; })   // rămân ultimele cotații primite; fără ele, widget-urile TradingView ca până acum
                .finally(() => { clearTimeout(to); if (liveMode === 'ETH') liveRender(); else liveLabel(); });
        }
        // sesiunea curentă (ET), reverificată la fiecare minut: trecerea la 09:30 / 16:00 reconstruiește banda și rândurile
        function liveTick() {
            const s = nySession(new Date());
            if (s === liveSes) return;
            const was = liveMode;
            liveSes = s; liveMode = s === 'REG' ? 'TV' : 'ETH';
            if (liveMode === 'TV') { liveRender(); if (was === null) ethFetch(); }
            else if (was === 'ETH') liveRender();              // PRE → POST → închis: aceleași date, alt badge / etichetă
            else {                                             // încărcare sau 16:00: banda și rândurile se desenează după răspuns
                if (was === null) { document.getElementById('tvTape').innerHTML = '<div class="tv-fail">Se încarcă cotațiile ETH…</div>'; liveLabel(); }
                ethFetch();
            }
        }

        // ===== Preț live pe fiecare rând (widget TradingView sau, în afara sesiunii regulate, flux ETH; doar rândurile vizibile) =====
        function rowLiveLoad(row) {
            if (row.dataset.live) return;
            row.dataset.live = '1';
            const t = row.querySelector('.ticker-symbol').innerText.trim();
            const perf = row.querySelector('.ticker-perf');
            let box = row.querySelector('.row-live');
            if (!box) { box = document.createElement('div'); perf.parentNode.insertBefore(box, perf); }
            if (ethOn()) { ethRow(box, t); return; }
            box.className = 'row-live';
            tvEmbed(box, 'single-quote', { symbol: tvSymbol(t), width: '100%', isTransparent: true, colorTheme: 'dark', locale: 'en' },
                () => { box.className = 'row-live'; box.innerHTML = ''; });   // rezervă: rămâne prețul din fișier
            box.classList.add('row-live');
            const iv = setInterval(() => { if (box.querySelector('iframe')) { box.classList.add('on'); clearInterval(iv); } }, 300);
            setTimeout(() => clearInterval(iv), 10500);
        }
        const rowLiveIO = ('IntersectionObserver' in window) ? new IntersectionObserver(entries => {
            entries.forEach(e => { if (e.isIntersecting && navigator.onLine) { rowLiveLoad(e.target); rowLiveIO.unobserve(e.target); } });
        }, { rootMargin: '200px' }) : null;
        function rowLiveObserve(row) { if (rowLiveIO) rowLiveIO.observe(row); }
        function rowLiveReset() {
            document.querySelectorAll('.ticker-row').forEach(row => {
                delete row.dataset.live;
                const box = row.querySelector('.row-live'); if (box) box.remove();
                rowLiveObserve(row);
            });
        }
        tvStamp = 'încărcat ' + fmtLocalTime(new Date());
        liveTick();
        setInterval(liveTick, 60e3);
        setInterval(ethFetch, 5 * 60e3);
'''

# (nume, forma veche, forma nouă) — înlocuiri exacte, câte o singură apariție
EDITS = [
    ("CSS flux ETH", OLD_CSS, NEW_CSS),
    ("eticheta live (liveSrc)", OLD_LABEL, NEW_LABEL),
    ("JS hibrid TradingView / ETH", OLD_JS, NEW_JS),
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
