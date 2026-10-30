"""Download daily prices from Yahoo Finance for the event firms (free fallback for Sharadar).

Run on your Mac (Terminal):
    pip3 install yfinance pandas pyarrow
    python3 fetch_prices_yfinance.py

Input : ticker_request.csv (same folder as this script), columns cik,ticker,isdelisted,...
Output: prices_yf/ (one Parquet per batch) and prices_yf_all.parquet in the Earnings folder,
        plus prices_yf_log.csv listing which tickers returned data.

Yahoo covers listed names and only a handful of delisted ones; the log records the gap so the
survivorship caveat is measured, not guessed. Re-running skips finished batches.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import pandas as pd
import yfinance as yf

HERE = Path(__file__).resolve().parent
OUT_DIR = HERE / "prices_yf"
OUT_DIR.mkdir(exist_ok=True)
BATCH = 150


def yahoo_symbol(t: str) -> str:
    return t.replace(".", "-")


def main():
    req = pd.read_csv(HERE / "ticker_request.csv")
    tickers = sorted(set(req["ticker"].dropna()))
    print(f"{len(tickers)} tickers in {len(tickers) // BATCH + 1} batches")
    log = []
    for i in range(0, len(tickers), BATCH):
        batch = tickers[i:i + BATCH]
        out = OUT_DIR / f"batch_{i // BATCH:04d}.parquet"
        if out.exists():
            continue
        sym = [yahoo_symbol(t) for t in batch]
        for attempt in range(3):
            try:
                df = yf.download(sym, period="max", interval="1d", auto_adjust=False, actions=False,
                                 group_by="ticker", threads=True, progress=False)
                break
            except Exception as e:  # noqa: BLE001
                print("retry", i, e)
                time.sleep(10 * (attempt + 1))
        else:
            print("batch failed", i)
            continue
        frames = []
        for t, s in zip(batch, sym):
            try:
                g = df[s] if len(sym) > 1 else df
            except KeyError:
                log.append({"ticker": t, "rows": 0})
                continue
            g = g.dropna(subset=["Close"])
            log.append({"ticker": t, "rows": len(g)})
            if len(g):
                g = g.reset_index().rename(columns={"Date": "date", "Open": "open", "High": "high", "Low": "low",
                                                    "Close": "close", "Adj Close": "closeadj", "Volume": "volume"})
                g["ticker"] = t
                frames.append(g[["ticker", "date", "open", "high", "low", "close", "closeadj", "volume"]])
        if frames:
            pd.concat(frames, ignore_index=True).to_parquet(out, index=False)
        print(f"batch {i // BATCH} done, {sum(1 for r in log[-len(batch):] if r['rows'] > 0)}/{len(batch)} with data")
        time.sleep(2)
    pd.DataFrame(log).to_csv(HERE / "prices_yf_log.csv", index=False)
    parts = sorted(OUT_DIR.glob("batch_*.parquet"))
    if parts:
        allp = pd.concat([pd.read_parquet(p) for p in parts], ignore_index=True)
        allp.to_parquet(HERE / "prices_yf_all.parquet", index=False)
        print("rows", len(allp), "tickers", allp["ticker"].nunique(), "->", HERE / "prices_yf_all.parquet")


if __name__ == "__main__":
    sys.exit(main())
