"""Earnings surprise from EDGAR companyfacts (point-in-time by first filing date).

Verified structure (2026-10-30, data.sec.gov companyconcept, Apple EarningsPerShareDiluted):
  facts["us-gaap"]["EarningsPerShareDiluted"]["units"]["USD/shares"] is a list of dicts with
  start, end, val, accn, fy, fp, form, filed, frame. Three-month facts have start/end about
  91 days apart. The same (start, end) appears again in later filings with a later "filed",
  so the first-filed record is the point-in-time value. Q4 quarterly EPS is usually NOT
  tagged separately: the 10-K carries the annual figure, so Q4 must be derived.

Do not use the frames API for this: it returns the most recent filing for a period
(verified: a 2025 accession for CY2024Q3), which is not point-in-time.
"""
from __future__ import annotations

import json
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

TAG = "EarningsPerShareDiluted"
UNIT = "USD/shares"
QTR_DAYS = (80, 100)
YEAR_DAYS = (350, 380)


def _facts_from_json(d: dict, cik: int) -> pd.DataFrame:
    try:
        rows = d["facts"]["us-gaap"][TAG]["units"][UNIT]
    except KeyError:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df["cik"] = cik
    df["start"] = pd.to_datetime(df["start"], errors="coerce")
    df["end"] = pd.to_datetime(df["end"], errors="coerce")
    df["filed"] = pd.to_datetime(df["filed"], errors="coerce")
    df["span"] = (df["end"] - df["start"]).dt.days
    return df


def read_companyfacts_zip(path: str | Path) -> pd.DataFrame:
    frames = []
    with zipfile.ZipFile(path) as z:
        for name in z.namelist():
            if not name.startswith("CIK") or not name.endswith(".json"):
                continue
            cik = int(name[3:13])
            with z.open(name) as fh:
                try:
                    d = json.load(fh)
                except json.JSONDecodeError:
                    continue
            df = _facts_from_json(d, cik)
            if not df.empty:
                frames.append(df)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def read_mirror_eps(path: str | Path, tag: str = TAG) -> pd.DataFrame:
    """Alternative input: Parquet extract of the DenyTranDFW companyfacts mirror with columns
    source_folder (CIK##########_NAME), item, unit_type, start, end, val_dec, accn, fy, fp,
    form, filed, frame. Keeps USD/shares facts for `tag` and returns the companyconcept shape."""
    df = pd.read_parquet(path)
    df = df[(df["item"] == tag) & (df["unit_type"] == UNIT)].copy()
    df["cik"] = df["source_folder"].str[3:13].astype(int)
    df["val"] = df["val_dec"].astype(float)
    df["start"] = pd.to_datetime(df["start"], errors="coerce")
    df["end"] = pd.to_datetime(df["end"], errors="coerce")
    df["filed"] = pd.to_datetime(df["filed"], errors="coerce")
    df["span"] = (df["end"] - df["start"]).dt.days
    return df[["cik", "start", "end", "val", "accn", "fy", "fp", "form", "filed", "frame", "span"]].dropna(subset=["start", "end", "filed"]).reset_index(drop=True)


def first_filed_quarters(facts: pd.DataFrame) -> pd.DataFrame:
    """Point-in-time quarterly EPS: for each (cik, start, end) with a ~3-month span, keep the
    record with the earliest filed date. Then derive Q4 for fiscal years where the three
    other quarters and the annual figure exist and Q4 itself is missing (flag derived=1)."""
    q = facts[facts["span"].between(*QTR_DAYS)].sort_values("filed")
    q = q.drop_duplicates(["cik", "start", "end"], keep="first")
    q = q[["cik", "start", "end", "val", "filed", "accn", "form"]].assign(derived=0)

    a = facts[facts["span"].between(*YEAR_DAYS)].sort_values("filed")
    a = a.drop_duplicates(["cik", "start", "end"], keep="first")
    derived = []
    for _, yr in a.iterrows():
        qs = q[(q["cik"] == yr["cik"]) & (q["start"] >= yr["start"]) & (q["end"] <= yr["end"])]
        if len(qs) == 3:
            last_end = qs["end"].max()
            if last_end < yr["end"] - pd.Timedelta(days=60):
                derived.append({
                    "cik": yr["cik"], "start": last_end + pd.Timedelta(days=1), "end": yr["end"],
                    "val": yr["val"] - qs["val"].sum(),  # approximation: diluted EPS is not additive
                    "filed": yr["filed"], "accn": yr["accn"], "form": yr["form"], "derived": 1,
                })
    if derived:
        q = pd.concat([q, pd.DataFrame(derived)], ignore_index=True)
    return q.sort_values(["cik", "end"]).reset_index(drop=True)


def sue(quarters: pd.DataFrame, lookback: int = 8, min_obs: int = 4) -> pd.DataFrame:
    """Seasonal random walk SUE: (EPS_q - EPS_{q-4}) / sd of that difference over the prior
    `lookback` quarters (minimum `min_obs`). Prior quarters only: the sd uses differences
    whose own fiscal quarter ends before the current one, so nothing from the future enters."""
    out = []
    for cik, g in quarters.groupby("cik"):
        g = g.sort_values("end").reset_index(drop=True)
        g["eps_lag4"] = g["val"].shift(4)
        g["dseas"] = g["val"] - g["eps_lag4"]
        g["sd_prior"] = g["dseas"].shift(1).rolling(lookback, min_periods=min_obs).std()
        g["sue"] = g["dseas"] / g["sd_prior"]
        out.append(g)
    return pd.concat(out, ignore_index=True) if out else quarters.assign(sue=np.nan)


def attach_quarter(events: pd.DataFrame, quarters: pd.DataFrame, max_gap_days: int = 120) -> pd.DataFrame:
    """Link each event to the latest fiscal quarter end strictly before the event date, within
    `max_gap_days`. Uses the quarter's economic end date, not its filed date, because the
    press release (the event) precedes the 10-Q that tags the number."""
    q = quarters.sort_values("end")
    ev = events.sort_values("event_date").copy()
    merged = pd.merge_asof(
        ev, q[["cik", "end", "val", "sue", "derived", "filed"]].rename(columns={"end": "q_end", "filed": "q_filed"}),
        left_on="event_date", right_on="q_end", by="cik", direction="backward",
        tolerance=pd.Timedelta(days=max_gap_days),
    )
    return merged


def decile_rank(x: pd.Series, by: pd.Series) -> pd.Series:
    """Decile rank within each group, rescaled to [-0.5, 0.5]."""
    def _r(s):
        if s.notna().sum() < 10:
            return pd.Series(np.nan, index=s.index)
        return (pd.qcut(s.rank(method="first"), 10, labels=False) / 9.0) - 0.5
    return x.groupby(by, group_keys=False).apply(_r)
