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
    mirror = RAW / "item202_filings.parquet"
    filings = evm.read_mirror_parquet(mirror) if mirror.exists() else evm.read_submissions_zip(RAW / "submissions.zip")
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
    mirror = RAW / "eps_facts.parquet"
    facts = sur.read_mirror_eps(mirror) if mirror.exists() else sur.read_companyfacts_zip(RAW / "companyfacts.zip")
    q = sur.sue(sur.first_filed_quarters(facts))
    q.to_parquet(PROC / "quarters.parquet")
    ev = pd.read_parquet(PROC / "events_crowded.parquet")
    ev = sur.attach_quarter(ev, q)
    ev.to_parquet(PROC / "events_with_sue.parquet")
    print(f"quarters={len(q)} events_with_sue={ev['sue'].notna().sum()} of {len(ev)}")


def stage_returns(args):
    ev = pd.read_parquet(PROC / "events_with_sue.parquet")
    ev = ev[ev["event_date"] >= "2005-01-01"].copy()
    factors = rtn.load_factors_decimal_csv(RAW / "ff5_umd_daily_full_decimal.csv")
    factors.to_parquet(PROC / "factors.parquet")
    td = pd.DatetimeIndex(factors.index)
    # reaction day on the real trading calendar, then crowding flags again on that day
    ev = ev.drop(columns=[c for c in ev.columns if c.startswith("crowded_") or c in ("macro_releases", "reaction_day", "reaction_day_is_fallback")])
    ev = evm.assign_reaction_day(ev, td)
    ev = cal.crowding_flags(ev, cal.load_macro_days(REF))
    # cik -> ticker whose price window covers the event (Sharadar free master); several tickers per cik allowed
    req = pd.read_csv(REF / "ticker_request.csv", parse_dates=["firstpricedate", "lastpricedate"])
    m = ev.merge(req[["cik", "ticker", "firstpricedate", "lastpricedate", "isdelisted"]], on="cik", how="inner")
    m = m[(m["event_date"] >= m["firstpricedate"] - pd.Timedelta(days=5)) & (m["event_date"] <= m["lastpricedate"])]
    m = m.sort_values(["cik", "event_date", "isdelisted"]).drop_duplicates(["cik", "event_date"], keep="first")
    px = rtn.load_prices_parquet(RAW / "prices_yf_all.parquet", tickers=set(m["ticker"]))
    have = set(px["ticker"])
    m = m[m["ticker"].isin(have)]
    print(f"events 2005+: {len(ev)}; with a ticker in window: {len(m)}; tickers with prices: {len(have)}")
    stats = rtn.event_window_stats(px, factors, m)
    panel = m.merge(stats.drop_duplicates(["cik", "ticker", "reaction_day"]), on=["cik", "ticker", "reaction_day"], how="inner")
    panel = panel.drop_duplicates(["cik", "reaction_day"])
    print(f"panel before filters: {len(panel)}")
    panel = panel[panel["price_m2"] >= 5]
    panel["market_surprise"] = panel["car_0_1"]
    panel["yq"] = pd.to_datetime(panel["reaction_day"]).dt.to_period("Q").astype(str)
    panel["surprise_rank"] = sur.decile_rank(panel["market_surprise"], panel["yq"])
    panel["sue_w"] = panel["sue"].clip(-10, 10)
    panel["sue_rank"] = sur.decile_rank(panel["sue_w"], panel["yq"])
    panel["same_day_n"] = cal.same_day_event_count(ev).reindex(panel.index) if False else panel["reaction_day"].map(ev.groupby("reaction_day").size()) - 1
    panel["season"] = panel["reaction_day"].map(ev.groupby("reaction_day").size().sort_index().rolling(5, min_periods=1).sum())
    panel["dow"] = pd.to_datetime(panel["reaction_day"]).dt.dayofweek
    panel = pd.get_dummies(panel, columns=["dow"], prefix="dow", drop_first=True, dtype=float)
    panel.to_parquet(PROC / "panel.parquet")
    print(f"panel rows={len(panel)} crowded_session={int(panel['crowded_session'].sum())} firms={panel['cik'].nunique()}")


def _git_committed(path: Path) -> bool:
    try:
        out = subprocess.run(["git", "status", "--porcelain", str(path)], capture_output=True, text=True, cwd=ROOT)
        return path.exists() and out.stdout.strip() == ""
    except Exception:
        return False


def _fast_interaction_coef(d, car_col, crowd_col, surprise_col, controls):
    """Demeaned OLS point estimate of the surprise x crowded interaction (no SE); used for placebos."""
    dd = d.copy()
    dd["sxc"] = dd[surprise_col] * dd[crowd_col]
    cols = [car_col, surprise_col, crowd_col, "sxc"] + controls
    dm = inf.demean_within(dd, cols, by=["cik", "yq"])
    X = np.column_stack([np.ones(len(dm)), dm[[c for c in cols if c != car_col]].values])
    beta, *_ = np.linalg.lstsq(X, dm[car_col].values, rcond=None)
    return float(beta[3])


def stage_tests(args):
    panel = pd.read_parquet(PROC / "panel.parquet")
    factors = pd.read_parquet(PROC / "factors.parquet")
    lo, hi = DEV if args.sample == "dev" else HOLDOUT
    if args.sample == "holdout" and not _git_committed(OUT / "results_dev.md"):
        sys.exit("Refusing to run the holdout: commit output/results_dev.md first.")
    p = panel[(panel["event_date"] >= lo) & (panel["event_date"] <= hi)].copy()
    controls = ["same_day_n", "season"] + [c for c in p.columns if c.startswith("dow_")]
    L = [f"# Results ({args.sample} sample {lo.date()}..{hi.date()})", "",
         f"N={len(p)} firms={p['cik'].nunique()} crowded_session N={int(p['crowded_session'].sum())} unknown-session N={int(p['crowded_session'].isna().sum())}"]
    n_c = int((p["crowded_session"] == 1).sum()); n_u = int((p["crowded_session"] == 0).sum())
    sigma = float(p["car_2_60"].std())
    L += [f"sigma(CAR[+2,+60])={sigma:.4f}; MDE for a difference in mean CAR at 80% power = {inf.mde(sigma, max(n_c,1), max(n_u,1)):.4f}", ""]
    for s_col in ["surprise_rank", "sue_rank"]:
        ex = p.dropna(subset=[s_col, "crowded_session"])
        top = ex[(ex[s_col] >= 0.4) & (ex.crowded_session == 1)].shape[0]; bot = ex[(ex[s_col] <= -0.4) & (ex.crowded_session == 1)].shape[0]
        L.append(f"cell check {s_col}: crowded top decile={top}, crowded bottom decile={bot} (pre-registered minimum 500)")
    L.append("")
    L.append("## H1 primary and secondary (coefficient on surprise_rank x crowded_session; firm+yq FE; 2-way clustered)")
    prim = None
    for car in ["car_2_60", "car_2_20"]:
        for s_col in ["surprise_rank", "sue_rank"]:
            try:
                b, se, t, n = inf.h1_regression(p, car_col=car, surprise_col=s_col, controls=controls)
                tag = "PRIMARY" if (car == "car_2_60" and s_col == "surprise_rank") else "secondary"
                L.append(f"{tag} {car} x {s_col}: b={b['sxc']:.5f} se={se['sxc']:.5f} t={t['sxc']:.2f} 95%CI=[{b['sxc']-1.96*se['sxc']:.5f},{b['sxc']+1.96*se['sxc']:.5f}] n={n}; main effects: surprise b={b[s_col]:.5f}, crowded b={b['crowded_session']:.5f}")
                if tag == "PRIMARY": prim = (b["sxc"], se["sxc"])
            except Exception as e:  # noqa: BLE001
                L.append(f"{car} x {s_col}: failed ({e})")
    L.append("")
    L.append("## Immediate reaction and attention channel")
    try:
        b, se, t, n = inf.h1_regression(p, car_col="car_0_1", surprise_col="sue_rank", controls=controls)
        L.append(f"CAR[0,+1] x sue_rank: sxc b={b['sxc']:.5f} t={t['sxc']:.2f}; sue main b={b['sue_rank']:.5f} n={n}")
    except Exception as e:  # noqa: BLE001
        L.append(f"immediate reaction failed ({e})")
    try:
        d = p.dropna(subset=["abn_volume", "crowded_session"]).copy(); d["yq"] = d["yq"]
        cols = ["abn_volume", "crowded_session"] + controls
        dm = inf.demean_within(d, cols, by=["cik", "yq"])
        b, se, t, n = inf.ols_twoway_cluster(dm["abn_volume"], dm[["crowded_session"] + controls], d["cik"], d["reaction_day"])
        L.append(f"abnormal volume on crowded: b={b['crowded_session']:.4f} se={se['crowded_session']:.4f} t={t['crowded_session']:.2f} n={n}")
        d["absr"] = d["car_0_1"].abs()
        cols = ["absr", "crowded_session"] + controls
        dm = inf.demean_within(d, cols, by=["cik", "yq"])
        b, se, t, n = inf.ols_twoway_cluster(dm["absr"], dm[["crowded_session"] + controls], d["cik"], d["reaction_day"])
        L.append(f"|CAR[0,+1]| on crowded (noise channel): b={b['crowded_session']:.4f} t={t['crowded_session']:.2f} n={n}")
    except Exception as e:  # noqa: BLE001
        L.append(f"volume/noise failed ({e})")
    L.append("")
    L.append("## Robustness grid (interaction coefficient, CAR[+2,+60] x surprise_rank)")
    base = p.dropna(subset=["surprise_rank", "crowded_session", "car_2_60"])
    grid = {
        "calendar-day crowding": base.assign(crowded_session=base["crowded_calendar"].astype(float)),
        "CPI only": base.assign(crowded_session=base["crowded_cpi"].astype(float)),
        "EMPSIT only": base.assign(crowded_session=base["crowded_empsit"].astype(float)),
        "FOMC only": base.assign(crowded_session=base["crowded_fomc"].astype(float)),
        "excl in-session filings": base[base["session"] != "in_session"],
        "excl 2008-09 and 2020": base[~base["event_date"].dt.year.isin([2008, 2009, 2020])],
        "positive surprises only": base[base["surprise_rank"] > 0],
        "negative surprises only": base[base["surprise_rank"] < 0],
        "listed-now firms only": base[base["isdelisted"] == "N"],
    }
    rob = {}
    for k, d in grid.items():
        try:
            b, se, t, n = inf.h1_regression(d, controls=controls)
            rob[k] = (b["sxc"], se["sxc"], t["sxc"], n)
            L.append(f"{k}: b={b['sxc']:.5f} se={se['sxc']:.5f} t={t['sxc']:.2f} n={n}")
        except Exception as e:  # noqa: BLE001
            L.append(f"{k}: failed ({e})")
    L.append("")
    L.append("## Placebos")
    macro = cal.load_macro_days(REF)
    for shift in (-7, 7):
        pl = cal.crowding_flags(base.drop(columns=[c for c in base.columns if c.startswith("crowded_") or c == "macro_releases"]), inf.placebo_shift(macro, shift))
        try:
            b, se, t, n = inf.h1_regression(pl, controls=controls)
            L.append(f"pseudo-macro days shifted {shift:+d}d: b={b['sxc']:.5f} t={t['sxc']:.2f} n={n}")
        except Exception as e:  # noqa: BLE001
            L.append(f"shift {shift}: failed ({e})")
    rng = np.random.default_rng(20261030)
    td = pd.DatetimeIndex(factors.index)
    n_per_year = macro[macro["date"].dt.year.between(lo.year, hi.year)].groupby(macro["date"].dt.year).size().to_dict()
    draws = []
    B = args.placebos
    for i in range(B):
        pl = inf.placebo_random_days(td, n_per_year, rng)
        flags = cal.crowding_flags(base[["cik", "session", "reaction_day", "acceptance_et"]].copy(), pl.assign(time_et=pd.Timestamp("08:30").time()), releases=("PLACEBO",))
        d = base.assign(crowded_session=flags["crowded_session"].values).dropna(subset=["crowded_session"])
        draws.append(_fast_interaction_coef(d, "car_2_60", "crowded_session", "surprise_rank", controls))
    draws = np.array(draws)
    if prim is not None and len(draws):
        L.append(f"random-day placebo ({B} draws): null mean={draws.mean():.5f} sd={draws.std():.5f}; actual b={prim[0]:.5f}; share |placebo|>=|actual| = {(np.abs(draws) >= abs(prim[0])).mean():.3f}")
    np.save(OUT / f"placebo_draws_{args.sample}.npy", draws)
    L.append("")
    L.append("## Calendar-time portfolios (top minus bottom market-surprise decile, 60-day hold, equal-weighted)")
    px = rtn.load_prices_parquet(RAW / "prices_yf_all.parquet", tickers=set(base["ticker"]))
    fx = factors.loc[(factors.index >= lo - pd.Timedelta(days=400)) & (factors.index <= hi + pd.Timedelta(days=120))]
    for name, d in [("crowded", base[base.crowded_session == 1]), ("uncrowded", base[base.crowded_session == 0])]:
        port, held, to = inf.calendar_time_portfolio(d, px, fx)
        a, t, n = inf.newey_west_alpha(port.dropna(), fx)
        gross = port.dropna()
        cost = float((d["cs_spread"].median() if d["cs_spread"].notna().any() else 0.0))
        net = gross - to.reindex(gross.index).fillna(0) * cost
        an, tn, _ = inf.newey_west_alpha(net, fx)
        L.append(f"{name}: daily alpha={a*1e4:.2f}bp (t={t:.2f}), net of Corwin-Schultz {cost*1e4:.0f}bp half-spread x turnover: {an*1e4:.2f}bp (t={tn:.2f}); mean names held={held.mean():.0f}; mean daily turnover={to.mean():.3f}; n days={n}")
        if name == "crowded": pc = port
        else: pu = port
    diff = (pc - pu).dropna()
    a, t, n = inf.newey_west_alpha(diff, fx)
    L.append(f"difference (crowded minus uncrowded): daily alpha={a*1e4:.2f}bp t={t:.2f} n={n}")
    OUT.mkdir(exist_ok=True)
    (OUT / f"results_{args.sample}.md").write_text("\n".join(L))
    print("\n".join(L))


def stage_h2(args):
    """H2 needs no prices: run on events_with_sue with the session-based crowding dummy."""
    ev = pd.read_parquet(PROC / "events_with_sue.parquet")
    lo, hi = DEV if args.sample == "dev" else HOLDOUT
    if args.sample == "holdout" and not _git_committed(OUT / "results_h2_dev.md"):
        sys.exit("Refusing to run the holdout: commit output/results_h2_dev.md first.")
    ev = ev[(ev["event_date"] >= lo) & (ev["event_date"] <= hi)].copy()
    ev = ev.sort_values(["cik", "event_date"])
    ev["doq"] = (ev["event_date"] - ev["q_end"]).dt.days
    ev["discretion"] = ev.groupby("cik")["doq"].transform(lambda s: s.shift(1).rolling(12, min_periods=6).std())
    ev["sue_w"] = ev["sue"].clip(-10, 10)
    ev["same_day_n"] = cal.same_day_event_count(ev)
    ev["season"] = cal.season_intensity(ev)
    ev["dow"] = pd.to_datetime(ev["reaction_day"]).dt.dayofweek
    ev = pd.get_dummies(ev, columns=["dow"], prefix="dow", drop_first=True, dtype=float)
    controls = ["same_day_n", "season"] + [c for c in ev.columns if c.startswith("dow_")]
    d = ev.dropna(subset=["sue_w", "crowded_session"])
    lines = [f"# H2 results ({args.sample} sample {lo.date()}..{hi.date()})", "",
             f"N with SUE and session class = {len(d)}; crowded_session N = {int(d['crowded_session'].sum())}",
             f"Raw means: SUE crowded {d.loc[d.crowded_session==1,'sue_w'].mean():.4f} vs uncrowded {d.loc[d.crowded_session==0,'sue_w'].mean():.4f}; "
             f"share SUE<0 crowded {(d.loc[d.crowded_session==1,'sue_w']<0).mean():.4f} vs {(d.loc[d.crowded_session==0,'sue_w']<0).mean():.4f}", ""]
    b, se, t, n = inf.h2_regression(d, surprise_col="sue_w", discretion_col=None, controls=controls)
    lines.append(f"H2 primary (SUE on crowded, firm+yq FE, 2-way cluster): b={b['crowded_session']:.4f} se={se['crowded_session']:.4f} t={t['crowded_session']:.2f} n={n}")
    dd = d.dropna(subset=["discretion"])
    b, se, t, n = inf.h2_regression(dd, surprise_col="sue_w", discretion_col="discretion", controls=controls)
    lines.append(f"H2 interaction (crowded x discretion): b_crowded={b['crowded_session']:.4f} (t={t['crowded_session']:.2f}); b_cxd={b['cxd']:.5f} (t={t['cxd']:.2f}); n={n}")
    d["neg"] = (d["sue_w"] < 0).astype(float)
    b, se, t, n = inf.h2_regression(d, surprise_col="neg", discretion_col=None, controls=controls)
    lines.append(f"H2 secondary (P[SUE<0] on crowded, LPM): b={b['crowded_session']:.4f} se={se['crowded_session']:.4f} t={t['crowded_session']:.2f} n={n}")
    for r in ["crowded_cpi", "crowded_empsit", "crowded_fomc"]:
        dr = d.copy(); dr["crowded_session"] = dr[r].astype(float)
        b, se, t, n = inf.h2_regression(dr, surprise_col="sue_w", discretion_col=None, controls=controls)
        lines.append(f"H2 by release {r} (calendar-day dummy): b={b['crowded_session']:.4f} t={t['crowded_session']:.2f}")
    OUT.mkdir(exist_ok=True)
    (OUT / f"results_h2_{args.sample}.md").write_text("\n".join(lines))
    print("\n".join(lines))


STAGES = {"events": stage_events, "h2": stage_h2, "gate": stage_gate, "surprise": stage_surprise,
          "returns": stage_returns, "tests": stage_tests}

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=STAGES)
    ap.add_argument("--sample", default="dev", choices=["dev", "holdout"])
    ap.add_argument("--placebos", type=int, default=1000)
    a = ap.parse_args()
    STAGES[a.stage](a)
