#!/usr/bin/env python3
"""Det öppna oraklet: kända problem, men oraklet vet inte om det finns något svar.

Oraklet ger bara kraven och betalar mat efter hur många som är uppfyllda, som
alltid. Det vet inte om problemet går att lösa och ger därför aldrig upp.
Vi har facit (lösbart/omöjligt och bästa möjliga antal uppfyllda krav, räknat
med en riktig SAT-lösare), men det används bara i analysen efteråt.

    python open_oracle.py --name oppet
    python open_oracle.py --name snabb --budget 5000 --only Schur

Arvsmassor som testas: instinkter, plus de .npy-filer som finns (evolverade
drottningar och den handgjorda reparatören som mätsticka).
"""
import argparse
import contextlib
import json
import os
import statistics
from multiprocessing import Pool
from pathlib import Path

import numpy as np

from antcomputer.baselines import walksat
from antcomputer.catalog import catalog
from antcomputer.world import Colony, Params

GENOMES = {
    "instinkt": None,
    "evolverad": "runs/evo/best_queen_workers.npy",
    "evolverad utan instinkter": "runs/evo-blank/best_queen_workers.npy",
    "handgjord reparatör": "runs/handgjord/reparatorer.npy",
}


def optimum(p):
    """Facit: lösbart? och högsta möjliga antal uppfyllda krav. Når aldrig myrorna."""
    try:
        from pysat.examples.rc2 import RC2
        from pysat.formula import WCNF
        from pysat.solvers import Cadical153
    except ImportError:
        return None, None
    with Cadical153(bootstrap_with=[list(c) for c in p.clauses]) as s:
        if s.solve():
            return True, len(p.clauses)
    w = WCNF()
    for c in p.clauses:
        w.append(list(c), weight=1)
    with RC2(w) as r:
        r.compute()
        return False, len(p.clauses) - r.cost


def job(args):
    idx, label, path, budget, seed, overrides = args
    p = catalog()[idx]
    params = Params(**overrides)
    rng = np.random.default_rng(seed)
    founders = None
    if path:
        G = np.load(path)
        founders = G[rng.integers(0, len(G), params.pop_init)] + rng.normal(0, 0.05, (params.pop_init,) + G.shape[1:])
    col = Colony(p, params, rng, founders=founders)
    m = len(p.clauses)
    best, best_t, held = -1, 0, 0
    flips_q, pops_q, sats_q = [], [], []
    solved_t, answer, verified = None, None, False
    flips = 0
    for t in range(1, budget + 1):
        s = col.step()
        flips += s["flips"]
        if s["n_sat"] > best:
            best, best_t = s["n_sat"], t
        if t > budget * 0.75:
            flips_q.append(s["flips"])
            pops_q.append(s["pop"])
            sats_q.append(s["n_sat"])
        held = held + 1 if s["all_sat"] else 0
        if held >= 20:
            verified, answer = p.verify(col.assignment())
            solved_t = t
            break
        if col.population == 0:
            break
    return dict(idx=idx, genome=label, solved=solved_t is not None, verified=verified, answer=answer,
                solve_tick=solved_t, flips=flips, best=best, best_tick=best_t, m=m,
                extinct=col.population == 0, late_flips_per_tick=statistics.mean(flips_q) if flips_q else None,
                late_pop=statistics.mean(pops_q) if pops_q else col.population,
                late_sat=statistics.mean(sats_q) / m if sats_q else None)


def parse_params(items):
    out = {}
    for it in items or []:
        k, v = it.split("=", 1)
        if not hasattr(Params(), k):
            raise SystemExit(f"okänd parameter: {k}")
        out[k] = type(getattr(Params(), k))(v)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--name", required=True)
    ap.add_argument("--budget", type=int, default=40000)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--only", default="", help="kör bara problem vars namn innehåller texten")
    ap.add_argument("--workers", type=int, default=os.cpu_count())
    ap.add_argument("--param", action="append", help="NAMN=VÄRDE, ändra en vikt i världen")
    ap.add_argument("--genomes", nargs="*", help="bara dessa arvsmassor (namn ur GENOMES)")
    a = ap.parse_args()
    overrides = parse_params(a.param)

    probs = catalog()
    idxs = [i for i, p in enumerate(probs) if a.only.lower() in p.name.lower()]
    genomes = {k: v for k, v in GENOMES.items() if (v is None or Path(v).exists())
               and (not a.genomes or k in a.genomes)}
    jobs = [(i, k, v, a.budget, a.seed, overrides) for i in idxs for k, v in genomes.items()]
    jobs.sort(key=lambda j: -len(probs[j[0]].clauses))  # stora först, för jämnare last
    results = []
    with Pool(a.workers) as pool:
        for r in pool.imap_unordered(job, jobs):
            results.append(r)
            print(f"klar: {probs[r['idx']].name} / {r['genome']}: "
                  f"{'LÖST' if r['solved'] else 'bäst ' + str(r['best']) + '/' + str(r['m'])}", flush=True)

    facit = {}
    for i in idxs:
        p = probs[i]
        sat, opt = optimum(p)
        ws = None
        if p.meta["truth"] == "lösbart":
            with contextlib.suppress(Exception):
                res = [walksat(p, max_flips=1_000_000, seed=s) for s in range(5)]
                ws = statistics.median([float("inf") if r is None else r for r in res])
        facit[i] = dict(truth=p.meta["truth"], sat=sat, optimum=opt, walksat=ws)

    names = list(genomes)
    L = [f"# Det öppna oraklet `{a.name}`", "",
         "Oraklet visste inte om problemen gick att lösa. Facit (kolumnerna *facit* och *bästa möjliga*) "
         "räknades ut i efterhand med en riktig SAT-lösare och nådde aldrig myrorna. "
         f"Varje koloni fick högst {a.budget} tick.", "",
         "Cell: **LÖST** (verifierat, tick) eller bästa antal uppfyllda krav kolonin nådde. "
         "★ = nådde bästa möjliga på ett omöjligt problem.", "",
         "| problem | facit | bästa möjliga | WalkSAT (flips) | " + " | ".join(names) + " |",
         "|" + "---|" * (4 + len(names))]
    by = {(r["idx"], r["genome"]): r for r in results}
    for i in idxs:
        p, f = probs[i], facit[i]
        cells = []
        for g in names:
            r = by[(i, g)]
            if r["solved"]:
                cells.append(f"**LÖST** (t={r['solve_tick']})" + ("" if r["verified"] else " EJ VERIFIERAT!"))
            else:
                star = " ★" if f["truth"] == "omöjligt" and r["best"] == f["optimum"] else ""
                cells.append(f"{r['best']}/{r['m']}{star}" + (" †" if r["extinct"] else ""))
        ws = "—" if f["walksat"] is None else ("—" if f["walksat"] == float("inf") else f"{f['walksat']:.0f}")
        L.append(f"| {p.name} | {f['truth']} | {f['optimum']}/{len(p.clauses)} | {ws} | " + " | ".join(cells) + " |")
    L += ["", "† = kolonin dog ut.", "",
          "## Vad gör kolonierna när det är omöjligt?", "",
          "Sista fjärdedelen av körningen, för kolonier som inte löste problemet. "
          "*Flips per tick* visar hur mycket de fortfarande ändrar sitt svar.", "",
          "| facit | antal körningar | befolkning | andel krav uppfyllda | flips per tick | andel som nådde bästa möjliga |",
          "|---|---|---|---|---|---|"]
    for truth in ("lösbart", "omöjligt"):
        rs = [r for r in results if facit[r["idx"]]["truth"] == truth and not r["solved"] and r["late_sat"] is not None]
        if rs:
            at_opt = sum(r["best"] == facit[r["idx"]]["optimum"] for r in rs)
            L.append(f"| {truth} (olösta) | {len(rs)} | {statistics.mean(r['late_pop'] for r in rs):.0f} | "
                     f"{statistics.mean(r['late_sat'] for r in rs):.3f} | "
                     f"{statistics.mean(r['late_flips_per_tick'] for r in rs):.2f} | {at_opt}/{len(rs)} |")
    out = Path("runs") / a.name
    out.mkdir(parents=True, exist_ok=True)
    (out / "open_oracle.md").write_text("\n".join(L) + "\n")
    (out / "open_oracle.json").write_text(json.dumps(dict(results=results, facit={str(k): v for k, v in facit.items()}),
                                                     indent=1, ensure_ascii=False, default=str))
    print("\n".join(L))


if __name__ == "__main__":
    main()
