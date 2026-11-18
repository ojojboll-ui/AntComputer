#!/usr/bin/env python3
"""Äkta evolutionärt tryck: många kolonier, drottningar som bär arvet, nya prov varje generation.

Ingen knuff mot något svar. Det enda vi bestämmer är arenan:

* Varje koloni har en drottning. Arbetarna är hennes döttrar (drottningens gener
  plus liten variation). Arbetarna fortplantar sig aldrig.
* Varje generation lever alla kolonier lika länge (`--lifetime` tick) i en
  värld där oraklet ställer en ström av HELT NYA slumpade 3-SAT-problem på den
  svåra gränsen (4,26 krav per variabel). Varje löst problem ger bonusmat och
  ett nytt problem. Alla kolonier i en generation får samma problemström, och
  strömmen är ny varje generation, så det går inte att memorera något.
* Mat ger överlevnad, lösningar ger fortplantning: datorn "betalar" i nya
  drottningar. Fitness = antal lösta problem under livet, och vid lika avgör
  insamlad mat. (Med bara mat som fitness lönade det sig att INTE lösa: ett löst
  problem byts mot ett nytt där färre krav är uppfyllda, och matflödet rasar.)
* De bästa drottningarna överlever. Resten ersätts av döttrar till drottningar
  från den bästa halvan, ibland efter parning (blandade gener), alltid med mutationer.
* När minst hälften av kolonierna löser minst ett problem under sitt liv blir
  problemen större (`--dn` variabler till). Trycket ökar av sig självt.

Exempel:
    python evolve.py --name evo                       # med medfödda födosöksinstinkter
    python evolve.py --name evo-blank --blank-slate   # helt utan instinkter
    python evolve.py --name test --queens 8 --generations 3 --lifetime 2000
"""
import argparse
import json
import os
import random
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np

from antcomputer.world import Colony, Params, genome_shape, in_names, out_names, prior_genome
from scaling import satisfiable_instance


def live(args):
    """En kolonis liv. Returnerar fitness och vad som hände."""
    queen, n, ratio, lifetime, stream_seed, colony_seed, hold, mode, culture_seed = args
    flags = parse_mode(mode)
    params = Params(learning=bool(flags & {"baldwin", "lamarck"}), culture="culture" in flags)
    rng = np.random.default_rng(colony_seed)
    k = 0
    problem = satisfiable_instance(n, ratio, stream_seed * 1000 + k, 100_000)
    col = Colony(problem, params, rng, queen=queen, culture_seed=culture_seed)
    food = 0.0
    solved, held = 0, 0
    dep = dep_help = base_w = 0.0
    solve_ticks = []
    since = 0
    for t in range(1, lifetime + 1):
        s = col.step()
        food += s["delivered"]
        dep += s["deposits"]
        dep_help += s["deposits_helpful"]
        base_w += s["helpful_base"] * s["deposits"]
        held = held + 1 if s["all_sat"] else 0
        if held >= hold:
            ok, _ = problem.verify(col.assignment())
            if ok:
                solved += 1
                solve_ticks.append(t - since)
                food += params.jackpot
                col.store += params.jackpot
            k += 1
            problem = satisfiable_instance(n, ratio, stream_seed * 1000 + k, 100_000)
            col.set_problem(problem)
            held, since = 0, t
        if col.population == 0:
            break
    focus = (dep_help / dep) / (base_w / dep) if dep and base_w else None
    learned = col.G[col.alive].mean(axis=0) if col.population else queen
    return dict(fitness=solved * 100_000 + food, food=food, solved=solved, learned=learned, survived=col.population > 0, final_pop=col.population,
                solve_ticks=solve_ticks, repair_focus=focus, deposits_per_tick=dep / max(t, 1))


MODE_TOKENS = {"none", "baldwin", "lamarck", "culture", "heritage"}


def parse_mode(mode: str) -> set:
    """Lägen kan kombineras med +, t.ex. baldwin+culture eller culture+heritage."""
    flags = set(mode.split("+")) - {"none"}
    bad = flags - MODE_TOKENS
    if bad:
        raise SystemExit(f"okänt läge: {bad}; välj bland {sorted(MODE_TOKENS)}")
    if "heritage" in flags and "culture" not in flags:
        raise SystemExit("heritage (kulturarv) kräver culture")
    return flags


def reproduce(queens, fitness, rng, elite, sigma, mut_prob, crossover):
    """Returnerar nya drottningar, rangordningen och vilken drottning som är (första) förälder."""
    order = np.argsort(-np.asarray(fitness))
    ranked = queens[order]
    top = ranked[: max(2, len(queens) // 2)]
    new = [ranked[i].copy() for i in range(elite)]
    parents = [int(order[i]) for i in range(elite)]
    while len(new) < len(queens):
        ia = rng.integers(len(top))
        parents.append(int(order[ia]))
        a = top[ia]
        if rng.random() < crossover:  # bröllopsflykt: två drottningar blandar gener
            b = top[rng.integers(len(top))]
            child = np.where(rng.random(a.shape) < 0.5, a, b)
        else:
            child = a.copy()
        mask = rng.random(child.shape) < mut_prob
        child = child + mask * rng.normal(0, sigma, child.shape)
        new.append(child)
    return np.stack(new), order, parents


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--name", required=True)
    ap.add_argument("--queens", type=int, default=24)
    ap.add_argument("--generations", type=int, default=60)
    ap.add_argument("--lifetime", type=int, default=12000)
    ap.add_argument("--n0", type=int, default=10)
    ap.add_argument("--dn", type=int, default=2)
    ap.add_argument("--ratio", type=float, default=4.26)
    ap.add_argument("--raise-at", type=float, default=0.5, help="andel kolonier som måste lösa något före större problem")
    ap.add_argument("--elite", type=int, default=4)
    ap.add_argument("--sigma", type=float, default=0.2)
    ap.add_argument("--mut-prob", type=float, default=0.15)
    ap.add_argument("--crossover", type=float, default=0.5)
    ap.add_argument("--mode", default="none",
                    help="none: bara gener. baldwin: inlärning under livet, ej ärftlig. "
                         "lamarck: inlärt skrivs in i generna. culture: myrorna härmar varandra. "
                         "heritage: ny koloni ärver mor-kolonins kultur. Kombinera med +, t.ex. baldwin+culture")
    ap.add_argument("--mem", type=int, default=0, help="antal minnesceller per myra (0 = inget minne)")
    ap.add_argument("--blank-slate", action="store_true", help="drottningarna börjar utan några instinkter")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--workers", type=int, default=os.cpu_count())
    ap.add_argument("--resume", action="store_true",
                    help="fortsätt en avbruten körning från runs/<namn>/queens.npy och state.json")
    ap.add_argument("--resume-log", help="äldre körning utan state.json: utskriften (stdout-loggen) att läsa historiken från")
    a = ap.parse_args()

    flags = parse_mode(a.mode)
    rng = np.random.default_rng(a.seed)
    shape = genome_shape(a.mem)
    base = np.zeros(shape) if a.blank_slate else prior_genome(a.mem)
    queens = base[None] + rng.normal(0, 0.3, (a.queens,) + shape)
    out = Path("runs") / a.name
    out.mkdir(parents=True, exist_ok=True)
    n = a.n0
    cultures = [None] * a.queens
    log = []
    best_ever = None
    start = 0
    if a.resume:
        state = out / "state.json"
        if state.exists():
            log = json.loads(state.read_text())["log"]
        else:
            log = [json.loads(line) for line in Path(a.resume_log).read_text().splitlines() if line.startswith("{")]
        last = log[-1]
        start = last["gen"] + 1
        n = last["n"] + (a.dn if last["share_solving"] >= a.raise_at else 0)
        queens = np.load(out / "queens.npy")
        best_ever = np.load(out / f"best_queen_gen{last['gen']:03d}.npy")
        if (out / "cultures.npy").exists():
            cultures = list(np.load(out / "cultures.npy"))
        rng = np.random.default_rng([a.seed, start])  # nytt slumpflöde efter avbrottet
        print(f"fortsätter från generation {start}, n={n}", flush=True)
    t0 = time.time() - (log[-1]["seconds"] if log else 0)
    with Pool(a.workers) as pool:
        for gen in range(start, a.generations):
            stream = a.seed * 100000 + gen
            jobs = [(q, n, a.ratio, a.lifetime, stream, a.seed * 10**6 + gen * 1000 + i, 20, a.mode, cultures[i])
                    for i, q in enumerate(queens)]
            res = pool.map(live, jobs)
            fit = [r["fitness"] for r in res]
            solving = sum(r["solved"] > 0 for r in res) / len(res)
            b = int(np.argmax(fit))
            row = dict(gen=gen, n=n, best_fitness=round(fit[b], 1), median_fitness=round(float(np.median(fit)), 1),
                       share_solving=round(solving, 3), best_solved=res[b]["solved"],
                       total_solved=sum(r["solved"] for r in res),
                       survived=sum(r["survived"] for r in res),
                       best_repair_focus=None if res[b]["repair_focus"] is None else round(res[b]["repair_focus"], 3),
                       median_repair_focus=round(float(np.median([r["repair_focus"] for r in res if r["repair_focus"]]
                                                                  or [0])), 3),
                       seconds=round(time.time() - t0))
            log.append(row)
            print(json.dumps(row, ensure_ascii=False), flush=True)
            if a.mode != "none":
                drift = float(np.mean([np.abs(r["learned"] - q).mean() for r, q in zip(res, queens)]))
                row["learned_drift"] = round(drift, 4)
            np.save(out / f"best_queen_gen{gen:03d}.npy", queens[b])
            best_ever = queens[b].copy()
            if solving >= a.raise_at:
                n += a.dn
            if "lamarck" in flags:
                # det kolonin lärt sig under livet skrivs in i drottningens arv
                queens = np.stack([r["learned"] for r in res])
            queens, _, parents = reproduce(queens, fit, rng, a.elite, a.sigma, a.mut_prob, a.crossover)
            if "heritage" in flags:
                # kulturarv: den nya kolonins grundare bär mor-kolonins inlärda beteende
                cultures = [res[p]["learned"] for p in parents]
            np.save(out / "queens.npy", queens)
            if "heritage" in flags:
                np.save(out / "cultures.npy", np.stack(cultures))
            (out / "state.json").write_text(json.dumps(dict(log=log), ensure_ascii=False))

    # bästa drottningens döttrar som fil för scaling.py
    np.save(out / "best_queen_workers.npy", best_ever[None] + np.random.default_rng(0).normal(0, 0.1, (50,) + shape))
    delta = best_ever - base
    top = np.argsort(-np.abs(delta), axis=None)[:15]
    OUT, IN = out_names(a.mem), in_names(a.mem)
    genes = [dict(output=OUT[o], input=IN[i], start=round(float(base[o, i]), 2),
                  now=round(float(best_ever[o, i]), 2))
             for o, i in (np.unravel_index(f, delta.shape) for f in top)]
    (out / "evolution.json").write_text(json.dumps(dict(args=vars(a), log=log, top_genes=genes), indent=1,
                                                   ensure_ascii=False))
    L = [f"# Evolution `{a.name}`", "",
         f"{a.queens} drottningar × {a.generations} generationer, liv {a.lifetime} tick, "
         f"{'utan instinkter' if a.blank_slate else 'med födosöksinstinkter'}, {a.mem} minnesceller, läge **{a.mode}**, frö {a.seed}. "
         f"Tid {round(time.time() - t0)} s.", "",
         "| gen | n | bästa fitness | median fitness | andel som löser | lösta totalt | överlevde | "
         "reparationsfokus bästa | median |", "|---|---|---|---|---|---|---|---|---|"]
    for r in log:
        L.append(f"| {r['gen']} | {r['n']} | {r['best_fitness']} | {r['median_fitness']} | {r['share_solving']:.0%} | "
                 f"{r['total_solved']} | {r['survived']}/{a.queens} | {r['best_repair_focus']} | {r['median_repair_focus']} |")
    L += ["", "## Bästa drottningens mest förändrade gener", "",
          "| output | input | start | nu |", "|---|---|---|---|"]
    L += [f"| {g['output']} | {g['input']} | {g['start']} | {g['now']} |" for g in genes]
    (out / "evolution.md").write_text("\n".join(L) + "\n")
    print(f"Klart: {out}/evolution.md")


if __name__ == "__main__":
    main()
