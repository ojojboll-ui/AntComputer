"""Kör med: python -m pytest tests  (eller python tests/test_core.py)"""
import random
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from antcomputer.baselines import walksat  # noqa: E402
from antcomputer.oracle import GrowingSAT  # noqa: E402
from antcomputer.problems import factoring, planted_3sat  # noqa: E402
from antcomputer.world import Colony, Params  # noqa: E402


def test_factoring_circuit_is_exact():
    """CNF:en är uppfylld exakt när p*q == N och p, q > 1."""
    for N in (15, 21, 35):
        P = factoring(N)
        cb, a, b, bits = P.meta["builder"], P.meta["p_vars"], P.meta["q_vars"], P.meta["bits"]
        for p in range(1 << bits):
            for q in range(1 << bits):
                inp = {v: bool((p >> i) & 1) for i, v in enumerate(a)}
                inp.update({v: bool((q >> i) & 1) for i, v in enumerate(b)})
                asg = cb.evaluate(inp)
                assert P.is_model(asg) == (p * q == N and p > 1 and q > 1)
                assert P.verify(asg)[0] == (p * q == N and p > 1 and q > 1)


def test_growing_sat_stays_satisfiable():
    o = GrowingSAT(seed=3)
    for _ in range(4):
        p = o.problem
        assert walksat(p, max_flips=100_000) is not None
        a = p.meta["planted"]
        assert p.is_model(a)
        o.advance(a)


def test_colony_runs_and_conserves_shapes():
    p = planted_3sat(8, 4.0, random.Random(0))
    c = Colony(p, Params(pop_init=50, pop_cap=100), np.random.default_rng(0))
    for _ in range(300):
        s = c.step()
    assert 0 <= s["pop"] <= 100
    c.set_problem(planted_3sat(12, 4.0, random.Random(1)))
    for _ in range(50):
        c.step()
    assert len(c.val) == 12


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
