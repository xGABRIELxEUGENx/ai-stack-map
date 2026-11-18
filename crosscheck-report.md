# Cross-check metoda B — v91

Rulat: 2026-11-18 08:49 UTC · fișier: `ai-stack-map-mobile-91.html` · tickeri: 156

**2905 verificări · 2870 OK · 2 erori · 33 diferențe**

Surse: TradingView scanner (154/156 tickeri cotați) · Yahoo Finance financiare (136 companii verificate; fără comparație: 1 — fără q în fișier sau trimestre lipsă la Yahoo)

## Erori (2)

| Ticker | Câmp | Fișier | Control | Sursă | Notă |
|---|---|---|---|---|---|
| CBRS | market cap | 2.532e+10 | 1.988e+10 | TradingView scanner | 27.35% |
| XE | venituri 2026-09-30 [SEC] | 66.34 | 51.56 | Yahoo (2026-09-30) | 28.65% Yahoo definește unele cifre diferit (bănci, derivate la energie, ajustări) |

## Diferențe (33)

| Ticker | Câmp | Fișier | Control | Sursă | Notă |
|---|---|---|---|---|---|
| CBRS | FIN trimestru lipsă | 2025-09-30 → 2026-03-31 | ≤ 100 zile | intern | lipsește în SEC și în FIN_PR (IPO recent: poate fi legitim) |
| SPCX | FIN trimestru lipsă | 2025-09-30 → 2026-06-30 | ≤ 100 zile | intern | lipsește în SEC și în FIN_PR (IPO recent: poate fi legitim) |
| OKLO | FIN trimestru lipsă | 2025-09-30 → 2026-06-30 | ≤ 100 zile | intern | lipsește în SEC și în FIN_PR (nu e IPO recent: verifică sursa) |
| APP | FIN trimestru lipsă | 2025-09-30 → 2026-03-31 | ≤ 100 zile | intern | lipsește în SEC și în FIN_PR (nu e IPO recent: verifică sursa) |
| XE | FIN trimestru lipsă | 2025-09-30 → 2026-03-31 | ≤ 100 zile | intern | lipsește în SEC și în FIN_PR (IPO recent: poate fi legitim) |
| TSM | market cap | 1.87e+12 | 1.743e+12 | TradingView scanner | 7.32% (ADR: prima față de bursa locală) |
| ARM | market cap | 1.962e+11 | 186262883136 | TradingView scanner | 5.35% |
| SKHY | market cap | 8.646e+11 | 6.082e+11 | TradingView scanner | 42.17% (ADR: prima față de bursa locală) |
| NBIS | market cap | 3.106e+10 | 2.881e+10 | TradingView scanner | 7.81% |
| ORCL | market cap | 3.585e+11 | 3.477e+11 | TradingView scanner | 3.11% (mai multe clase de acțiuni: fișierul toate clasele, TradingView doar clasa cotată) |
| SAP | market cap | 2.568e+11 | 2.74e+11 | TradingView scanner | 6.25% (ADR: prima față de bursa locală) |
| PANW | P/E | 773.2 | 603.5 | TradingView scanner | 28.13% (TTM calculat diferit) |
| CRWD | P/E | 4,392 | 6,151 | TradingView scanner | 28.60% (TTM calculat diferit) |
| WTI | % zi | -2.01 | -3.558 | TradingView scanner | 1.55pp (se tranzacționează ~24h; momentul citirii diferă) |
| BRENT | preț | 89.04 | 91.65 | TradingView scanner | 2.85% (se tranzacționează ~24h; momentul citirii diferă) |
| SMR | market cap | 1.68e+09 | 1.758e+09 | TradingView scanner | 4.45% |
| VIX | % zi | -5.69 | -6.287 | TradingView scanner | 0.60pp (se tranzacționează ~24h; momentul citirii diferă) |
| SFTBY | volum | 3.8e+06 | 16430927 | TradingView scanner | 76.87% OTC: agregare volum / închidere de referință diferită între Yahoo și TradingView |
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

Fără verificare financiară (Yahoo): SFTBY
