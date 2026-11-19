# Cross-check metoda B — v92

Rulat: 2026-11-19 02:47 UTC · fișier: `ai-stack-map-mobile-92.html` · tickeri: 156

**2903 verificări · 2866 OK · 2 erori · 35 diferențe**

Surse: TradingView scanner (154/156 tickeri cotați) · Yahoo Finance financiare (136 companii verificate; fără comparație: 1 — fără q în fișier sau trimestre lipsă la Yahoo)

## Erori (2)

| Ticker | Câmp | Fișier | Control | Sursă | Notă |
|---|---|---|---|---|---|
| CBRS | market cap | 2.288e+10 | 1.797e+10 | TradingView scanner | 27.34% |
| XE | venituri 2026-09-30 [SEC] | 66.34 | 51.56 | Yahoo (2026-09-30) | 28.65% Yahoo definește unele cifre diferit (bănci, derivate la energie, ajustări) |

## Diferențe (35)

| Ticker | Câmp | Fișier | Control | Sursă | Notă |
|---|---|---|---|---|---|
| CBRS | FIN trimestru lipsă | 2025-09-30 → 2026-03-31 | ≤ 100 zile | intern | lipsește în SEC și în FIN_PR (IPO recent: poate fi legitim) |
| SPCX | FIN trimestru lipsă | 2025-09-30 → 2026-06-30 | ≤ 100 zile | intern | lipsește în SEC și în FIN_PR (IPO recent: poate fi legitim) |
| OKLO | FIN trimestru lipsă | 2025-09-30 → 2026-06-30 | ≤ 100 zile | intern | lipsește în SEC și în FIN_PR (nu e IPO recent: verifică sursa) |
| APP | FIN trimestru lipsă | 2025-09-30 → 2026-03-31 | ≤ 100 zile | intern | lipsește în SEC și în FIN_PR (nu e IPO recent: verifică sursa) |
| XE | FIN trimestru lipsă | 2025-09-30 → 2026-03-31 | ≤ 100 zile | intern | lipsește în SEC și în FIN_PR (IPO recent: poate fi legitim) |
| NVDA | P/E | 19.08 | 16.22 | TradingView scanner | 17.63% (TTM calculat diferit) |
| TSM | market cap | 1.88e+12 | 1.71e+12 | TradingView scanner | 9.97% (ADR: prima față de bursa locală) |
| ASML | market cap | 5.378e+11 | 5.195e+11 | TradingView scanner | 3.51% (ADR: prima față de bursa locală) |
| SKHY | market cap | 8.636e+11 | 5.962e+11 | TradingView scanner | 44.85% (ADR: prima față de bursa locală) |
| NBIS | market cap | 3.133e+10 | 2.906e+10 | TradingView scanner | 7.81% |
| EQIX | % zi | 0.66 | 0.1614 | TradingView scanner | 0.50pp ex-dividend: Yahoo scade ~5.13 din închiderea anterioară; preț(N)/preț(N−1) = TradingView |
| EQIX | volum | 4.63e+05 | 627216 | TradingView scanner | 26.18% (metode de agregare diferite) |
| ORCL | market cap | 3.551e+11 | 3.444e+11 | TradingView scanner | 3.11% (mai multe clase de acțiuni: fișierul toate clasele, TradingView doar clasa cotată) |
| SAP | market cap | 2.433e+11 | 2.587e+11 | TradingView scanner | 5.97% (ADR: prima față de bursa locală) |
| PANW | P/E | 849.8 | 663.3 | TradingView scanner | 28.12% (TTM calculat diferit) |
| CRWD | P/E | 4,741 | 6,639 | TradingView scanner | 28.60% (TTM calculat diferit) |
| BRENT | preț | 89.39 | 92.06 | TradingView scanner | 2.90% (se tranzacționează ~24h; momentul citirii diferă) |
| CVX | % zi | -3.95 | -4.743 | TradingView scanner | 0.79pp ex-dividend: Yahoo scade ~1.78 din închiderea anterioară; preț(N)/preț(N−1) = TradingView |
| SMR | market cap | 1.61e+09 | 1.681e+09 | TradingView scanner | 4.22% (TradingView: calculat cu o închidere din ultimele 3 zile) |
| SFTBY | volum | 2.1e+06 | 9768747 | TradingView scanner | 78.50% OTC: agregare volum / închidere de referință diferită între Yahoo și TradingView |
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
