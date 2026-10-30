# Presentation plan (filled only after RESULTS.md exists)

Package: LinkedIn document carousel, 9-12 slides, 1080x1350, caption 150-600 chars, document
title at most 58 chars. All figures copied from RESULTS.md; nothing else enters the slides.

Slide order
1. Cover: heading as a question; one line on what was done; chips: N events, period, horizon.
2. The scene: calendar heatmap of earnings announcements per trading day with macro days marked
   (needs only the event table, so it can be drawn before any return is computed).
3. Method: five numbered steps (EDGAR PIT events, session rule, two surprises, controls, holdout).
4. H1: CAR[-1,+60] paths, top-minus-bottom surprise, crowded vs uncrowded.
5. H1: immediate reaction vs drift coefficients, paired bars with CIs.
6. H2: surprise distribution on crowded vs uncrowded sessions.
7. Placebo distribution with the actual coefficient marked.
8. Limits: MDE, same-day filing share, delisted coverage, GAAP vs non-GAAP surprise.
9. Verdict and what would change it; repo link.
10. Sources and checks.

Heading options (slots from RESULTS.md only)
- "When CPI and earnings land at 8:30, who reads the 10-Q? I checked [N] announcements."
- "[X]% of US earnings releases share a session with a top-tier macro print. The market [does / does not] care."
- "Do CFOs hide bad quarters behind the Fed?"

First comment: repo link, pre-registration commit hash, the caveat a sceptic checks first
(filing-lag share), method list (PIT from EDGAR acceptance timestamps, two-way clustered SE,
calendar-time portfolios, holdout run once, placebo).

Clearance: not cleared until Justin has signed off (US equities overlap with Gotrade's product).
