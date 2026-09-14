"""Evolutionary dynamics on the network.

Myopic best response with inertia: each generation every node looks at what its neighbours
did last generation, computes the payoff it *would* have earned with each of its four actions,
and switches to the best one with probability `1 - inertia` (otherwise it keeps its action).
Ties are broken uniformly at random. This is the standard discrete-time best-response dynamic
for spatial games; inertia keeps the population from oscillating in lockstep.

After `transient` generations the state is sampled for `measure` generations and P_J is the
mean share of malicious nodes jamming over that window.
"""

from __future__ import annotations

import numpy as np

from wsngame.game import DJ, N_ACTIONS, Params, cost_table, gain_table
from wsngame.network import Network


def candidate_payoffs(net: Network, actions: np.ndarray, p: Params) -> np.ndarray:
    """payoff[node, a]: what every node would earn with action a, given the neighbours'
    current actions."""
    cost = cost_table(p)
    gain = gain_table(p)
    tu, tv = net.node_type[net.src], net.node_type[net.dst]
    av = actions[net.dst]
    per_edge = gain[tu, :, tv, av]  # (2E, N_ACTIONS)
    total = np.zeros((net.n, N_ACTIONS))
    for a in range(N_ACTIONS):
        total[:, a] = np.bincount(net.src, weights=per_edge[:, a], minlength=net.n)
    return total - cost[net.node_type]


def best_response_step(
    net: Network, actions: np.ndarray, p: Params, rng: np.random.Generator, inertia: float
) -> np.ndarray:
    pay = candidate_payoffs(net, actions, p)
    # random tie-break: add a tiny jitter before argmax
    best = (pay + rng.uniform(0, 1e-9, size=pay.shape)).argmax(axis=1)
    keep = rng.random(net.n) < inertia
    return np.where(keep, actions, best)


def evolve(
    net: Network,
    p: Params,
    rng: np.random.Generator,
    transient: int = 200,
    measure: int = 50,
    inertia: float = 0.5,
) -> float:
    """P_J after the transient, averaged over the measurement window."""
    mal = net.malicious
    if len(mal) == 0:
        return float("nan")
    actions = rng.integers(0, N_ACTIONS, size=net.n)
    for _ in range(transient):
        actions = best_response_step(net, actions, p, rng, inertia)
    jam = 0.0
    for _ in range(measure):
        actions = best_response_step(net, actions, p, rng, inertia)
        jam += float((actions[mal] == DJ).mean())
    return jam / measure
