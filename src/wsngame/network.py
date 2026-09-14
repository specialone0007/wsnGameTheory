"""Random wireless sensor network: a simple undirected graph with a malicious subset.

Stored as directed edge arrays (both directions of every edge) so that per-neighbour payoffs
can be computed with NumPy in one pass.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

NORMAL, MALICIOUS = 0, 1


@dataclass(frozen=True)
class Network:
    n: int
    src: np.ndarray        # directed edge sources, shape (2E,)
    dst: np.ndarray        # directed edge targets, shape (2E,)
    node_type: np.ndarray  # NORMAL or MALICIOUS per node, shape (n,)

    @property
    def n_edges(self) -> int:
        return len(self.src) // 2

    @property
    def malicious(self) -> np.ndarray:
        return np.flatnonzero(self.node_type == MALICIOUS)

    def degree(self) -> np.ndarray:
        return np.bincount(self.src, minlength=self.n)


def random_network(n: int, n_edges: int, n_malicious: int, rng: np.random.Generator) -> Network:
    """Simple graph with exactly `n_edges` undirected edges, every node of degree >= 1,
    `n_malicious` nodes chosen uniformly at random as malicious."""
    max_edges = n * (n - 1) // 2
    if not 0 <= n_malicious <= n:
        raise ValueError("n_malicious must be within [0, n]")
    if n_edges > max_edges or n_edges < (n + 1) // 2:
        raise ValueError(f"n_edges must be in [{(n + 1) // 2}, {max_edges}] for n={n}")

    edges: set[tuple[int, int]] = set()

    def add(u: int, v: int) -> bool:
        if u == v:
            return False
        key = (u, v) if u < v else (v, u)
        if key in edges:
            return False
        edges.add(key)
        return True

    # every node gets at least one edge first
    order = rng.permutation(n)
    for u in order:
        if len(edges) >= n_edges:
            break
        while not add(int(u), int(rng.integers(n))):
            pass
    # then fill uniformly
    while len(edges) < n_edges:
        add(int(rng.integers(n)), int(rng.integers(n)))

    e = np.array(sorted(edges), dtype=np.int64)
    src = np.concatenate([e[:, 0], e[:, 1]])
    dst = np.concatenate([e[:, 1], e[:, 0]])
    node_type = np.zeros(n, dtype=np.int64)
    node_type[rng.choice(n, size=n_malicious, replace=False)] = MALICIOUS
    return Network(n=n, src=src, dst=dst, node_type=node_type)
