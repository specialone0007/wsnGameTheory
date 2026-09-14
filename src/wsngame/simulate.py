"""Simulation protocols and the P_J statistic.

Two ways to turn the one-shot game into a prediction of how many malicious nodes jam:

* **best-response** (default): the population evolves by myopic best response with inertia
  (see `dynamics.py`); P_J is the share of malicious nodes jamming after a transient. Normal
  nodes react to jammers (fewer receivers, more detectors), so the result has feedback.
* **sampled**: the 2022 replication's scheme. Every node picks an action uniformly at random
  each round; after `rounds` rounds each malicious node is assigned the active action
  (Forward / Jam / Receive) with the highest mean payoff, and P_J is the share assigned Jam.
  There is no feedback: neighbours never react.

P_J is averaged over `networks` independent random networks. The same networks are reused for
every parameter value so a sweep shows the parameter's effect, not the network draw.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np

from wsngame.dynamics import evolve
from wsngame.game import DJ, N_ACTIONS, F, Params, R, random_actions, round_payoffs
from wsngame.network import Network, random_network

ACTIVE = (F, DJ, R)
Method = Literal["best-response", "sampled"]


@dataclass(frozen=True)
class Config:
    n_nodes: int = 1000
    avg_degree: int = 8
    malicious_share: float = 0.10
    networks: int = 20
    method: Method = "best-response"
    # best-response
    transient: int = 200
    measure: int = 50
    inertia: float = 0.5
    # sampled
    rounds: int = 250

    @property
    def n_edges(self) -> int:
        return self.n_nodes * self.avg_degree // 2

    @property
    def n_malicious(self) -> int:
        return int(round(self.n_nodes * self.malicious_share))


def jamming_fraction(net: Network, p: Params, rounds: int, rng: np.random.Generator) -> float:
    """P_J for one network under the *sampled* scheme."""
    mal = net.malicious
    if len(mal) == 0:
        return float("nan")
    sums = np.zeros((len(mal), N_ACTIONS))
    counts = np.zeros((len(mal), N_ACTIONS))
    rows = np.arange(len(mal))
    for _ in range(rounds):
        actions = random_actions(net, rng)
        pay = round_payoffs(net, actions, p)
        a = actions[mal]
        np.add.at(sums, (rows, a), pay[mal])
        np.add.at(counts, (rows, a), 1)
    with np.errstate(invalid="ignore", divide="ignore"):
        means = sums / counts
    means[:, [x for x in range(N_ACTIONS) if x not in ACTIVE]] = -np.inf
    means = np.where(np.isnan(means), -np.inf, means)
    return float((means.argmax(axis=1) == DJ).mean())


def pj_for(net: Network, p: Params, cfg: Config, rng: np.random.Generator) -> float:
    if cfg.method == "sampled":
        return jamming_fraction(net, p, cfg.rounds, rng)
    return evolve(net, p, rng, cfg.transient, cfg.measure, cfg.inertia)


def sweep(
    param: str,
    values: list[float],
    cfg: Config | None = None,
    base: Params | None = None,
    seed: int = 42,
) -> dict[float, tuple[float, float]]:
    """P_J (mean, std over networks) for each value of one parameter, all others at `base`."""
    cfg = cfg or Config()
    base = base or Params()
    if param not in Params.__dataclass_fields__:
        raise KeyError(f"unknown parameter {param!r}")
    rng = np.random.default_rng(seed)
    nets = [random_network(cfg.n_nodes, cfg.n_edges, cfg.n_malicious, rng)
            for _ in range(cfg.networks)]
    out: dict[float, tuple[float, float]] = {}
    for v in values:
        p = base.with_(**{param: float(v)})
        pj = np.array([pj_for(net, p, cfg, rng) for net in nets])
        out[float(v)] = (float(pj.mean()), float(pj.std()))
    return out
