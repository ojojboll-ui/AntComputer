"""Matematiska problem som oraklet kan ställa.

Alla problem uttrycks som CNF (konjunktiv normalform): en lista av klausuler där
varje klausul är en tupel av DIMACS-literaler (+v betyder variabel v sann, -v
betyder falsk, variabler numreras från 1). Varje problem har dessutom en
oberoende verifierare som kontrollerar svaret i problemets egna termer
(t.ex. p*q == N), så att vi aldrig litar blint på simuleringen.
"""
from __future__ import annotations

import itertools
import random
from dataclasses import dataclass, field
from typing import Callable, Optional


@dataclass
class Problem:
    name: str
    n_vars: int
    clauses: list[tuple[int, ...]]
    # verify(assignment) -> (ok, human readable answer). assignment[i] = värdet på variabel i+1
    verify: Callable[[list[bool]], tuple[bool, str]] = field(repr=False)
    meta: dict = field(default_factory=dict)

    def n_satisfied(self, assignment: list[bool]) -> int:
        return sum(any((lit > 0) == assignment[abs(lit) - 1] for lit in c) for c in self.clauses)

    def is_model(self, assignment: list[bool]) -> bool:
        return self.n_satisfied(assignment) == len(self.clauses)


# --------------------------------------------------------------------------
# Slumpmässig 3-SAT med planterad lösning (garanterat lösbar)
# --------------------------------------------------------------------------

def _random_clause(n_vars: int, planted: list[bool], rng: random.Random, k: int = 3) -> tuple[int, ...]:
    while True:
        vs = rng.sample(range(1, n_vars + 1), k)
        clause = tuple(v if rng.random() < 0.5 else -v for v in vs)
        if any((lit > 0) == planted[abs(lit) - 1] for lit in clause):
            return clause


def planted_3sat(n_vars: int, ratio: float, rng: random.Random, planted: Optional[list[bool]] = None,
                 base: Optional[Problem] = None) -> Problem:
    """Skapa (eller bygg ut) en planterad 3-SAT-instans.

    Om `base` ges behålls alla dess klausuler och variabler; nya variabler och
    klausuler läggs till. Det är så oraklet "skärper kraven" utan att riva det
    kolonin redan byggt.
    """
    if planted is None:
        planted = [rng.random() < 0.5 for _ in range(n_vars)]
    clauses = list(base.clauses) if base else []
    seen = set(clauses)
    target = int(round(ratio * n_vars))
    while len(clauses) < target:
        c = _random_clause(n_vars, planted, rng)
        key = tuple(sorted(c))
        if key in seen:
            continue
        seen.add(key)
        clauses.append(key)

    def verify(a: list[bool]) -> tuple[bool, str]:
        ok = all(any((lit > 0) == a[abs(lit) - 1] for lit in c) for c in clauses)
        bits = "".join("1" if x else "0" for x in a[:n_vars])
        return ok, f"tilldelning {bits}"

    return Problem(f"3-SAT n={n_vars} m={len(clauses)}", n_vars, clauses, verify,
                   meta={"planted": planted, "ratio": ratio})


def with_blocking_clause(p: Problem, assignment: list[bool]) -> Problem:
    """Förbjud en redan funnen lösning, så att kolonin måste hitta en ny."""
    block = tuple(sorted(-(i + 1) if assignment[i] else (i + 1) for i in range(p.n_vars)))
    clauses = p.clauses + [block]
    found = p.meta.get("found", 0) + 1

    def verify(a: list[bool]) -> tuple[bool, str]:
        ok = all(any((lit > 0) == a[abs(lit) - 1] for lit in c) for c in clauses)
        return ok, "lösning #%d: %s" % (found + 1, "".join("1" if x else "0" for x in a[:p.n_vars]))

    meta = dict(p.meta, found=found)
    return Problem(f"{p.name.split(' [')[0]} [{found} lösningar spärrade]", p.n_vars, clauses, verify, meta)


# --------------------------------------------------------------------------
# Faktorisering kodad som en multiplikationskrets (Tseitin-kodning)
# --------------------------------------------------------------------------

class CircuitBuilder:
    """Bygger CNF för en boolesk krets och kan även utvärdera den framåt."""

    def __init__(self) -> None:
        self.n = 0
        self.clauses: list[tuple[int, ...]] = []
        self.gates: list[tuple[int, Callable[..., bool], tuple[int, ...]]] = []

    def new_var(self) -> int:
        self.n += 1
        return self.n

    def gate(self, fn: Callable[..., bool], inputs: tuple[int, ...]) -> int:
        """Ny variabel z med z <-> fn(inputs), via sanningstabell."""
        z = self.new_var()
        for vals in itertools.product([False, True], repeat=len(inputs)):
            out = fn(*vals)
            clause = tuple((-x if v else x) for x, v in zip(inputs, vals)) + ((z,) if out else (-z,))
            self.clauses.append(clause)
        self.gates.append((z, fn, inputs))
        return z

    def evaluate(self, inputs: dict[int, bool]) -> list[bool]:
        val = dict(inputs)
        for z, fn, ins in self.gates:
            val[z] = fn(*(val[i] for i in ins))
        return [val.get(i, False) for i in range(1, self.n + 1)]


def _add_bits(cb: CircuitBuilder, x: list[Optional[int]], y: list[Optional[int]]) -> list[Optional[int]]:
    """Ripple-carry-addition; None betyder konstant 0."""
    out: list[Optional[int]] = []
    carry: Optional[int] = None
    for i in range(max(len(x), len(y))):
        bits = [b for b in (x[i] if i < len(x) else None, y[i] if i < len(y) else None, carry) if b is not None]
        if not bits:
            out.append(None)
            carry = None
        elif len(bits) == 1:
            out.append(bits[0])
            carry = None
        elif len(bits) == 2:
            out.append(cb.gate(lambda a, b: a != b, tuple(bits)))
            carry = cb.gate(lambda a, b: a and b, tuple(bits))
        else:
            out.append(cb.gate(lambda a, b, c: (a + b + c) % 2 == 1, tuple(bits)))
            carry = cb.gate(lambda a, b, c: (a + b + c) >= 2, tuple(bits))
    if carry is not None:
        out.append(carry)
    return out


def factoring(N: int, bits: Optional[int] = None) -> Problem:
    """Hitta p, q > 1 med p*q == N."""
    if bits is None:
        bits = N.bit_length() // 2 + 1
    cb = CircuitBuilder()
    a = [cb.new_var() for _ in range(bits)]  # p, minst signifikanta bit först
    b = [cb.new_var() for _ in range(bits)]  # q
    acc: list[Optional[int]] = []
    for j in range(bits):
        row: list[Optional[int]] = [None] * j + [cb.gate(lambda x, y: x and y, (a[i], b[j])) for i in range(bits)]
        acc = _add_bits(cb, acc, row)
    clauses = list(cb.clauses)
    width = max(len(acc), N.bit_length())
    for i in range(width):
        want = (N >> i) & 1
        lit = acc[i] if i < len(acc) else None
        if lit is None:
            if want:
                raise ValueError("för få bitar för N")
            continue
        clauses.append((lit,) if want else (-lit,))
    clauses.append(tuple(a[1:]))  # p >= 2
    clauses.append(tuple(b[1:]))  # q >= 2
    # ta bort dubbletter men behåll ordning
    clauses = list(dict.fromkeys(tuple(sorted(c)) for c in clauses))

    def decode(asg: list[bool]) -> tuple[int, int]:
        p = sum(1 << i for i, v in enumerate(a) if asg[v - 1])
        q = sum(1 << i for i, v in enumerate(b) if asg[v - 1])
        return p, q

    def verify(asg: list[bool]) -> tuple[bool, str]:
        p, q = decode(asg)
        return (p * q == N and p > 1 and q > 1), f"{N} = {p} x {q}"

    return Problem(f"faktorisera {N}", cb.n, clauses, verify,
                   meta={"N": N, "bits": bits, "p_vars": a, "q_vars": b, "builder": cb, "decode": decode})


def semiprimes(start: int = 15, limit: int = 10**9):
    """Halvprimtal (produkt av två primtal >1), i växande ordning."""
    def is_prime(k: int) -> bool:
        if k < 2:
            return False
        i = 2
        while i * i <= k:
            if k % i == 0:
                return False
            i += 1
        return True

    n = start
    while n < limit:
        if not is_prime(n):
            for d in range(2, int(n ** 0.5) + 1):
                if n % d == 0:
                    if is_prime(d) and is_prime(n // d):
                        yield n
                    break
        n += 1
