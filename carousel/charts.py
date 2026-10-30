"""Chart exhibits for the carousel (matplotlib, static PNG at 2x for 1080-wide slides).

dataviz rules applied: one accent (#2a78d6, crowded sessions), one contrast (#eb6834), grey for
the comparison series; bars from zero; direct labels; recessive axes; no dual axis; text in ink.
Reads only files under output/ and data/processed/. Writes carousel/figs/*.png.
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib import font_manager  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
FIGS = ROOT / "carousel" / "figs"
FIGS.mkdir(exist_ok=True)
for f in (Path.home() / "fonts").glob("*.ttf"):
    font_manager.fontManager.addfont(str(f))
import logging; logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)
_names = {font_manager.FontProperties(fname=str(f)).get_name() for f in (Path.home() / "fonts").glob("*.ttf")}
BODY_FONT = "Schibsted Grotesk" if "Schibsted Grotesk" in _names else "DejaVu Sans"
MONO_FONT = "JetBrains Mono" if "JetBrains Mono" in _names else "DejaVu Sans Mono"

ACCENT, CONTRAST, GREY, INK, LINE, CREAM = "#2a78d6", "#eb6834", "#8a8477", "#141311", "#d9d2c2", "#f6f1e7"
plt.rcParams.update({
    "font.family": BODY_FONT, "font.size": 22, "axes.edgecolor": LINE, "axes.linewidth": 1.5,
    "axes.spines.top": False, "axes.spines.right": False, "xtick.color": INK, "ytick.color": INK,
    "axes.labelcolor": INK, "figure.facecolor": CREAM, "axes.facecolor": CREAM, "savefig.facecolor": CREAM,
    "axes.titlesize": 26, "axes.titleweight": "bold", "axes.titlelocation": "left",
})
MONO = {"family": MONO_FONT}


def fig_calendar():
    """Average announcements per trading day: FOMC days vs CPI/jobs days vs other days."""
    d = pd.read_csv(ROOT / "output/exhibit_daily_events_vs_macro.csv", parse_dates=["reaction_day"])
    d["macro"] = d["macro"].fillna("")
    cats = {"FOMC statement day": d[d.macro.str.contains("FOMC")].events.mean(),
            "CPI or jobs day": d[d.macro.str.contains("CPI|EMPSIT") & ~d.macro.str.contains("FOMC")].events.mean(),
            "Other trading day": d[d.macro == ""].events.mean()}
    fig, ax = plt.subplots(figsize=(11, 7), dpi=160)
    names = list(cats); vals = [cats[k] for k in names]
    colors = [ACCENT, ACCENT, GREY]
    bars = ax.barh(names[::-1], vals[::-1], color=colors[::-1], height=0.55)
    for b, v in zip(bars, vals[::-1]):
        ax.text(v + 2, b.get_y() + b.get_height() / 2, f"{v:.0f}", va="center", fontdict=MONO, fontsize=26, color=INK)
    ax.set_xlim(0, max(vals) * 1.18); ax.set_xlabel("Earnings 8-Ks per trading day, 2005–2025 mean")
    ax.tick_params(axis="y", length=0); ax.spines["left"].set_visible(False)
    ax.set_xticks([]); ax.spines["bottom"].set_visible(False)
    fig.tight_layout(); fig.savefig(FIGS / "calendar.png"); plt.close(fig)
    return cats


def fig_sameday():
    """Share of earnings 8-Ks filed on the release day, by year."""
    y = pd.read_csv(ROOT / "output/exhibit_by_year.csv", index_col=0)
    fig, ax = plt.subplots(figsize=(11, 6.5), dpi=160)
    ax.plot(y.index, y.same_day * 100, color=ACCENT, lw=3)
    ax.scatter([y.index[0], y.index[-1]], [y.same_day.iloc[0] * 100, y.same_day.iloc[-1] * 100], color=ACCENT, s=80, zorder=3)
    ax.text(y.index[0] + 0.3, y.same_day.iloc[0] * 100 - 4, f"{y.same_day.iloc[0]*100:.0f}%", fontdict=MONO, fontsize=24)
    ax.text(y.index[-1] - 2.6, y.same_day.iloc[-1] * 100 + 2, f"{y.same_day.iloc[-1]*100:.0f}%", fontdict=MONO, fontsize=24)
    ax.set_ylim(0, 100); ax.set_ylabel("% of 8-Ks filed on the release day"); ax.yaxis.grid(True, color=LINE, lw=1); ax.set_axisbelow(True)
    ax.set_xticks([2005, 2010, 2015, 2020, 2025])
    fig.tight_layout(); fig.savefig(FIGS / "sameday.png"); plt.close(fig)


def fig_h2(rows: list[tuple[str, float, float]]):
    """Share of negative GAAP surprises, crowded vs uncrowded, two samples. rows: (label, crowded, uncrowded) in %."""
    fig, ax = plt.subplots(figsize=(11, 6.5), dpi=160)
    x = np.arange(len(rows)); w = 0.34
    c = [r[1] for r in rows]; u = [r[2] for r in rows]
    b1 = ax.bar(x - w / 2 - 0.01, c, w, color=ACCENT, label="Crowded session")
    b2 = ax.bar(x + w / 2 + 0.01, u, w, color=GREY, label="Uncrowded session")
    for bars in (b1, b2):
        for b in bars:
            ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 1, f"{b.get_height():.1f}%", ha="center", fontdict=MONO, fontsize=22)
    ax.set_xticks(x); ax.set_xticklabels([r[0] for r in rows]); ax.set_ylim(0, 60)
    ax.set_ylabel("Share with EPS below last year (%)"); ax.legend(frameon=False, loc="upper left", fontsize=20)
    ax.tick_params(axis="x", length=0)
    fig.tight_layout(); fig.savefig(FIGS / "h2.png"); plt.close(fig)


def fig_car_paths(paths: pd.DataFrame):
    """paths: index day (-1..60), columns crowded, uncrowded (cumulative top-minus-bottom abnormal return, %)."""
    fig, ax = plt.subplots(figsize=(11, 7), dpi=160)
    ax.axhline(0, color=LINE, lw=1.5); ax.axvline(1.5, color=LINE, lw=1.5, ls=":")
    ax.plot(paths.index, paths["uncrowded"], color=GREY, lw=3, label="Uncrowded session")
    ax.plot(paths.index, paths["crowded"], color=ACCENT, lw=3, label="Crowded session")
    for col, color in (("crowded", ACCENT), ("uncrowded", GREY)):
        ax.text(paths.index[-1] + 1, paths[col].iloc[-1], f"{paths[col].iloc[-1]:+.1f}%", fontdict=MONO, fontsize=22, color=color, va="center")
    ax.set_xlabel("Trading days after the reaction day"); ax.set_ylabel("Top minus bottom surprise decile, cumulative abnormal return (%)")
    ax.legend(frameon=False, loc="upper left", fontsize=20); ax.yaxis.grid(True, color=LINE, lw=1); ax.set_axisbelow(True)
    ax.set_xlim(-1, 66)
    fig.tight_layout(); fig.savefig(FIGS / "car_paths.png"); plt.close(fig)


def fig_coef(rows: list[tuple[str, float, float]]):
    """Interaction coefficients with 95% CI. rows: (label, b, se), in CAR units; plotted in percentage points."""
    fig, ax = plt.subplots(figsize=(11, 6.5), dpi=160)
    y = np.arange(len(rows))[::-1]
    for yi, (lab, b, se) in zip(y, rows):
        col = ACCENT if lab.startswith("Primary") else GREY
        ax.plot([(b - 1.96 * se) * 100, (b + 1.96 * se) * 100], [yi, yi], color=col, lw=4, solid_capstyle="round")
        ax.scatter([b * 100], [yi], color=col, s=140, zorder=3)
        ax.text((b + 1.96 * se) * 100 + 0.3, yi, f"{b*100:+.2f} pp", va="center", fontdict=MONO, fontsize=22)
    ax.axvline(0, color=INK, lw=1.5)
    ax.set_yticks(y); ax.set_yticklabels([r[0] for r in rows]); ax.tick_params(axis="y", length=0); ax.spines["left"].set_visible(False)
    ax.set_xlabel("Extra drift per decile of surprise on crowded sessions, percentage points (95% CI)")
    fig.tight_layout(); fig.savefig(FIGS / "coef.png"); plt.close(fig)


def fig_placebo(draws: np.ndarray, actual: float):
    fig, ax = plt.subplots(figsize=(11, 6.5), dpi=160)
    ax.hist(draws * 100, bins=40, color=GREY, edgecolor=CREAM)
    ax.axvline(actual * 100, color=CONTRAST, lw=4)
    ax.text(actual * 100, ax.get_ylim()[1] * 0.92, f" actual {actual*100:+.2f} pp", color=CONTRAST, fontdict=MONO, fontsize=24)
    ax.set_xlabel("Interaction coefficient on randomly drawn pseudo-macro days, percentage points"); ax.set_ylabel("Draws")
    fig.tight_layout(); fig.savefig(FIGS / "placebo.png"); plt.close(fig)


if __name__ == "__main__":
    print(fig_calendar()); fig_sameday()
    if len(sys.argv) > 1 and sys.argv[1] == "all":
        pass
