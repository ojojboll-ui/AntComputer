"""Katalog med kända matematiska problem för ett orakel som inte vet svaret.

Oraklet får bara problemet (kraven) och kan kontrollera ett föreslaget svar.
Det vet INTE om det finns något svar. Vi människor vet det för de här problemen
(`truth` = "lösbart" eller "omöjligt"), men den informationen används bara i
efterhand, i analysen, och når aldrig oraklet eller myrorna.
"""
from __future__ import annotations

import itertools

from .problems import Problem, factoring


def _cnf_problem(name: str, n_vars: int, clauses, truth: str, family: str, decode=None, **meta) -> Problem:
    clauses = list(dict.fromkeys(tuple(sorted(c)) for c in clauses))

    def verify(a):
        ok = all(any((lit > 0) == a[abs(lit) - 1] for lit in c) for c in clauses)
        return ok, decode(a) if decode else "".join("1" if x else "0" for x in a[:n_vars])
    return Problem(name, n_vars, clauses, verify, meta=dict(meta, truth=truth, family=family))


def ramsey(n: int, s: int, t: int, truth: str) -> Problem:
    """Färga linjerna i K_n röda/blå utan röd K_s och utan blå K_t."""
    edges = list(itertools.combinations(range(n), 2))
    var = {e: i + 1 for i, e in enumerate(edges)}  # sann = röd
    clauses = []
    for S in itertools.combinations(range(n), s):
        clauses.append(tuple(-var[e] for e in itertools.combinations(S, 2)))   # inte alla röda
    for T in itertools.combinations(range(n), t):
        clauses.append(tuple(var[e] for e in itertools.combinations(T, 2)))    # inte alla blå
    return _cnf_problem(f"Ramsey: K{n} utan röd K{s} och blå K{t}", len(edges), clauses, truth, "ramsey")


def schur(n: int, k: int, truth: str) -> Problem:
    """Dela {1..n} i k färger så att inget x + y = z har alla tre i samma färg."""
    def v(i, c):
        return (i - 1) * k + c + 1
    clauses = [tuple(v(i, c) for c in range(k)) for i in range(1, n + 1)]  # varje tal får en färg
    for x in range(1, n + 1):
        for y in range(x, n + 1 - x):
            z = x + y
            for c in range(k):
                clauses.append(tuple({-v(x, c), -v(y, c), -v(z, c)}))
    return _cnf_problem(f"Schur: 1..{n} i {k} färger", n * k, clauses, truth, "schur")


def van_der_waerden(n: int, length: int, truth: str) -> Problem:
    """Färga {1..n} i två färger utan enfärgad aritmetisk följd av given längd."""
    clauses = []
    for a in range(1, n + 1):
        for d in range(1, n):
            ap = [a + i * d for i in range(length)]
            if ap[-1] > n:
                break
            clauses.append(tuple(ap))
            clauses.append(tuple(-x for x in ap))
    return _cnf_problem(f"van der Waerden: 1..{n} utan enfärgad följd av längd {length}", n, clauses, truth,
                        "van der Waerden")


def pigeonhole(pigeons: int, holes: int) -> Problem:
    """Placera duvor i hål, högst en per hål."""
    def v(p, h):
        return p * holes + h + 1
    clauses = [tuple(v(p, h) for h in range(holes)) for p in range(pigeons)]
    for h in range(holes):
        for p, q in itertools.combinations(range(pigeons), 2):
            clauses.append((-v(p, h), -v(q, h)))
    truth = "lösbart" if pigeons <= holes else "omöjligt"
    return _cnf_problem(f"Duvslag: {pigeons} duvor i {holes} hål", pigeons * holes, clauses, truth, "duvslag")


PETERSEN = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 0), (0, 5), (1, 6), (2, 7), (3, 8), (4, 9),
            (5, 7), (7, 9), (9, 6), (6, 8), (8, 5)]


def coloring(name: str, n: int, edges, k: int, truth: str) -> Problem:
    def v(i, c):
        return i * k + c + 1
    clauses = [tuple(v(i, c) for c in range(k)) for i in range(n)]
    for i in range(n):
        for c, d in itertools.combinations(range(k), 2):
            clauses.append((-v(i, c), -v(i, d)))
    for a, b in edges:
        for c in range(k):
            clauses.append((-v(a, c), -v(b, c)))
    return _cnf_problem(f"Färgning: {name} med {k} färger", n * k, clauses, truth, "graffärgning")


def queens(n: int) -> Problem:
    def v(r, c):
        return r * n + c + 1
    clauses = [tuple(v(r, c) for c in range(n)) for r in range(n)]
    cells = [(r, c) for r in range(n) for c in range(n)]
    for (r1, c1), (r2, c2) in itertools.combinations(cells, 2):
        if r1 == r2 or c1 == c2 or abs(r1 - r2) == abs(c1 - c2):
            clauses.append((-v(r1, c1), -v(r2, c2)))
    truth = "omöjligt" if n in (2, 3) else "lösbart"
    return _cnf_problem(f"{n} damer på {n}x{n}-bräde", n * n, clauses, truth, "damer")


def factor_problem(N: int, truth: str) -> Problem:
    p = factoring(N)
    p.meta.update(truth=truth, family="faktorisering")
    p.name = f"Faktorisera {N}" + (" (primtal?)" if truth == "omöjligt" else "")
    return p


def catalog() -> list[Problem]:
    """Par av närliggande problem: ett lösbart och ett bevisat omöjligt, där det går."""
    return [
        ramsey(5, 3, 3, "lösbart"), ramsey(6, 3, 3, "omöjligt"),
        ramsey(8, 3, 4, "lösbart"), ramsey(9, 3, 4, "omöjligt"),
        ramsey(17, 4, 4, "lösbart"),
        schur(4, 2, "lösbart"), schur(5, 2, "omöjligt"),
        schur(13, 3, "lösbart"), schur(14, 3, "omöjligt"),
        van_der_waerden(8, 3, "lösbart"), van_der_waerden(9, 3, "omöjligt"),
        van_der_waerden(34, 4, "lösbart"), van_der_waerden(35, 4, "omöjligt"),
        pigeonhole(4, 4), pigeonhole(5, 4),
        coloring("Petersengrafen", 10, PETERSEN, 3, "lösbart"),
        coloring("Petersengrafen", 10, PETERSEN, 2, "omöjligt"),
        queens(8), queens(3),
        factor_problem(15, "lösbart"), factor_problem(13, "omöjligt"),
    ]
