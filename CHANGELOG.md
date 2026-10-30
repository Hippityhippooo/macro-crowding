# Changelog and decision log

Every [PROPOSED] threshold in PREREGISTRATION.md is promoted or changed here, with the reason,
before the first regression on the development sample.

## 2026-10-30

- Repository created. Pipeline written and tested on synthetic fixtures (17 tests). No real data run.
- Verified EDGAR record formats recorded in module docstrings.
- Gate numbers (events per year, same-day share, crowded cells): not yet computed.
- MDE: not yet computed.
- Macro calendar built from federalreserve.gov (FOMC 2004-2026, 183 scheduled statement dates) and ALFRED (CPI 303, EMPSIT 292 dates from 2003). 48 BLS dates sit in within-10-day pairs (seasonal-factor or benchmark revisions); flagged, not resolved. See data/reference/REPORT.md.
