#!/usr/bin/env python3
"""Vikter mot krav: vilka inställningar av världens ekonomi passar vilken problemfamilj?

Kör hela katalogen (det öppna oraklet) med flera uppsättningar vikter och
sammanfattar per problemfamilj: andel lösbara som löstes, andel omöjliga där
bästa möjliga nåddes, och andel kolonier som dog ut. Facit används bara i
analysen, precis som i open_oracle.py.

    python weights.py --name vikter
    python weights.py --name snabb --budget 3000 --only Schur
"""
import argparse
import json
import os
import statistics
from collections import defaultdict
from multiprocessing import Pool
from pathlib import Path

from antcomputer.catalog import catalog
from open_oracle import GENOMES, job, optimum

# Varje uppsättning ändrar några vikter från standardvärdena i world.Params.
CONFIGS = {
    "standard": {},
    "mat per krav 0,05": dict(food_per_clause=0.05),
    "mat per krav 0,2": dict(food_per_clause=0.2),
    "mat från 60 %": dict(sat_floor=0.6),
    "mat först från 90 %": dict(sat_floor=0.9),
    "låg tröghet (1)": dict(flip_margin=1.0),
    "hög tröghet (4)": dict(flip_margin=4.0),
    "billig myra": dict(metabolism=0.005, birth_cost=0.5),
    "mat per krav 0,05 + från 60 %": dict(food_per_clause=0.05, sat_floor=0.6),
    "mat per krav 0,05 + låg tröghet": dict(food_per_clause=0.05, flip_margin=1.0),
}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--name", required=True)
    ap.add_argument("--budget", type=int, default=20000)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--only", default="")
    ap.add_argument("--genomes", nargs="*", default=["evolverad", "handgjord reparatör"])
    ap.add_argument("--workers", type=int, default=os.cpu_count())
    a = ap.parse_args()

    probs = catalog()
    idxs = [i for i, p in enumerate(probs) if a.only.lower() in p.name.lower()]
    genomes = {k: GENOMES[k] for k in a.genomes if GENOMES[k] is None or Path(GENOMES[k]).exists()}
    jobs = [(i, g, path, a.budget, a.seed, ov, cname)
            for cname, ov in CONFIGS.items() for i in idxs for g, path in genomes.items()]
    jobs.sort(key=lambda j: -len(probs[j[0]].clauses))
    facit = {i: optimum(probs[i]) for i in idxs}

    results = []
    with Pool(a.workers) as pool:
        for r in pool.imap_unordered(run, jobs):
            results.append(r)
            print(f"klar {len(results)}/{len(jobs)}: {r['config']} / {probs[r['idx']].name} / {r['genome']}", flush=True)

    fams = sorted({probs[i].meta["family"] for i in idxs})
    cell = defaultdict(lambda: dict(solv=0, solv_n=0, opt=0, imp_n=0, dead=0, n=0))
    for r in results:
        p = probs[r["idx"]]
        _, opt = facit[r["idx"]]
        for key in ((r["config"], p.meta["family"]), (r["config"], "ALLA")):
            c = cell[key]
            c["n"] += 1
            c["dead"] += r["extinct"]
            if p.meta["truth"] == "lösbart":
                c["solv_n"] += 1
                c["solv"] += r["solved"]
            else:
                c["imp_n"] += 1
                c["opt"] += r["best"] == opt

    def fmt(c):
        s = f"{c['solv']}/{c['solv_n']}" if c["solv_n"] else "–"
        o = f"{c['opt']}/{c['imp_n']}" if c["imp_n"] else "–"
        return f"{s} · {o} · {c['dead']}†"

    L = [f"# Vikter mot krav `{a.name}`", "",
         f"Hela katalogen med {len(CONFIGS)} uppsättningar vikter, arvsmassor: {', '.join(genomes)}. "
         f"Högst {a.budget} tick per koloni, frö {a.seed}.", "",
         "Cell: **lösta lösbara · omöjliga där bästa möjliga nåddes · utdöda kolonier**.", "",
         "| vikter | ALLA | " + " | ".join(fams) + " |", "|" + "---|" * (2 + len(fams))]
    ranking = sorted(CONFIGS, key=lambda k: (-(cell[(k, 'ALLA')]["solv"] + cell[(k, 'ALLA')]["opt"]),
                                             cell[(k, 'ALLA')]["dead"]))
    for k in ranking:
        L.append(f"| {k} | **{fmt(cell[(k, 'ALLA')])}** | " + " | ".join(fmt(cell[(k, f)]) for f in fams) + " |")
    L += ["", "## Bästa vikter per familj", "", "| familj | bästa vikter | resultat |", "|---|---|---|"]
    for f in fams:
        best = max(CONFIGS, key=lambda k: (cell[(k, f)]["solv"] + cell[(k, f)]["opt"], -cell[(k, f)]["dead"]))
        L.append(f"| {f} | {best} | {fmt(cell[(best, f)])} |")
    L += ["", "Ett frö per kombination: skillnader på en eller två körningar är brus. "
          "Använd tabellen för att välja vikter att testa vidare, inte som slutsats."]
    out = Path("runs") / a.name
    out.mkdir(parents=True, exist_ok=True)
    (out / "weights.md").write_text("\n".join(L) + "\n")
    (out / "weights.json").write_text(json.dumps(dict(configs=CONFIGS, results=results), indent=1,
                                                 ensure_ascii=False, default=str))
    print("\n".join(L))


def run(args):
    *base, cname = args
    r = job(tuple(base))
    r["config"] = cname
    return r


if __name__ == "__main__":
    main()
