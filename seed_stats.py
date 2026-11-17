#!/usr/bin/env python3
"""Parvis jämförelse av två evolutionslägen över många frön.

    python seed_stats.py baldwin none 1 2 3 4 5 6 7 8 9 10

Frö 1 heter runs/evo-<läge> (runs/evo för none), övriga runs/evo-<läge>-s<frö>.
Skriver medianer, parat t-test, teckentest och reparationsgenen per frö.
"""
import json
import math
import statistics as st
import sys
from pathlib import Path

import numpy as np

from antcomputer.world import IN_NAMES, OUT_NAMES


def path(mode, seed):
    base = "evo" if mode == "none" else f"evo-{mode}"
    return Path("runs") / (base if seed == 1 else f"{base}-s{seed}")


def run(mode, seed):
    d = path(mode, seed)
    log = json.loads((d / "evolution.json").read_text())["log"]
    q = np.load(d / f"best_queen_gen{log[-1]['gen']:03d}.npy")
    gene = float(q[OUT_NAMES.index("deposit_clay"), IN_NAMES.index("last_clause_dead")])
    return dict(n=log[-1]["n"], solved=sum(r["total_solved"] for r in log), gene=gene)


def t_cdf(t, df):
    """P(T <= t) för Students t, via den regulariserade ofullständiga betafunktionen (numerisk integration)."""
    xs = np.linspace(0, abs(t), 20001)
    pdf = math.gamma((df + 1) / 2) / (math.sqrt(df * math.pi) * math.gamma(df / 2)) * (1 + xs ** 2 / df) ** (-(df + 1) / 2)
    half = float(np.trapezoid(pdf, xs)) if hasattr(np, "trapezoid") else float(np.trapz(pdf, xs))
    return 0.5 + math.copysign(half, t)


def main():
    a, b, *seeds = sys.argv[1:]
    seeds = [int(s) for s in seeds]
    rows = [(s, run(a, s), run(b, s)) for s in seeds if (path(a, s) / "evolution.json").exists()
            and (path(b, s) / "evolution.json").exists()]
    L = [f"| frö | {a}: storlek | {a}: lösta | {b}: storlek | {b}: lösta | reparationsgen {a} / {b} |",
         "|---|---|---|---|---|---|"]
    for s, x, y in rows:
        L.append(f"| {s} | {x['n']} | {x['solved']} | {y['n']} | {y['solved']} | {x['gene']:+.1f} / {y['gene']:+.1f} |")
    k = len(rows)
    med = lambda m, i: st.median(r[i][m] for r in rows)
    L.append(f"| **median** | **{med('n', 1)}** | **{med('solved', 1)}** | **{med('n', 2)}** | **{med('solved', 2)}** | "
             f"**{med('gene', 1):+.1f} / {med('gene', 2):+.1f}** |")
    L.append("")
    for m, label in (("solved", "lösta problem"), ("n", "nådd storlek"), ("gene", "reparationsgen")):
        d = [x[m] - y[m] for _, x, y in rows]
        wins = sum(v > 0 for v in d)
        losses = sum(v < 0 for v in d)
        nn = wins + losses
        sign_p = min(1.0, 2 * sum(math.comb(nn, i) for i in range(max(wins, losses), nn + 1)) / 2 ** nn) if nn else 1.0
        sd = st.stdev(d) if k > 1 else 0
        if sd > 0:
            t = st.mean(d) / (sd / math.sqrt(k))
            tp = 2 * (1 - t_cdf(abs(t), k - 1))
            ttxt = f"t = {t:.2f}, p ≈ {tp:.3f}"
        else:
            ttxt = "—"
        L.append(f"* **{label}:** {a} bättre i {wins} av {k} frön, sämre i {losses}. Medelskillnad "
                 f"{st.mean(d):+.1f}. Parat t-test {ttxt}. Teckentest p ≈ {sign_p:.3f}.")
    print("\n".join(L))


if __name__ == "__main__":
    main()
