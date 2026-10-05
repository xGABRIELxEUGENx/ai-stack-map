# AI Stack Map — reguli pentru Claude

Proiectul lui Gabriel (trader independent). Comunicare în **română**, concis, verificat, cu surse.
Link public (GitHub Pages): https://xgabrielxeugenx.github.io/ai-stack-map/ (deschide `ai-stack-map-LATEST.html`).

## Ce e în repo

| Fișier | Rol |
|---|---|
| `ai-stack-map-mobile-N.html` | Versiunile, câte una pe actualizare. N cel mai mare = starea curentă. |
| `ai-stack-map-LATEST.html` | Copie identică a ultimei versiuni. E adresa fixă din spatele linkului. |
| `index.html` | Redirecționează linkul către `ai-stack-map-LATEST.html`. |
| `update_stack_map.py` | Scriptul de actualizare: prețuri, earnings, EPS, consens, reacții din Yahoo Finance (`yfinance`); venituri/profit net trimestrial din SEC EDGAR + `FIN_PR`, iar trimestrul abia raportat provizoriu din TradingView scanner. |
| `tools/apply_fin_oficial.py` | Aplică idempotent blocul `FIN_PR` și JS-ul pentru sursele financiare pe o versiune dată, scriind N+1. |
| `.github/workflows/update.yml` | Rulează scriptul luni–vineri, 21:30 UTC, după închiderea bursei US. Se poate porni și manual. Cere secretul `SEC_USER_AGENT` = „Nume email”. |
| `update-log.txt` | Jurnalul rulărilor: schimbări de earnings, tickeri fără date. |
| `live_quotes.py` | Fluxul ETH (pre-market / after-hours / închis): scrie `quotes.json` din Yahoo (`yfinance`). Independent de `update_stack_map.py`. |
| `.github/workflows/live.yml` | Rulează `live_quotes.py` la 15 minute, luni–vineri, și publică `quotes.json` pe ramura orfană `live`. |
| `tools/apply_live_eth.py` | Aplică idempotent pe o versiune dată CSS-ul, eticheta și JS-ul hibrid TradingView / ETH, scriind N+1. |

Ce face scriptul la fiecare rulare:
1. Pornește de la ultima versiune N și scrie N+1 plus `LATEST`.
2. Pentru fiecare ticker actualizează prețul, %, market cap, volumul și P/E.
3. Actualizează datele de earnings, numai ca `estimat`.
4. Actualizează datele trimestriale (blocul `FIN`):
   - venituri și profit net (`q`), ultimele 5 trimestre:
     - istoricul din rapoartele SEC 10-Q/10-K (XBRL, marcate `SEC`), automat; dacă SEC nu răspunde, păstrează `q` din versiunea anterioară;
     - companiile fără SEC trimestrial (străine: TSM, ASML, SAP, SKHY, CCJ, GFS, NBIS) din comunicatele din `FIN_PR` (marcate `C`); un rând `C` intră și la americani, dacă e la > 45 de zile după ultimul raport SEC;
     - **trimestrul abia raportat**, din seara publicării: TradingView scanner (`revenue_fq`, `net_income_fq`, `fiscal_period_end_fq`), marcat `TV` = provizoriu, doar dacă e la > 45 de zile după ultimul rând oficial și doar în USD (TradingView convertește companiile străine în USD, deci la ele nu se folosește). Rândul `TV` e înlocuit automat când apare trimestrul în SEC sau în `FIN_PR`; atunci scriptul scrie în `update-log.txt` „OK/DIFERENȚĂ TradingView vs SEC|C …”;
   - EPS raportat vs estimat, consensul trimestrului următor (`nx`) și reacția prețului (`rx`): Yahoo;
   - scrie în `update-log.txt` „DIFERENȚĂ comunicat vs SEC …” când un trimestru din `FIN_PR` diferă cu > 0.5% de valoarea SEC (sfârșit ±12 zile).

## Prețurile live din pagină — hibrid TradingView / flux ETH

Sesiunea se calculează în browser, în America/New_York, și se reverifică la fiecare minut. Trecerea la 09:30 și la 16:00 ET reconstruiește banda și rândurile fără reîncărcare.

- **Sesiunea regulată (09:30–16:00 ET, luni–vineri):** widget-urile TradingView, la deschiderea paginii: banda `ticker-tape` și `single-quote` pe fiecare rând vizibil. Eticheta: „Live · TradingView”.
- **PRE (04:00–09:30), POST (16:00–20:00) și închis (noaptea, weekend):** widget-urile gratuite TV arată la acțiuni doar sesiunea regulată, deci pagina trece pe fluxul propriu `quotes.json`:
  - pe rânduri: prețul, % colorat după semn și un badge de sesiune („PRE 08:45 ET”, „POST 17:30 ET”, „ÎNCHIS · POST 19:55 ET”; cu ziua, dacă cotația e din altă zi ET); fără date pentru ticker rămâne prețul din fișier;
  - banda: proprie, aceleași elemente ca `TAPE`; NAS100 → `NQ` (contractul futures NQ=F, care se mișcă în ETH);
  - eticheta: „Live · ETH (PRE/POST, ~15 min întârziere)” sau „Închis · ultimele cotații ETH”, cu ora generării;
  - fetch-ul se face la încărcare, la Refresh și automat la 5 minute. Dacă eșuează, rămân ultimele cotații primite; fără ele, widget-urile TV ca înainte. Eticheta spune „flux ETH indisponibil”.
- Drawer-ul (graficul mini TV) e același în toate sesiunile.
- Zilele de sărbătoare ale bursei nu sunt tratate separat: între 09:30 și 16:00 ET pagina arată widget-urile TV.

**Fluxul ETH (`quotes.json`):**
- Sursă: Yahoo prin `yfinance`, în două cereri pe loturi: `period="2d", interval="5m", prepost=True` pentru ultimul preț și ora lui; `period="7d", interval="1d"` pentru închiderile regulate.
- Tickeri: toți `openDetails('T'` din ultima versiune. Simboluri speciale: NDX→^NDX, VIX→^VIX, WTI→CL=F, BRENT→BZ=F. Doar pentru bandă: NQ→NQ=F, BTC→BTC-USD, DXY→DX-Y.NYB, US10Y→^TNX.
- Program: `live.yml`, cron `*/15 8-23 * * 1-5` și `*/15 0-1 * * 2-6` (UTC), care acoperă 04:00–20:00 ET și vara, și iarna. Scriptul iese fără să scrie în weekend și în afara intervalului 04:00–20:15 ET (`--force` doar pentru teste). Se poate porni și manual (Run workflow).
- Format: `{"generated": "…Z", "q": {"NVDA": {"p": preț, "c": % față de ref, "ref": închiderea de referință, "s": "PRE|REG|POST|CLOSED", "t": "ora barei, ISO UTC"}, …}, "missing": [tickeri fără date]}`.
  - `s` = sesiunea după ora barei în ET;
  - `ref`: în PRE și REG, închiderea regulată anterioară; în POST, închiderea regulată de azi; la BTC, închiderea zilei UTC anterioare.
- Dacă lipsesc peste jumătate dintre tickeri, scriptul nu scrie fișierul (exit 1), iar pe ramura `live` rămâne ultimul `quotes.json` bun.
- Publicare: ramura orfană `live`, un singur commit, refăcut la fiecare rulare și împins cu force push. Pagina îl citește de la `https://raw.githubusercontent.com/xGABRIELxEUGENx/ai-stack-map/live/quotes.json?ts=<timp>` (CORS permis).
- **`quotes.json` nu e versiune și nu se ține în `main`.** Nu intră sub regula 1 sau regula 4: e un flux live, refăcut la 15 minute. Pagina rămâne completă fără el (cade pe widget-urile TV și pe prețurile din fișier).
- O schimbare de pagină pentru live se aplică tot ca versiune nouă N+1 (`tools/apply_live_eth.py`).

## Regulile, fiecare cu domeniul ei de aplicare

1. **Versiunile se păstrează (la nivel de fișier).** Nu șterge și nu rescrie niciodată un `ai-stack-map-mobile-N.html` existent. Orice schimbare devine o versiune nouă N+1, apoi se copiază identic în `LATEST`. Versiunile vechi servesc la urmărirea bug-urilor: când ceva se strică, compari cu ultima versiune bună înainte să faci teorii sau să scrii cod.
2. **Fără resturi (la nivel de cod, în versiunea nouă).** Ce înlocuiește o schimbare se șterge **întâi**, apoi se scrie codul nou. Codul mort creat sau rămas în urma schimbării se elimină în același update, fără să întrebi. Regula nu contrazice regula 1: versiunile vechi rămân ca fișiere, dar în fișierul nou nu rămân resturi.
3. **Nu schimba ce nu s-a cerut.** Regula 2 se aplică doar codului atins de cerere. Restul fișierului rămâne neatins. „Refă” înseamnă „readu ce mergea”, nu „reproiectează”.
4. **Fișierul conține mereu starea completă.** Fiecare actualizare scrie **toate** datele fiecărui ticker, nu doar un câmp. Ultima versiune trebuie să fie completă și corectă fără să depindă de alte fișiere.
5. **Earnings — statusurile:**
   - `confirmat`: **doar** cu anunț oficial al companiei (comunicat sau pagina de investitori). Sursa se trece în `src`. Ora exactă ET se trece în `time`, doar dacă e anunțată.
   - `estimat`: orice altă sursă (Yahoo, MarketBeat, Nasdaq, TradingView…), inclusiv când Yahoo spune „dată neestimată”.
   - `neverificat`: nu există nicio dată publică. `n/a`: ETF-uri, indici, mărfuri.
   - Nu ghici niciodată o dată.
6. **Independență = fără cont, fără cheie API.** Sursele publice gratuite sunt permise: Yahoo, TradingView, GitHub. Excepție acceptată de Gabriel: confirmarea oficială a earnings o face Claude zilnic (vezi mai jos).
7. **Fără verificări sâmbăta și duminica** (bursa US e închisă).
8. **Versiunea la finalul numelui.** Orice fișier livrat se termină cu versiunea (`…-25.html`, „… v25”), nu cu data sau cu o etichetă descriptivă. Fac excepție doar `ai-stack-map-LATEST.html` și `index.html`, care sunt adrese fixe, nu versiuni.

## Formate pe care scriptul le citește — nu le schimba forma

- **Rândul unui ticker** (`ROW_RE` în script):
  `<div class="ticker-row" onclick="openDetails('T','Nume','$preț','+x.xx%','#culoare','mcap','vol','pe',['strat'],'descriere')">`, apoi `price-badge` și `change-badge`.
  Contorul `(N)` din antetul stratului trebuie actualizat când adaugi sau scoți rânduri.
- **Earnings**: o linie pe ticker, exact așa (`EARN_LINE_RE`):
  `'T': { date:'YYYY-MM-DD', session:'BMO|AMC|?', status:'confirmat|estimat|neverificat|n/a', time:'HH:MM sau gol', src:'...' },`
  Scriptul **nu suprascrie** un `confirmat` cu dată viitoare. Dacă Yahoo arată altă dată, scriptul doar scrie un AVERTISMENT în `update-log.txt`.
- **`FIN`**: blocul dintre `// FIN-START` și `// FIN-END` e scris **doar de script**. Nu-l edita de mână.
  Rândul din `q`: `[sfârșit_trimestru, venituri_M, profit_net_M, "SEC"|"C"|"TV"]`, în moneda raportului. În pagină: `*` = comunicat, `†` = TradingView provizoriu.
- **`FIN_PR`**: blocul dintre `// FINPR-START` și `// FINPR-END`, imediat după `FIN-END`, e scris **doar de Claude** (scriptul doar îl citește), numai din documentul oficial al companiei (8-K/6-K anexa 99.1 pe sec.gov, comunicatul sau raportul de pe pagina de investitori), cu URL-ul exact. JSON valid, o linie pe ticker, trimestrele în ordine cronologică:
  `"T": [["YYYY-MM-DD" (sfârșitul trimestrului fiscal), venituri_milioane, profit_net_milioane, "url_sursă", "YYYY-MM-DD" (data comunicatului), "MONEDA"], ...]`
  - venituri = venitul total raportat (la bănci, venitul net total); profit net = profitul net GAAP/IFRS atribuibil companiei (nu ajustat). Dacă documentul nu dă cifra, scrii `null` — nu calculezi și nu ghicești;
  - cifrele în moneda raportului, fără conversie, în milioane;
  - fără document găsit, nu completezi.

## Când adaugi un ticker nou, completezi toate locurile

1. Rândul în stratul potrivit și contorul `(N)`.
2. Linia în `EARNINGS`.
3. `IR_LINKS` (pagina oficială de investitori).
4. Bursa în `TV_EX` (NASDAQ/NYSE/AMEX).
5. Dacă nu e acțiune:
   - în pagină: `TV_SPECIAL`, `NO_EDGAR` și eventual `SRC_OVERRIDE`;
   - în script: `YAHOO_SYMBOL` și `NO_EARNINGS`;
   - în `live_quotes.py`: `YAHOO_SYMBOL` (simbolul Yahoo pentru fluxul ETH);
   - în pagină, dacă e indice fără „$”: `ETH_NO_DOLLAR`.

## Verificări înainte de commit

- JS valid: extrage conținutul tag-urilor `<script>` și rulează `node --check`.
- `python3 -m py_compile update_stack_map.py` dacă ai atins scriptul.
- Deschide pagina, de exemplu cu Playwright, și verifică că rândurile și drawer-ul se afișează fără erori.
- Yahoo poate fi blocat din mediul tău de lucru. Datele reale le aduce workflow-ul de pe GitHub (Actions → Update AI Stack Map → Run workflow).

## Confirmarea zilnică a earnings (luni–vineri, făcută de Claude)

1. Ia starea curentă: ultimul `ai-stack-map-mobile-N.html` din repo, după `git pull`.
2. Verifică tickerii din `EARNINGS` care au data în următoarele ~21 de zile și nu sunt încă `confirmat`, plus cei `neverificat`.
   - Sursa principală: pagina oficială din `IR_LINKS` (comunicatul „to report / conference call”).
   - Poți căuta pe web anunțul companiei, dar treci `confirmat` doar dacă vezi comunicatul oficial.
3. Pentru fiecare confirmare scrie:
   - data și sesiunea (`BMO`/`AMC`) din comunicat;
   - `time` = ora exactă ET a publicării, dacă e anunțată (nu ora call-ului);
   - `src` = sursa și data comunicatului.
   Dacă data oficială diferă de cea din fișier, folosește data oficială.
3b. **Trimestrul nou în `FIN_PR`, doar pentru companiile fără SEC trimestrial** (TSM, ASML, SAP, SKHY, CCJ, GFS, NBIS — cele al căror `q` vine din rânduri `C`): dacă una a raportat în ultimele 3 zile lucrătoare, citește comunicatul de rezultate (6-K anexa 99.1 pe sec.gov sau pagina de investitori) și adaugă trimestrul nou în `FIN_PR`, cu regulile de mai sus (cifre citite efectiv, URL exact, moneda raportului). Companiile americane nu se completează de mână: trimestrul nou vine automat din TradingView (provizoriu), apoi din SEC.
4. Fără nicio confirmare nouă și niciun trimestru nou în `FIN_PR`: nu crea versiune nouă și nu face commit. Raportează scurt: „nicio confirmare nouă azi”.
5. Cu confirmări noi sau trimestre noi în `FIN_PR`:
   - creează N+1 cu **doar** acele linii schimbate (regula 3) și copiază-l în `LATEST`;
   - validează JS-ul;
   - fă commit cu mesajul `Confirmări earnings <data> — v<N+1>` și push pe `main`;
   - raportează lui Gabriel un tabel scurt: ticker, data, sesiunea, ora și link spre sursa oficială; pentru `FIN_PR`: ticker, trimestru, venituri, profit, link.

## Cross-check — două metode DIFERITE, în paralel (luni, miercuri, vineri)

Principiul lui Gabriel: o verificare făcută cu aceeași metodă repetă aceleași unghiuri moarte. De aceea cele două verificări folosesc metode, surse și trasee de date diferite, iar erorile lor nu se suprapun.

Pentru amândouă:
- **Nu modifici fișierele și nu faci commit** (doar `crosscheck.yml` scrie raportul B). O eroare găsită se corectează la cauză, adică în script sau în procedură, după discuția cu Gabriel, nu prin peticirea unei valori.
- Yahoo nu e sursă de control pentru preț, %, market cap, volum, P/E și earnings, pentru că e chiar sursa scriptului pentru acestea. La venituri și profit net, pagina folosește doar documente oficiale (SEC + comunicate), deci acolo Yahoo e o sursă de control independentă.

### Cross-check aleatoriu — Metoda A (judecată pe eșantion, din documente primare; în conversația cu Gabriel)

1. Starea verificată: ultimul `ai-stack-map-mobile-N.html`, plus data rulării care l-a produs, din `update-log.txt`.
2. Eșantion: **8 tickeri aleși cu `random.sample`**. Cel puțin unul din Energy sau Macro și unul care raportează în altă monedă decât USD. Scrie lista în raport.
3. Citește documentele primare și compară:
   - **Prețul și %** față de închiderea zilei: StockAnalysis, Nasdaq.com sau site-ul bursei.
   - **Earnings**:
     - un `confirmat` trebuie să aibă comunicatul oficial (deschizi sursa din `src`);
     - un `estimat` trebuie să fie apropiat de cel puțin încă o estimare publică;
     - dacă compania a anunțat între timp data oficial, semnalezi.
   - **Trimestrial**: ultimul trimestru față de comunicatul de rezultate sau de 10-Q/6-K; pentru un rând `C`, deschizi URL-ul din `FIN_PR`.
   - **Ce nu poate prinde codul**:
     - ticker delistat, fuzionat sau redenumit;
     - companie pusă în stratul greșit;
     - descriere depășită;
     - bursa greșită (widget-ul live nu se încarcă);
     - link oficial mort.
4. Raport: tabel cu ticker, câmp, fișier, control, sursă (link) și verdict, plus sumarul.

### Metoda B (cod automat pe TOȚI tickerii, alte surse; GitHub + Claude Code)

- `crosscheck.py` e un script independent: nu importă nimic din `update_stack_map.py`. Rulează prin `.github/workflows/crosscheck.yml` (luni, miercuri, vineri, 06:10 UTC) și scrie `crosscheck-report.md` și `crosscheck-history.csv`.
- **Surse de control**:
  - TradingView scanner pentru preț, %, market cap, volum și P/E;
  - Yahoo Finance (`yfinance`, `quarterly_income_stmt`: „Total Revenue”, „Net Income”) pentru venituri și profit net trimestrial, comparat cu rândurile `q` (potrivire după dată ±12 zile; Yahoo normalizează la sfârșit de lună). EROARE la ≥ 15%, DIFERENȚĂ la ≥ 3%, cu nota „Yahoo definește unele cifre diferit (bănci, derivate la energie, ajustări)”.
- **Verificări interne**:
  - JS valid; `LATEST` identic cu ultima versiune;
  - contoarele straturilor; dubluri în același strat;
  - EARNINGS ↔ rânduri; culoarea % față de semn; badge-ul față de drawer;
  - acțiuni (mcap/preț) stabile între versiuni;
  - nicio dată de earnings trecută; niciun `confirmat` fără sursă oficială;
  - vechimea `FIN`; bursa din `TV_EX` față de bursa reală.
- **Clasificare**: „EROARE” = probabil greșit; „DIFERENȚĂ” = poate avea cauză legitimă:
  - P/E calculat diferit între surse;
  - prima ADR față de bursa locală;
  - instrumente care se tranzacționează ~24h (WTI, BRENT, VIX), unde contează momentul citirii;
  - dividend la data ex-dividend.
- **Rolul lui Claude Code** (sarcina programată, 09:54 ora României): citește raportul B al zilei, investighează fiecare EROARE până la cauza probabilă (bug de script, sursă, definiție) și raportează lui Gabriel. Nu repetă metoda A.
