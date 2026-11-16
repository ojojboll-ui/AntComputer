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

    # Ett vanligt orakel visar hela problemet direkt.
    def complete(self) -> bool:
        return True

    def threshold(self) -> float:
        return 1.0

    def progress(self) -> float:
        return 1.0


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


class Progressive(Oracle):
    """Döljer större delen av problemet och avslöjar nya krav under räkningens gång.

    Kolonin ser bara de krav som avslöjats hittills. När den uppfyller en viss
    andel (`reveal_at`) av dem i `solve_hold` tick avslöjar oraklet fler. Först
    när hela problemet är avslöjat och uppfyllt räknas det som löst.

    Ordningen styr vilken sorts lärare oraklet är:
      natural      problemets egen ordning; för faktorisering siffra för siffra
                   (produktens lägsta bit först, med kretsen som bestämmer den)
      random       slumpade krav
      adversarial  krav som kolonins nuvarande svar bryter mot (motståndare)
      friendly     krav som kolonin redan råkar uppfylla (snäll lärare)
    """
    kind = "progressive"
    ORDERS = ("natural", "random", "adversarial", "friendly")

    def __init__(self, base: Oracle, order: str = "natural", step: float = 0.1, reveal_at: float = 1.0,
                 seed: int = 0) -> None:
        assert order in self.ORDERS
        self.base, self.order, self.step, self.reveal_at = base, order, step, reveal_at
        self.rng = random.Random(seed * 7919 + 17)
        self.level = base.level
        self.revealed: set[tuple[int, ...]] = set()
        self.problem = self._reveal_more(None)

    @property
    def full(self) -> Problem:
        return self.base.problem

    def complete(self) -> bool:
        return len(self.revealed) >= len(self.full.clauses)

    def threshold(self) -> float:
        return 1.0 if self.complete() else self.reveal_at

    def progress(self) -> float:
        return len(self.revealed) / len(self.full.clauses)

    def _target(self) -> int:
        """Hur många krav som ska vara synliga efter nästa avslöjande."""
        m, r = len(self.full.clauses), len(self.revealed)
        stages = self.full.meta.get("stages")
        if stages:
            return next((b for b in stages if b > r), m)
        return min(m, r + max(1, round(self.step * m)))

    def _reveal_more(self, assignment) -> Problem:
        full = self.full.clauses
        hidden = [c for c in full if c not in self.revealed]
        k = max(0, self._target() - len(self.revealed))
        if self.order == "natural" or assignment is None and self.order in ("adversarial", "friendly"):
            pick = hidden[:k]
        elif self.order == "random":
            pick = self.rng.sample(hidden, k)
        else:
            n = self.full.n_vars
            assignment = list(assignment[:n]) + [False] * max(0, n - len(assignment))

            def sat(c):
                return any((lit > 0) == assignment[abs(lit) - 1] for lit in c)
            want_sat = self.order == "friendly"
            ranked = sorted(hidden, key=lambda c: (sat(c) != want_sat, self.rng.random()))
            pick = ranked[:k]
        self.revealed.update(pick)
        return self._view()

    def _view(self) -> Problem:
        full = self.full
        clauses = [c for c in full.clauses if c in self.revealed]
        return Problem(f"{full.name} · avslöjat {len(clauses)}/{len(full.clauses)}", full.n_vars, clauses,
                       full.verify, meta=dict(full.meta, revealed=len(clauses), total=len(full.clauses)))

    def reveal(self, assignment: list[bool]) -> Problem:
        self.problem = self._reveal_more(assignment)
        return self.problem

    def advance(self, solution: list[bool]) -> Problem:
        self.base.advance(solution)
        self.level = self.base.level
        if self.full.meta.get("stages"):
            # problem med naturliga steg (t.ex. ny faktorisering) avslöjas från början igen;
            # det kolonin byggt i leran finns ändå kvar i världen
            self.revealed = set()
        else:
            # krav som fortfarande finns i det nya problemet förblir synliga
            self.revealed &= set(self.full.clauses)
        self.problem = self._reveal_more(solution)
        return self.problem
