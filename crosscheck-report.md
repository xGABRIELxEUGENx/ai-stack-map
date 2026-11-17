# Cross-check metoda B — v85

Rulat: 2026-11-17 04:12 UTC · fișier: `ai-stack-map-mobile-85.html` · tickeri: 150

**2806 verificări · 2761 OK · 4 erori · 41 diferențe**

Surse: TradingView scanner (148/150 tickeri cotați) · Yahoo Finance financiare (132 companii verificate; fără comparație: 1 — fără q în fișier sau trimestre lipsă la Yahoo)

## Erori (4)

| Ticker | Câmp | Fișier | Control | Sursă | Notă |
|---|---|---|---|---|---|
| NBIS | acțiuni (mcap/preț) | 2.929e+08 | 2.718e+08 | v84 | 7.76% număr de acțiuni schimbat brusc |
| CBRS | market cap | 2.454e+10 | 1.927e+10 | TradingView scanner | 27.33% |
| SLAB | volum | 4.21e+05 | 814366 | TradingView scanner | 48.30% (metode de agregare diferite) |
| XE | venituri 2026-09-30 [SEC] | 66.34 | 51.56 | Yahoo (2026-09-30) | 28.65% Yahoo definește unele cifre diferit (bănci, derivate la energie, ajustări) |

## Diferențe (41)

| Ticker | Câmp | Fișier | Control | Sursă | Notă |
|---|---|---|---|---|---|
| CBRS | acțiuni (mcap/preț) | 2.43e+08 | 2.376e+08 | v84 | 2.28% număr de acțiuni schimbat brusc |
| CBRS | FIN trimestru lipsă | 2025-09-30 → 2026-03-31 | ≤ 100 zile | intern | lipsește în SEC și în FIN_PR (IPO recent: poate fi legitim) |
| SPCX | FIN trimestru lipsă | 2025-09-30 → 2026-06-30 | ≤ 100 zile | intern | lipsește în SEC și în FIN_PR (IPO recent: poate fi legitim) |
| OKLO | FIN trimestru lipsă | 2025-09-30 → 2026-06-30 | ≤ 100 zile | intern | lipsește în SEC și în FIN_PR (nu e IPO recent: verifică sursa) |
| APP | FIN trimestru lipsă | 2025-09-30 → 2026-03-31 | ≤ 100 zile | intern | lipsește în SEC și în FIN_PR (nu e IPO recent: verifică sursa) |
| XE | FIN trimestru lipsă | 2025-09-30 → 2026-03-31 | ≤ 100 zile | intern | lipsește în SEC și în FIN_PR (IPO recent: poate fi legitim) |
| KLAC | % zi | -5.35 | -5.488 | TradingView scanner | 0.14pp ex-dividend: Yahoo scade ~0.22 din închiderea anterioară; preț(N)/preț(N−1) = TradingView |
| TSM | market cap | 1.94e+12 | 1.85e+12 | TradingView scanner | 4.84% (ADR: prima față de bursa locală) |
| ASML | market cap | 5.422e+11 | 5.636e+11 | TradingView scanner | 3.80% (ADR: prima față de bursa locală) |
| ARM | market cap | 1.873e+11 | 202734454601 | TradingView scanner | 7.61% (TradingView: calculat cu o închidere din ultimele 3 zile) |
| SKHY | market cap | 8.616e+11 | 659407513875 | TradingView scanner | 30.66% (ADR: prima față de bursa locală) |
| NBIS | market cap | 3.138e+10 | 2.911e+10 | TradingView scanner | 7.81% |
| NBIS | P/E | 83.7 | 489 | TradingView scanner | 82.88% (TTM calculat diferit) |
| CEG | % zi | -0.7 | -0.8494 | TradingView scanner | 0.15pp ex-dividend: Yahoo scade ~0.42 din închiderea anterioară; preț(N)/preț(N−1) = TradingView |
| ORCL | market cap | 3.713e+11 | 3.601e+11 | TradingView scanner | 3.11% (mai multe clase de acțiuni: fișierul toate clasele, TradingView doar clasa cotată) |
| SAP | volum | 1.4e+06 | 1815365 | TradingView scanner | 22.88% (metode de agregare diferite) |
| CRWD | P/E | 4,464 | 6,252 | TradingView scanner | 28.60% (TTM calculat diferit) |
| PANW | P/E | 810.5 | 616.8 | TradingView scanner | 31.41% (TTM calculat diferit) |
| XOM | % zi | -1.56 | -2.181 | TradingView scanner | 0.62pp ex-dividend: Yahoo scade ~1.08 din închiderea anterioară; preț(N)/preț(N−1) = TradingView |
| COP | % zi | -0.59 | -1.237 | TradingView scanner | 0.65pp ex-dividend: Yahoo scade ~0.93 din închiderea anterioară; preț(N)/preț(N−1) = TradingView |
| CEG | % zi | -0.7 | -0.8494 | TradingView scanner | 0.15pp ex-dividend: Yahoo scade ~0.42 din închiderea anterioară; preț(N)/preț(N−1) = TradingView |
| SMR | market cap | 1.75e+09 | 1.836e+09 | TradingView scanner | 4.67% |
| SFTBY | preț | 10.44 | 10.4 | TradingView scanner | 0.38% |
| SFTBY | % zi | -4.66 | -5.023 | TradingView scanner | 0.36pp OTC: agregare volum / închidere de referință diferită între Yahoo și TradingView |
| SFTBY | market cap | 1.19e+11 | 1.268e+11 | TradingView scanner | 6.12% (ADR: prima față de bursa locală) |
| SFTBY | volum | 1.5e+06 | 6783929 | TradingView scanner | 77.89% OTC: agregare volum / închidere de referință diferită între Yahoo și TradingView |
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
