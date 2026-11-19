#!/usr/bin/env python3
"""Ablation: används minnet? Kör färdiga drottningar med och utan fungerande minne.

Varje drottning (sista generationens bästa) får leva flera kolonieliv på samma
problemström som i evolve.py, en gång med minnet påslaget och en gång med minnet
fruset (mem_rate=0: cellerna förblir 0, hjärnan läser bara nollor). Samma problem
och samma slumpfrön i båda fallen, så skillnaden beror bara på minnet.

    python ablation.py --runs evo-baldwin-mem4 evo-baldwin-mem4-s2 --lives 4
"""
import argparse
import functools
import json
import os
from multiprocessing import Pool
from pathlib import Path

import numpy as np

import evolve
from antcomputer.world import Params


def job(args):
    run, queen_path, n, life_k, mem_rate, mode, lifetime, ratio, hold = args
    evolve.Params = functools.partial(Params, mem_rate=mem_rate)
    queen = np.load(queen_path)
    r = evolve.live((queen, n, ratio, lifetime, 90_000 + life_k, 7_000 + life_k, hold, mode, None))
    return dict(run=run, n=n, life=life_k, mem_rate=mem_rate, solved=r["solved"], food=r["food"],
                survived=r["survived"])


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--name", default="ablation-minne")
    ap.add_argument("--runs", nargs="+", required=True)
    ap.add_argument("--mode", default="baldwin")
    ap.add_argument("--lives", type=int, default=4)
    ap.add_argument("--n", type=int, default=0, help="problemstorlek (0 = den storlek körningen nådde)")
    ap.add_argument("--lifetime", type=int, default=12000)
    ap.add_argument("--ratio", type=float, default=4.26)
    ap.add_argument("--hold", type=int, default=20)
    ap.add_argument("--workers", type=int, default=os.cpu_count())
    a = ap.parse_args()

    jobs = []
    for run in a.runs:
        log = json.load(open(f"runs/{run}/state.json"))["log"]
        last = log[-1]["gen"]
        n = a.n or log[-1]["n"]
        q = f"runs/{run}/best_queen_gen{last:03d}.npy"
        for k in range(a.lives):
            for r in (0.5, 0.0):
                jobs.append((run, q, n, k, r, a.mode, a.lifetime, a.ratio, a.hold))
    res = []
    with Pool(a.workers) as pool:
        for r in pool.imap_unordered(job, jobs):
            res.append(r)
            print(f"klar {len(res)}/{len(jobs)}: {r['run']} liv {r['life']} minne {'på' if r['mem_rate'] else 'fruset'}: "
                  f"{r['solved']} lösta", flush=True)

    L = [f"# Ablation `{a.name}`: används minnet?", "",
         f"Sista generationens bästa drottning, {a.lives} kolonieliv per läge, {a.lifetime} tick, läge {a.mode}. "
         "Fruset minne = cellerna förblir 0 hela livet. Samma problem och frön i båda lägena.", "",
         "| körning | n | lösta, minne på | lösta, fruset minne | mat, på | mat, fruset |", "|---|---|---|---|---|---|"]
    diffs = []
    for run in a.runs:
        on = [r for r in res if r["run"] == run and r["mem_rate"] > 0]
        off = [r for r in res if r["run"] == run and r["mem_rate"] == 0]
        s_on, s_off = sum(r["solved"] for r in on), sum(r["solved"] for r in off)
        f_on, f_off = np.mean([r["food"] for r in on]), np.mean([r["food"] for r in off])
        diffs.append(s_on - s_off)
        L.append(f"| {run} | {on[0]['n']} | {s_on} | {s_off} | {f_on:.0f} | {f_off:.0f} |")
    better = sum(d > 0 for d in diffs)
    worse = sum(d < 0 for d in diffs)
    L += ["", f"Minnet på löser fler i {better} körningar, färre i {worse}, lika i {len(diffs) - better - worse}. "
          "Löser drottningarna lika mycket med fruset minne används minnet inte till något."]
    out = Path("runs") / a.name
    out.mkdir(parents=True, exist_ok=True)
    (out / "ablation.md").write_text("\n".join(L) + "\n")
    (out / "ablation.json").write_text(json.dumps(res, indent=1))
    print("\n".join(L))


if __name__ == "__main__":
    main()
