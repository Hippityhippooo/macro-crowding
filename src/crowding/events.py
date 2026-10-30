"""Build the Item 2.02 event table from the EDGAR bulk submissions archive.

Verified structure (2026-10-30, data.sec.gov/submissions/CIK0000320193.json):
  filings.recent is a dict of parallel arrays: accessionNumber, filingDate, reportDate,
  acceptanceDateTime, act, form, fileNumber, filmNumber, items, size, isXBRL,
  isInlineXBRL, primaryDocument, primaryDocDescription.
  acceptanceDateTime is UTC, e.g. "2024-10-31T20:30:25.000Z"  (== 16:30:25 EDT, matching
  the filing index page "Accepted 2024-10-31 16:30:25").
  Older filings live in filings.files[*].name, each a JSON with the same arrays at top level.
  items is a comma-separated string, e.g. "2.02,9.01".
"""
from __future__ import annotations

import json
import zipfile
from dataclasses import dataclass
from datetime import datetime, time
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

ET = ZoneInfo("America/New_York")
OPEN = time(9, 30)
CLOSE = time(16, 0)

COLS = ["accessionNumber", "filingDate", "reportDate", "acceptanceDateTime", "form", "items",
        "primaryDocument"]


def parse_acceptance_et(value: str) -> datetime | None:
    """Parse an EDGAR acceptanceDateTime into an aware US/Eastern datetime.

    Accepts the JSON form ("...Z", UTC) and the filing-index form ("YYYY-MM-DD HH:MM:SS",
    already Eastern). Returns None for empty values.
    """
    if value is None or value == "" or (isinstance(value, float) and np.isnan(value)):
        return None
    s = str(value).strip()
    if s.endswith("Z"):
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        return dt.astimezone(ET)
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=ET)
    return dt.astimezone(ET)


def session_class(acceptance_et: datetime | None, filing_date: str, report_date: str) -> str:
    """pre_market / in_session / post_close when the 8-K was filed on the release date,
    otherwise unknown (acceptance time says nothing about when the press release went out).
    """
    if acceptance_et is None or not report_date or filing_date != report_date:
        return "unknown"
    t = acceptance_et.timetz().replace(tzinfo=None)
    if t < OPEN:
        return "pre_market"
    if t <= CLOSE:
        return "in_session"
    return "post_close"


def _frame_from_arrays(d: dict, cik: str) -> pd.DataFrame:
    missing = [c for c in COLS if c not in d]
    if missing:
        return pd.DataFrame(columns=COLS + ["cik"])
    df = pd.DataFrame({c: d[c] for c in COLS})
    df["cik"] = int(cik)
    return df


def _is_202(items: str) -> bool:
    if not isinstance(items, str):
        return False
    return "2.02" in [x.strip() for x in items.split(",")]


def read_submissions_zip(path: str | Path, forms=("8-K",)) -> pd.DataFrame:
    """Stream the bulk submissions.zip and return every filing of the given forms that
    carries Item 2.02. Amendments (8-K/A) are excluded by default and counted separately.
    """
    frames = []
    with zipfile.ZipFile(path) as z:
        for name in z.namelist():
            if not name.endswith(".json") or not name.startswith("CIK"):
                continue
            cik = name[3:13]
            with z.open(name) as fh:
                try:
                    d = json.load(fh)
                except json.JSONDecodeError:
                    continue
            if "filings" in d:  # main file
                arrays = d["filings"].get("recent", {})
            else:  # -submissions-NNN.json archive: arrays at top level
                arrays = d
            df = _frame_from_arrays(arrays, cik)
            if df.empty:
                continue
            df = df[df["form"].isin(forms) & df["items"].map(_is_202)]
            if not df.empty:
                frames.append(df)
    if not frames:
        return pd.DataFrame(columns=COLS + ["cik"])
    return pd.concat(frames, ignore_index=True)


def build_event_table(filings: pd.DataFrame) -> pd.DataFrame:
    """Add event date, Eastern acceptance time, filing lag and session class."""
    df = filings.copy()
    df["acceptance_et"] = df["acceptanceDateTime"].map(parse_acceptance_et)
    df["event_date"] = pd.to_datetime(df["reportDate"], errors="coerce")
    df["filing_date"] = pd.to_datetime(df["filingDate"], errors="coerce")
    ok = df["event_date"].notna() & df["filing_date"].notna()
    df["lag_bdays"] = np.nan
    df.loc[ok, "lag_bdays"] = np.busday_count(
        df.loc[ok, "event_date"].values.astype("datetime64[D]"),
        df.loc[ok, "filing_date"].values.astype("datetime64[D]"),
    )
    df["session"] = [
        session_class(a, f, r) for a, f, r in zip(df["acceptance_et"], df["filingDate"], df["reportDate"])
    ]
    df["acceptance_time_et"] = df["acceptance_et"].map(lambda d: d.strftime("%H:%M:%S") if d else None)
    # one event per firm per event date: keep the earliest accepted filing
    df = df.sort_values(["cik", "event_date", "acceptance_et"]).drop_duplicates(["cik", "event_date"], keep="first")
    return df.reset_index(drop=True)


def assign_reaction_day(events: pd.DataFrame, trading_days: pd.DatetimeIndex) -> pd.DataFrame:
    """Reaction day: pre_market/in_session -> event date (or next trading day if the event
    date is not a trading day); post_close -> next trading day after the event date;
    unknown -> event date (calendar-day fallback, flagged)."""
    td = pd.DatetimeIndex(sorted(trading_days))
    df = events.copy()
    nat = np.datetime64("NaT", "ns")
    tv = td.values.astype("datetime64[ns]")
    pos = td.searchsorted(df["event_date"].values, side="left")
    same_or_next = np.where(pos < len(td), tv[np.minimum(pos, len(td) - 1)], nat)
    pos_after = td.searchsorted(df["event_date"].values, side="right")
    strictly_next = np.where(pos_after < len(td), tv[np.minimum(pos_after, len(td) - 1)], nat)
    df["reaction_day"] = pd.to_datetime(np.where(df["session"].eq("post_close"), strictly_next, same_or_next))
    df["reaction_day_is_fallback"] = df["session"].eq("unknown")
    return df


@dataclass
class EventSummary:
    n_events: int
    n_firms: int
    first_date: str
    last_date: str
    session_shares: dict


def summarise(events: pd.DataFrame) -> EventSummary:
    shares = events["session"].value_counts(normalize=True).round(4).to_dict()
    return EventSummary(
        n_events=len(events),
        n_firms=events["cik"].nunique(),
        first_date=str(events["event_date"].min().date()) if len(events) else "",
        last_date=str(events["event_date"].max().date()) if len(events) else "",
        session_shares=shares,
    )
