"""wsngame: run parameter sweeps and plot P_J.

  wsngame sweep  --params B1 B2 dB1 dB2 P S --lo 0 --hi 10 --networks 20
  wsngame sweep  --method sampled --rounds 250      # the 2022 replication's scheme
  wsngame plot   results/*.csv
"""

from __future__ import annotations

import argparse
import csv
import sys
import time
from pathlib import Path

from wsngame.simulate import Config, Params, sweep

ROOT = Path(__file__).resolve().parents[2]


def cmd_sweep(a: argparse.Namespace) -> int:
    cfg = Config(n_nodes=a.nodes, avg_degree=a.degree, malicious_share=a.malicious,
                 networks=a.networks, method=a.method, transient=a.transient,
                 measure=a.measure, inertia=a.inertia, rounds=a.rounds)
    values = list(range(a.lo, a.hi + 1))
    a.out.mkdir(parents=True, exist_ok=True)
    for param in a.params:
        t0 = time.perf_counter()
        res = sweep(param, values, cfg, Params(), seed=a.seed)
        path = a.out / f"{param}.csv"
        with path.open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["value", "pj_mean", "pj_std", "method", "networks", "nodes", "seed"])
            for v, (m, s) in res.items():
                w.writerow([v, f"{m:.4f}", f"{s:.4f}", cfg.method, cfg.networks, cfg.n_nodes,
                            a.seed])
        line = "  ".join(f"{v:g}:{m:.2f}" for v, (m, _) in res.items())
        print(f"{param:<4} {line}   ({time.perf_counter() - t0:.0f}s)", flush=True)
    return 0


def cmd_plot(a: argparse.Namespace) -> int:
    from wsngame.plots import plot_sweeps

    out = plot_sweeps([Path(p) for p in a.csvs], a.out)
    print(f"wrote {out}")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="wsngame", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("sweep", help="P_J against one or more parameters")
    s.add_argument("--params", nargs="+", default=["B1", "B2", "dB1", "dB2", "P", "S"],
                   choices=list(Params.__dataclass_fields__))
    s.add_argument("--lo", type=int, default=0)
    s.add_argument("--hi", type=int, default=10)
    s.add_argument("--nodes", type=int, default=1000)
    s.add_argument("--degree", type=int, default=8)
    s.add_argument("--malicious", type=float, default=0.10)
    s.add_argument("--networks", type=int, default=20)
    s.add_argument("--method", choices=["best-response", "sampled"], default="best-response")
    s.add_argument("--transient", type=int, default=200, help="best-response: burn-in generations")
    s.add_argument("--measure", type=int, default=50, help="best-response: generations averaged")
    s.add_argument("--inertia", type=float, default=0.5, help="best-response: P(keep action)")
    s.add_argument("--rounds", type=int, default=250, help="sampled: random rounds per network")
    s.add_argument("--seed", type=int, default=42)
    s.add_argument("--out", type=Path, default=ROOT / "results")
    s.set_defaults(fn=cmd_sweep)

    s = sub.add_parser("plot", help="plot sweep CSVs on one figure")
    s.add_argument("csvs", nargs="+")
    s.add_argument("--out", type=Path, default=ROOT / "docs" / "figures" / "pj-sweeps.png")
    s.set_defaults(fn=cmd_plot)

    a = p.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
