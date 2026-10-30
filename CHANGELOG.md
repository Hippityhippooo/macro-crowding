# Changelog and decision log

Every [PROPOSED] threshold in PREREGISTRATION.md is promoted or changed here, with the reason,
before the first regression on the development sample.

## 2026-10-30

- Repository created. Pipeline written and tested on synthetic fixtures (17 tests). No real data run.
- Verified EDGAR record formats recorded in module docstrings.
- Gate numbers (events per year, same-day share, crowded cells): not yet computed.
- MDE: not yet computed.
- Macro calendar built from federalreserve.gov (FOMC 2004-2026, 183 scheduled statement dates) and ALFRED (CPI 303, EMPSIT 292 dates from 2003). 48 BLS dates sit in within-10-day pairs (seasonal-factor or benchmark revisions); flagged, not resolved. See data/reference/REPORT.md.

## 2026-10-30, data in (mirrors, no prices)

- Inputs: Gow sec_submissions_data release 2026-09-30 (filings.parquet, 27.27M rows) filtered to 8-K with Item 2.02 -> 430,579 rows (426,208 8-K, 4,371 8-K/A); DenyTranDFW companyfacts mirror filtered to EPS facts -> 2,004,375 rows. Four accessions verified today against live EDGAR index pages match the mirror exactly (Apple, JPMorgan, Seer, Sachem). Mirror timestamp provenance: trusted_snapshot_eastern 386,664; live_file_inferred 38,646; live_pair 4,595; sgml 610; cross_cik_pair 64.
- Events stage: 421,885 events (8-K only, one per firm-day), 12,985 firms. Session shares: post_close 39.0%, pre_market 26.9%, unknown (lagged filing) 24.0%, in_session 10.1%.
- Gate: events per year 17-24k (2005-2025). Same-day filing share rises from 57% (2005) to 89% (2026). Crowded-session share of classified events 11-21% by year; crowded-session events 1.4k-3.3k per year; development sample 2005-2015 holds about 20.6k crowded-session events. Gate passed; no widening of the crowding set needed.
- Surprise stage: 277,144 point-in-time quarters (11.9% derived Q4); SUE non-null for 73% of quarters and for 64-86% of events from 2013. Apple Q4 FY2024 derived diluted EPS 0.97 matches the reported GAAP figure. Quarter-to-event gap: median 34 days, 95th pct 65.
- BLOCKER: no price data. Package contains only the Sharadar AAPL demo. H1 (returns) cannot run until Sharadar Prices Full History is downloaded.
- Thresholds in PREREGISTRATION.md remain [PROPOSED]; no hypothesis test has been run.

## 2026-10-30, thresholds promoted

Faldo delegated all non-payment decisions ("everything else is up to you"). On that authority the [PROPOSED]
defaults in PREREGISTRATION.md are promoted unchanged: $5 price filter on day -2; windows [0,+1], [+2,+20],
[+2,+60]; estimation window [-250,-21], minimum 120 obs; SUE lookback 8 quarters, minimum 4; development
2005-2015, holdout 2016-2025; 500-event minimum per crowded extreme decile; 1,000 placebo draws; 2% position
cap; Newey-West lag 5. Price source changed from Sharadar to Yahoo Finance (free): survivorship is now a
measured limitation (see events-by-firm-status numbers below), not a solved one. This entry precedes any
hypothesis test.

- Events 2005+ by firm status (Sharadar free ticker master): listed now 208,988; delisted 206,088; no map 39,... (see output/gate.md); crowded_session mean 15.9% listed vs 14.6% delisted.

## 2026-10-30, data-quality rules for Yahoo prices (set before the first H1 regression on real data)

First real panel (733 tickers, partial download) showed: 187 tickers with daily |return| > 100% (OTC
bankruptcy symbols ending in Q, relistings) and ticker reuse (Yahoo's PARA history is not the old
Paramount Global). Rules, applied in run.py returns stage:
1. Exchange must be NYSE, NASDAQ or NYSEMKT in the Sharadar ticker master (OTC excluded).
2. Any ticker with a daily |return| > 100% after 2004 is dropped whole.
3. CARs winsorised at the 1st/99th percentile within the panel; raw CARs kept as *_raw and reported in a
   robustness line. Ticker reuse cannot be detected without a second price source; it is a stated limitation.
No hypothesis test on real data has been run before this entry.
