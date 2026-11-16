#!/usr/bin/env python3
"""Kontrollerat experiment: jämför inställningar över många slumpfrön.

Exempel:
    python sweep.py --name reveal-sat --oracle sat --seeds 6 --ticks 30000
    python sweep.py --name reveal-factor --oracle factor --seeds 6 --ticks 30000
    python sweep.py --name at95 --modes off natural --reveal-at 0.95

Varje (läge, frö) körs som ett eget experiment. Resultatet skrivs till
runs/<namn>/sweep.md och sweep.json.
"""
import argparse
import contextlib
import io
import json
import os
import statistics
from multiprocessing import Pool
from pathlib import Path

from antcomputer.experiment import Config, Experiment
from antcomputer.world import Params


def job(args):
    name, oracle, mode, seed, ticks, reveal_at, colonies = args
    cfg = Config(name=f"{mode}_s{seed}", oracle=oracle, ticks=ticks, seed=seed, colonies=colonies,
                 trace_every=0, baseline_runs=1, out_dir=f"runs/{name}", reveal=mode, reveal_at=reveal_at,
                 params=Params())
    with contextlib.redirect_stdout(io.StringIO()):
        out = Experiment(cfg).run()
    s = json.loads((out / "summary.json").read_text())
    solved = [e for e in s["events"] if e["type"] == "solved"]
    best = max(range(len(s["levels"])), key=lambda i: (s["levels"][i], s["full_satisfied"][i] / s["full_clauses"][i]))
    return dict(mode=mode, seed=seed, solved=len(solved), max_level=max(s["levels"]),
                first_solve=min((e["tick"] for e in solved), default=None),
                all_verified=all(e["verified"] for e in solved),
                answers=sorted({e["answer"] for e in solved if oracle == "factor"}),
                best_full_frac=s["full_satisfied"][best] / s["full_clauses"][best],
                best_progress=s["progress"][best])


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--name", required=True)
    ap.add_argument("--oracle", default="sat", choices=["sat", "enumerate", "factor", "fresh"])
    ap.add_argument("--modes", nargs="+", default=["off", "natural", "random", "adversarial", "friendly"])
    ap.add_argument("--seeds", type=int, default=6)
    ap.add_argument("--ticks", type=int, default=30000)
    ap.add_argument("--colonies", type=int, default=4)
    ap.add_argument("--reveal-at", type=float, default=1.0)
    ap.add_argument("--workers", type=int, default=os.cpu_count())
    a = ap.parse_args()

    jobs = [(a.name, a.oracle, m, s, a.ticks, a.reveal_at, a.colonies) for s in range(1, a.seeds + 1) for m in a.modes]
    with Pool(a.workers) as pool:
        results = []
        for r in pool.imap_unordered(job, jobs):
            results.append(r)
            print(f"klar: {r['mode']:<12} frö {r['seed']}: löst {r['solved']}, nivå {r['max_level']}", flush=True)

    def med(xs):
        xs = [x for x in xs if x is not None]
        return statistics.median(xs) if xs else None

    L = [f"# Svep `{a.name}`", "",
         f"Orakel **{a.oracle}**, {a.seeds} frön × {a.colonies} kolonier × {a.ticks} tick, avslöja vid {a.reveal_at:.0%}.", "",
         "| läge | lösta problem (medel) | frön med minst en lösning | högsta nivå (medel) | första lösning, median-tick | "
         "bästa koloni: andel av hela problemet uppfyllt | alla svar verifierade |",
         "|---|---|---|---|---|---|---|"]
    for m in a.modes:
        rs = [r for r in results if r["mode"] == m]
        fs = med([r["first_solve"] for r in rs])
        L.append(f"| {m} | {statistics.mean(r['solved'] for r in rs):.2f} | "
                 f"{sum(r['solved'] > 0 for r in rs)}/{len(rs)} | {statistics.mean(r['max_level'] for r in rs):.2f} | "
                 f"{'—' if fs is None else int(fs)} | {statistics.mean(r['best_full_frac'] for r in rs):.3f} | "
                 f"{'ja' if all(r['all_verified'] for r in rs) else 'NEJ'} |")
    answers = sorted({x for r in results for x in r["answers"]})
    if answers:
        L += ["", "Faktoriseringar som hittats: " + ", ".join(answers)]
    out = Path("runs") / a.name
    (out / "sweep.md").write_text("\n".join(L) + "\n")
    (out / "sweep.json").write_text(json.dumps(results, indent=1, ensure_ascii=False))
    print("\n".join(L))


if __name__ == "__main__":
    main()
