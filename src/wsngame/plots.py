"""Figures."""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

LABELS = {"B1": r"$B_1$ receive cost", "B2": r"$B_2$ forward cost",
          "dB1": r"$\Delta B_1$ extra detect cost", "dB2": r"$\Delta B_2$ extra jam cost",
          "P": r"$P$ penalty when detected", "S": r"$S$ reward for detecting"}
COLOURS = {"B1": "#1f4e79", "B2": "#c0392b", "dB1": "#2e86c1", "dB2": "#e67e22",
           "P": "#27ae60", "S": "#8e44ad"}


def read(path: Path) -> tuple[str, list[float], list[float], list[float]]:
    with path.open(newline="") as f:
        rows = list(csv.DictReader(f))
    v = [float(r["value"]) for r in rows]
    m = [float(r["pj_mean"]) for r in rows]
    s = [float(r["pj_std"]) for r in rows]
    return path.stem, v, m, s


def plot_sweeps(paths: list[Path], out: Path) -> Path:
    plt.rcParams.update({"figure.dpi": 150, "font.size": 9, "axes.spines.top": False,
                         "axes.spines.right": False, "axes.grid": True, "grid.alpha": 0.3})
    cost_like = [p for p in paths if p.stem in ("B1", "B2", "dB1", "dB2")]
    other = [p for p in paths if p.stem not in ("B1", "B2", "dB1", "dB2")]
    groups = [g for g in (cost_like, other) if g]
    fig, axes = plt.subplots(1, len(groups), figsize=(5.6 * len(groups), 3.8), squeeze=False)
    for ax, group in zip(axes[0], groups, strict=True):
        for path in group:
            name, v, m, s = read(path)
            c = COLOURS.get(name, None)
            ax.plot(v, m, "o-", ms=4, color=c, label=LABELS.get(name, name))
            ax.fill_between(v, [a - b for a, b in zip(m, s, strict=True)],
                            [a + b for a, b in zip(m, s, strict=True)], color=c, alpha=0.12)
        ax.set_xlabel("parameter value (others fixed at 1)")
        ax.set_ylabel(r"$P_J$  share of malicious nodes that jam")
        top = max((max(read(p)[2]) for p in group), default=0.0)
        ax.set_ylim(0, max(0.5, min(1.0, top * 1.25 + 0.05)))
        ax.legend(frameon=False, fontsize=8)
    axes[0][0].set_title(r"$P_J$ against costs", loc="left")
    if len(groups) > 1:
        axes[0][1].set_title(r"$P_J$ against detection penalty / reward", loc="left")
    fig.tight_layout()
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out)
    plt.close(fig)
    return out
