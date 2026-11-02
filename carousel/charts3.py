"""Page-scale charts for the v2 deck. Each chart renders at exactly 1080 x H px (dpi 100) so it fills
the slide below a header band; type is sized for a phone at 360px wide. Two themes: cream and navy.
Figures only from output/*.csv and RESULTS.md numbers passed in by build2.py."""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib import font_manager  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
FIGS = ROOT / "carousel" / "figs2"; FIGS.mkdir(exist_ok=True)
for f in (Path.home() / "fonts").glob("*.ttf"):
    font_manager.fontManager.addfont(str(f))

THEMES = {
    "cream": dict(bg="#f6f1e7", ink="#141311", muted="#6b665c", line="#d9d2c2", accent="#2a78d6", accent2="#143c6e", contrast="#eb6834", grey="#9a9384", band="#e9e2d2"),
    "navy":  dict(bg="#0f1f33", ink="#f6f1e7", muted="#aab4c3", line="#2a3a52", accent="#7faae0", accent2="#c9d8ee", contrast="#f08a5a", grey="#6f7d92", band="#162a44"),
}
MONO = "JetBrains Mono"; SANS = "Schibsted Grotesk"; SERIF = "Fraunces"


def _fig(theme, h=1000, w=1080):
    T = THEMES[theme]
    plt.rcParams.update({"font.family": SANS, "font.size": 34, "axes.edgecolor": T["line"], "axes.linewidth": 2,
                         "axes.spines.top": False, "axes.spines.right": False, "xtick.color": T["ink"], "ytick.color": T["ink"],
                         "axes.labelcolor": T["muted"], "text.color": T["ink"], "figure.facecolor": T["bg"], "axes.facecolor": T["bg"],
                         "savefig.facecolor": T["bg"], "xtick.labelsize": 32, "ytick.labelsize": 32, "axes.labelsize": 32,
                         "xtick.major.size": 0, "ytick.major.size": 0, "legend.fontsize": 32})
    fig = plt.figure(figsize=(w / 100, h / 100), dpi=100)
    return fig, T


def _save(fig, name):
    fig.savefig(FIGS / f"{name}.png", dpi=100)
    plt.close(fig)


def heatmap(theme="cream"):
    H = pd.read_csv(ROOT / "output/exhibit_heatmap.csv", index_col=0); H.columns = H.columns.astype(int)
    F = pd.read_csv(ROOT / "output/exhibit_heatmap_fomc.csv")
    fig, T = _fig(theme, h=1050)
    ax = fig.add_axes([0.14, 0.15, 0.80, 0.81])
    cmap = LinearSegmentedColormap.from_list("seq", [T["bg"], "#c9d8ee", "#7faae0", "#2a78d6", "#143c6e"])
    ax.imshow(H.values, aspect="auto", cmap=cmap, vmin=0, vmax=np.nanpercentile(H.values, 98), interpolation="nearest")
    ax.scatter(F["doq"] - 1, [H.index.get_loc(y) for y in F["year"]], s=26, color=T["contrast"], linewidths=0)
    ax.set_yticks(range(0, len(H.index) - 1, 5)); ax.set_yticklabels(H.index[:-1:5], fontfamily=MONO)
    ax.set_xticks([0, 20, 40, 60]); ax.set_xticklabels(["1", "21", "41", "61"], fontfamily=MONO); ax.tick_params(axis="x", pad=14)
    ax.set_xlabel("trading day of the quarter")
    for s in ax.spines.values(): s.set_visible(False)
    _save(fig, "heatmap")


def minutes(theme="cream"):
    h = pd.read_csv(ROOT / "output/exhibit_minute_hist.csv", index_col=0)["n"]
    full = pd.Series(0.0, index=range(1440)); full.loc[h.index] = h.values; full = full / full.sum() * 100
    fig, T = _fig(theme, h=900)
    ax = fig.add_axes([0.12, 0.18, 0.82, 0.76])
    x = np.arange(1440) / 60
    ax.fill_between(x, 0, full.values, color=T["accent"], step="mid", lw=0)
    for m, lab in ((8.5, "08:30 CPI, jobs"), (14.0, "14:00 FOMC")):
        ax.axvline(m, color=T["contrast"], lw=3)
        ax.text(m - 0.15, 2.35, lab, rotation=90, va="top", ha="right", fontsize=30, color=T["contrast"], fontfamily=MONO)
    for m, lab in ((9.5, "open"), (16.0, "close")):
        ax.axvline(m, color=T["ink"], lw=1.5, ls=(0, (2, 3)))
        ax.text(m + 0.12, 2.35, lab, rotation=90, va="top", fontsize=28, color=T["muted"], fontfamily=MONO)
    ax.annotate("20% of releases land in\nthe 15 min after the close", xy=(16.1, 1.1), xytext=(9.9, 0.72), fontsize=30, ha="left", va="center", color=T["ink"], arrowprops=dict(arrowstyle="-", color=T["muted"], lw=1.5, shrinkB=6))
    ax.set_xlim(5.5, 21); ax.set_ylim(0, 2.5)
    ax.set_xticks([6, 9, 12, 15, 18]); ax.set_xticklabels([f"{t:02d}:00" for t in [6, 9, 12, 15, 18]], fontfamily=MONO)
    ax.set_yticks([1, 2]); ax.set_yticklabels(["1%", "2%"], fontfamily=MONO)
    ax.set_xlabel("time the 8-K hit EDGAR, Eastern"); ax.yaxis.grid(True, color=T["line"], lw=1.5); ax.set_axisbelow(True)
    _save(fig, "minutes")


def drift_paths(theme="cream"):
    p = pd.read_csv(ROOT / "output/exhibit_car_paths.csv", index_col=0); d = p.loc[1:]; d = d - d.iloc[0]
    fig, T = _fig(theme, h=900)
    ax = fig.add_axes([0.14, 0.18, 0.70, 0.76])
    ax.axhline(0, color=T["line"], lw=2)
    ax.plot(d.index, d["uncrowded"], color=T["grey"], lw=5)
    ax.plot(d.index, d["crowded"], color=T["accent"], lw=5)
    ax.text(61.5, d["uncrowded"].iloc[-1] + 0.1, "quiet\n+1.48 pp", color=T["grey"], fontsize=32, va="center", fontfamily=MONO)
    ax.text(61.5, d["crowded"].iloc[-1] - 0.12, "crowded\n+1.11 pp", color=T["accent"], fontsize=32, va="center", fontfamily=MONO)
    ax.set_xlim(1, 75); ax.set_ylim(-0.4, 2.2)
    ax.set_xticks([1, 20, 40, 60]); ax.set_xticklabels(["day 1", "20", "40", "60"], fontfamily=MONO)
    ax.set_yticks([0, 1, 2]); ax.set_yticklabels(["0", "+1 pp", "+2 pp"], fontfamily=MONO)
    ax.set_xlabel("trading days after the two-day reaction"); ax.yaxis.grid(True, color=T["line"], lw=1.5); ax.set_axisbelow(True)
    _save(fig, "drift_paths")


def forest(rows, name, theme="cream", xlim=(-5.8, 5.8), h=900, highlight=lambda i: i < 2):
    fig, T = _fig(theme, h=h)
    ax = fig.add_axes([0.42, 0.18, 0.52, 0.76])
    y = np.arange(len(rows))[::-1]
    for i, (yi, (lab, b, se)) in enumerate(zip(y, rows)):
        col = T["accent"] if highlight(i) else T["grey"]
        b, se = b * 100, se * 100
        ax.plot([b - 1.96 * se, b + 1.96 * se], [yi, yi], color=col, lw=7, solid_capstyle="round")
        ax.scatter([b], [yi], color=col, s=320, zorder=3, edgecolor=T["bg"], linewidth=2)
        ax.text(b + 1.96 * se + 0.15, yi, f"{b:+.2f}", va="center", fontsize=32, fontfamily=MONO, color=T["ink"])
        ax.text(xlim[0] - 0.15, yi, lab, va="center", ha="right", fontsize=32, color=T["ink"], clip_on=False)
    ax.axvline(0, color=T["ink"], lw=2)
    ax.set_xlim(*xlim); ax.set_ylim(-0.7, len(rows) - 0.3); ax.set_yticks([])
    ax.spines["left"].set_visible(False)
    ax.set_xticks([-4, -2, 0, 2]); ax.set_xticklabels(["−4", "−2", "0", "+2"], fontfamily=MONO)
    ax.set_xlabel("extra drift on crowded sessions")
    _save(fig, name)


def placebo(theme="cream"):
    draws = np.load(ROOT / "output/placebo_draws_holdout.npy") * 100
    fig, T = _fig(theme, h=900)
    ax = fig.add_axes([0.08, 0.18, 0.86, 0.76])
    ax.hist(draws, bins=36, color=T["grey"], edgecolor=T["bg"], lw=1.5)
    ax.axvline(0.748, color=T["contrast"], lw=5)
    ax.text(0.85, ax.get_ylim()[1] * 0.93, "holdout\nestimate\n+0.75 pp", color=T["contrast"], fontsize=32, fontfamily=MONO, va="top")
    ax.set_xlabel("same test on 1,000 random macro calendars, pp"); ax.set_yticks([])
    ax.spines["left"].set_visible(False)
    ax.set_xticks([-2, -1, 0, 1, 2]); ax.set_xticklabels(["−2", "−1", "0", "+1", "+2"], fontfamily=MONO)
    _save(fig, "placebo")


def positive_control(theme="navy"):
    fig, T = _fig(theme, h=900)
    rows = [("liquid third", 0.0063, 0.0024, -0.0032, 0.0062), ("middle third", 0.0105, 0.0028, 0.0011, 0.0071), ("illiquid third", 0.0227, 0.0036, 0.0007, 0.0088)]
    y = np.arange(3)[::-1]
    for k, (x0, bi, si, title, col, xl) in enumerate(((0.33, 1, 2, "drift, pp", T["accent"], (-0.5, 3.5)), (0.69, 3, 4, "crowded, pp", T["grey"], (-2.5, 2.5)))):
        ax = fig.add_axes([x0, 0.16, 0.28, 0.70])
        for yi, r in zip(y, rows):
            b, se = r[bi] * 100, r[si] * 100
            ax.plot([b - 1.96 * se, b + 1.96 * se], [yi, yi], color=col, lw=7, solid_capstyle="round")
            ax.scatter([b], [yi], color=col, s=320, zorder=3, edgecolor=T["bg"], linewidth=2)
            ax.text(b, yi + 0.3, f"{b:+.2f}", ha="center", fontsize=32, fontfamily=MONO, color=T["ink"])
        ax.axvline(0, color=T["ink"], lw=2); ax.set_xlim(*xl); ax.set_ylim(-0.6, 2.8); ax.set_yticks([])
        ax.spines["left"].set_visible(False); ax.set_title(title, fontsize=34, loc="left", color=T["muted"], pad=18)
        ax.set_xticks([xl[0] + 0.5, 0, xl[1] - 0.5]); ax.set_xticklabels([f"{xl[0]+0.5:+.0f}", "0", f"{xl[1]-0.5:+.0f}"], fontfamily=MONO)
        if k == 0:
            for yi, r in zip(y, rows): ax.text(-0.75, yi, r[0], ha="right", va="center", fontsize=32, color=T["ink"], clip_on=False)
    _save(fig, "positive_control")


def bars2(rows, name, theme, ylim, ylabel, legend):
    fig, T = _fig(theme, h=900)
    ax = fig.add_axes([0.12, 0.18, 0.82, 0.74])
    x = np.arange(len(rows)); w = 0.36
    for j, (col, lab) in enumerate(legend):
        bars = ax.bar(x + (j - 0.5) * (w + 0.02), [r[1 + j] for r in rows], w, color=col, label=lab)
        for b in bars:
            ax.text(b.get_x() + b.get_width() / 2, b.get_height() + ylim[1] * 0.015, f"{b.get_height():.1f}%", ha="center", fontsize=32, fontfamily=MONO, color=T["ink"])
    ax.set_xticks(x); ax.set_xticklabels([r[0] for r in rows]); ax.set_ylim(ylim[0], ylim[1] * 1.3); ax.set_yticks([])
    ax.spines["left"].set_visible(False); ax.set_ylabel(ylabel)
    ax.legend(frameon=False, loc="upper right", handlelength=1.2)
    _save(fig, name)


def pead_by_year(theme="cream"):
    d = pd.read_csv(ROOT / "output/exhibit_pead_by_year.csv")
    fig, T = _fig(theme, h=900)
    ax = fig.add_axes([0.15, 0.18, 0.79, 0.76])
    ax.fill_between(d.year, d.drift_pp - 1.96 * d.se_pp, d.drift_pp + 1.96 * d.se_pp, color="#c9d8ee" if theme == "cream" else "#2a3a52", lw=0, alpha=0.8)
    ax.plot(d.year, d.drift_pp, color=T["accent"], lw=5, marker="o", ms=11, markeredgecolor=T["bg"])
    ax.axhline(0, color=T["ink"], lw=2)
    for yr, v in ((2007, 4.42), (2024, 3.93), (2020, -0.03)):
        ax.annotate(f"{yr}: {v:+.1f}", xy=(yr, v), xytext=(0, 24 if v > 0 else -40), textcoords="offset points", ha="right" if yr == 2024 else "center", fontsize=30, fontfamily=MONO)
    ax.set_xticks([2005, 2010, 2015, 2020, 2025]); ax.set_xticklabels(["2005", "2010", "2015", "2020", "2025"], fontfamily=MONO)
    ax.set_yticks([0, 2, 4]); ax.set_yticklabels(["0", "+2 pp", "+4 pp"], fontfamily=MONO)
    ax.set_ylim(-1.5, 6.2); ax.yaxis.grid(True, color=T["line"], lw=1.5); ax.set_axisbelow(True)
    ax.set_xlabel("60-day drift, top vs bottom decile, by year")
    _save(fig, "pead_by_year")


def equity(theme="cream"):
    d = pd.read_csv(ROOT / "output/exhibit_portfolio_daily.csv", index_col=0, parse_dates=True).dropna(how="all").fillna(0).loc["2005-04-01":"2025-12-31"]
    cum = (1 + d).cumprod() * 100
    fig, T = _fig(theme, h=900)
    ax = fig.add_axes([0.12, 0.18, 0.72, 0.76])
    ax.plot(cum.index, cum["uncrowded"], color=T["grey"], lw=4)
    ax.plot(cum.index, cum["crowded"], color=T["accent"], lw=4)
    ax.text(cum.index[-1] + pd.Timedelta(days=90), cum["uncrowded"].iloc[-1], "quiet\n188", color=T["grey"], fontsize=32, fontfamily=MONO, va="center")
    ax.text(cum.index[-1] + pd.Timedelta(days=90), cum["crowded"].iloc[-1], "crowded\n92", color=T["accent"], fontsize=32, fontfamily=MONO, va="center")
    ax.axhline(100, color=T["ink"], lw=1.5)
    ax.set_yticks([50, 100, 150]); ax.set_yticklabels(["50", "100", "150"], fontfamily=MONO)
    ax.set_xticks(pd.to_datetime(["2008-01-01", "2012-01-01", "2016-01-01", "2020-01-01", "2024-01-01"])); ax.set_xticklabels(["2008", "2012", "2016", "2020", "2024"], fontfamily=MONO)
    ax.yaxis.grid(True, color=T["line"], lw=1.5); ax.set_axisbelow(True); ax.set_xlim(cum.index[0], cum.index[-1] + pd.Timedelta(days=1100))
    ax.set_xlabel("long top, short bottom decile; 100 = start")
    _save(fig, "equity")


if __name__ == "__main__":
    heatmap(); minutes(); drift_paths(); placebo(); positive_control("navy"); pead_by_year(); equity()
    forest([("development 2005–15", -0.01482, 0.00714), ("holdout 2016–25", 0.00748, 0.00662), ("FOMC only, dev", -0.03838, 0.00901),
            ("FOMC only, holdout", 0.00059, 0.00925), ("CPI only, holdout", 0.00795, 0.01457), ("jobs only, holdout", 0.00919, 0.00902)], "coef")
    bars2([("2010–15\ndevelopment", 42.7, 42.4), ("2016–25\nholdout", 44.8, 43.6)], "h2", "cream", (0, 58), "EPS below last year, share",
          ((THEMES["cream"]["accent"], "crowded session"), (THEMES["cream"]["grey"], "quiet session")))
    bars2([("8-K filed after\nthe release day", 16.9, 15.7), ("Friday\nafter close", 1.72, 1.39)], "lag", "navy", (0, 22), "share of announcements",
          ((THEMES["navy"]["contrast"], "EPS below last year"), (THEMES["navy"]["grey"], "EPS at or above")))
    print("ok")
