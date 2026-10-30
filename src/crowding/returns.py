"""Prices, factors, abnormal returns and event-window statistics.

Price source: Sharadar SEP (daily OHLCV, active + delisted). Expected columns:
  ticker, date, open, high, low, close, volume, closeadj, closeunadj, lastupdated
Factor source: Kenneth French daily "F-F_Research_Data_5_Factors_2x3_daily" and
  "F-F_Momentum_Factor_daily" CSVs (values in percent).

CIK-to-ticker mapping: Sharadar TICKERS has a `secfilings` column holding the EDGAR browse
URL with the CIK [to verify on your download]; `parse_cik_from_url` handles that. The SEC's
company_tickers.json is current-only and must not be used for delisted names.
"""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd

FACTOR_COLS = ["mktrf", "smb", "hml", "rmw", "cma", "umd"]


def parse_cik_from_url(url: str) -> int | None:
    if not isinstance(url, str):
        return None
    m = re.search(r"CIK=0*(\d+)", url, flags=re.I)
    return int(m.group(1)) if m else None


def load_sep(path: str | Path, tickers: set[str] | None = None) -> pd.DataFrame:
    usecols = ["ticker", "date", "open", "high", "low", "close", "volume", "closeadj"]
    it = pd.read_csv(path, usecols=usecols, parse_dates=["date"], chunksize=1_000_000)
    parts = []
    for ch in it:
        if tickers is not None:
            ch = ch[ch["ticker"].isin(tickers)]
        parts.append(ch)
    px = pd.concat(parts, ignore_index=True).sort_values(["ticker", "date"])
    px["ret"] = px.groupby("ticker")["closeadj"].pct_change()
    return px


def load_french_daily(ff5_csv: str | Path, mom_csv: str | Path) -> pd.DataFrame:
    """Reads the two French daily files after the header junk has been stripped to a plain
    CSV with a date column in YYYYMMDD. Returns decimal returns indexed by date."""
    ff = pd.read_csv(ff5_csv)
    ff.columns = [c.strip().lower().replace("-", "") for c in ff.columns]
    ff = ff.rename(columns={ff.columns[0]: "date", "mktrf": "mktrf"})
    mom = pd.read_csv(mom_csv)
    mom.columns = [c.strip().lower() for c in mom.columns]
    mom = mom.rename(columns={mom.columns[0]: "date", "mom": "umd"})
    f = ff.merge(mom, on="date", how="inner")
    f["date"] = pd.to_datetime(f["date"].astype(str), format="%Y%m%d")
    for c in FACTOR_COLS + ["rf"]:
        f[c] = f[c].astype(float) / 100.0
    return f.set_index("date").sort_index()


def trading_days(factors: pd.DataFrame) -> pd.DatetimeIndex:
    return pd.DatetimeIndex(factors.index)


def _ols_beta(y: np.ndarray, X: np.ndarray) -> np.ndarray:
    Xc = np.column_stack([np.ones(len(X)), X])
    beta, *_ = np.linalg.lstsq(Xc, y, rcond=None)
    return beta


def event_window_stats(
    px: pd.DataFrame, factors: pd.DataFrame, events: pd.DataFrame,
    est_window=(-250, -21), windows=((0, 1), (2, 20), (2, 60)), vol_window=(-60, -11),
    min_est_obs: int = 120,
) -> pd.DataFrame:
    """Per event: FF5+UMD abnormal returns, CARs over each window, abnormal volume on the
    reaction day, Corwin-Schultz spread estimate over the estimation window.
    Day 0 is the reaction day. Loadings use days est_window only (no look-ahead)."""
    td = trading_days(factors)
    pos_of = {d: i for i, d in enumerate(td)}
    F = factors[FACTOR_COLS].values
    rf = factors["rf"].values
    out = []
    px_by_t = {t: g.set_index("date") for t, g in px.groupby("ticker")}
    for _, ev in events.iterrows():
        t = ev["ticker"]
        d0 = pd.Timestamp(ev["reaction_day"])
        if t not in px_by_t or d0 not in pos_of:
            continue
        g = px_by_t[t]
        i0 = pos_of[d0]
        lo, hi = i0 + est_window[0], i0 + est_window[1]
        if lo < 0 or hi >= len(td):
            continue
        est_days = td[lo:hi + 1]
        r_est = g["ret"].reindex(est_days)
        if r_est.notna().sum() < min_est_obs:
            continue
        mask = r_est.notna().values
        y = r_est.values[mask] - rf[lo:hi + 1][mask]
        beta = _ols_beta(y, F[lo:hi + 1][mask])
        rec = {"cik": ev["cik"], "ticker": t, "reaction_day": d0}
        for a, b in windows:
            ja, jb = i0 + a, i0 + b
            if jb >= len(td):
                rec[f"car_{a}_{b}"] = np.nan
                continue
            days = td[ja:jb + 1]
            r = g["ret"].reindex(days).values
            if np.isnan(r).any():
                rec[f"car_{a}_{b}"] = np.nan
                continue
            expected = rf[ja:jb + 1] + beta[0] + F[ja:jb + 1] @ beta[1:]
            rec[f"car_{a}_{b}"] = float(np.sum(r - expected))
        # abnormal volume
        vdays = td[i0 + vol_window[0]: i0 + vol_window[1] + 1]
        base = g["volume"].reindex(vdays).mean()
        v0 = g["volume"].get(d0, np.nan)
        rec["abn_volume"] = float(np.log(v0 / base)) if base and base > 0 and v0 and v0 > 0 else np.nan
        # Corwin-Schultz spread
        hl = g[["high", "low"]].reindex(est_days).dropna()
        rec["cs_spread"] = corwin_schultz(hl["high"].values, hl["low"].values)
        rec["price_m2"] = float(g["close"].reindex(td[i0 - 2: i0 - 1]).iloc[0]) if i0 >= 2 else np.nan
        out.append(rec)
    return pd.DataFrame(out)


def corwin_schultz(high: np.ndarray, low: np.ndarray) -> float:
    """Corwin and Schultz (2012) high-low spread estimator, averaged over the window.
    Negative two-day estimates are set to zero, as in the paper."""
    if len(high) < 3:
        return np.nan
    h, l = np.log(high), np.log(low)
    beta = (h[:-1] - l[:-1]) ** 2 + (h[1:] - l[1:]) ** 2
    h2 = np.maximum(h[:-1], h[1:])
    l2 = np.minimum(l[:-1], l[1:])
    gamma = (h2 - l2) ** 2
    k = 3 - 2 * np.sqrt(2)
    alpha = (np.sqrt(2 * beta) - np.sqrt(beta)) / k - np.sqrt(gamma / k)
    s = 2 * (np.exp(alpha) - 1) / (1 + np.exp(alpha))
    s = np.where(s < 0, 0.0, s)
    return float(np.nanmean(s))


def market_cap_proxy(px: pd.DataFrame, shares: pd.DataFrame | None = None) -> pd.Series:
    """Placeholder: Sharadar DAILY table (marketcap) is the right source when available.
    Returns NaN series so the pipeline runs without it; the regression drops the control."""
    return pd.Series(np.nan, index=px.index)
