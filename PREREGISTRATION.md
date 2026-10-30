# Pre-registration: earnings announcements and competing macro news

Author: Faldo Lyon. Status: DRAFT, to be committed before any return series is downloaded.
The commit hash of the final version of this file is the pre-registration timestamp and goes
in the LinkedIn first comment. Nothing below is a result.

Thresholds marked [PROPOSED] are defaults; each is promoted or changed before the first
regression on the development sample, and the reason is logged in CHANGELOG.md.

## 1. Research question

When a US firm's earnings release lands in the same trading session as a top-tier scheduled
macro release (CPI, Employment Situation, FOMC statement), is the earnings news absorbed
differently, and do firms behave as if they know that?

## 2. Hypotheses

H1 (attention). On crowded sessions the immediate price reaction to the earnings surprise is
smaller and the post-announcement drift is larger than on uncrowded sessions, holding the
known confounds fixed. Mechanism: limited investor attention (Hirshleifer, Lim and Teoh 2009;
DellaVigna and Pollet 2009). The macro calendar is set a year ahead and is exogenous to the firm.

H2 (strategic timing). Firms with worse news are over-represented on crowded sessions, and the
over-representation is stronger for firms with discretion over their announcement date.

Competing explanation for H1 that the design must separate: macro sessions are high-volatility
sessions, so earnings reactions could look muted through noise rather than inattention.
Attention predicts lower abnormal volume on the event and a later catch-up in price;
noise predicts similar average reaction, wider dispersion, and no later catch-up.

## 3. Primary tests (one per hypothesis)

Primary H1 test: in the regression of CAR[+2,+60] on surprise-decile rank interacted with the
crowded dummy (controls in section 6, two-way clustered SE by firm and reaction date), the
interaction coefficient is positive. Reported with its 95% CI and the pre-computed MDE.

Primary H2 test: in the regression of the standardised earnings surprise on the crowded dummy
(same controls), the coefficient is negative.

Everything else (section 8) is secondary and reported with Romano-Wolf adjusted p-values
across the whole grid, with the total number of tests run stated.

## 4. Evidence against

H1 is rejected for this sample if the interaction coefficient is not positive at the 5% level
AND its CI excludes the MDE. H1 is "not detectable" (not rejected) if the CI includes the MDE.
H2 is rejected if the crowded coefficient is not negative at the 5% level and the discretion
interaction is flat. A null is reported as the finding; the post is written either way.

## 5. Sample

Events: every 8-K with Item 2.02 in EDGAR submissions, report date 2005-01-01 to 2025-12-31
[PROPOSED start; Item 2.02 numbering begins with the August 2004 8-K reform, earlier Item 12
events are excluded]. Event date = Period of Report. Session class from acceptanceDateTime
(US/Eastern) only when filingDate == reportDate: before 09:30 = pre-market, 09:30-16:00 =
in-session, after 16:00 = post-close. Lagged filings keep the date, get class "unknown", and
are excluded from the session-based primary test; their share is reported.

Reaction day: pre-market -> event date; post-close -> next trading day; in-session -> event
date, dropped in a robustness run; unknown -> excluded from primary, included in a calendar-day
robustness run.

Universe: US common stocks in Sharadar SEP with price >= $5 [PROPOSED] on day -2 and
non-missing returns through day +60; ADRs, funds and REIT-like trusts excluded by Sharadar
category. Delisted firms included; delisting returns included.

Development sample: report dates 2005-2015. Holdout: 2016-2025, run once, after the
development results are committed. [PROPOSED split]

## 6. Variables

Crowded (primary): the reaction session contains a CPI release, an Employment Situation
release, or an FOMC statement. Session rule: CPI and Employment Situation release at 08:30 ET
[to verify on the BLS schedule]; FOMC statements at 14:00 ET from 2013, 14:15 earlier
[to verify on the Fed pages]. A pre-market or in-session earnings release on such a day is
crowded; a post-close release on an FOMC day is crowded only if the next trading day carries
a release. Secondary crowding dummies: each release alone; a wider set adding PCE, ISM
Manufacturing and GDP advance. BLS dates that sit in within-10-day pairs (one headline release,
one revision-only date, see data/reference/REPORT.md) both count as crowded in the primary
dummy until verified against the BLS schedule; a robustness run drops both. Unscheduled FOMC
meetings and notation votes are excluded from the primary dummy and used in a robustness run.

Surprise, two measures, both reported:
- SUE: first-filed quarterly diluted EPS from EDGAR companyfacts minus the same quarter a
  year earlier, scaled by the standard deviation of that difference over the prior 8 quarters
  (minimum 4) [PROPOSED]; 2009 onward.
- Market-based: abnormal return over [0,+1] relative to the reaction day; full sample.
Surprise decile rank is formed within each calendar quarter, 0-9 rescaled to [-0.5, 0.5].

Abnormal returns: daily return minus the FF5+UMD fitted return, loadings estimated on days
-250 to -21 [PROPOSED]. CAR windows [0,+1], [+2,+20], [+2,+60].

Controls (all pre-event): number of other Item 2.02 events on the same reaction day
(Hirshleifer-Lim-Teoh), reaction-day day-of-week dummies (FOMC is Wednesday, Employment
Situation is Friday), earnings-season intensity (events in the trailing 5 days), log market
cap, book-to-market where available, prior 6-month return, firm fixed effects, year-quarter
fixed effects.

Discretion (H2): standard deviation of the firm's report day-of-quarter over the prior 12
quarters (minimum 6).

Abnormal volume: log(volume / mean volume over days -60 to -11).

## 7. Power

Before any return regression on the development sample, compute from the event table and the
residual SD of CAR[+2,+60] in a pilot of 200 randomly chosen 2005 events [PROPOSED]:
MDE = 2.8 x sigma x sqrt(1/N_crowded + 1/N_uncrowded) at 80% power, 5% two-sided.
Record N_crowded, N_uncrowded, sigma and the MDE in CHANGELOG.md. If the crowded top and
bottom surprise deciles each hold fewer than 500 events [PROPOSED] in the development sample,
widen crowding to the secondary set before testing and log the change.

## 8. Secondary analyses and robustness (fixed in advance)

- Immediate reaction: CAR[0,+1] on surprise x crowded; abnormal volume on crowded.
- Windows [+2,+20] and [+2,+60]; SUE vs market-based surprise.
- Each macro release type alone; wider crowding set; calendar-day crowding.
- Size terciles; surprise sign (positive vs negative) separately.
- Exclude 2008-09 and 2020; exclude in-session filings.
- Placebo 1: pseudo-macro days shifted by +7 and -7 calendar days.
- Placebo 2: 1,000 random draws [PROPOSED] of the same number of trading days per year,
  block-bootstrapped by month, to give the null distribution of the interaction coefficient.
- Portfolio form: calendar-time long top-decile short bottom-decile surprise portfolios,
  entered at close of day +1, held 60 days, equal-weighted, built separately from crowded
  and uncrowded events, plus the difference portfolio; FF5+UMD alpha with Newey-West (lag 5)
  [PROPOSED]; gross and net of Corwin-Schultz spread cost at measured turnover; position cap
  2% [PROPOSED]; number of names held reported.

## 9. What is not pre-registered

Any analysis not listed above is exploratory and labelled as such in RESULTS.md.
