import numpy as np
import pandas as pd
import pytest

from crowding import calendar as cal
from crowding import events as evm
from crowding import inference as inf
from crowding import returns as rtn
from crowding import surprise as sur


# ---------- events ----------

def test_acceptance_utc_to_eastern():
    d = evm.parse_acceptance_et("2024-10-31T20:30:25.000Z")
    assert d.strftime("%Y-%m-%d %H:%M:%S") == "2024-10-31 16:30:25"  # matches filing index page
    d = evm.parse_acceptance_et("2024-10-11T10:46:16.000Z")
    assert d.strftime("%H:%M:%S") == "06:46:16"
    d = evm.parse_acceptance_et("2023-01-10T22:00:00.000Z")  # EST, not EDT
    assert d.strftime("%H:%M:%S") == "17:00:00"
    assert evm.parse_acceptance_et("2024-10-31 16:30:25").strftime("%H:%M") == "16:30"


def test_event_table_classes_and_lag(submissions_zip):
    f = evm.read_submissions_zip(submissions_zip)
    assert set(f["form"]) == {"8-K"}  # 8-K/A and 10-Q excluded
    assert all("2.02" in i for i in f["items"])  # 7.01-only 8-K excluded
    ev = evm.build_event_table(f)
    by = ev.set_index("accessionNumber")
    assert by.loc["0000320193-24-000120", "session"] == "post_close"
    assert by.loc["0000019617-24-000555", "session"] == "pre_market"
    assert by.loc["0000000777-24-000001", "session"] == "in_session"
    assert by.loc["0001104659-23-040966", "session"] == "unknown"
    assert by.loc["0001104659-23-040966", "lag_bdays"] == 2
    assert by.loc["0001047469-05-000001", "lag_bdays"] == 1  # archive file parsed
    assert "0000019617-24-000556" not in by.index  # same firm, same day: earliest kept
    assert len(ev) == 5


def test_reaction_day_rules(submissions_zip):
    ev = evm.build_event_table(evm.read_submissions_zip(submissions_zip))
    td = pd.bdate_range("2004-01-01", "2025-12-31")
    ev = evm.assign_reaction_day(ev, td)
    by = ev.set_index("accessionNumber")
    assert by.loc["0000320193-24-000120", "reaction_day"] == pd.Timestamp("2024-11-01")  # post_close -> next day
    assert by.loc["0000019617-24-000555", "reaction_day"] == pd.Timestamp("2024-10-11")
    assert by.loc["0001104659-23-040966", "reaction_day"] == pd.Timestamp("2023-03-30")
    assert bool(by.loc["0001104659-23-040966", "reaction_day_is_fallback"])


# ---------- calendar ----------

def test_crowding_session_rules(reference_dir):
    macro = cal.load_macro_days(reference_dir)
    assert set(macro["release"]) == {"CPI", "EMPSIT", "FOMC"}
    mk = lambda acc, sess, rd: {"cik": 1, "session": sess, "reaction_day": pd.Timestamp(rd),  # noqa: E731
                                "acceptance_et": evm.parse_acceptance_et(acc)}
    ev = pd.DataFrame([
        mk("2024-10-10T10:30:00.000Z", "pre_market", "2024-10-10"),   # CPI day, pre-market -> 1
        mk("2024-10-10T14:30:00.000Z", "in_session", "2024-10-10"),   # 10:30 after 08:30 CPI -> 0
        mk("2024-09-18T14:30:00.000Z", "in_session", "2024-09-18"),   # 10:30 before 14:00 FOMC -> 1
        mk("2024-09-17T20:30:00.000Z", "post_close", "2024-09-18"),   # next day is FOMC -> 1
        mk("2024-09-18T20:30:00.000Z", "post_close", "2024-09-19"),   # next day clean -> 0
        mk("2024-10-10T21:00:00.000Z", "unknown", "2024-10-10"),      # unknown -> NaN
        mk("2024-10-15T10:30:00.000Z", "pre_market", "2024-10-15"),   # clean day -> 0
    ])
    out = cal.crowding_flags(ev, macro)
    assert out["crowded_session"].tolist()[:5] == [1.0, 0.0, 1.0, 1.0, 0.0]
    assert np.isnan(out["crowded_session"].iloc[5])
    assert out["crowded_session"].iloc[6] == 0.0
    assert out["crowded_calendar"].tolist() == [1, 1, 1, 1, 0, 1, 0]
    assert out["crowded_cpi"].iloc[0] == 1 and out["crowded_fomc"].iloc[0] == 0


def test_same_day_and_season_controls():
    ev = pd.DataFrame({"cik": range(6), "reaction_day": pd.to_datetime(
        ["2024-10-10"] * 3 + ["2024-10-11"] * 2 + ["2024-10-14"])})
    assert cal.same_day_event_count(ev).tolist() == [2, 2, 2, 1, 1, 0]
    assert cal.season_intensity(ev, window_days=2).tolist() == [3, 3, 3, 5, 5, 3]


# ---------- surprise ----------

def test_first_filed_and_q4_derivation(companyfacts_zip):
    facts = sur.read_companyfacts_zip(companyfacts_zip)
    q = sur.first_filed_quarters(facts)
    q1 = q[(q["end"] == "2022-03-31")].iloc[0]
    assert q1["val"] == 1.0 and q1["accn"] == "a0"  # first filed, not the restated b0
    q4_22 = q[(q["end"] == "2022-12-31")].iloc[0]
    assert q4_22["derived"] == 1 and abs(q4_22["val"] - 1.2) < 1e-9
    q4_23 = q[(q["end"] == "2023-12-31")].iloc[0]
    assert abs(q4_23["val"] - 1.6) < 1e-9
    assert len(q) == 8


def test_sue_uses_only_prior_quarters(companyfacts_zip):
    q = sur.sue(sur.first_filed_quarters(sur.read_companyfacts_zip(companyfacts_zip)), lookback=8, min_obs=1)
    g = q.sort_values("end").reset_index(drop=True)
    # dseas: Q1'23 = 1.3-1.0 = 0.3, Q2'23 = 0.3, Q3'23 = 0.3, Q4'23 = 1.6-1.2 = 0.4
    assert abs(g.loc[4, "dseas"] - 0.3) < 1e-9
    assert np.isnan(g.loc[4, "sue"])  # no prior differences yet
    # Q4'23: sd of prior diffs (0.3,0.3,0.3) = 0 -> inf/NaN guard not applied; just check dseas
    assert abs(g.loc[7, "dseas"] - 0.4) < 1e-9


def test_attach_quarter_links_latest_prior_quarter(companyfacts_zip):
    q = sur.sue(sur.first_filed_quarters(sur.read_companyfacts_zip(companyfacts_zip)))
    ev = pd.DataFrame({"cik": [320193, 320193], "event_date": pd.to_datetime(["2023-05-02", "2023-02-01"])})
    out = sur.attach_quarter(ev, q)
    out = out.set_index("event_date")
    assert out.loc["2023-05-02", "q_end"] == pd.Timestamp("2023-03-31")
    assert out.loc["2023-02-01", "q_end"] == pd.Timestamp("2022-12-31")


def test_decile_rank_range():
    x = pd.Series(np.arange(40, dtype=float))
    by = pd.Series(["a"] * 20 + ["b"] * 20)
    r = sur.decile_rank(x, by)
    assert r.min() == -0.5 and r.max() == 0.5


# ---------- returns ----------

def test_car_recovers_known_bump(synthetic_market):
    F, px, bump_day = synthetic_market
    ev = pd.DataFrame({"cik": [1, 2], "ticker": ["AAA", "BBB"], "reaction_day": [bump_day, bump_day]})
    st = rtn.event_window_stats(px, F, ev).set_index("ticker")
    assert abs(st.loc["AAA", "car_0_1"] - 0.03) < 1e-3
    assert abs(st.loc["BBB", "car_0_1"]) < 1e-3
    assert abs(st.loc["AAA", "car_2_60"]) < 1e-3  # no drift planted
    assert st.loc["AAA", "abn_volume"] > 0.5  # 3x volume -> log(3) ~ 1.1
    assert st.loc["AAA", "cs_spread"] >= 0


def test_corwin_schultz_constant_range():
    h = np.full(30, 101.0)
    l = np.full(30, 99.0)
    assert rtn.corwin_schultz(h, l) > 0


def test_parse_cik_from_url():
    assert rtn.parse_cik_from_url("https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000320193") == 320193
    assert rtn.parse_cik_from_url(None) is None


# ---------- inference ----------

def test_twoway_cluster_recovers_slope():
    rng = np.random.default_rng(1)
    n_firm, n_day = 60, 40
    firm = np.repeat(np.arange(n_firm), n_day)
    day = np.tile(np.arange(n_day), n_firm)
    x = rng.normal(size=len(firm))
    e = rng.normal(size=n_firm)[firm] + rng.normal(size=n_day)[day] + rng.normal(size=len(firm))
    y = 2.0 * x + e
    b, se, t, n = inf.ols_twoway_cluster(pd.Series(y), pd.DataFrame({"x": x}), pd.Series(firm), pd.Series(day))
    assert abs(b["x"] - 2.0) < 0.1 and se["x"] > 0 and n == len(y)


def test_mde_formula():
    assert abs(inf.mde(0.10, 1000, 9000) - 2.8 * 0.10 * np.sqrt(1 / 1000 + 1 / 9000)) < 1e-12


def test_h1_h2_regressions_run_on_synthetic_panel():
    rng = np.random.default_rng(2)
    n = 2000
    days = pd.bdate_range("2010-01-04", periods=250)
    panel = pd.DataFrame({
        "cik": rng.integers(0, 100, n),
        "reaction_day": rng.choice(days, n),
        "surprise_rank": rng.uniform(-0.5, 0.5, n),
        "crowded_session": rng.integers(0, 2, n).astype(float),
        "sue": rng.normal(size=n),
        "same_day_n": rng.integers(0, 30, n).astype(float),
    })
    panel["car_2_60"] = 0.02 * panel["surprise_rank"] + 0.03 * panel["surprise_rank"] * panel["crowded_session"] + rng.normal(0, 0.05, n)
    b, se, t, nobs = inf.h1_regression(panel, controls=["same_day_n"])
    assert "sxc" in b and nobs == n and abs(b["sxc"] - 0.03) < 0.03
    b2, se2, t2, n2 = inf.h2_regression(panel, discretion_col=None, controls=["same_day_n"])
    assert "crowded_session" in b2 and n2 == n


def test_calendar_time_portfolio_and_alpha(synthetic_market):
    F, px, bump_day = synthetic_market
    ev = pd.DataFrame({"cik": [1, 2], "ticker": ["AAA", "CCC"], "reaction_day": [bump_day, bump_day],
                       "surprise_rank": [0.5, -0.5]})
    port, held, turnover = inf.calendar_time_portfolio(ev, px, F, hold_days=20)
    assert held.max() == 2 and port.abs().sum() > 0
    a, t, n = inf.newey_west_alpha(port.dropna(), F)
    assert n > 0


def test_placebo_random_days_counts():
    td = pd.bdate_range("2010-01-01", "2011-12-31")
    pl = inf.placebo_random_days(td, {2010: 32, 2011: 32}, np.random.default_rng(0))
    assert pl.groupby(pl["date"].dt.year).size().tolist() == [32, 32]
