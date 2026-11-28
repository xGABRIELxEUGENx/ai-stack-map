# Cross-check metoda B — v105

Rulat: 2026-11-28 03:30 UTC · fișier: `ai-stack-map-mobile-105.html` · tickeri: 162

**2951 verificări · 2913 OK · 3 erori · 35 diferențe**

Surse: TradingView scanner (160/162 tickeri cotați) · Yahoo Finance financiare (139 companii verificate; fără comparație: 0 — fără q în fișier sau trimestre lipsă la Yahoo)

## Erori (3)

| Ticker | Câmp | Fișier | Control | Sursă | Notă |
|---|---|---|---|---|---|
| MU | market cap | 7.342e+11 | 8.287e+11 | TradingView scanner | 11.40% |
| VIX | % zi | -11.16 | -15.81 | TradingView scanner | 4.65pp (se tranzacționează ~24h; momentul citirii diferă) |
| XE | venituri 2026-09-30 [SEC] | 66.34 | 51.56 | Yahoo (2026-09-30) | 28.65% Yahoo definește unele cifre diferit (bănci, derivate la energie, ajustări) |

## Diferențe (35)

| Ticker | Câmp | Fișier | Control | Sursă | Notă |
|---|---|---|---|---|---|
| CBRS | FIN trimestru lipsă | 2025-09-30 → 2026-03-31 | ≤ 100 zile | intern | lipsește în SEC și în FIN_PR (IPO recent: poate fi legitim) |
| SPCX | FIN trimestru lipsă | 2025-09-30 → 2026-06-30 | ≤ 100 zile | intern | lipsește în SEC și în FIN_PR (IPO recent: poate fi legitim) |
| OKLO | FIN trimestru lipsă | 2025-09-30 → 2026-06-30 | ≤ 100 zile | intern | lipsește în SEC și în FIN_PR (nu e IPO recent: verifică sursa) |
| APP | FIN trimestru lipsă | 2025-09-30 → 2026-03-31 | ≤ 100 zile | intern | lipsește în SEC și în FIN_PR (nu e IPO recent: verifică sursa) |
| XE | FIN trimestru lipsă | 2025-09-30 → 2026-03-31 | ≤ 100 zile | intern | lipsește în SEC și în FIN_PR (IPO recent: poate fi legitim) |
| TSM | market cap | 1.83e+12 | 1.688e+12 | TradingView scanner | 8.43% (ADR: prima față de bursa locală) |
| ASML | market cap | 5.11e+11 | 4.894e+11 | TradingView scanner | 4.42% (ADR: prima față de bursa locală) |
| CBRS | market cap | 2.29e+10 | 2.161e+10 | TradingView scanner | 5.98% (TradingView: calculat cu o închidere din ultimele 3 zile) |
| ARM | market cap | 1.836e+11 | 171855565311 | TradingView scanner | 6.81% (TradingView: calculat cu o închidere din ultimele 3 zile) |
| SKHY | market cap | 8.427e+11 | 5.495e+11 | TradingView scanner | 53.36% (ADR: prima față de bursa locală) |
| NEE | % zi | 0.19 | -0.5386 | TradingView scanner | 0.73pp ex-dividend: Yahoo scade ~0.62 din închiderea anterioară; preț(N)/preț(N−1) = TradingView |
| DELL | P/E | 18.43 | 13.33 | TradingView scanner | 38.21% (TTM calculat diferit) |
| ORCL | market cap | 3.34e+11 | 3.239e+11 | TradingView scanner | 3.11% (TradingView: calculat cu o închidere din ultimele 3 zile) |
| CRWD | P/E | 1,810 | 2,333 | TradingView scanner | 22.42% (TTM calculat diferit) |
| BRENT | % zi | 0.22 | -0.9054 | TradingView scanner | 1.13pp (se tranzacționează ~24h; momentul citirii diferă) |
| SMR | market cap | 1.43e+09 | 1.496e+09 | TradingView scanner | 4.42% |
| XAUUSD | % zi | 2.91 | 3.753 | TradingView scanner | 0.84pp (se tranzacționează ~24h; momentul citirii diferă) |
| SFTBY | preț | 9.28 | 9.34 | TradingView scanner | 0.64% |
| SFTBY | % zi | 6.42 | 7.11 | TradingView scanner | 0.69pp OTC: agregare volum / închidere de referință diferită între Yahoo și TradingView |
| SFTBY | volum | 4.93e+05 | 2401059 | TradingView scanner | 79.47% OTC: agregare volum / închidere de referință diferită între Yahoo și TradingView |
| WDC | profit net 2026-07-03 [SEC] | 3,195 | 3,069 | Yahoo (2026-06-30) | 4.11% Yahoo definește unele cifre diferit (bănci, derivate la energie, ajustări) |
| SAP | profit net 2025-12-31 [C] | 1846 | 1,680 | Yahoo (2025-12-31) | 9.88% Yahoo definește unele cifre diferit (bănci, derivate la energie, ajustări) |
| CVX | venituri 2026-06-30 [SEC] | 7.006e+04 | 6.72e+04 | Yahoo (2026-06-30) | 4.25% Yahoo definește unele cifre diferit (bănci, derivate la energie, ajustări) |
| CVX | venituri 2026-09-30 [SEC] | 6.78e+04 | 6.524e+04 | Yahoo (2026-09-30) | 3.93% Yahoo definește unele cifre diferit (bănci, derivate la energie, ajustări) |
| EQT | venituri 2026-03-31 [SEC] | 3,379 | 3,617 | Yahoo (2026-03-31) | 6.59% Yahoo definește unele cifre diferit (bănci, derivate la energie, ajustări) |
| EQT | venituri 2026-09-30 [SEC] | 1,770 | 1,670 | Yahoo (2026-09-30) | 6.00% Yahoo definește unele cifre diferit (bănci, derivate la energie, ajustări) |
| TLN | venituri 2026-03-31 [SEC] | 1,129 | 1,241 | Yahoo (2026-03-31) | 9.02% venitul raportat include derivatele nerealizate: https://www.sec.gov/Archives/edgar/data/0001622536/000162253626000065/a20260805q22026earningsrel.htm |
| TLN | venituri 2026-06-30 [SEC] | 747 | 959 | Yahoo (2026-06-30) | 22.11% venitul raportat include derivatele nerealizate: https://www.sec.gov/Archives/edgar/data/0001622536/000162253626000065/a20260805q22026earningsrel.htm |
| TLN | venituri 2026-09-30 [SEC] | 1,327 | 1,510 | Yahoo (2026-09-30) | 12.12% venitul raportat include derivatele nerealizate: https://www.sec.gov/Archives/edgar/data/0001622536/000162253626000065/a20260805q22026earningsrel.htm |
| XE | venituri 2026-03-31 [SEC] | 43.42 | 39.91 | Yahoo (2026-03-31) | 8.81% Yahoo definește unele cifre diferit (bănci, derivate la energie, ajustări) |
| XE | venituri 2026-06-30 [SEC] | 54.6 | 50.12 | Yahoo (2026-06-30) | 8.94% Yahoo definește unele cifre diferit (bănci, derivate la energie, ajustări) |
| JPM | venituri 2026-06-30 [SEC] | 5.735e+04 | 5.285e+04 | Yahoo (2026-06-30) | 8.50% Yahoo definește unele cifre diferit (bănci, derivate la energie, ajustări) |
| MS | venituri 2026-03-31 [SEC] | 2.058e+04 | 1.932e+04 | Yahoo (2026-03-31) | 6.50% Yahoo definește unele cifre diferit (bănci, derivate la energie, ajustări) |
| MS | venituri 2026-06-30 [SEC] | 2.135e+04 | 1.988e+04 | Yahoo (2026-06-30) | 7.36% Yahoo definește unele cifre diferit (bănci, derivate la energie, ajustări) |
| MS | venituri 2026-09-30 [SEC] | 2.034e+04 | 1.887e+04 | Yahoo (2026-09-30) | 7.77% Yahoo definește unele cifre diferit (bănci, derivate la energie, ajustări) |
