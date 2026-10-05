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
