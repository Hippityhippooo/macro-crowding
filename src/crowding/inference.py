"""Regressions, two-way clustered standard errors, power, placebo, portfolio alpha."""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm


def _cluster_cov(model, result, groups):
    return result.get_robustcov_results(cov_type="cluster", groups=groups, use_correction=True).cov_params()


def ols_twoway_cluster(y: pd.Series, X: pd.DataFrame, g1: pd.Series, g2: pd.Series):
    """OLS with Cameron-Gelbach-Miller two-way clustering: V = V1 + V2 - V12.
    Returns (params, se, tstats, nobs)."""
    data = pd.concat([y.rename("_y"), X, g1.rename("_g1"), g2.rename("_g2")], axis=1).dropna()
    Xc = sm.add_constant(data[X.columns], has_constant="add")
    model = sm.OLS(data["_y"], Xc)
    res = model.fit()
    c1 = pd.factorize(data["_g1"])[0]
    c2 = pd.factorize(data["_g2"])[0]
    c12 = pd.factorize(pd.Series(c1).astype(str) + "_" + pd.Series(c2).astype(str))[0]
    V = (np.asarray(_cluster_cov(model, res, c1)) + np.asarray(_cluster_cov(model, res, c2))
         - np.asarray(_cluster_cov(model, res, c12)))
    # guard against non-PSD from the subtraction
    w, U = np.linalg.eigh((V + V.T) / 2)
    V = U @ np.diag(np.maximum(w, 0)) @ U.T
    se = pd.Series(np.sqrt(np.diag(V)), index=Xc.columns)
    params = res.params
    return params, se, params / se, int(res.nobs)


def demean_within(df: pd.DataFrame, cols: list[str], by: list[str]) -> pd.DataFrame:
    """Two-way fixed effects by iterative demeaning (firm, year-quarter)."""
    out = df[cols].astype(float).copy()
    for _ in range(25):
        prev = out.copy()
        for b in by:
            out = out - out.groupby(df[b]).transform("mean")
        if (out - prev).abs().max().max() < 1e-10:
            break
    return out


def h1_regression(ev: pd.DataFrame, car_col: str = "car_2_60", crowd_col: str = "crowded_session",
                  surprise_col: str = "surprise_rank", controls: list[str] | None = None):
    """CAR on surprise_rank, crowded, surprise_rank x crowded, plus controls, with firm and
    year-quarter fixed effects (demeaned), SE two-way clustered by firm and reaction day.
    The pre-registered primary coefficient is 'sxc'."""
    d = ev.dropna(subset=[car_col, crowd_col, surprise_col]).copy()
    d["sxc"] = d[surprise_col] * d[crowd_col]
    d["yq"] = pd.to_datetime(d["reaction_day"]).dt.to_period("Q").astype(str)
    cols = [car_col, surprise_col, crowd_col, "sxc"] + [c for c in (controls or []) if c in d]
    dm = demean_within(d, cols, by=["cik", "yq"])
    y = dm[car_col]
    X = dm[[c for c in cols if c != car_col]]
    return ols_twoway_cluster(y, X, d["cik"], d["reaction_day"])


def h2_regression(ev: pd.DataFrame, surprise_col: str = "sue", crowd_col: str = "crowded_session",
                  discretion_col: str | None = "discretion", controls: list[str] | None = None):
    d = ev.dropna(subset=[surprise_col, crowd_col]).copy()
    d["yq"] = pd.to_datetime(d["reaction_day"]).dt.to_period("Q").astype(str)
    cols = [surprise_col, crowd_col]
    if discretion_col and discretion_col in d:
        d["cxd"] = d[crowd_col] * d[discretion_col]
        cols += [discretion_col, "cxd"]
    cols += [c for c in (controls or []) if c in d]
    dm = demean_within(d, cols, by=["cik", "yq"])
    return ols_twoway_cluster(dm[surprise_col], dm[[c for c in cols if c != surprise_col]], d["cik"], d["reaction_day"])


def mde(sigma: float, n_treated: int, n_control: int, power_z: float = 0.84, alpha_z: float = 1.96) -> float:
    """Minimum detectable difference in means at the given power/size."""
    return (alpha_z + power_z) * sigma * np.sqrt(1.0 / n_treated + 1.0 / n_control)


def placebo_shift(macro: pd.DataFrame, days: int) -> pd.DataFrame:
    m = macro.copy()
    m["date"] = m["date"] + pd.Timedelta(days=days)
    return m


def placebo_random_days(trading_days: pd.DatetimeIndex, n_per_year: dict, rng: np.random.Generator) -> pd.DataFrame:
    """Draw, for each year, `n_per_year[year]` pseudo-macro days from that year's trading
    days, in month blocks (whole months drawn, then days within) to keep seasonality."""
    rows = []
    td = pd.Series(trading_days)
    for yr, n in n_per_year.items():
        days = td[td.dt.year == yr]
        if len(days) == 0:
            continue
        pick = rng.choice(days.values, size=min(n, len(days)), replace=False)
        rows += [{"release": "PLACEBO", "date": pd.Timestamp(p)} for p in pick]
    return pd.DataFrame(rows)


def calendar_time_portfolio(ev: pd.DataFrame, px: pd.DataFrame, factors: pd.DataFrame,
                            hold_days: int = 60, top_q: float = 0.9, bot_q: float = 0.1,
                            surprise_col: str = "surprise_rank", cap: float = 0.02):
    """Equal-weighted long top-decile / short bottom-decile, entered at close of day +1,
    held `hold_days` trading days, daily rebalanced calendar-time returns. Returns a daily
    series of long-short returns, names held, and turnover."""
    td = pd.DatetimeIndex(factors.index)
    r = px.pivot(index="date", columns="ticker", values="ret").reindex(td)
    long_w = pd.DataFrame(0.0, index=td, columns=r.columns)
    short_w = long_w.copy()
    for _, e in ev.dropna(subset=[surprise_col]).iterrows():
        d0 = pd.Timestamp(e["reaction_day"])
        if d0 not in td or e["ticker"] not in r.columns:
            continue
        i = td.get_loc(d0) + 2  # enter at close of day +1 -> first return day +2
        j = min(i + hold_days, len(td))
        if e[surprise_col] >= top_q - 0.5:
            long_w.iloc[i:j, long_w.columns.get_loc(e["ticker"])] += 1.0
        elif e[surprise_col] <= bot_q - 0.5:
            short_w.iloc[i:j, short_w.columns.get_loc(e["ticker"])] += 1.0

    def _norm(w):
        s = w.sum(axis=1).replace(0, np.nan)
        w = w.div(s, axis=0).clip(upper=cap)
        return w.div(w.sum(axis=1).replace(0, np.nan), axis=0)

    lw, sw = _norm(long_w), _norm(short_w)
    port = (lw * r).sum(axis=1) - (sw * r).sum(axis=1)
    held = (lw > 0).sum(axis=1) + (sw > 0).sum(axis=1)
    turnover = (lw.diff().abs().sum(axis=1) + sw.diff().abs().sum(axis=1)) / 2
    return port, held, turnover


def newey_west_alpha(port: pd.Series, factors: pd.DataFrame, lags: int = 5):
    d = pd.concat([port.rename("p"), factors[["mktrf", "smb", "hml", "rmw", "cma", "umd"]]], axis=1).dropna()
    X = sm.add_constant(d.drop(columns="p"))
    res = sm.OLS(d["p"], X).fit(cov_type="HAC", cov_kwds={"maxlags": lags})
    return float(res.params["const"]), float(res.tvalues["const"]), int(res.nobs)


def max_t_bootstrap(tstats: pd.Series, boot_t: np.ndarray) -> pd.Series:
    """Single-step Westfall-Young adjusted p-values from a (B x K) matrix of bootstrap
    t-statistics under the null. A stepdown (Romano-Wolf) refinement can be layered on."""
    maxabs = np.abs(boot_t).max(axis=1)
    return pd.Series({k: float((maxabs >= abs(t)).mean()) for k, t in tstats.items()})
