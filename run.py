"""Pipeline entry point.

Stages (run in order; each writes to data/processed and prints a short summary):
  events    submissions.zip        -> events.parquet
  gate      events + reference     -> output/gate.md   (counts, same-day share, cells)
  surprise  companyfacts.zip       -> quarters.parquet, events_with_sue.parquet
  returns   SEP csv + French csvs  -> panel.parquet (CARs, volume, spread)
  tests     panel                  -> output/results_dev.md  (development sample only)

Usage: python run.py <stage> [--sample dev|holdout]
The holdout stage refuses to run unless output/results_dev.md exists and is committed.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent / "src"))
from crowding import calendar as cal  # noqa: E402
from crowding import events as evm  # noqa: E402
from crowding import inference as inf  # noqa: E402
from crowding import returns as rtn  # noqa: E402
from crowding import surprise as sur  # noqa: E402

ROOT = Path(__file__).parent
RAW, REF, PROC, OUT = ROOT / "data/raw", ROOT / "data/reference", ROOT / "data/processed", ROOT / "output"
DEV = (pd.Timestamp("2005-01-01"), pd.Timestamp("2015-12-31"))
HOLDOUT = (pd.Timestamp("2016-01-01"), pd.Timestamp("2025-12-31"))


def stage_events(args):
    filings = evm.read_submissions_zip(RAW / "submissions.zip")
    ev = evm.build_event_table(filings)
    PROC.mkdir(parents=True, exist_ok=True)
    ev.to_parquet(PROC / "events.parquet")
    s = evm.summarise(ev)
    print(f"events={s.n_events} firms={s.n_firms} {s.first_date}..{s.last_date} sessions={s.session_shares}")


def stage_gate(args):
    ev = pd.read_parquet(PROC / "events.parquet")
    macro = cal.load_macro_days(REF)
    # trading-day calendar: use macro-free weekday calendar until prices are in; replaced by
    # the French factor index once returns stage has run
    fx = PROC / "factors.parquet"
    td = pd.DatetimeIndex(pd.read_parquet(fx).index) if fx.exists() else pd.bdate_range(ev["event_date"].min(), ev["event_date"].max() + pd.Timedelta(days=5))
    ev = evm.assign_reaction_day(ev, td)
    ev = cal.crowding_flags(ev, macro)
    ev["year"] = ev["event_date"].dt.year
    lines = ["# Feasibility gate", "", "## Events per year and same-day filing share", ""]
    g = ev.groupby("year").agg(events=("cik", "size"),
                               same_day=("session", lambda s: (s != "unknown").mean()),
                               crowded_cal=("crowded_calendar", "mean"),
                               crowded_sess=("crowded_session", "mean"))
    lines.append(g.round(3).to_markdown())
    lines += ["", "## Session class shares", "", ev["session"].value_counts(normalize=True).round(3).to_markdown()]
    lines += ["", "## Crowded-session events by year (count)", "",
              ev[ev["crowded_session"] == 1].groupby("year").size().to_frame("n").to_markdown()]
    OUT.mkdir(exist_ok=True)
    (OUT / "gate.md").write_text("\n".join(lines))
    ev.to_parquet(PROC / "events_crowded.parquet")
    print((OUT / "gate.md").read_text())


def stage_surprise(args):
    facts = sur.read_companyfacts_zip(RAW / "companyfacts.zip")
    q = sur.sue(sur.first_filed_quarters(facts))
    q.to_parquet(PROC / "quarters.parquet")
    ev = pd.read_parquet(PROC / "events_crowded.parquet")
    ev = sur.attach_quarter(ev, q)
    ev.to_parquet(PROC / "events_with_sue.parquet")
    print(f"quarters={len(q)} events_with_sue={ev['sue'].notna().sum()} of {len(ev)}")


def stage_returns(args):
    ev = pd.read_parquet(PROC / "events_with_sue.parquet")
    tk = pd.read_csv(RAW / "SHARADAR_TICKERS.csv")
    tk["cik"] = tk["secfilings"].map(rtn.parse_cik_from_url) if "secfilings" in tk else np.nan
    tk = tk.dropna(subset=["cik"]).astype({"cik": int})
    tk = tk[tk["table"].eq("SEP") & tk["category"].str.contains("Domestic", na=False)] if "table" in tk else tk
    ev = ev.merge(tk[["cik", "ticker"]].drop_duplicates("cik"), on="cik", how="inner")
    factors = rtn.load_french_daily(RAW / "ff5_daily.csv", RAW / "mom_daily.csv")
    factors.to_parquet(PROC / "factors.parquet")
    px = rtn.load_sep(RAW / "SHARADAR_SEP.csv", tickers=set(ev["ticker"]))
    ev = evm.assign_reaction_day(ev, pd.DatetimeIndex(factors.index))
    stats = rtn.event_window_stats(px, factors, ev)
    panel = ev.merge(stats, on=["cik", "ticker", "reaction_day"], how="inner")
    panel = panel[panel["price_m2"] >= 5]
    panel["market_surprise"] = panel["car_0_1"]
    panel["yq"] = pd.to_datetime(panel["reaction_day"]).dt.to_period("Q").astype(str)
    panel["surprise_rank"] = sur.decile_rank(panel["market_surprise"], panel["yq"])
    panel["sue_rank"] = sur.decile_rank(panel["sue"], panel["yq"])
    panel["same_day_n"] = cal.same_day_event_count(panel)
    panel["season"] = cal.season_intensity(panel)
    panel["dow"] = pd.to_datetime(panel["reaction_day"]).dt.dayofweek
    panel = pd.get_dummies(panel, columns=["dow"], prefix="dow", drop_first=True, dtype=float)
    panel.to_parquet(PROC / "panel.parquet")
    print(f"panel rows={len(panel)} crowded_session={panel['crowded_session'].sum()}")


def _git_committed(path: Path) -> bool:
    try:
        out = subprocess.run(["git", "status", "--porcelain", str(path)], capture_output=True, text=True, cwd=ROOT)
        return path.exists() and out.stdout.strip() == ""
    except Exception:
        return False


def stage_tests(args):
    panel = pd.read_parquet(PROC / "panel.parquet")
    lo, hi = DEV if args.sample == "dev" else HOLDOUT
    if args.sample == "holdout" and not _git_committed(OUT / "results_dev.md"):
        sys.exit("Refusing to run the holdout: commit output/results_dev.md first.")
    p = panel[(panel["event_date"] >= lo) & (panel["event_date"] <= hi)]
    controls = ["same_day_n", "season"] + [c for c in p.columns if c.startswith("dow_")]
    lines = [f"# Results ({args.sample} sample {lo.date()}..{hi.date()})", "",
             f"N={len(p)}, crowded_session N={int(p['crowded_session'].sum())}", ""]
    n_c = int(p["crowded_session"].sum()); n_u = int((p["crowded_session"] == 0).sum())
    sigma = float(p["car_2_60"].std())
    lines += [f"MDE (CAR[+2,+60], 80% power): {inf.mde(sigma, max(n_c,1), max(n_u,1)):.4f} with sigma={sigma:.4f}", ""]
    for car in ["car_0_1", "car_2_20", "car_2_60"]:
        for s in ["surprise_rank", "sue_rank"]:
            try:
                b, se, t, n = inf.h1_regression(p, car_col=car, surprise_col=s, controls=controls)
                lines.append(f"H1 {car} x {s}: sxc={b['sxc']:.5f} se={se['sxc']:.5f} t={t['sxc']:.2f} n={n}")
            except Exception as e:  # noqa: BLE001
                lines.append(f"H1 {car} x {s}: failed ({e})")
    try:
        b, se, t, n = inf.h2_regression(p, surprise_col="sue", controls=controls)
        lines.append(f"H2 sue on crowded: b={b['crowded_session']:.4f} se={se['crowded_session']:.4f} t={t['crowded_session']:.2f} n={n}")
    except Exception as e:  # noqa: BLE001
        lines.append(f"H2: failed ({e})")
    OUT.mkdir(exist_ok=True)
    (OUT / f"results_{args.sample}.md").write_text("\n".join(lines))
    print("\n".join(lines))


STAGES = {"events": stage_events, "gate": stage_gate, "surprise": stage_surprise,
          "returns": stage_returns, "tests": stage_tests}

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=STAGES)
    ap.add_argument("--sample", default="dev", choices=["dev", "holdout"])
    a = ap.parse_args()
    STAGES[a.stage](a)
