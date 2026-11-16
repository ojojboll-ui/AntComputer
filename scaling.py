#!/usr/bin/env python3
"""Skalningsexperiment: hur växer svårigheten när problemen blir större?

Det här är kärnan i P mot NP-frågan i mätbar form. Alla kända metoder kräver en
tid som växer exponentiellt på svåra slumpade 3-SAT-problem (runt 4,26 krav per
variabel). Om myrornas kurva växer långsammare än de klassiska metodernas,
även om den börjar högre, vore det ett verkligt fynd.

Exempel:
    python scaling.py --name skala
    python scaling.py --name skala --genomes runs/trana/genomes_colony0.npy
    python scaling.py --name snabb --sizes 10 15 20 --instances 6 --budget 20000

Varje instans är ett nytt slumpat 3-SAT-problem (inte planterat) som WalkSAT
bevisligen kan lösa. Det är samma filtrering som i standardtestsviterna (SATLIB):
osatisfierbara instanser kan inte användas för att mäta tid till lösning.
"""
import argparse
import functools
import json
import math
import os
import random
import statistics
from multiprocessing import Pool
from pathlib import Path

import numpy as np

from antcomputer.baselines import random_walk, walksat
from antcomputer.problems import Problem
from antcomputer.world import Colony, Params


def random_3sat(n: int, ratio: float, rng: random.Random) -> Problem:
    m = round(ratio * n)
    clauses = []
    seen = set()
    while len(clauses) < m:
        vs = rng.sample(range(1, n + 1), 3)
        c = tuple(sorted(v if rng.random() < 0.5 else -v for v in vs))
        if c not in seen:
            seen.add(c)
            clauses.append(c)

    def verify(a):
        ok = all(any((lit > 0) == a[abs(lit) - 1] for lit in c) for c in clauses)
        return ok, "".join("1" if x else "0" for x in a)
    return Problem(f"slump-3-SAT n={n} m={m}", n, clauses, verify)


@functools.lru_cache(maxsize=256)
def satisfiable_instance(n: int, ratio: float, seed: int, max_flips: int = 2_000_000) -> Problem:
    """Slumpa tills WalkSAT hittar en lösning (osatisfierbara instanser kastas)."""
    rng = random.Random(seed)
    while True:
        p = random_3sat(n, ratio, rng)
        if walksat(p, max_flips=max_flips, seed=seed) is not None:
            return p


def run_ants(p: Problem, genomes, budget: int, seed: int, hold: int = 20) -> dict:
    params = Params()
    rng = np.random.default_rng(seed)
    founders = None
    if genomes is not None:
        idx = rng.integers(0, len(genomes), params.pop_init)
        founders = genomes[idx] + rng.normal(0, 0.05, genomes[idx].shape)
    col = Colony(p, params, rng, founders=founders)
    flips, held = 0, 0
    for t in range(1, budget + 1):
        s = col.step()
        flips += s["flips"]
        held = held + 1 if s["all_sat"] else 0
        if held >= hold:
            ok, _ = p.verify(col.assignment())
            return dict(solved=True, verified=ok, ticks=t, flips=flips)
        if col.population == 0:
            break
    return dict(solved=False, verified=False, ticks=None, flips=None)


def job(args):
    n, k, ratio, budget, genome_paths, baseline_runs = args
    p = satisfiable_instance(n, ratio, seed=1000 * n + k)
    out = dict(n=n, instance=k)
    for name, fn in (("walksat", walksat), ("random_walk", random_walk)):
        res = [fn(p, max_flips=1_000_000, seed=s) for s in range(baseline_runs)]
        out[name] = statistics.median([math.inf if r is None else r for r in res])
    out["ants_instinct"] = run_ants(p, None, budget, seed=k)
    for label, path in genome_paths.items():
        out[f"ants_{label}"] = run_ants(p, np.load(path), budget, seed=k)
    return out


def median_censored(xs):
    m = statistics.median([math.inf if x is None else x for x in xs])
    return None if m == math.inf else m


def fit(sizes, meds):
    """Anpassa log(median) mot n (exponentiell) och mot log n (polynomiell)."""
    pts = [(n, m) for n, m in zip(sizes, meds) if m is not None and m > 0]
    if len(pts) < 3:
        return None
    x = np.array([n for n, _ in pts], float)
    y = np.log(np.array([m for _, m in pts], float))
    b_exp, a_exp = np.polyfit(x, y, 1)
    b_pol, a_pol = np.polyfit(np.log(x), y, 1)
    r_exp = np.corrcoef(x, y)[0, 1] ** 2
    r_pol = np.corrcoef(np.log(x), y)[0, 1] ** 2
    return dict(growth_per_var=float(np.exp(b_exp)), r2_exp=float(r_exp), degree=float(b_pol), r2_poly=float(r_pol),
                sizes_used=[int(n) for n, _ in pts])


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--name", required=True)
    ap.add_argument("--sizes", type=int, nargs="+", default=[10, 15, 20, 25, 30, 40])
    ap.add_argument("--instances", type=int, default=10)
    ap.add_argument("--ratio", type=float, default=4.26)
    ap.add_argument("--budget", type=int, default=40000, help="max tick för myrorna per instans")
    ap.add_argument("--genomes", nargs="*", default=[], help="npy-filer med evolverad arvsmassa")
    ap.add_argument("--baseline-runs", type=int, default=10)
    ap.add_argument("--workers", type=int, default=os.cpu_count())
    a = ap.parse_args()

    genome_paths = {Path(g).parent.name + ("" if len(a.genomes) == 1 else "_" + Path(g).stem): g for g in a.genomes}
    jobs = [(n, k, a.ratio, a.budget, genome_paths, a.baseline_runs) for n in a.sizes for k in range(a.instances)]
    results = []
    with Pool(a.workers) as pool:
        for r in pool.imap_unordered(job, jobs):
            results.append(r)
            print(f"klar: n={r['n']} instans {r['instance']}", flush=True)

    ant_keys = ["ants_instinct"] + [f"ants_{k}" for k in genome_paths]
    L = [f"# Skalning `{a.name}`", "",
         f"Slumpad 3-SAT med {a.ratio} krav per variabel, {a.instances} lösbara instanser per storlek. "
         f"Myrorna får högst {a.budget} tick per instans. Värden är medianer i antal variabelbyten (flips); "
         "en olöst instans räknas som oändligt lång (— = median olöst).", "",
         "| n | WalkSAT | slumpvandring | " + " | ".join(f"{k[5:]} (flips)" for k in ant_keys)
         + " | " + " | ".join(f"{k[5:]} lösta" for k in ant_keys) + " |",
         "|" + "---|" * (3 + 2 * len(ant_keys))]
    series = {k: [] for k in ["walksat", "random_walk"] + ant_keys}
    for n in a.sizes:
        rs = [r for r in results if r["n"] == n]
        row = [str(n)]
        for k in ("walksat", "random_walk"):
            m = statistics.median(r[k] for r in rs)
            m = None if m == math.inf else m
            series[k].append(m)
            row.append("—" if m is None else f"{m:.0f}")
        solved_cells = []
        for k in ant_keys:
            m = median_censored([r[k]["flips"] for r in rs])
            series[k].append(m)
            row.append("—" if m is None else f"{m:.0f}")
            ok = sum(r[k]["solved"] for r in rs)
            bad = sum(r[k]["solved"] and not r[k]["verified"] for r in rs)
            solved_cells.append(f"{ok}/{len(rs)}" + (f" ({bad} EJ verifierade!)" if bad else ""))
        L.append("| " + " | ".join(row + solved_cells) + " |")
    L += ["", "## Tillväxt", "",
          "*Faktor per variabel*: hur mycket svårare varje extra variabel gör problemet, om tillväxten är exponentiell. "
          "*Grad*: exponenten om den i stället är polynomiell (n^grad). R² visar vilken modell som passar bäst. "
          "Med så här få storlekar är siffrorna en fingervisning, inte ett bevis.", "",
          "| metod | faktor per variabel | R² exp | grad | R² poly | storlekar |", "|---|---|---|---|---|---|"]
    fits = {}
    for k, meds in series.items():
        f = fit(a.sizes, meds)
        fits[k] = f
        if f:
            L.append(f"| {k} | {f['growth_per_var']:.3f} | {f['r2_exp']:.2f} | {f['degree']:.2f} | {f['r2_poly']:.2f} | "
                     f"{f['sizes_used']} |")
        else:
            L.append(f"| {k} | för få lösta storlekar | | | | |")
    out = Path("runs") / a.name
    out.mkdir(parents=True, exist_ok=True)
    (out / "scaling.md").write_text("\n".join(L) + "\n")
    (out / "scaling.json").write_text(json.dumps(dict(results=results, fits=fits, args=vars(a)), indent=1, default=str))
    print("\n".join(L))


if __name__ == "__main__":
    main()
