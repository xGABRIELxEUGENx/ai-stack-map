# Investigație: eroarea „!" pe DXY/US10Y în banda live (ticker-tape TradingView)

**Status: investigat, NU am schimbat codul** (nu am putut confirma o soluție prin testul
Playwright cerut — vezi mai jos de ce — iar o schimbare de simbol neverificată riscă să fie mai
rea decât eroarea actuală, dacă scala e diferită).

## Ce am verificat

Captura lui Gabriel: în sesiunea regulată (09:30–16:00 ET), banda `ticker-tape` arată BTC cu preț
normal, dar DXY și US10Y arată doar cerculețul roșu cu „!" în loc de preț.

`const TAPE` (ai-stack-map-mobile-39.html, ~linia 2013) conține un **singur** widget `ticker-tape`
cu toate simbolurile într-un singur apel `tvEmbed(box, 'ticker-tape', { symbols: TAPE.map(...) })`:
`OANDA:NAS100USD, NASDAQ:QQQ, AMEX:SPY, TVC:VIX, BITSTAMP:BTCUSD, TVC:DXY, TVC:US10Y, NASDAQ:NVDA,
NYSE:TSM, NASDAQ:AVGO, NASDAQ:MSFT, NASDAQ:META, NASDAQ:SMH`.

**Concluzie importantă, verificabilă fără rețea, doar citind codul:** parametrii widget-ului
(`showSymbolLogo`, `isTransparent`, `displayMode`, `colorTheme`, `locale`) sunt **identici** pentru
toate cele 13 simboluri din același widget. Dacă doar 2 din 13 simboluri eșuează în timp ce
restul (inclusiv BTC) funcționează, bug-ul **nu poate fi în codul din ai-stack-map** (regulile 2/3
din CLAUDE.md nu se aplică — nu e „resturi de cod" de șters) — e specific simbolului, pe partea
TradingView.

## De ce nu am putut testa live cu Playwright (cum cerea task-ul)

Mediul acesta (sesiune cloud, rulare neasistată) merge printr-un proxy de rețea cu politică de
organizație care **blochează explicit** `s3.tradingview.com` (și alte domenii de widget-uri/
quote-uri live, ex. `query2.finance.yahoo.com`, `www.google.com`) — confirmat direct din
`curl http://127.0.0.1:43545/__agentproxy/status`, care arată `403` („gateway answered 403 to
CONNECT — policy denial") pe `s3.tradingview.com:443`. Instrucțiunile mediului spun explicit să NU
repet și să NU ocolesc o respingere de politică (403/407) — am respectat asta, inclusiv încercarea
de a citi o oglindă web.archive.org (blocată separat, altă eroare).

Am rulat totuși Playwright pe o copie locală (necommisă) a paginii pentru BAC/SFTBY (task-urile 1
și 2) — acolo widget-ul TradingView a eșuat să se încarce din același motiv (`ERR_TUNNEL_
CONNECTION_FAILED`), confirmând din nou că acest mediu nu poate ajunge deloc la tradingview.com,
indiferent de simbol. Deci nu am putut reproduce eroarea „!" nici încerca alternative live, pentru
niciun simbol — testul empiric cerut de task e irealizabil din acest mediu.

## Cercetare (fără acces live la widget, din documentația și suportul TradingView)

- Pagina oficială de FAQ a widget-urilor (`tradingview.com/widget-docs/faq/data/`) spune explicit
  că unele simboluri dau mesajul **„This symbol is only available on TradingView"** în widget-uri
  — o restricție specifică embed-urilor, diferită de disponibilitatea pe tradingview.com însuși.
  Exact genul de bug deja documentat în acest cod pentru NDX: `// NDX e blocat în widget-uri
  (licență Nasdaq) → CFD Nasdaq-100` (`TV_SPECIAL`, linia ~2007) — NDX a fost înlocuit cu
  `OANDA:NAS100USD`, un feed CFD de la un broker, nu simbolul „oficial" al indicelui.
- Articolul de suport TradingView despre DXY (`in.tradingview.com/support/solutions/
  43000474958`) spune că `INDEX:DXY` are doar date EOD, iar **`TVC:DXY`** (cel deja folosit în
  cod) e prezentat ca alternativa CFD cu date real-time gratuite pe tradingview.com — dar asta nu
  exclude ca `TVC:DXY` să fie, separat, restricționat la embed-uri (cele două limitări sunt
  documentat diferite: EOD-only vs. „only available on TradingView").
- Nu am găsit o confirmare clară, independentă, că un simbol alternativ anume (ex. `CAPITALCOM:
  DXY`, `ICEUS:DX1!` pentru DXY; `TVC:TNX`, `CBOT:ZN1!` pentru US10Y) rezolvă exact această eroare
  în widget-ul `ticker-tape` — iar unele din ele schimbă și SCARA valorii afișate (ex. `TNX` e
  istoric cotat ×10 pe unele fluxuri; un futures de preț precum `ZN1!` arată prețul contractului,
  nu randamentul). O schimbare greșită de simbol ar putea afișa o cifră greșită, cu încredere, în
  loc de eroarea vizibilă de acum — mai rău decât starea actuală.
- VIX (`TVC:VIX`) nu a fost menționat ca eronat în captura lui Gabriel (doar DXY și US10Y) — e
  posibil să funcționeze deja corect; nu am schimbat nimic la el.

## Recomandare

Cineva cu acces normal la internet (Gabriel, sau rularea pe GitHub Actions / pe propriul browser)
poate testa direct pe pagina publicată, schimbând pe rând în `TAPE`:
- DXY: încearcă `CAPITALCOM:DXY` (CFD broker, același pattern ca NDX→OANDA) înainte de orice
  variantă `FRED:` (acelea sunt date zilnice ale Fed, nu live intraday — ar „rezolva" eroarea dar
  ar face banda statică pentru acel simbol, o regresie diferită).
- US10Y: încearcă `TVC:TNX`, dar **verifică scara afișată** (ar trebui ~4.x, nu ~43.x) înainte să
  o lași; dacă scara e greșită, nu e o soluție validă.
- Dacă ambele eșuează la fel (cerculeț „!"), e o confirmare suplimentară a limitării generale a
  widget-ului gratuit pentru aceste simboluri (nu doar lipsă de rețea în acest mediu) — caz în care
  rămân cele din `TAPE` neschimbate, cu nota asta ca referință.

Nu am făcut nicio schimbare de cod pentru task-ul 3 (regula CLAUDE.md 3 — nu schimb ce nu pot
verifica, mai degrabă decât să ghicesc un simbol care ar putea afișa o cifră greșită fără avertisment).
