"""Oraklet: datorn som ställer problem och skärper kraven när kolonin gör framsteg.

Oraklet vet ingenting om myror. Det ser bara en tilldelning (vilka kammare som
"vinner") och avgör hur mycket mat världen ska ge. När ett problem är löst
verifieras svaret oberoende och oraklet går vidare till nästa nivå.
"""
from __future__ import annotations

import random

from .problems import Problem, factoring, planted_3sat, semiprimes, with_blocking_clause


class Oracle:
    kind = "base"

    def __init__(self, seed: int = 0) -> None:
        self.rng = random.Random(seed)
        self.level = 0
        self.problem: Problem = self.first()

    def first(self) -> Problem:
        raise NotImplementedError

    def next(self, solution: list[bool]) -> Problem:
        raise NotImplementedError

    def advance(self, solution: list[bool]) -> Problem:
        self.level += 1
        self.problem = self.next(solution)
        return self.problem


class GrowingSAT(Oracle):
    """3-SAT som växer: varje lösning belönas med fler variabler och fler krav.

    Gamla klausuler finns kvar, så det kolonin byggt är fortfarande delvis
    giltigt; nya krav läggs ovanpå.
    """
    kind = "sat"

    def __init__(self, seed: int = 0, n0: int = 10, dn: int = 4, ratio: float = 4.0) -> None:
        self.n0, self.dn, self.ratio = n0, dn, ratio
        super().__init__(seed)

    def first(self) -> Problem:
        return planted_3sat(self.n0, self.ratio, self.rng)

    def next(self, solution: list[bool]) -> Problem:
        old = self.problem
        n = old.n_vars + self.dn
        # Den planterade lösningen byggs ut med koloninas egen lösning för de gamla
        # variablerna, så att instansen förblir lösbar oavsett vilken lösning de hittat.
        planted = list(solution[:old.n_vars]) + [self.rng.random() < 0.5 for _ in range(self.dn)]
        return planted_3sat(n, self.ratio, self.rng, planted=planted, base=old)


class Enumerate(Oracle):
    """Samma problem, men varje funnen lösning förbjuds: hitta en till."""
    kind = "enumerate"

    def __init__(self, seed: int = 0, n: int = 12, ratio: float = 3.0) -> None:
        self.n, self.ratio = n, ratio
        super().__init__(seed)

    def first(self) -> Problem:
        return planted_3sat(self.n, self.ratio, self.rng)

    def next(self, solution: list[bool]) -> Problem:
        return with_blocking_clause(self.problem, solution)


class Factoring(Oracle):
    """Faktorisera allt större halvprimtal."""
    kind = "factor"

    def __init__(self, seed: int = 0, start: int = 15) -> None:
        self.gen = semiprimes(start)
        super().__init__(seed)

    def first(self) -> Problem:
        return factoring(next(self.gen))

    def next(self, solution: list[bool]) -> Problem:
        return factoring(next(self.gen))


ORACLES = {"sat": GrowingSAT, "enumerate": Enumerate, "factor": Factoring}
