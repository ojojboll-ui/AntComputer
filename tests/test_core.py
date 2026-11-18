"""Kör med: python -m pytest tests  (eller python tests/test_core.py)"""
import random
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from antcomputer.baselines import walksat  # noqa: E402
from antcomputer.oracle import Factoring, GrowingSAT, Progressive  # noqa: E402
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


def test_progressive_reveals_everything_and_verifies():
    for order in Progressive.ORDERS:
        o = Progressive(Factoring(), order=order)
        P = o.full
        cb, a, b = P.meta["builder"], P.meta["p_vars"], P.meta["q_vars"]
        inp = {v: bool((3 >> i) & 1) for i, v in enumerate(a)}
        inp.update({v: bool((5 >> i) & 1) for i, v in enumerate(b)})
        sol = cb.evaluate(inp)
        sizes = [len(o.problem.clauses)]
        while not o.complete():
            assert P.is_model(sol)  # en riktig lösning uppfyller alltid varje synligt steg
            o.reveal([False] * P.n_vars)
            sizes.append(len(o.problem.clauses))
        assert sizes == sorted(sizes) and sizes[-1] == len(P.clauses)
        assert o.problem.verify(sol)[0]
        o.advance(sol)
        assert o.full.meta["N"] == 21 and not o.complete()


def test_memory_brain_runs_and_old_genomes_still_work():
    import numpy as np
    from antcomputer.problems import planted_3sat
    from antcomputer.world import Colony, Params, genome_shape, prior_genome
    rng = np.random.default_rng(0)
    import random
    p = planted_3sat(8, 4.0, random.Random(0))
    col = Colony(p, Params(mem=3), rng)
    assert col.G.shape[1:] == genome_shape(3)
    for _ in range(50):
        col.step()
    assert np.abs(col.mem[col.alive]).max() > 0          # minnet används
    old = prior_genome()[None].repeat(20, axis=0)         # arvsmassa utan minne
    col2 = Colony(p, Params(mem=3), rng, founders=old)    # formen styr, inte parametern
    assert col2.M == 0
    col2.step()


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
