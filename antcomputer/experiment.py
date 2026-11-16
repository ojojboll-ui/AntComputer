"""Experimentloopen: flera kolonier, ett orakel per koloni, loggning och rapport."""
from __future__ import annotations

import csv
import json
import math
import time
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from .baselines import benchmark
from .oracle import ORACLES
from .world import IN_NAMES, OUT_NAMES, Colony, Params, prior_genome


@dataclass
class Config:
    name: str = "run"
    oracle: str = "sat"
    ticks: int = 20000
    colonies: int = 4
    seed: int = 1
    solve_hold: int = 20           # alla krav måste hålla så här många tick
    migrate_every: int = 1000      # ö-selektion: sämsta kolonin ersätts av den bästas avkomma
    log_every: int = 50
    trace_every: int = 10          # inspelning av koloni 0 för spelaren (0 = av)
    trace_max_frames: int = 3000
    baseline_runs: int = 20
    out_dir: str = "runs"
    params: Params = field(default_factory=Params)


class Experiment:
    def __init__(self, cfg: Config) -> None:
        self.cfg = cfg
        self.rng = np.random.default_rng(cfg.seed)
        self.oracles = [ORACLES[cfg.oracle](seed=cfg.seed) for _ in range(cfg.colonies)]
        self.colonies = [Colony(o.problem, cfg.params, np.random.default_rng(cfg.seed * 1000 + i))
                         for i, o in enumerate(self.oracles)]
        self.hold = [0] * cfg.colonies
        self.since = [dict(tick=0, flips=0) for _ in range(cfg.colonies)]
        self.window = [self._empty_window() for _ in range(cfg.colonies)]
        self.income = [0.0] * cfg.colonies
        self.events: list[dict] = []
        self.series: list[dict] = []
        self.solved_problems: dict[str, object] = {}
        self.trace = {"layouts": [], "frames": []}
        self._trace_problem = None
        self.dir = Path(cfg.out_dir) / cfg.name
        self.dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _empty_window() -> dict:
        return dict(deposits=0, deposits_helpful=0, helpful_base=0.0, deposits_carrying=0,
                    deposits_after_dead=0, removals=0, delivered=0, ticks=0, flips=0)

    def event(self, **kw) -> None:
        self.events.append(kw)
        msg = " ".join(f"{k}={v}" for k, v in kw.items())
        print(msg, flush=True)

    # --------------------------------------------------------------- run loop
    def run(self) -> Path:
        cfg = self.cfg
        t0 = time.time()
        for t in range(1, cfg.ticks + 1):
            for i, col in enumerate(self.colonies):
                s = col.step()
                w = self.window[i]
                for k in ("deposits", "deposits_helpful", "deposits_carrying", "deposits_after_dead",
                          "removals", "delivered", "flips"):
                    w[k] += s[k]
                w["helpful_base"] += s["helpful_base"] * s["deposits"]
                w["ticks"] += 1
                self.since[i]["flips"] += s["flips"]
                self.income[i] += s["delivered"]
                self.hold[i] = self.hold[i] + 1 if s["all_sat"] else 0
                if self.hold[i] >= cfg.solve_hold:
                    self._solved(i, t)
                if col.population == 0:
                    self._extinct(i, t)
                if t % cfg.log_every == 0:
                    self._log(i, t, s)
            if cfg.colonies > 1 and t % cfg.migrate_every == 0:
                self._migrate(t)
            if cfg.trace_every and t % cfg.trace_every == 0 and len(self.trace["frames"]) < cfg.trace_max_frames:
                self._record(t)
            if t % 2000 == 0:
                lv = [o.level for o in self.oracles]
                pops = [c.population for c in self.colonies]
                sats = [round(float(c.sat.mean()), 3) for c in self.colonies]
                print(f"[t={t}] nivåer={lv} befolkning={pops} uppfyllt={sats} ({time.time() - t0:.0f}s)", flush=True)
        return self._finish(time.time() - t0)

    def _solved(self, i: int, t: int) -> None:
        col, orc = self.colonies[i], self.oracles[i]
        asg = col.assignment()
        ok, answer = orc.problem.verify(asg)
        self.event(type="solved", tick=t, colony=i, level=orc.level, problem=orc.problem.name,
                   verified=ok, answer=answer, ticks_used=t - self.since[i]["tick"],
                   flips_used=self.since[i]["flips"], population=col.population)
        self.solved_problems.setdefault(orc.problem.name, orc.problem)
        col.store += col.p.jackpot
        new = orc.advance(asg)
        col.set_problem(new)
        self.hold[i] = 0
        self.since[i] = dict(tick=t, flips=0)
        self.event(type="new_problem", tick=t, colony=i, level=orc.level, problem=new.name,
                   n_vars=new.n_vars, n_clauses=len(new.clauses))

    def _extinct(self, i: int, t: int) -> None:
        alive = [j for j, c in enumerate(self.colonies) if c.population > 0]
        if alive:
            donor = max(alive, key=lambda j: (self.oracles[j].level, self.income[j]))
            genomes = self.colonies[donor].living_genomes()
            reps = math.ceil(self.cfg.params.pop_init / len(genomes))
            self.colonies[i].reseed(np.tile(genomes, (reps, 1, 1)))
            self.event(type="extinct", tick=t, colony=i, reseeded_from=donor)
        else:
            base = prior_genome() if self.cfg.params.prior else np.zeros_like(prior_genome())
            self.colonies[i].reseed(base[None] + self.rng.normal(0, 0.3, (self.cfg.params.pop_init,) + base.shape))
            self.event(type="extinct", tick=t, colony=i, reseeded_from="prior")

    def _migrate(self, t: int) -> None:
        score = [(self.oracles[i].level, self.income[i]) for i in range(len(self.colonies))]
        best = max(range(len(score)), key=lambda i: score[i])
        worst = min(range(len(score)), key=lambda i: score[i])
        if best != worst and self.colonies[best].population > 0:
            g = self.colonies[best].living_genomes()
            reps = math.ceil(self.cfg.params.pop_init / len(g))
            self.colonies[worst].reseed(np.tile(g, (reps, 1, 1)))
            self.event(type="migration", tick=t, from_colony=best, to_colony=worst)
        self.income = [0.0] * len(self.colonies)

    def _log(self, i: int, t: int, s: dict) -> None:
        w = self.window[i]
        d = max(w["deposits"], 1)
        col = self.colonies[i]
        self.series.append(dict(
            tick=t, colony=i, level=self.oracles[i].level, pop=s["pop"], store=s["store"],
            sat_frac=round(s["sat_frac"], 4), delivered=w["delivered"], flips=w["flips"],
            deposits=w["deposits"], removals=w["removals"],
            # "reparationsfokus": hur mycket oftare lera hamnar i en kammare som skulle
            # uppfylla ett brutet krav, jämfört med om leran lades helt slumpmässigt (=1.0)
            repair_focus=round((w["deposits_helpful"] / d) / max(w["helpful_base"] / d, 1e-9), 3) if w["deposits"] else None,
            share_carrying=round(w["deposits_carrying"] / d, 3),
            share_after_dead=round(w["deposits_after_dead"] / d, 3),
            signal=round(col.signal, 3)))
        self.window[i] = self._empty_window()

    def _record(self, t: int) -> None:
        col = self.colonies[0]
        g = col.g
        if self._trace_problem is not col.problem:
            self._trace_problem = col.problem
            self.trace["layouts"].append(dict(
                problem=col.problem.name, n_vars=g.n_vars,
                clauses=[list(c) for c in col.problem.clauses], edges=g.edges.tolist()))
        counts = np.bincount(col.node[col.alive], minlength=g.N)
        carrying = np.bincount(col.node[col.alive & col.carrying], minlength=g.N)
        ph = col.pher.sum(axis=1)
        self.trace["frames"].append(dict(
            t=t, L=len(self.trace["layouts"]) - 1, level=self.oracles[0].level, pop=col.population,
            store=round(col.store, 1), val="".join("1" if v else "0" for v in col.val),
            sat="".join("1" if v else "0" for v in col.sat),
            ants=counts.tolist(), carry=carrying.tolist(),
            clay=[int(x) for x in np.rint(col.clay[1:1 + 2 * g.n_vars])],
            ph=[int(x) for x in np.minimum(9, np.rint(np.log1p(ph) * 2))],
            ch=[int(x) for x in np.minimum(9, np.rint(np.log1p(col.pher) * 2)).argmax(axis=1)]))

    # ----------------------------------------------------------------- output
    def _finish(self, seconds: float) -> Path:
        cfg = self.cfg
        print("Kör jämförelsealgoritmer ...", flush=True)
        bench = {name: benchmark(p, runs=cfg.baseline_runs) for name, p in self.solved_problems.items()}
        for o in self.oracles:  # även det olösta problemet som kolonierna fastnade på
            if o.problem.name not in bench:
                bench[o.problem.name] = benchmark(o.problem, runs=cfg.baseline_runs)

        # genetisk drift: vilka gener har förändrats mest jämfört med medfödd instinkt?
        start = prior_genome() if cfg.params.prior else np.zeros_like(prior_genome())
        genes = []
        for i, col in enumerate(self.colonies):
            if col.population == 0:
                continue
            G = col.living_genomes()
            mean, std = G.mean(axis=0), G.std(axis=0)
            delta = mean - start
            flat = np.argsort(-np.abs(delta), axis=None)[:12]
            for f in flat:
                o, inp = np.unravel_index(f, delta.shape)
                genes.append(dict(colony=i, output=OUT_NAMES[o], input=IN_NAMES[inp],
                                  start=round(float(start[o, inp]), 2), now=round(float(mean[o, inp]), 2),
                                  spread=round(float(std[o, inp]), 2)))
            np.save(self.dir / f"genomes_colony{i}.npy", G)

        summary = dict(config=dict(cfg.__dict__, params=cfg.params.to_dict()), seconds=round(seconds, 1),
                       levels=[o.level for o in self.oracles], events=self.events,
                       baselines=bench, gene_drift=genes)
        (self.dir / "summary.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False, default=str))
        with open(self.dir / "timeseries.csv", "w", newline="") as f:
            if self.series:
                wr = csv.DictWriter(f, fieldnames=list(self.series[0].keys()))
                wr.writeheader()
                wr.writerows(self.series)
        if cfg.trace_every:
            self._write_replay()
        self._write_report(summary)
        print(f"Klart. Resultat i {self.dir}/", flush=True)
        return self.dir

    def _write_replay(self) -> None:
        tpl = (Path(__file__).parent / "replay_template.html").read_text()
        data = json.dumps(self.trace, separators=(",", ":"))
        (self.dir / "replay.html").write_text(tpl.replace("/*__TRACE__*/null", data))

    def _write_report(self, s: dict) -> None:
        cfg = self.cfg
        L = [f"# Körning `{cfg.name}`", "",
             f"Orakel: **{cfg.oracle}**, {cfg.colonies} kolonier, {cfg.ticks} tick, frö {cfg.seed}, "
             f"evolution {'på' if cfg.params.evolution else 'AV'} (urval: {cfg.params.selection}), "
             f"förvarning vid byte {'på' if cfg.params.announce_changes else 'av'}. Tid: {s['seconds']} s.", "",
             f"Uppnådda nivåer per koloni: {s['levels']}", "", "## Lösta problem", "",
             "| tick | koloni | problem | svar | verifierat | myr-flips | WalkSAT | slumpvandring | blind slump |",
             "|---|---|---|---|---|---|---|---|---|"]

        def fmt(b):
            return "—" if b["median_flips"] is None else f"{b['median_flips']:.0f}"
        for e in s["events"]:
            if e["type"] != "solved":
                continue
            b = s["baselines"].get(e["problem"], {})
            L.append(f"| {e['tick']} | {e['colony']} | {e['problem']} | {e['answer']} | "
                     f"{'ja' if e['verified'] else 'NEJ'} | {e['flips_used']} | "
                     + " | ".join(fmt(b[k]) if k in b else "?" for k in ("walksat", "random_walk", "blind_flip")) + " |")
        L += ["", "Flips = antal gånger en variabel bytt värde innan lösningen. Jämförelsealgoritmerna visar median "
              f"över {cfg.baseline_runs} körningar (— = löste inte hälften inom gränsen).", "",
              "## Var kolonierna slutade", ""]
        for i, (o, c) in enumerate(zip(self.oracles, self.colonies)):
            L.append(f"- Koloni {i}: nivå {o.level}, {o.problem.name}, befolkning {c.population}, "
                     f"{int(c.sat.sum())}/{len(c.sat)} krav uppfyllda")
        L += ["", "## Beteendets fingeravtryck (sista tiondelen av körningen)", "",
              "*Reparationsfokus* > 1 betyder att leran oftare än slumpen läggs där den lagar ett brutet krav "
              "(det är kärnan i WalkSAT). Andelar visar *vem* som bygger.", "",
              "| koloni | reparationsfokus | andel lera från matbärare | andel lera efter död automat |", "|---|---|---|---|"]
        tail = [r for r in self.series if r["tick"] > cfg.ticks * 0.9]
        for i in range(cfg.colonies):
            rs = [r for r in tail if r["colony"] == i and r["repair_focus"] is not None]
            if rs:
                L.append(f"| {i} | {np.mean([r['repair_focus'] for r in rs]):.2f} | "
                         f"{np.mean([r['share_carrying'] for r in rs]):.2f} | {np.mean([r['share_after_dead'] for r in rs]):.2f} |")
        L += ["", "## Gener som förändrats mest (jämfört med medfödd instinkt)", "",
              "Läs som: *när myran känner `input`, påverkas `output` med vikten `nu`*.", "",
              "| koloni | output | input | start | nu | spridning |", "|---|---|---|---|---|---|"]
        for gdr in s["gene_drift"]:
            L.append(f"| {gdr['colony']} | {gdr['output']} | {gdr['input']} | {gdr['start']} | {gdr['now']} | {gdr['spread']} |")
        (self.dir / "report.md").write_text("\n".join(L) + "\n")
