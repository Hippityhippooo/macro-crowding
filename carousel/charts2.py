"""Second set of exhibits (exploratory slides). Same palette and type rules as charts.py."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import charts  # noqa: E402  (sets rcParams, fonts, colours)
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402

ROOT, FIGS = charts.ROOT, charts.FIGS
ACCENT, CONTRAST, GREY, INK, LINE, CREAM, MONO = charts.ACCENT, charts.CONTRAST, charts.GREY, charts.INK, charts.LINE, charts.CREAM, charts.MONO


def fig_minutes():
    h = pd.read_csv(ROOT / "output/exhibit_minute_hist.csv", index_col=0)["n"]
    full = pd.Series(0.0, index=range(0, 1440)); full.loc[h.index] = h.values; full = full / full.sum() * 100
    fig, ax = plt.subplots(figsize=(10, 7.5), dpi=160)
    x = np.arange(1440) / 60
    ax.fill_between(x, 0, full.values, color=GREY, step="mid", lw=0)
    for m, lab, col in ((8.5, "CPI, jobs 08:30", CONTRAST), (14.0, "FOMC 14:00", CONTRAST), (9.5, "open", INK), (16.0, "close", INK)):
        ax.axvline(m, color=col, lw=2.5 if col == CONTRAST else 1.5, ls="-" if col == CONTRAST else ":")
        ax.text(m + 0.1, ax.get_ylim()[1] * 0.0 + 2.1, lab, rotation=90, va="bottom", fontsize=24, color=col, fontdict=MONO)
    ax.set_xlim(5, 21); ax.set_ylim(0, 2.5)
    ax.set_xticks([6, 9, 12, 15, 18]); ax.set_xticklabels([f"{t:02d}:00" for t in [6, 9, 12, 15, 18]])
    ax.set_xlabel("Time the 8-K was accepted, Eastern"); ax.set_ylabel("Share of releases per minute (%)")
    ax.yaxis.grid(True, color=LINE, lw=1); ax.set_axisbelow(True)
    fig.tight_layout(); fig.savefig(FIGS / "minutes.png"); plt.close(fig)


def fig_heatmap():
    H = pd.read_csv(ROOT / "output/exhibit_heatmap.csv", index_col=0); H.columns = H.columns.astype(int)
    F = pd.read_csv(ROOT / "output/exhibit_heatmap_fomc.csv")
    cmap = LinearSegmentedColormap.from_list("seq", ["#f6f1e7", "#c9d8ee", "#7faae0", ACCENT, "#143c6e"])
    fig, ax = plt.subplots(figsize=(10, 7.5), dpi=160)
    im = ax.imshow(H.values, aspect="auto", cmap=cmap, vmin=0, vmax=np.nanpercentile(H.values, 98), interpolation="nearest")
    # FOMC days: one dot per (year, day-of-quarter) wherever any quarter had a statement that day
    ax.scatter(F["doq"] - 1, [H.index.get_loc(y) for y in F["year"]], s=14, color=CONTRAST, marker="o", linewidths=0, alpha=0.9)
    ax.set_yticks(range(0, len(H.index), 4)); ax.set_yticklabels(H.index[::4])
    ax.set_xticks([0, 19, 39, 59]); ax.set_xticklabels(["day 1", "day 20", "day 40", "day 60"])
    ax.set_xlabel("Trading day within the calendar quarter"); ax.set_ylabel("Year")
    ax.tick_params(length=0)
    for s in ax.spines.values(): s.set_visible(False)
    cb = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02); cb.set_label("8-Ks per day", fontsize=24); cb.ax.tick_params(labelsize=22); cb.outline.set_visible(False)
    ax.text(0.0, 1.02, "orange dots: FOMC statement days", transform=ax.transAxes, ha="left", fontsize=24, color=CONTRAST, fontdict=MONO)
    fig.tight_layout(); fig.savefig(FIGS / "heatmap.png"); plt.close(fig)


def fig_positive_control(rows):
    """rows: (label, drift_main_b, drift_main_se, interaction_b, interaction_se) in CAR units."""
    fig, axes = plt.subplots(1, 2, figsize=(10, 7.5), dpi=160, sharey=True)
    y = np.arange(len(rows))[::-1]
    for ax, (title, bi, si, col) in zip(axes, (("Drift (pp)", 1, 2, ACCENT), ("Crowded extra (pp)", 3, 4, GREY))):
        for yi, r in zip(y, rows):
            b, se = r[bi] * 100, r[si] * 100
            ax.plot([b - 1.96 * se, b + 1.96 * se], [yi, yi], color=col, lw=5, solid_capstyle="round")
            ax.scatter([b], [yi], color=col, s=160, zorder=3)
            ax.text(b, yi + 0.28, f"{b:+.2f}", ha="center", fontdict=MONO, fontsize=26, color=INK)
        ax.set_ylim(-0.6, len(rows) - 0.4 + 0.5); ax.axvline(0, color=INK, lw=1.5); ax.set_title(title, fontsize=26, loc="left"); ax.set_xlabel("95% CI")
        ax.spines["left"].set_visible(False); ax.tick_params(axis="y", length=0)
    axes[0].set_yticks(y); axes[0].set_yticklabels([r[0] for r in rows]); axes[0].set_xlim(-1.2, 4.2); axes[1].set_xlim(-2.5, 2.5)
    fig.tight_layout(); fig.savefig(FIGS / "positive_control.png"); plt.close(fig)


def fig_pead_by_year():
    d = pd.read_csv(ROOT / "output/exhibit_pead_by_year.csv")
    fig, ax = plt.subplots(figsize=(10, 7.5), dpi=160)
    ax.fill_between(d.year, d.drift_pp - 1.96 * d.se_pp, d.drift_pp + 1.96 * d.se_pp, color="#c9d8ee", lw=0)
    ax.plot(d.year, d.drift_pp, color=ACCENT, lw=3, marker="o", ms=7)
    ax.axhline(0, color=INK, lw=1.5)
    ax.set_xticks([2005, 2010, 2015, 2020, 2025]); ax.set_ylabel("60-day drift (pp)"); ax.set_xlabel("Year of announcement")
    ax.yaxis.grid(True, color=LINE, lw=1); ax.set_axisbelow(True)
    fig.tight_layout(); fig.savefig(FIGS / "pead_by_year.png"); plt.close(fig)


def fig_lag(rows):
    """rows: (label, share_neg, share_pos) in %."""
    fig, ax = plt.subplots(figsize=(10, 7.5), dpi=160)
    x = np.arange(len(rows)); w = 0.34
    b1 = ax.bar(x - w / 2 - 0.01, [r[1] for r in rows], w, color=CONTRAST, label="EPS below last year")
    b2 = ax.bar(x + w / 2 + 0.01, [r[2] for r in rows], w, color=GREY, label="EPS at or above")
    for bars in (b1, b2):
        for b in bars:
            ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.3, f"{b.get_height():.1f}%", ha="center", fontdict=MONO, fontsize=26)
    ax.set_xticks(x); ax.set_xticklabels([r[0] for r in rows]); ax.set_ylim(0, 22)
    ax.set_ylabel("Share of announcements (%)"); ax.legend(frameon=False, loc="upper right", fontsize=24); ax.tick_params(axis="x", length=0)
    fig.tight_layout(); fig.savefig(FIGS / "lag.png"); plt.close(fig)


def fig_equity():
    d = pd.read_csv(ROOT / "output/exhibit_portfolio_daily.csv", index_col=0, parse_dates=True).dropna(how="all").fillna(0)
    d = d.loc["2005-04-01":"2025-12-31"]
    cum = (1 + d).cumprod() * 100
    fig, ax = plt.subplots(figsize=(10, 7.5), dpi=160)
    ax.plot(cum.index, cum["uncrowded"], color=GREY, lw=3, label="Events on quiet sessions")
    ax.plot(cum.index, cum["crowded"], color=ACCENT, lw=3, label="Events on crowded sessions")
    for c, col in (("uncrowded", GREY), ("crowded", ACCENT)):
        ax.text(cum.index[-1] + pd.Timedelta(days=60), cum[c].iloc[-1], f"{cum[c].iloc[-1]:.0f}", fontdict=MONO, fontsize=26, color=col, va="center")
    ax.axhline(100, color=INK, lw=1.2)
    ax.set_ylabel("Long-short book, 100 = start"); ax.legend(frameon=False, loc="upper left", fontsize=24)
    ax.yaxis.grid(True, color=LINE, lw=1); ax.set_axisbelow(True); ax.set_xlim(cum.index[0], cum.index[-1] + pd.Timedelta(days=900))
    fig.tight_layout(); fig.savefig(FIGS / "equity.png"); plt.close(fig)


if __name__ == "__main__":
    fig_minutes(); fig_heatmap(); fig_pead_by_year(); fig_equity()
    fig_positive_control([("Liquid third", 0.0063, 0.0024, -0.0032, 0.0062), ("Middle third", 0.0105, 0.0028, 0.0011, 0.0071), ("Illiquid third", 0.0227, 0.0036, 0.0007, 0.0088)])
    fig_lag([("8-K filed after\nthe release day", 16.9, 15.7), ("Friday after close", 1.72, 1.39)])
    print("ok")
