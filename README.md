# Buried by the macro calendar?

Do earnings announcements that land in the same trading session as a CPI print, the jobs
report or an FOMC statement get absorbed differently, and do firms behave as if they know?

Status: pipeline built and unit-tested on synthetic fixtures; no real data run yet; no results.
Pre-registration: `PREREGISTRATION.md` (commit it before downloading prices).

## What this repository does

| Stage | Input | Output | Code |
|---|---|---|---|
| events | EDGAR `submissions.zip` | every 8-K with Item 2.02: event date (Period of Report), Eastern acceptance time, filing lag, session class (pre-market / in-session / post-close / unknown) | `src/crowding/events.py` |
| gate | events + macro calendar | `output/gate.md`: events per year, same-day filing share, crowded-session counts | `run.py gate` |
| surprise | EDGAR `companyfacts.zip` | point-in-time quarterly diluted EPS (first filing wins), derived Q4, SUE | `src/crowding/surprise.py` |
| returns | Sharadar SEP + French factors | FF5+UMD abnormal returns, CAR windows, abnormal volume, Corwin-Schultz spread | `src/crowding/returns.py` |
| tests | panel | H1/H2 regressions with two-way clustered SE, MDE, placebo, calendar-time portfolios | `src/crowding/inference.py` |

Crowding is defined by session, not calendar day: a 06:46 release on a CPI day competes with
the 08:30 print; a 16:30 release on an FOMC day does not compete with the 14:00 statement.
The EDGAR acceptance timestamp makes that distinction (see `events.py` docstring for the
verified record formats, 2026-10-30).

## Data you need (not in the repo)

Put these in `data/raw/`:

| File | Source | Cost |
|---|---|---|
| `submissions.zip` | https://www.sec.gov/edgar/sec-api-documentation (bulk "submissions.zip", ~1 GB) | free |
| `companyfacts.zip` | same page, bulk "companyfacts.zip" | free |
| `SHARADAR_SEP.csv`, `SHARADAR_TICKERS.csv` | https://sharadar.com/subscribe, Prices Full History (active + delisted, from Dec 1997) | $39/month or $299/year |
| `ff5_daily.csv`, `mom_daily.csv` | Kenneth French data library, daily FF5 2x3 and momentum, header lines stripped, first column YYYYMMDD | free |

`data/reference/` holds the macro calendar (FOMC statement dates 2004-2026 from
federalreserve.gov; CPI and Employment Situation release dates from ALFRED). See
`data/reference/REPORT.md` for what was fetched and any anomalies. Release times of day are
parameters in `calendar.py`, flagged [to verify].

Set a descriptive `User-Agent` with your email for any direct sec.gov request (SEC policy).

## Run

```
pip install -r requirements.txt
python -m pytest tests            # 17 tests on synthetic fixtures
python run.py events
python run.py gate                # decide: proceed, or widen crowding (log it in CHANGELOG.md)
python run.py surprise
python run.py returns
python run.py tests --sample dev  # development sample 2005-2015
git add output/results_dev.md && git commit -m "dev results"
python run.py tests --sample holdout   # refuses to run until dev results are committed
```

## Things the code is explicit about

- Frames API is not point-in-time (verified: a 2025 accession returned for CY2024Q3); the
  pipeline uses companyfacts first-filed records instead.
- Q4 quarterly EPS is usually not tagged; it is derived from the annual figure and flagged
  `derived=1` so robustness runs can drop it.
- Lagged 8-K filings keep their event date and lose their session class (`unknown`); the share
  is reported in the gate and those events are excluded from the session-based primary test.
- Two surprise measures (GAAP SUE 2009+, market-based 2005+) because consensus data is paid.
- CIK-to-ticker mapping uses Sharadar's `secfilings` URL so delisted names map too; the SEC's
  `company_tickers.json` is current-only and is not used.

## Authorship

Research question, design, pre-registration and checks: Faldo Lyon. Code drafted with AI
assistance and reviewed and run by the author. Nothing in this repository is investment advice.
