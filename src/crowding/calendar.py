"""Macro release calendar and the crowding dummies.

Inputs (data/reference):
  fomc_dates.csv        year,meeting_start,meeting_end,statement_date,scheduled,source_url
  bls_release_dates.csv release,release_date,source      release in {CPI, EMPSIT}
Both are transcribed from federalreserve.gov and ALFRED (see data/reference/REPORT.md).

Release times are parameters, not data. Defaults below are the standard times and are
flagged [to verify] in PREREGISTRATION.md section 6.
"""
from __future__ import annotations

from datetime import time
from pathlib import Path

import pandas as pd

RELEASE_TIMES = {
    "CPI": time(8, 30),      # [to verify] BLS schedule
    "EMPSIT": time(8, 30),   # [to verify] BLS schedule
    "FOMC": time(14, 0),     # [to verify] 14:15 before 2013-ish; see fomc_time()
}
PRIMARY_SET = ("CPI", "EMPSIT", "FOMC")


def fomc_time(d: pd.Timestamp) -> time:
    # Statement release moved from 14:15 to 14:00 ET; the switch year is to be verified
    # on the Fed pages before use. Both are afternoon, so the session rule is unaffected.
    return time(14, 15) if d.year < 2013 else time(14, 0)


def load_macro_days(ref_dir: str | Path, scheduled_only: bool = True) -> pd.DataFrame:
    ref = Path(ref_dir)
    fomc = pd.read_csv(ref / "fomc_dates.csv", parse_dates=["statement_date"])
    if scheduled_only:
        fomc = fomc[fomc["scheduled"] == 1]
    fomc = pd.DataFrame({"release": "FOMC", "date": fomc["statement_date"]})
    bls = pd.read_csv(ref / "bls_release_dates.csv", parse_dates=["release_date"])
    bls = pd.DataFrame({"release": bls["release"], "date": bls["release_date"]})
    out = pd.concat([fomc, bls], ignore_index=True).drop_duplicates()
    out["date"] = pd.to_datetime(out["date"]).dt.normalize()
    out["time_et"] = [fomc_time(d) if r == "FOMC" else RELEASE_TIMES[r] for r, d in zip(out["release"], out["date"])]
    return out.sort_values(["date", "release"]).reset_index(drop=True)


def crowding_flags(events: pd.DataFrame, macro: pd.DataFrame, releases=PRIMARY_SET) -> pd.DataFrame:
    """Two definitions.

    crowded_calendar: a release in `releases` falls on the reaction day.
    crowded_session:  the release lands inside the reaction session of the earnings news.
        pre_market  -> any release on the reaction day (08:30 prints and 14:00 statements both
                       hit the first session the news trades in)
        in_session  -> release on the reaction day at or after the acceptance time
                       (an 08:30 print before a 10:00 filing is already in prices; treated
                       as not competing) -- conservative; robustness run flips this
        post_close  -> reaction day is the next trading day: any release that day competes
        unknown     -> NaN (excluded from the session-based primary test)
    Also returns per-release flags for the secondary tests.
    """
    m = macro[macro["release"].isin(releases)]
    by_day = m.groupby("date").agg(releases=("release", lambda s: sorted(set(s))),
                                   earliest=("time_et", "min"))
    df = events.copy()
    rd = pd.to_datetime(df["reaction_day"]).dt.normalize()
    df["macro_releases"] = rd.map(by_day["releases"]).apply(lambda x: x if isinstance(x, list) else [])
    df["crowded_calendar"] = df["macro_releases"].map(len).gt(0).astype(int)
    for r in releases:
        df[f"crowded_{r.lower()}"] = df["macro_releases"].map(lambda L, r=r: int(r in L))

    def _session_flag(row):
        s = row["session"]
        if s == "unknown":
            return float("nan")
        if not row["macro_releases"]:
            return 0.0
        if s in ("pre_market", "post_close"):
            return 1.0
        # in_session: compare acceptance time with each release time that day
        acc = row["acceptance_et"].timetz().replace(tzinfo=None)
        times = m[m["date"] == rd.loc[row.name]]["time_et"]
        return 1.0 if any(t >= acc for t in times) else 0.0

    df["crowded_session"] = df.apply(_session_flag, axis=1)
    return df


def same_day_event_count(events: pd.DataFrame) -> pd.Series:
    """Hirshleifer-Lim-Teoh control: other Item 2.02 events on the same reaction day."""
    counts = events.groupby("reaction_day")["cik"].transform("count")
    return counts - 1


def season_intensity(events: pd.DataFrame, window_days: int = 5) -> pd.Series:
    """Events in the trailing `window_days` trading days (including the day), per event."""
    daily = events.groupby("reaction_day").size().sort_index()
    rolled = daily.rolling(window_days, min_periods=1).sum()
    return events["reaction_day"].map(rolled)
