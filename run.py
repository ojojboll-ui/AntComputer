#!/usr/bin/env python3
"""Kör ett myrdatorexperiment.

Exempel:
    python run.py --name forsta --oracle sat --ticks 30000
    python run.py --name faktor --oracle factor --ticks 100000 --trace-every 0
    python run.py --name kontroll --no-evolution          # ablation: samma men utan evolution
    python run.py --name snall --announce-changes          # myrorna förvarnas när reglerna byts
"""
import argparse
import dataclasses

from antcomputer.experiment import Config, Experiment
from antcomputer.world import Params


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--name", default="run")
    ap.add_argument("--oracle", default="sat", choices=["sat", "enumerate", "factor", "fresh"])
    ap.add_argument("--ticks", type=int, default=20000)
    ap.add_argument("--colonies", type=int, default=4)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--migrate-every", type=int, default=1000, help="ö-selektion mellan kolonier")
    ap.add_argument("--reveal", default="off", choices=["off", "natural", "random", "adversarial", "friendly"],
                    help="progressivt orakel: avslöja problemet under räkningens gång")
    ap.add_argument("--reveal-at", type=float, default=1.0, help="andel synliga krav som måste hålla före nästa steg")
    ap.add_argument("--reveal-step", type=float, default=0.1, help="andel krav per steg (om problemet saknar naturliga steg)")
    ap.add_argument("--trace-every", type=int, default=10, help="0 stänger av inspelningen")
    ap.add_argument("--baseline-runs", type=int, default=20)
    ap.add_argument("--announce-changes", action="store_true", help="förvarna myrorna när problemet byts")
    ap.add_argument("--no-evolution", action="store_true", help="kontrollgrupp: arvsmassan förändras aldrig")
    ap.add_argument("--blank-slate", action="store_true", help="inga medfödda instinkter alls")
    ap.add_argument("--selection", choices=["colony", "individual"], default="colony")
    ap.add_argument("--param", action="append", default=[], metavar="NAMN=VÄRDE",
                    help="ändra en världsparameter, t.ex. --param erosion=0.005")
    a = ap.parse_args()

    params = Params(announce_changes=a.announce_changes, evolution=not a.no_evolution,
                    prior=not a.blank_slate, selection=a.selection)
    types = {f.name: f.type for f in dataclasses.fields(Params)}
    for kv in a.param:
        k, v = kv.split("=", 1)
        cast = {"int": int, "float": float, "bool": lambda s: s.lower() in ("1", "true", "ja")}[types[k]]
        setattr(params, k, cast(v))

    cfg = Config(name=a.name, oracle=a.oracle, ticks=a.ticks, colonies=a.colonies, seed=a.seed, migrate_every=a.migrate_every,
                 trace_every=a.trace_every, reveal=a.reveal, reveal_at=a.reveal_at,
                 reveal_step=a.reveal_step, baseline_runs=a.baseline_runs, params=params)
    Experiment(cfg).run()


if __name__ == "__main__":
    main()
