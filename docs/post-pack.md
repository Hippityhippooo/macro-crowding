# Post pack (linkedin-presence section 8), 30 Oct 2026

Clearance: personal research on public data, posted from a personal account. Courtesy heads-up to Justin before posting (Faldo is identifiable as a Gotrade employee and the subject is US equities); not a sign-off requirement. No named security with a view, so no [[DISCLAIMER]] slot placed; E16 (POJK on non-licensed parties sharing financial information) is a judgement for Justin.

Package: A, document carousel (E1, E19), 15 slides (5 marked exploratory on the slide; cover on a heatmap backdrop, hero-number slide, two dark exploratory slides), 1080x1350, carousel/out/carousel.pdf (1.2 MB).
Document title (53 chars): Does the market read earnings differently on Fed day?
Caption: carousel/caption.txt (599 chars, first block 116). First comment: carousel/first_comment.txt (970 chars) with [REPO URL] and [HASH] to fill after the push.

Heading options (draft uses 1):
1. "When CPI and earnings land in the same session, who reads the 10-Q?" (reader who trades the open)
2. "FOMC days carry 126 earnings releases. The market reads them like any other." (reader who wants the number)
3. "Do CFOs hide bad quarters behind the Fed? No." (reader who comes for governance)

Posting time: Tuesday 3 Nov 2026, 13:00 London = 08:00 New York = 20:00 Jakarta (US clocks back on 1 Nov; UK on 25 Oct). First 90 minutes: Faldo answers every substantive comment with a number from RESULTS.md or a source. No pods, no automation.

Line most open to challenge: "What replicates is zero." Reply: development −1.48 pp (t −2.1) vs holdout +0.75 pp (t 1.1); FOMC-only −3.84 vs +0.06; 1,000 random calendars give 9% and 30% of draws at least as large. The two samples disagree in sign, so neither sign is the finding.

Interview list (one-line answers from RESULTS.md):
- Why no consensus data? Paid. Two free surprises instead: first-filed GAAP vs last year, and the two-day market reaction; both reported.
- Why session rather than calendar day? A 16:30 release on an FOMC day competes with nothing; a 06:46 release on a CPI day competes with the 08:30 print. The acceptance stamp makes the distinction.
- Why did the development sample show a negative? Concentrated on FOMC days; 9% of random calendars match it; it did not survive the holdout. Reported, not spun.
- Why calendar-time portfolios? Overlapping 60-day holds make event-time t-stats overstate; calendar-time with Newey-West handles the overlap.
- Attention vs noise, how separated? Volume and |CAR| on crowded sessions: both flat in both samples. Neither story fits.
- Biggest weakness? Survivorship: 94 of 6,274 delisted tickers covered. Crowded share 14.6% vs 15.9% survivors, so selection is weakly related to treatment.
- What would change your mind? A consensus-surprise version, or delisted prices, showing a gap.
- Who wrote the code? Drafted with AI assistance, reviewed and run by me; design, pre-registration and checks mine.

Portfolio pack: Featured decision at 5 days (post if substantive comments, else repo link with cover slide); Projects entry: "Earnings announcements and competing macro news, Nov 2026: pre-registered test of 421,885 EDGAR-timed earnings releases against the CPI, jobs and FOMC calendar; no drift or timing effect replicates across 2005–2015 and 2016–2025." Series name: "Public tests".

Scorecards at 5 and 30 days: impressions, comments, saves; profile views, viewer titles and firms, conversations started.

QA gate: figures in caption, comment, title, slides traced to RESULTS.md; first block 116 ≤ 140; caption 599 inside the 600 extension; no Unicode bold, no emoji, 0 hashtags; title 53 ≤ 58; every slide rendered and viewed at 360px; innerText counts (kicker, title and page number included) 38–79, body text at most 62 words [PROPOSED cap of 60 applied to body]; body ≥ 34px; human-voice strip pass run on all copy; authorship line true.
