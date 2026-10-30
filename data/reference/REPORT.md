# US macro release calendar build report

Generated 2026-10-30. All dates transcribed from the pages listed in the "URLs fetched" section; nothing added from memory.

## Files

- `/home/claude/calendar_work/fomc_dates.csv` — 209 rows (2004–2026). Columns: year, meeting_start, meeting_end, statement_date, scheduled, source_url.
- `/home/claude/calendar_work/bls_release_dates.csv` — 595 rows (CPI 298, EMPSIT 297), 2003-01-01 through the last date in each ALFRED file (CPI 2026-10-14, EMPSIT 2026-10-02). Columns: release, release_date, source.

## Transcription rules applied

- FOMC: statement_date = second day of a two-day meeting, or the single day of a one-day meeting. ISO dates throughout.
- scheduled = 0 for every entry the Fed page labels "Conference Call", "(unscheduled)" or "(notation vote)"; scheduled = 1 for entries labelled "Meeting" with no such qualifier.
- Cross-month entries resolved as: 2012 "July 31-August 1" -> 2012-07-31/2012-08-01; 2013 and 2019 "April/May 30-1" -> 04-30/05-01; 2017 "Jan/Feb 31-1" -> 01-31/02-01; 2017 "Oct/Nov 31-1" -> 10-31/11-01; 2018 "Jul/Aug 31-1" -> 07-31/08-01; 2023 "Jan/Feb 31-1" -> 01-31/02-01; 2023 "Oct/Nov 31-1" -> 10-31/11-01; 2024 "Apr/May 30-1" -> 04-30/05-01.
- 2020: the "March 17-18 (cancelled) Meeting" entry was NOT written as a row (no meeting took place; the unscheduled March 2 and March 15 meetings replaced it). The four "(notation vote)" entries (March 19, March 23, March 31, August 27) were written as rows with scheduled = 0. If notation votes should be excluded, drop those four rows plus 2025-08-22.
- 2025: "August 22 (notation vote)" (links to the Statement on Longer-Run Goals) written as a row with scheduled = 0.
- 2027 meetings shown on the calendars page were not written (outside the 2004–2026 range).
- BLS: all dates in the ALFRED txt files from 2003-01-01 onward were transcribed exactly; none removed. ALFRED notes that the list "contains the dates when any series from this release was revised", so revision-only dates appear alongside the headline release dates.

## Per-year counts

| Year | FOMC rows | FOMC scheduled | FOMC unscheduled (sched=0) | CPI dates | EMPSIT dates |
|---|---|---|---|---|---|
| 2003 | n/a | n/a | n/a | 12 | 13 |
| 2004 | 8 | 8 | 0 | 12 | 12 |
| 2005 | 8 | 8 | 0 | 13 | 12 |
| 2006 | 8 | 8 | 0 | 13 | 13 |
| 2007 | 11 | 8 | 3 | 13 | 12 |
| 2008 | 14 | 8 | 6 | 13 | 12 |
| 2009 | 11 | 8 | 3 | 13 | 12 |
| 2010 | 10 | 8 | 2 | 13 | 12 |
| 2011 | 10 | 8 | 2 | 13 | 12 |
| 2012 | 8 | 8 | 0 | 13 | 13 |
| 2013 | 9 | 8 | 1 | 13 | 13 |
| 2014 | 9 | 8 | 1 | 13 | 12 |
| 2015 | 8 | 8 | 0 | 13 | 12 |
| 2016 | 8 | 8 | 0 | 12 | 12 |
| 2017 | 8 | 8 | 0 | 13 | 12 |
| 2018 | 8 | 8 | 0 | 12 | 12 |
| 2019 | 9 | 8 | 1 | 13 | 12 |
| 2020 | 13 | 7 | 6 | 13 | 13 |
| 2021 | 8 | 8 | 0 | 13 | 12 |
| 2022 | 8 | 8 | 0 | 13 | 12 |
| 2023 | 8 | 8 | 0 | 13 | 12 |
| 2024 | 8 | 8 | 0 | 13 | 14 |
| 2025 | 9 | 8 | 1 | 11 | 11 |
| 2026 | 8 | 8 | 0 | 10 (through Oct) | 10 (through Oct) |

## Flags

### FOMC — years with scheduled count other than 8

- **2020: 7 scheduled.** The March 17-18 meeting is labelled "(cancelled)" on the Fed page and was not written. Unscheduled/other rows for 2020 (scheduled=0): 2020-03-02 (unscheduled), 2020-03-15 (unscheduled), 2020-03-19, 2020-03-23, 2020-03-31, 2020-08-27 (notation votes).

All other years have exactly 8 scheduled meetings. Unscheduled rows (scheduled=0) by year, for reference:

- 2007: 2007-08-10, 2007-08-16, 2007-12-06 (conference calls)
- 2008: 2008-01-09, 2008-01-21, 2008-03-10, 2008-07-24, 2008-09-29, 2008-10-07 (conference calls)
- 2009: 2009-01-16, 2009-02-07, 2009-06-03 (conference calls)
- 2010: 2010-05-09, 2010-10-15 (conference calls)
- 2011: 2011-08-01, 2011-11-28 (conference calls)
- 2013: 2013-10-16 (unscheduled)
- 2014: 2014-03-04 (unscheduled)
- 2019: 2019-10-04 (unscheduled)
- 2020: see above
- 2025: 2025-08-22 (notation vote)

### CPI — years with count other than 12

Extra dates are almost all a second February date (the annual seasonal-factor revision, published a few days after the January CPI release). Flagged, not deleted:

- 2005 (13): 2005-02-18 and 2005-02-23
- 2006 (13): 2006-02-17 and 2006-02-22
- 2007 (13): 2007-02-16 and 2007-02-21
- 2008 (13): 2008-02-15 and 2008-02-20
- 2009 (13): 2009-02-18 and 2009-02-20
- 2010 (13): 2010-02-17 and 2010-02-19
- 2011 (13): 2011-02-15 and 2011-02-17
- 2012 (13): 2012-02-15 and 2012-02-17
- 2013 (13): 2013-02-19 and 2013-02-21
- 2014 (13): 2014-02-18 and 2014-02-20
- 2015 (13): 2015-02-20 and 2015-02-26
- 2017 (13): 2017-02-13 and 2017-02-15
- 2019 (13): 2019-02-11 and 2019-02-13
- 2020 (13): 2020-02-11 and 2020-02-13
- 2021 (13): 2021-02-08 and 2021-02-10
- 2022 (13): 2022-02-08 and 2022-02-10
- 2023 (13): 2023-02-10 and 2023-02-14
- 2024 (13): 2024-02-09 and 2024-02-13
- **2025 (11): no November 2025 date.** September CPI appears as 2025-10-24 (delayed), and the next date is 2025-12-18 (consistent with the autumn 2025 federal shutdown).
- 2026 (10): year in progress; last date 2026-10-14.

Other notable CPI dates (count unaffected but date shifted): 2013-10-30 (September 2013 CPI delayed by the October 2013 shutdown).

### EMPSIT — years with count other than 12

- 2003 (13): 2003-10-03 and 2003-10-10 (second October date; likely revision-only)
- 2006 (13): 2006-05-05 and 2006-05-08 (second May date; likely revision-only)
- 2012 (13): 2012-12-07 and 2012-12-12 (second December date; likely revision-only)
- 2013 (13): 2013-05-03 and 2013-05-06 (second May date; likely revision-only). Also 2013-10-22 is the shutdown-delayed September report.
- 2020 (13): 2020-05-08 and 2020-05-11 (second May date; likely revision-only)
- **2024 (14):** 2024-01-05 and 2024-01-10 (second January date); 2024-08-02 and 2024-08-21 (the 2024-08-21 date coincides with the preliminary benchmark revision; likely revision-only)
- **2025 (11): no October 2025 date.** 2025-09-05, then 2025-11-20 (delayed September report), then 2025-12-16 (consistent with the autumn 2025 shutdown).
- 2026 (10): year in progress; last date 2026-10-02.

## URLs fetched (all succeeded)

FOMC historical year pages:

- https://www.federalreserve.gov/monetarypolicy/fomchistorical2004.htm — OK
- https://www.federalreserve.gov/monetarypolicy/fomchistorical2005.htm — OK
- https://www.federalreserve.gov/monetarypolicy/fomchistorical2006.htm — OK
- https://www.federalreserve.gov/monetarypolicy/fomchistorical2007.htm — OK
- https://www.federalreserve.gov/monetarypolicy/fomchistorical2008.htm — OK
- https://www.federalreserve.gov/monetarypolicy/fomchistorical2009.htm — OK
- https://www.federalreserve.gov/monetarypolicy/fomchistorical2010.htm — OK
- https://www.federalreserve.gov/monetarypolicy/fomchistorical2011.htm — OK
- https://www.federalreserve.gov/monetarypolicy/fomchistorical2012.htm — OK
- https://www.federalreserve.gov/monetarypolicy/fomchistorical2013.htm — OK
- https://www.federalreserve.gov/monetarypolicy/fomchistorical2014.htm — OK
- https://www.federalreserve.gov/monetarypolicy/fomchistorical2015.htm — OK
- https://www.federalreserve.gov/monetarypolicy/fomchistorical2016.htm — OK
- https://www.federalreserve.gov/monetarypolicy/fomchistorical2017.htm — OK
- https://www.federalreserve.gov/monetarypolicy/fomchistorical2018.htm — OK
- https://www.federalreserve.gov/monetarypolicy/fomchistorical2019.htm — OK
- https://www.federalreserve.gov/monetarypolicy/fomchistorical2020.htm — OK
- https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm (2021–2027) — OK

ALFRED release dates:

- https://alfred.stlouisfed.org/release/downloaddates?rid=10 (CPI landing page; gave txt/xlsx links) — OK
- https://alfred.stlouisfed.org/release/downloaddates?rid=50 (Employment Situation landing page) — OK
- https://alfred.stlouisfed.org/release/downloaddates?rid=10&ff=txt (CPI dates; file created 2026-10-29 10:36 AM CDT; first date 1949-03-24, last 2026-10-14) — OK
- https://alfred.stlouisfed.org/release/downloaddates?rid=50&ff=txt (Employment Situation dates; file created 2026-10-28 6:36 PM CDT; first date 1955-05-06, last 2026-10-02) — OK

The xlsx links were not needed and were not fetched. No year pages were skipped.

## Post-processing (parent session, 2026-10-30)

- Row counts in the CSV as loaded: CPI 303, EMPSIT 292 (the "298 / 297" above was a reporting slip; the per-year table is the authoritative count and sums to these).
- Added column `flag` to bls_release_dates.csv: "pair_within_10d_verify_against_bls_schedule" marks any date of the same release within 10 days of another (48 rows). One of each pair is the headline release and the other a revision-only date; which is which is NOT decided here. Verify each pair against the BLS schedule pages from a browser (bls.gov refuses non-browser fetches). Until then the primary crowding dummy counts both (over-inclusion), and a robustness run drops both.
- FOMC rows with scheduled=0 (26) are excluded from the primary dummy by `load_macro_days(scheduled_only=True)`.
