import numpy as np
import pytest

from wsngame import (
    Params,
    cost_table,
    gain_table,
    jamming_fraction,
    random_network,
    round_payoffs,
    sweep,
)
from wsngame.game import DJ, F, R, S
from wsngame.network import MALICIOUS, NORMAL
from wsngame.simulate import Config


def test_random_network_shape():
    rng = np.random.default_rng(0)
    net = random_network(200, 800, 20, rng)
    assert net.n == 200 and net.n_edges == 800
    assert len(net.malicious) == 20
    assert net.degree().min() >= 1
    # simple: no self loops, no duplicates
    assert (net.src != net.dst).all()
    pairs = set(zip(net.src.tolist(), net.dst.tolist(), strict=True))
    assert len(pairs) == 1600


def test_random_network_rejects_impossible():
    rng = np.random.default_rng(0)
    with pytest.raises(ValueError):
        random_network(5, 11, 1, rng)
    with pytest.raises(ValueError):
        random_network(5, 4, 6, rng)


def test_cost_and_gain_tables_match_paper():
    p = Params(B1=2, B2=3, dB1=0.5, dB2=0.25, P=4, S=5, Y=1, aF=0.75, aJ=1)
    c, g = cost_table(p), gain_table(p)
    assert c[NORMAL, F] == c[MALICIOUS, F] == 3            # forward costs B2
    assert c[NORMAL, DJ] == 2.5                            # detect = B1 + dB1
    assert c[MALICIOUS, DJ] == 3.25                        # jam = B2 + dB2
    assert c[NORMAL, R] == c[MALICIOUS, R] == 2            # receive costs B1
    assert c[:, S].sum() == 0                              # sleep is free
    assert g[NORMAL, F, NORMAL, R] == g[MALICIOUS, F, MALICIOUS, R] == 0.75
    assert g[NORMAL, F, NORMAL, S] == 0                    # forwarding to a sleeper earns nothing
    assert g[MALICIOUS, DJ, NORMAL, R] == 1                # jam a receiver: aJ*Y
    assert g[MALICIOUS, DJ, NORMAL, DJ] == -4              # jam next to a detector: -P
    assert g[NORMAL, DJ, MALICIOUS, DJ] == 5               # detect a jammer: +S
    assert g[NORMAL, DJ, NORMAL, DJ] == 0                  # two detectors: nothing
    assert g[NORMAL, R, NORMAL, F] == pytest.approx(0.25)   # receiver keeps (1-aF)*Y
    assert g[NORMAL, R, MALICIOUS, DJ] == pytest.approx(-0.25)  # ... and loses it to a jammer
    assert g[:, S].sum() == 0                              # sleep never earns


def test_round_payoffs_triangle_by_hand():
    # 0 (normal) forwards, 1 (normal) receives, 2 (malicious) jams; complete triangle
    from wsngame.network import Network
    src = np.array([0, 0, 1, 1, 2, 2])
    dst = np.array([1, 2, 0, 2, 0, 1])
    net = Network(3, src, dst, np.array([NORMAL, NORMAL, MALICIOUS]))
    p = Params()  # all ones, aF .75
    pay = round_payoffs(net, np.array([F, R, DJ]), p)
    assert pay[0] == pytest.approx(0.75 - 1)      # +aF*Y from the receiver, -B2 once
    assert pay[1] == pytest.approx(-1)            # receiving costs B1, earns nothing
    assert pay[2] == pytest.approx(1 - 2)         # jams the receiver (+aJ*Y), pays B2+dB2


def test_action_cost_paid_once_regardless_of_degree():
    rng = np.random.default_rng(1)
    net = random_network(50, 200, 5, rng)
    p = Params()
    everyone_sleeps = np.full(50, S)
    assert np.allclose(round_payoffs(net, everyone_sleeps, p), 0)
    everyone_forwards = np.full(50, F)
    # nobody receives, so every node just pays B2 once
    assert np.allclose(round_payoffs(net, everyone_forwards, p), -p.B2)


def test_jamming_fraction_bounds_and_determinism():
    net = random_network(300, 1200, 30, np.random.default_rng(2))
    a = jamming_fraction(net, Params(), rounds=60, rng=np.random.default_rng(7))
    b = jamming_fraction(net, Params(), rounds=60, rng=np.random.default_rng(7))
    assert 0 <= a <= 1 and a == b


def test_jamming_fraction_extremes():
    net = random_network(300, 1200, 30, np.random.default_rng(3))
    # jamming free and hugely rewarded: every malicious node should jam
    p = Params(B2=0.0, dB2=0.0, aJ=50.0, P=0.0)
    assert jamming_fraction(net, p, rounds=40, rng=np.random.default_rng(0)) == 1.0
    # jamming ruinous: nobody jams
    p = Params(dB2=100.0)
    assert jamming_fraction(net, p, rounds=40, rng=np.random.default_rng(0)) == 0.0


def test_sweep_small():
    cfg = Config(n_nodes=100, avg_degree=6, malicious_share=0.1, rounds=20, networks=3)
    res = sweep("dB2", [0, 5, 10], cfg, Params(), seed=0)
    assert list(res) == [0.0, 5.0, 10.0]
    means = [m for m, _ in res.values()]
    assert all(0 <= m <= 1 for m in means)
    assert means[0] >= means[-1]  # more jamming cost, less jamming
    with pytest.raises(KeyError):
        sweep("nope", [1], cfg)


def test_candidate_payoffs_agree_with_round_payoffs():
    from wsngame.dynamics import candidate_payoffs
    net = random_network(80, 300, 8, np.random.default_rng(4))
    rng = np.random.default_rng(5)
    actions = rng.integers(0, 4, size=80)
    cand = candidate_payoffs(net, actions, Params(B1=2, P=3))
    actual = round_payoffs(net, actions, Params(B1=2, P=3))
    assert np.allclose(cand[np.arange(80), actions], actual)


def test_best_response_step_is_a_best_response_when_no_inertia():
    from wsngame.dynamics import best_response_step, candidate_payoffs
    net = random_network(80, 300, 8, np.random.default_rng(4))
    rng = np.random.default_rng(6)
    actions = rng.integers(0, 4, size=80)
    new = best_response_step(net, actions, Params(), rng, inertia=0.0)
    cand = candidate_payoffs(net, actions, Params())
    assert np.allclose(cand[np.arange(80), new], cand.max(axis=1))
    same = best_response_step(net, actions, Params(), rng, inertia=1.0)
    assert (same == actions).all()


def test_evolve_extremes():
    from wsngame.dynamics import evolve
    net = random_network(300, 1200, 30, np.random.default_rng(3))
    free_jam = Params(B2=0.0, dB2=0.0, aJ=50.0, P=0.0)
    cheap = evolve(net, free_jam, np.random.default_rng(0), transient=30, measure=10)
    ruinous = evolve(net, Params(dB2=100.0), np.random.default_rng(0), transient=30, measure=10)
    # free jamming drives receivers away, so jam and sleep tie once nobody receives;
    # the population oscillates rather than locking at 1.0
    assert cheap > 0.4
    assert ruinous == 0.0


def test_sweep_best_response_small():
    cfg = Config(n_nodes=100, avg_degree=6, networks=2, transient=20, measure=5)
    res = sweep("P", [0, 10], cfg, Params(), seed=0)
    means = [m for m, _ in res.values()]
    assert all(0 <= m <= 1 for m in means)
    assert means[0] >= means[-1]  # a harsher penalty never increases jamming
