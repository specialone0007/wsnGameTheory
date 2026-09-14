"""The spatial game of Mao, Zhu & Wei (2013), vectorised.

Every node picks one action per round. Normal nodes choose from {Forward, Detect, Receive,
Sleep}; malicious nodes from {Forward, Jam, Receive, Sleep}. Action code 1 means Detect for a
normal node and Jam for a malicious one, so both types share one 4-symbol alphabet.

Payoff of a node in one round = -(cost of its action, paid once) + sum over neighbours of the
interaction gain that depends on the two actions and the two node types. Paying the action
cost once, rather than once per neighbour, is what the paper's "spatial structured game" rules
(its Figure 3) amount to: a node that forwards spends B2 once however many neighbours it has,
and collects the forwarding reward from every neighbour that receives.

One addition to the paper's pairwise table: a receiver earns the remaining share (1 - aF)·Y of
every packet forwarded to it and loses that share to every jamming neighbour. In the paper the
value of receiving is implicit (the network is supposed to deliver packets); without it,
Receive is strictly dominated by Sleep, nobody receives, forwarding earns nothing, and any
adaptive dynamic collapses to everyone sleeping.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np

from wsngame.network import MALICIOUS, NORMAL, Network

F, DJ, R, S = 0, 1, 2, 3
ACTIONS = ("F", "D/J", "R", "S")
N_ACTIONS = 4


@dataclass(frozen=True)
class Params:
    """Costs and rewards. Names follow the paper.

    B1      cost to receive a packet (also the base cost of detecting)
    B2      cost to forward a packet (also the base cost of jamming)
    dB1     additional cost of detecting on top of receiving
    dB2     additional cost of jamming on top of forwarding
    P       penalty paid by a jammer that is detected
    S       reward to a normal node that detects a jammer
    Y       value of a successfully delivered packet
    aF      share of Y the forwarder earns when the neighbour receives
    aJ      share of Y the jammer earns when it disrupts a receiving neighbour
    """
    B1: float = 1.0
    B2: float = 1.0
    dB1: float = 1.0
    dB2: float = 1.0
    P: float = 1.0
    S: float = 1.0
    Y: float = 1.0
    aF: float = 0.75
    aJ: float = 1.0

    def with_(self, **kw: float) -> Params:
        return replace(self, **kw)


def cost_table(p: Params) -> np.ndarray:
    """cost[type, action]: what a node pays once for choosing that action."""
    c = np.zeros((2, N_ACTIONS))
    c[:, F] = p.B2
    c[NORMAL, DJ] = p.B1 + p.dB1       # detect
    c[MALICIOUS, DJ] = p.B2 + p.dB2    # jam
    c[:, R] = p.B1
    c[:, S] = 0.0
    return c


def gain_table(p: Params) -> np.ndarray:
    """gain[type_u, action_u, type_v, action_v]: what u earns from neighbour v in one round."""
    g = np.zeros((2, N_ACTIONS, 2, N_ACTIONS))
    # forwarding succeeds when the neighbour receives, whoever the neighbour is
    g[:, F, :, R] = p.aF * p.Y
    # the receiver gets the rest of the packet's value from each forwarding neighbour ...
    g[:, R, :, F] = (1 - p.aF) * p.Y
    # ... and loses it to each jamming neighbour
    g[:, R, MALICIOUS, DJ] = -(1 - p.aF) * p.Y
    # a normal node that detects earns S if the neighbour is a jammer
    g[NORMAL, DJ, MALICIOUS, DJ] = p.S
    # a jammer earns aJ*Y against a receiving neighbour and pays P if a neighbour detects it
    g[MALICIOUS, DJ, :, R] = p.aJ * p.Y
    g[MALICIOUS, DJ, NORMAL, DJ] = -p.P
    return g


def round_payoffs(net: Network, actions: np.ndarray, p: Params) -> np.ndarray:
    """Total payoff of every node for one round of simultaneous actions."""
    if actions.shape != (net.n,):
        raise ValueError("actions must have one entry per node")
    cost = cost_table(p)
    gain = gain_table(p)
    tu, tv = net.node_type[net.src], net.node_type[net.dst]
    au, av = actions[net.src], actions[net.dst]
    per_edge = gain[tu, au, tv, av]
    total = np.bincount(net.src, weights=per_edge, minlength=net.n)
    return total - cost[net.node_type, actions]


def random_actions(net: Network, rng: np.random.Generator) -> np.ndarray:
    """Every node picks one of its four actions uniformly at random."""
    return rng.integers(0, N_ACTIONS, size=net.n)
