"""Synthetic fixtures shaped exactly like the verified EDGAR structures (see events.py and
surprise.py docstrings). No real returns: everything here is generated."""
from __future__ import annotations

import io
import json
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

COLS = ["accessionNumber", "filingDate", "reportDate", "acceptanceDateTime", "act", "form",
        "fileNumber", "filmNumber", "items", "size", "isXBRL", "isInlineXBRL", "primaryDocument",
        "primaryDocDescription"]


def _arrays(rows):
    return {c: [r.get(c, "") for r in rows] for c in COLS}


def _row(acc, fdate, rdate, acc_dt, form="8-K", items="2.02,9.01"):
    return {"accessionNumber": acc, "filingDate": fdate, "reportDate": rdate,
            "acceptanceDateTime": acc_dt, "form": form, "items": items, "primaryDocument": "x.htm"}


@pytest.fixture(scope="session")
def submissions_zip(tmp_path_factory) -> Path:
    p = tmp_path_factory.mktemp("raw") / "submissions.zip"
    apple = {"cik": "320193", "name": "Apple Inc.", "filings": {"recent": _arrays([
        _row("0000320193-24-000120", "2024-10-31", "2024-10-31", "2024-10-31T20:30:25.000Z"),  # 16:30:25 EDT
        _row("0000320193-24-000999", "2024-09-10", "2024-09-10", "2024-09-10T20:05:00.000Z", items="7.01,9.01"),
        _row("0000320193-24-000081", "2024-08-02", "2024-06-29", "2024-08-02T20:01:00.000Z", form="10-Q", items=""),
    ]), "files": [{"name": "CIK0000320193-submissions-001.json", "filingFrom": "2005-01-01", "filingTo": "2010-12-31"}]}}
    apple_old = _arrays([
        _row("0001047469-05-000001", "2005-01-13", "2005-01-12", "2005-01-13T13:05:00.000Z"),  # lag 1 bday
    ])
    jpm = {"cik": "19617", "filings": {"recent": _arrays([
        _row("0000019617-24-000555", "2024-10-11", "2024-10-11", "2024-10-11T10:46:16.000Z"),  # 06:46:16 EDT
        _row("0000019617-24-000556", "2024-10-11", "2024-10-11", "2024-10-11T11:00:00.000Z"),  # duplicate same day
    ])}}
    sachem = {"cik": "1682220", "filings": {"recent": _arrays([
        _row("0001104659-23-040966", "2023-04-03", "2023-03-30", "2023-04-03T21:05:18.000Z"),  # lag 2 bdays
        _row("0001104659-23-040967", "2023-04-03", "2023-04-03", "2023-04-03T21:05:18.000Z", form="8-K/A"),
    ])}}
    insess = {"cik": "777", "filings": {"recent": _arrays([
        _row("0000000777-24-000001", "2024-10-10", "2024-10-10", "2024-10-10T14:30:00.000Z"),  # 10:30 EDT in-session
    ])}}
    with zipfile.ZipFile(p, "w") as z:
        z.writestr("CIK0000320193.json", json.dumps(apple))
        z.writestr("CIK0000320193-submissions-001.json", json.dumps(apple_old))
        z.writestr("CIK0000019617.json", json.dumps(jpm))
        z.writestr("CIK0001682220.json", json.dumps(sachem))
        z.writestr("CIK0000000777.json", json.dumps(insess))
    return p


@pytest.fixture(scope="session")
def companyfacts_zip(tmp_path_factory) -> Path:
    p = tmp_path_factory.mktemp("raw2") / "companyfacts.zip"

    def fact(start, end, val, filed, accn, form, fy, fp):
        return {"start": start, "end": end, "val": val, "accn": accn, "fy": fy, "fp": fp,
                "form": form, "filed": filed, "frame": None}

    facts = []
    # 8 quarters of 2022-2023 for CIK 320193, each filed twice (first in its own 10-Q, again a year later)
    base = [1.0, 1.1, 1.2, None, 1.3, 1.4, 1.5, None]  # Q4s missing -> derived from annual
    qdates = [("2022-01-01", "2022-03-31"), ("2022-04-01", "2022-06-30"), ("2022-07-01", "2022-09-30"),
              ("2022-10-01", "2022-12-31"), ("2023-01-01", "2023-03-31"), ("2023-04-01", "2023-06-30"),
              ("2023-07-01", "2023-09-30"), ("2023-10-01", "2023-12-31")]
    for i, ((s, e), v) in enumerate(zip(qdates, base)):
        if v is None:
            continue
        first = pd.Timestamp(e) + pd.Timedelta(days=35)
        facts.append(fact(s, e, v, first.strftime("%Y-%m-%d"), f"a{i}", "10-Q", int(e[:4]), f"Q{i % 4 + 1}"))
        facts.append(fact(s, e, v + 0.5, (first + pd.Timedelta(days=365)).strftime("%Y-%m-%d"), f"b{i}", "10-Q", int(e[:4]) + 1, f"Q{i % 4 + 1}"))
    facts.append(fact("2022-01-01", "2022-12-31", 4.5, "2023-02-15", "k22", "10-K", 2022, "FY"))  # Q4 2022 = 4.5-3.3 = 1.2
    facts.append(fact("2023-01-01", "2023-12-31", 5.8, "2024-02-15", "k23", "10-K", 2023, "FY"))  # Q4 2023 = 5.8-4.2 = 1.6
    d = {"cik": 320193, "facts": {"us-gaap": {"EarningsPerShareDiluted": {"units": {"USD/shares": facts}}}}}
    with zipfile.ZipFile(p, "w") as z:
        z.writestr("CIK0000320193.json", json.dumps(d))
    return p


@pytest.fixture(scope="session")
def reference_dir(tmp_path_factory) -> Path:
    d = tmp_path_factory.mktemp("ref")
    pd.DataFrame({"year": [2024, 2024], "meeting_start": ["2024-09-17", "2024-11-06"],
                  "meeting_end": ["2024-09-18", "2024-11-07"], "statement_date": ["2024-09-18", "2024-11-07"],
                  "scheduled": [1, 1], "source_url": ["x", "x"]}).to_csv(d / "fomc_dates.csv", index=False)
    pd.DataFrame({"release": ["CPI", "EMPSIT", "CPI", "EMPSIT"],
                  "release_date": ["2024-10-10", "2024-10-04", "2024-11-13", "2024-11-01"],
                  "source": ["alfred"] * 4}).to_csv(d / "bls_release_dates.csv", index=False)
    return d


@pytest.fixture(scope="session")
def synthetic_market():
    """Two years of daily factors and three tickers whose returns are rf + exact factor
    exposure + noise-free, with a known 3% abnormal bump on a chosen reaction day."""
    rng = np.random.default_rng(0)
    days = pd.bdate_range("2023-01-02", "2024-12-31")
    F = pd.DataFrame(rng.normal(0, 0.01, (len(days), 6)), index=days,
                     columns=["mktrf", "smb", "hml", "rmw", "cma", "umd"])
    F["rf"] = 0.0001
    betas = {"AAA": np.array([1.0, 0.2, -0.1, 0.0, 0.0, 0.1]),
             "BBB": np.array([0.8, 0.5, 0.3, 0.1, -0.2, 0.0]),
             "CCC": np.array([1.2, -0.3, 0.0, 0.2, 0.1, -0.1])}
    bump_day = pd.Timestamp("2024-08-15")
    rows = []
    for t, b in betas.items():
        r = F["rf"].values + F[["mktrf", "smb", "hml", "rmw", "cma", "umd"]].values @ b
        r = r.copy()
        r[days.get_loc(bump_day)] += 0.03 if t == "AAA" else 0.0
        price = 50 * np.cumprod(1 + r)
        rows.append(pd.DataFrame({"ticker": t, "date": days, "open": price, "high": price * 1.01,
                                  "low": price * 0.99, "close": price, "closeadj": price,
                                  "volume": 1_000_000 + (days == bump_day) * 2_000_000}))
    px = pd.concat(rows, ignore_index=True)
    px["ret"] = px.groupby("ticker")["closeadj"].pct_change()
    return F, px, bump_day
