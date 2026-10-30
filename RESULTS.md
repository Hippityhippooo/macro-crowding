# Results

Written 2026-10-30 after both samples were run. Every figure below is copied from
`output/results_dev.md`, `output/results_holdout.md`, `output/results_h2_dev.md`,
`output/results_h2_holdout.md`, `output/gate.md` and `output/exhibit_*.csv`. Development sample
2005-2015 was run first and committed (b3ce22d); the holdout 2016-2025 was run once after that
(e9da60b). Pre-registration: `PREREGISTRATION.md`; threshold decisions: `CHANGELOG.md`.

## Sample

- 421,885 earnings 8-Ks (Item 2.02), 12,985 firms, 2004-2026, from EDGAR submissions.
- Session class from the acceptance timestamp when the 8-K was filed on the release day:
  post-close 39.0%, pre-market 26.9%, in-session 10.1%, unknown (filed later) 24.0%.
  Same-day filing share rose from 57% (2005) to 89% (2025).
- Crowded session = the earnings news first trades in the same session as a CPI release, an
  Employment Situation release or an FOMC statement. 11-21% of classified events per year.
- FOMC statement days carry 126 earnings 8-Ks on average against 72 on an ordinary trading day
  (CPI or jobs days: 79), 2005-2025.
- Return panel (Yahoo Finance, NYSE/NASDAQ/NYSEMKT, price >= $5, FF5+UMD abnormal returns):
  162,841 events, 2,998 firms, 20,693 crowded. Development sample 63,042 events (45,380 with a
  session class and surprise rank); holdout 91,595 (79,879).

## H1: does crowding change how earnings news is absorbed?

Pre-registered primary test: coefficient on surprise-decile rank x crowded session in a regression
of CAR[+2,+60] with firm and year-quarter fixed effects, SE clustered by firm and reaction day.
Units: CAR in decimal. The surprise rank spans -0.5 (bottom decile) to +0.5 (top decile), so b is the extra CAR for the top decile relative to the bottom decile on crowded sessions; one decile step is 0.111 of that.

| Sample | b | se | t | 95% CI | n | MDE |
|---|---|---|---|---|---|---|
| Development 2005-2015 | -0.01482 | 0.00714 | -2.07 | [-0.02882, -0.00082] | 45,380 | 0.0063 |
| Holdout 2016-2025 | +0.00748 | 0.00662 | +1.13 | [-0.00550, +0.02045] | 79,879 | 0.0048 |

Verdict by the pre-registered rule: development sample rejects H1 (not positive; CI excludes the
MDE). Holdout: not distinguishable from zero and the CI includes the MDE, so "not detectable".
The development-sample sign does not replicate.

By release type (CAR[+2,+60] x surprise rank, calendar-day dummy):

| Release | Development b (t) | Holdout b (t) |
|---|---|---|
| CPI only | +0.00347 (0.27) | +0.00795 (0.55) |
| Employment Situation only | +0.00164 (0.15) | +0.00919 (1.02) |
| FOMC only | -0.03838 (-4.26) | +0.00059 (0.06) |

Attention channel (both samples): immediate reaction CAR[0,+1] x GAAP surprise, t = -0.02 (dev)
and -0.33 (holdout); abnormal volume on crowded, t = -0.51 and +0.65; |CAR[0,+1]| on crowded,
t = -0.86 and +0.11. No attention signature and no noise signature in either sample.

Placebos: 1,000 random pseudo-macro-day draws give a null SD of 0.0088 (dev) and 0.0073
(holdout); the share of draws at least as large in absolute value as the actual coefficient is
0.090 (dev) and 0.299 (holdout). Shifts of +-7 days: dev -0.0105 (t -1.29) and +0.0130 (t 1.58);
holdout -0.0092 (t -1.44) and +0.0155 (t 1.90).

GAAP SUE version (secondary): dev -0.01059 (t -1.23, cells below the 500 minimum); holdout
-0.00967 (t -1.66, cells 1,100 and 1,120).

Cumulative abnormal return, top minus bottom market-surprise decile, all events 2005-2025
(26,531 extreme-decile events): day +1 crowded 29.82 pp vs uncrowded 28.57 pp; day +60 30.93 vs
30.04. Drift from day +1 to +60: 1.11 pp crowded, 1.47 pp uncrowded.

Calendar-time portfolios (top minus bottom decile, 60-day hold, equal-weighted, daily alpha vs
FF5+UMD, Newey-West 5 lags): development crowded -1.16 bp (t -0.58), uncrowded +1.64 bp (t 2.02),
difference -2.81 bp (t -1.38); holdout crowded +2.47 bp (t 1.70), uncrowded +0.83 bp (t 0.96),
difference +1.64 bp (t 1.07). Net of Corwin-Schultz spread costs every book is negative.

## H2: do firms put bad news on crowded sessions?

SUE (winsorised at +-10) on crowded session, firm and year-quarter fixed effects, two-way
clustered SE; no prices needed.

| Sample | b | se | t | n | share SUE<0 crowded vs uncrowded |
|---|---|---|---|---|---|
| Development 2010-2015 | -0.0003 | 0.0302 | -0.01 | 38,181 | 42.7% vs 42.4% |
| Holdout 2016-2025 | +0.0249 | 0.0206 | +1.21 | 110,075 | 44.8% vs 43.6% |

Discretion interaction (crowded x SD of the firm's report timing): t = -0.70 (dev), +0.54 (holdout).
By release: all |t| < 1.1 in both samples. H2 rejected in both samples.

## Limits

- Prices from Yahoo Finance: 3,878 of 3,879 currently listed tickers covered, 94 of 6,274
  delisted. Events for firms since delisted (206,088 of 415,076 since 2005) are mostly absent.
  Their crowded-session share was 14.6% against 15.9% for surviving firms.
- 737 tickers dropped whole for a daily |return| > 100% after 2004 (OTC relistings, data faults);
  OTC exchanges excluded; CARs winsorised at 1%/99%. Ticker reuse in Yahoo histories cannot be
  detected without a second source.
- 24% of events (filed after the release day) have no time of day and are outside the session
  test; 17,662 in the development sample, 11,716 in the holdout.
- GAAP EPS against the same quarter last year is not the consensus surprise analysts trade.
- 48 BLS dates sit in within-10-day pairs with a revision date; both count as crowded.
- Release times (08:30 ET BLS, 14:00/14:15 ET FOMC) are parameters, not verified per date.

## Exploratory (not pre-registered)

None run.
