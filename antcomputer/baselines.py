"""Jämförelsealgoritmer. Utan dem går det inte att säga om myrorna är bra.

Alla räknar "flips": hur många gånger en variabel byter värde innan lösningen
hittas. Det är samma mått som vi räknar för kolonin.
"""
from __future__ import annotations

import random
from statistics import median

from .problems import Problem


def _setup(p: Problem, rng: random.Random):
    a = [rng.random() < 0.5 for _ in range(p.n_vars)]
    occ = [[] for _ in range(p.n_vars)]
    for ci, c in enumerate(p.clauses):
        for lit in c:
            occ[abs(lit) - 1].append(ci)
    ntrue = [sum((lit > 0) == a[abs(lit) - 1] for lit in c) for c in p.clauses]
    unsat = {ci for ci, k in enumerate(ntrue) if k == 0}
    return a, occ, ntrue, unsat


def _flip(p, a, occ, ntrue, unsat, v):
    a[v] = not a[v]
    for ci in occ[v]:
        lit = next(l for l in p.clauses[ci] if abs(l) - 1 == v)
        if (lit > 0) == a[v]:
            ntrue[ci] += 1
            unsat.discard(ci)
        else:
            ntrue[ci] -= 1
            if ntrue[ci] == 0:
                unsat.add(ci)


def walksat(p: Problem, max_flips: int = 10**6, noise: float = 0.5, seed: int = 0) -> int | None:
    """Klassisk WalkSAT (Selman, Kautz & Cohen 1994)."""
    rng = random.Random(seed)
    a, occ, ntrue, unsat = _setup(p, rng)
    for flips in range(max_flips):
        if not unsat:
            return flips
        c = p.clauses[rng.choice(tuple(unsat))]
        if rng.random() < noise:
            v = abs(rng.choice(c)) - 1
        else:
            def breaks(v):
                return sum(1 for ci in occ[v] if ntrue[ci] == 1 and
                           any(abs(l) - 1 == v and (l > 0) == a[v] for l in p.clauses[ci]))
            v = min((abs(l) - 1 for l in c), key=lambda v: (breaks(v), rng.random()))
        _flip(p, a, occ, ntrue, unsat, v)
    return None


def random_walk(p: Problem, max_flips: int = 10**6, seed: int = 0) -> int | None:
    """Papadimitrious slumpvandring: välj ett ouppfyllt krav, vänd en slumpad variabel i det."""
    return walksat(p, max_flips, noise=1.0, seed=seed)


def blind_flip(p: Problem, max_flips: int = 10**6, seed: int = 0) -> int | None:
    """Vänd en helt slumpad variabel. Ingen information om vilka krav som brister."""
    rng = random.Random(seed)
    a, occ, ntrue, unsat = _setup(p, rng)
    for flips in range(max_flips):
        if not unsat:
            return flips
        _flip(p, a, occ, ntrue, unsat, rng.randrange(p.n_vars))
    return None


def benchmark(p: Problem, runs: int = 20, max_flips: int = 200_000) -> dict:
    out = {}
    for name, fn in (("walksat", walksat), ("random_walk", random_walk), ("blind_flip", blind_flip)):
        res = [fn(p, max_flips=max_flips, seed=s) for s in range(runs)]
        solved = [r for r in res if r is not None]
        # misslyckade körningar räknas som oändligt långa
        med = median([float("inf") if r is None else r for r in res])
        out[name] = {"median_flips": None if med == float("inf") else med,
                     "solved": len(solved), "runs": runs, "max_flips": max_flips}
    return out
