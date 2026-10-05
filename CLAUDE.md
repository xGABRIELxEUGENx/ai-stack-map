# AI Stack Map — reguli pentru Claude

Proiectul lui Gabriel (trader independent). Comunicare în **română**, concis, verificat, cu surse.
Link public (GitHub Pages): https://xgabrielxeugenx.github.io/ai-stack-map/ (deschide `ai-stack-map-LATEST.html`).

## Ce e în repo

| Fișier | Rol |
|---|---|
| `ai-stack-map-mobile-N.html` | Versiunile, câte una pe actualizare. N cel mai mare = starea curentă. |
| `ai-stack-map-LATEST.html` | Copie identică a ultimei versiuni. E adresa fixă din spatele linkului. |
| `index.html` | Redirecționează linkul către `ai-stack-map-LATEST.html`. |
| `update_stack_map.py` | Scriptul de actualizare (Yahoo Finance prin `yfinance`). |
| `.github/workflows/update.yml` | Rulează scriptul luni–vineri, 21:30 UTC, după închiderea bursei US. Se poate porni și manual. |
| `update-log.txt` | Jurnalul rulărilor: schimbări de earnings, tickeri fără date. |

Ce face scriptul la fiecare rulare:
1. Pornește de la ultima versiune N și scrie N+1 plus `LATEST`.
2. Pentru fiecare ticker actualizează prețul, %, market cap, volumul și P/E.
3. Actualizează datele de earnings, numai ca `estimat`.
4. Actualizează datele trimestriale (blocul `FIN`).

Prețurile live din pagină vin din widget-urile TradingView, la deschiderea paginii.

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

## Când adaugi un ticker nou, completezi toate locurile

1. Rândul în stratul potrivit și contorul `(N)`.
2. Linia în `EARNINGS`.
3. `IR_LINKS` (pagina oficială de investitori).
4. Bursa în `TV_EX` (NASDAQ/NYSE/AMEX).
5. Dacă nu e acțiune:
   - în pagină: `TV_SPECIAL`, `NO_EDGAR` și eventual `SRC_OVERRIDE`;
   - în script: `YAHOO_SYMBOL` și `NO_EARNINGS`.

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
4. Fără nicio confirmare nouă: nu crea versiune nouă și nu face commit. Raportează scurt: „nicio confirmare nouă azi”.
5. Cu confirmări noi:
   - creează N+1 cu **doar** acele linii schimbate (regula 3) și copiază-l în `LATEST`;
   - validează JS-ul;
   - fă commit cu mesajul `Confirmări earnings <data> — v<N+1>` și push pe `main`;
   - raportează lui Gabriel un tabel scurt: ticker, data, sesiunea, ora și link spre sursa oficială.

## Cross-check — două metode DIFERITE, în paralel (luni, miercuri, vineri)

Principiul lui Gabriel: o verificare făcută cu aceeași metodă repetă aceleași unghiuri moarte. De aceea cele două verificări folosesc metode, surse și trasee de date diferite, iar erorile lor nu se suprapun.

Pentru amândouă:
- **Nu modifici fișierele și nu faci commit** (doar `crosscheck.yml` scrie raportul B). O eroare găsită se corectează la cauză, adică în script sau în procedură, după discuția cu Gabriel, nu prin peticirea unei valori.
- Yahoo nu e sursă de control, pentru că e chiar sursa scriptului de actualizare.

### Cross-check aleatoriu — Metoda A (judecată pe eșantion, din documente primare; în conversația cu Gabriel)

1. Starea verificată: ultimul `ai-stack-map-mobile-N.html`, plus data rulării care l-a produs, din `update-log.txt`.
2. Eșantion: **8 tickeri aleși cu `random.sample`**. Cel puțin unul din Energy sau Macro și unul care raportează în altă monedă decât USD. Scrie lista în raport.
3. Citește documentele primare și compară:
   - **Prețul și %** față de închiderea zilei: StockAnalysis, Nasdaq.com sau site-ul bursei.
   - **Earnings**:
     - un `confirmat` trebuie să aibă comunicatul oficial (deschizi sursa din `src`);
     - un `estimat` trebuie să fie apropiat de cel puțin încă o estimare publică;
     - dacă compania a anunțat între timp data oficial, semnalezi.
   - **Trimestrial**: ultimul trimestru față de comunicatul de rezultate sau de 10-Q/6-K.
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
  - SEC EDGAR XBRL pentru venituri și profit net trimestrial; cere secretul `SEC_USER_AGENT` = „Nume email”.
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
