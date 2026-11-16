"""Myrvärlden: en graf av kammare och tunnlar där matematiken är fysik.

Kretsmodellen
-------------
* Boet (nod 0) är där maten lämnas och drottningen föder nya myror.
* Varje variabel x är ett par kammare, "sann" och "falsk". Myrorna kan bära dit
  lera. Den kammare som har mest lera "vinner" och bestämmer variabelns värde.
  Leran eroderar långsamt, så minnet måste underhållas.
* Varje klausul (krav) är en matautomat. Den är förbunden med tunnlar till de
  kammare vars literaler ingår i kravet. Oraklet låter mat växa i automaten
  bara om kravet är uppfyllt. Annars ruttnar maten bort.
* Totalt matflöde beror kraftigt på hur stor andel krav som är uppfyllda, så
  kolonin kan bara växa om den håller "rätt" kammare vinnande.

Myrorna vet inget av detta. Varje myra har en liten arvsmassa: en matris W som
översätter vad hon känner just nu (bär hon mat, finns det mat här, lera här,
var senaste automaten tom ...) till hur hon väljer tunnel, om hon lägger eller
tar bort lera och vilka av tre doftämnen hon lägger. Doftämnena har ingen
förbestämd betydelse. Arvsmassan muteras vid födsel och föräldrar väljs efter
hur mycket mat de burit hem.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Optional

import numpy as np

from .problems import Problem

K = 3  # antal feromonkanaler

IN_NAMES = ["bias", "carrying", "food_here", "at_nest", "at_pad", "at_clause", "clay_here",
            "pad_winning", "hunger", "change_signal", "last_clause_dead"]
OUT_NAMES = [f"follow_{k}" for k in range(K)] + ["food_attr", "clay_attr", "nest_attr", "back_attr",
                                                  "deposit_clay", "remove_clay"] + [f"lay_{k}" for k in range(K)]
NI, NO = len(IN_NAMES), len(OUT_NAMES)
I = {n: i for i, n in enumerate(IN_NAMES)}
O = {n: i for i, n in enumerate(OUT_NAMES)}
FOLLOW = slice(O["follow_0"], O["follow_0"] + K)
LAY = slice(O["lay_0"], O["lay_0"] + K)

NEST, PAD, CLAUSE = 0, 1, 2


@dataclass
class Params:
    pop_init: int = 150
    pop_cap: int = 400
    store_init: float = 20.0
    store_target: float = 20.0      # över detta känner kolonin ingen hunger
    metabolism: float = 0.01        # mat per myra och tick
    birth_cost: float = 1.0
    max_births_per_tick: int = 5
    starve_prob: float = 0.01       # dödsrisk per tick när förrådet är tomt
    lifespan: int = 1500
    lifespan_jitter: int = 500
    food_full: float = 6.0          # matflöde per tick när alla krav är uppfyllda
    food_cap: float = 5.0           # max mat i en automat
    sat_floor: float = 0.8          # under denna andel uppfyllda krav: ingen mat alls
    sat_power: float = 2.0
    food_rot: float = 0.9           # mat i ouppfyllda automater ruttnar
    full_bonus: float = 2.0         # matfest: flödet multipliceras när ALLA krav är uppfyllda
    flip_margin: float = 2.0        # tröghet: en kammare tar över först när den leder med så mycket lera
    clay_cap: float = 20.0
    erosion: float = 0.002
    pher_evap: float = 0.01
    lay_amount: float = 1.0
    mutation_sigma: float = 0.15
    mutation_prob: float = 0.2
    jackpot: float = 50.0           # bonusmat när ett problem är löst
    announce_changes: bool = False  # säg till myrorna när problemet byts
    signal_decay: float = 0.995
    evolution: bool = True
    worker_sigma: float = 0.1       # variation mellan systrar i drottningsläge
    # --- inlärning under livet (belöningsstyrd, bara lokala signaler)
    learning: bool = False
    learn_rate: float = 0.05
    trace_decay: float = 0.9        # hur långt bakåt en belöning når (eligibility trace)
    # --- kultur: härma grannar som lever där det blomstrar, nyfödda lär av äldre
    culture: bool = False
    copy_rate: float = 0.05         # chans per tick att härma bästa grannen på samma plats
    copy_strength: float = 0.3      # hur mycket av grannens beteende som tas över
    copy_noise: float = 0.05        # kulturell mutation: man härmar aldrig perfekt
    prosper_decay: float = 0.95     # minne av hur ofta myran hittat levande automater
    prior: bool = True              # börja med enkla födosöksinstinkter (inget om lera)
    # "colony": arbetarna är sterila, bara kolonier konkurrerar (ö-selektion) - som i naturen.
    # "individual": nya myror ärver främst från de som burit hem mest mat.
    selection: str = "colony"

    def to_dict(self) -> dict:
        return asdict(self)


def prior_genome() -> np.ndarray:
    """Medfödda födosöksinstinkter. Medvetet inget om lera: det ska de uppfinna själva."""
    W = np.zeros((NO, NI))
    W[O["follow_0"], I["bias"]] = 1.0
    W[O["follow_0"], I["carrying"]] = -1.0
    W[O["follow_1"], I["carrying"]] = 1.0
    W[O["lay_0"], I["bias"]] = -2.0
    W[O["lay_0"], I["carrying"]] = 4.0
    W[O["lay_1"], I["bias"]] = 1.0
    W[O["lay_1"], I["carrying"]] = -4.0
    W[O["lay_2"], I["bias"]] = -2.0
    W[O["food_attr"], I["bias"]] = 2.0
    W[O["food_attr"], I["carrying"]] = -2.0
    W[O["nest_attr"], I["bias"]] = -0.5
    W[O["nest_attr"], I["carrying"]] = 3.0
    W[O["back_attr"], I["bias"]] = -1.0
    W[O["deposit_clay"], I["bias"]] = -2.0
    W[O["remove_clay"], I["bias"]] = -2.0
    return W


def sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(x, -30, 30)))


class Graph:
    def __init__(self, problem: Problem) -> None:
        n, clauses = problem.n_vars, problem.clauses
        self.n_vars, self.m = n, len(clauses)
        self.labels: list[tuple] = [("nest",)]
        for v in range(1, n + 1):
            self.labels += [("pad", v, True), ("pad", v, False)]
        self.labels += [("clause", c) for c in clauses]
        self.N = len(self.labels)
        self.index = {lab: i for i, lab in enumerate(self.labels)}
        self.ntype = np.array([NEST] + [PAD] * (2 * n) + [CLAUSE] * self.m)
        self.pad_var = np.full(self.N, -1)
        self.pad_sign = np.zeros(self.N, dtype=bool)
        for v in range(n):
            self.pad_var[1 + 2 * v] = v
            self.pad_var[2 + 2 * v] = v
            self.pad_sign[1 + 2 * v] = True
        self.clause_node = np.arange(1 + 2 * n, self.N)

        edges, keys = [], []
        for v in range(1, n + 1):
            for lit in (v, -v):
                edges.append((0, self.pad(lit)))
                keys.append(("N", lit))
        seen = set()
        for ci, c in enumerate(clauses):
            for lit in c:
                key = (lit, c)
                if key in seen:
                    continue
                seen.add(key)
                edges.append((self.pad(lit), int(self.clause_node[ci])))
                keys.append(key)
        self.edges = np.array(edges, dtype=np.int64)
        self.edge_keys = keys
        self.E = len(edges)

        nbrs: list[list[tuple[int, int]]] = [[] for _ in range(self.N)]
        for e, (a, b) in enumerate(edges):
            nbrs[a].append((b, e))
            nbrs[b].append((a, e))
        D = max(len(x) for x in nbrs)
        self.adj = np.full((self.N, D), -1, dtype=np.int64)
        self.adj_e = np.zeros((self.N, D), dtype=np.int64)
        for i, lst in enumerate(nbrs):
            for j, (b, e) in enumerate(lst):
                self.adj[i, j] = b
                self.adj_e[i, j] = e
        self.adj_valid = self.adj >= 0
        self.adj_safe = np.where(self.adj_valid, self.adj, 0)

        L = max(len(c) for c in clauses)
        self.c_var = np.zeros((self.m, L), dtype=np.int64)
        self.c_sign = np.zeros((self.m, L), dtype=bool)
        self.c_mask = np.zeros((self.m, L), dtype=bool)
        self.c_pad = np.zeros((self.m, L), dtype=np.int64)
        for ci, c in enumerate(clauses):
            for j, lit in enumerate(c):
                self.c_var[ci, j] = abs(lit) - 1
                self.c_sign[ci, j] = lit > 0
                self.c_mask[ci, j] = True
                self.c_pad[ci, j] = self.pad(lit)

    @staticmethod
    def pad(lit: int) -> int:
        return 1 + 2 * (abs(lit) - 1) + (0 if lit > 0 else 1)

    def satisfied(self, val: np.ndarray) -> np.ndarray:
        return ((val[self.c_var] == self.c_sign) & self.c_mask).any(axis=1)


class Colony:
    def __init__(self, problem: Problem, params: Params, rng: np.random.Generator,
                 founders: Optional[np.ndarray] = None, queen: Optional[np.ndarray] = None,
                 culture_seed: Optional[np.ndarray] = None) -> None:
        """`queen`: om given är alla arbetare döttrar till denna drottning (drottningsläge).
        `culture_seed`: kulturarv; grundarmyrorna börjar med detta beteende (mor-kolonins kultur)
        i stället för drottningens gener. Nyfödda är ändå drottningens döttrar."""
        self.p = params
        self.queen = queen
        self.rng = rng
        cap = params.pop_cap
        self.alive = np.zeros(cap, dtype=bool)
        self.node = np.zeros(cap, dtype=np.int64)
        self.prev = np.zeros(cap, dtype=np.int64)
        self.carrying = np.zeros(cap, dtype=bool)
        self.age = np.zeros(cap, dtype=np.int64)
        self.life = np.zeros(cap, dtype=np.int64)
        self.delivered = np.zeros(cap)
        self.last_empty = np.zeros(cap)
        self.G = np.zeros((cap, NO, NI))
        self.elig = np.zeros((cap, 2, NI))   # spår av nyliga lerbeslut (för inlärning)
        self.prosper = np.full(cap, 0.5)     # hur ofta myran nyligen hittat levande automater
        self.reward_base = 0.5
        self.store = params.store_init
        self.signal = 0.0
        self.tick = 0
        self.g: Optional[Graph] = None
        self.set_problem(problem, announce=False)
        if queen is not None:
            founders = self._daughters(params.pop_init)
            if culture_seed is not None:
                founders = culture_seed[None] + rng.normal(0, params.worker_sigma, founders.shape)
        if founders is None:
            base = prior_genome() if params.prior else np.zeros((NO, NI))
            founders = base[None] + rng.normal(0, 0.3, (params.pop_init, NO, NI))
        self.founders = founders.copy()
        self._spawn(founders)

    # ------------------------------------------------------------------ setup
    def set_problem(self, problem: Problem, announce: Optional[bool] = None) -> None:
        """Byt problem. Det som går att känna igen (kammare, tunnlar) behålls."""
        old = self.g
        g = Graph(problem)
        clay = np.zeros(g.N)
        food = np.zeros(g.N)
        pher = np.zeros((g.E, K))
        if old is not None:
            for i, lab in enumerate(old.labels):
                j = g.index.get(lab)
                if j is not None:
                    clay[j] = self.clay[i]
                    food[j] = self.food[i]
            ekey = {k: e for e, k in enumerate(g.edge_keys)}
            for e, k in enumerate(old.edge_keys):
                j = ekey.get(k)
                if j is not None:
                    pher[j] = self.pher[e]
            remap = np.array([g.index.get(lab, 0) for lab in old.labels])
            self.node = remap[self.node]
            self.prev = remap[self.prev]
        self.g, self.clay, self.food, self.pher = g, clay, food, pher
        self.problem = problem
        self.val = self._values(np.zeros(g.n_vars, dtype=bool))
        if announce if announce is not None else self.p.announce_changes:
            self.signal = 1.0

    def _values(self, prev_val: np.ndarray) -> np.ndarray:
        t = self.clay[1:1 + 2 * self.g.n_vars:2]
        f = self.clay[2:2 + 2 * self.g.n_vars:2]
        m = self.p.flip_margin
        return np.where(t > f + m, True, np.where(f > t + m, False, prev_val))

    def _spawn(self, genomes: np.ndarray) -> None:
        free = np.nonzero(~self.alive)[0][:len(genomes)]
        k = len(free)
        if k == 0:
            return
        self.alive[free] = True
        self.node[free] = 0
        self.prev[free] = 0
        self.carrying[free] = False
        self.age[free] = 0
        self.life[free] = self.p.lifespan + self.rng.integers(-self.p.lifespan_jitter, self.p.lifespan_jitter + 1, k)
        self.delivered[free] = 0
        self.last_empty[free] = 0
        self.elig[free] = 0
        self.prosper[free] = 0.5
        self.G[free] = genomes[:k]
        if self.p.culture and self.population > k:
            # nyfödda lär av en äldre syster; de som lever där det blomstrar är förebilder oftare
            elders = np.nonzero(self.alive)[0]
            elders = elders[~np.isin(elders, free)]
            w = self.prosper[elders] ** 2 + 1e-6
            teach = self.rng.choice(elders, size=k, p=w / w.sum())
            self._imitate(free, teach)

    def _imitate(self, pupils: np.ndarray, models: np.ndarray) -> None:
        b = self.p.copy_strength
        self.G[pupils] += b * (self.G[models] - self.G[pupils])
        self.G[pupils] += self.rng.normal(0, self.p.copy_noise, self.G[pupils].shape)

    def _daughters(self, k: int) -> np.ndarray:
        """Arbetare: drottningens gener plus liten individuell variation (systrar)."""
        return self.queen[None] + self.rng.normal(0, self.p.worker_sigma, (k,) + self.queen.shape)

    def mutate(self, genomes: np.ndarray) -> np.ndarray:
        mask = self.rng.random(genomes.shape) < self.p.mutation_prob
        return genomes + mask * self.rng.normal(0, self.p.mutation_sigma, genomes.shape)

    def reseed(self, genomes: np.ndarray) -> None:
        """Ersätt hela befolkningen (används av ö-selektion och vid utdöende)."""
        self.alive[:] = False
        self.store = max(self.store, self.p.store_init)
        self._spawn(self.mutate(genomes[: self.p.pop_init]))

    def living_genomes(self) -> np.ndarray:
        return self.G[self.alive]

    @property
    def population(self) -> int:
        return int(self.alive.sum())

    # ------------------------------------------------------------------- step
    def step(self) -> dict:
        p, g, rng = self.p, self.g, self.rng
        self.tick += 1
        ids = np.nonzero(self.alive)[0]
        stats = {"deposits": 0, "deposits_helpful": 0, "deposits_carrying": 0, "deposits_after_dead": 0,
                 "removals": 0, "delivered": 0, "births": 0, "deaths": 0, "flips": 0}
        sat = g.satisfied(self.val)
        self.sat_prev = sat
        # "hjälpsamma" kammare: förlorande kammare som skulle uppfylla ett ouppfyllt krav
        helpful = np.zeros(g.N, dtype=bool)
        unsat_idx = np.nonzero(~sat)[0]
        if len(unsat_idx):
            helpful[g.c_pad[unsat_idx][g.c_mask[unsat_idx]]] = True
        stats["helpful_base"] = float(helpful[1:1 + 2 * g.n_vars].mean())

        if len(ids):
            node = self.node[ids]
            nt = g.ntype[node]
            at_pad = nt == PAD
            X = np.zeros((len(ids), NI))
            X[:, I["bias"]] = 1.0
            X[:, I["carrying"]] = self.carrying[ids]
            X[:, I["food_here"]] = np.minimum(self.food[node], p.food_cap) / p.food_cap
            X[:, I["at_nest"]] = nt == NEST
            X[:, I["at_pad"]] = at_pad
            X[:, I["at_clause"]] = nt == CLAUSE
            X[:, I["clay_here"]] = self.clay[node] / p.clay_cap
            winning = np.zeros(len(ids), dtype=bool)
            winning[at_pad] = self.val[g.pad_var[node[at_pad]]] == g.pad_sign[node[at_pad]]
            X[:, I["pad_winning"]] = winning
            X[:, I["hunger"]] = np.clip(1 - self.store / p.store_target, 0, 1)
            X[:, I["change_signal"]] = self.signal
            X[:, I["last_clause_dead"]] = self.last_empty[ids]
            out = np.einsum("aoi,ai->ao", self.G[ids], X)

            # --- lera
            p_dep = sigmoid(out[:, O["deposit_clay"]])
            p_rem = sigmoid(out[:, O["remove_clay"]])
            dep = at_pad & (rng.random(len(ids)) < p_dep)
            rem = at_pad & ~dep & (rng.random(len(ids)) < p_rem)
            if p.learning:
                # REINFORCE-spår: (gjorde - sannolikhet) * sinnesintryck, bara där beslutet spelade roll
                gd = ((dep - p_dep) * at_pad)[:, None] * X
                gr = ((rem - p_rem) * (at_pad & ~dep))[:, None] * X
                self.elig[ids] = p.trace_decay * self.elig[ids] + np.stack([gd, gr], axis=1)
            if dep.any():
                np.add.at(self.clay, node[dep], 1.0)
                stats["deposits"] = int(dep.sum())
                stats["deposits_helpful"] = int(helpful[node[dep]].sum())
                stats["deposits_carrying"] = int(self.carrying[ids][dep].sum())
                stats["deposits_after_dead"] = int((self.last_empty[ids][dep] > 0).sum())
            if rem.any():
                np.subtract.at(self.clay, node[rem], 1.0)
                stats["removals"] = int(rem.sum())

            # --- rörelse
            nb = g.adj_safe[node]
            valid = g.adj_valid[node]
            ph = np.log1p(self.pher[g.adj_e[node]])                     # (A, D, K)
            score = np.einsum("adk,ak->ad", ph, out[:, FOLLOW])
            score += (np.minimum(self.food[nb], p.food_cap) / p.food_cap) * out[:, [O["food_attr"]]]
            score += (self.clay[nb] / p.clay_cap) * out[:, [O["clay_attr"]]]
            score += (nb == 0) * out[:, [O["nest_attr"]]]
            score += (nb == self.prev[ids][:, None]) * out[:, [O["back_attr"]]]
            score += rng.gumbel(size=score.shape)
            score[~valid] = -np.inf
            choice = score.argmax(axis=1)
            rows = np.arange(len(ids))
            nxt = nb[rows, choice]
            edge = g.adj_e[node, choice]
            lay = sigmoid(out[:, LAY]) * p.lay_amount
            np.add.at(self.pher, edge, lay)
            self.prev[ids] = node
            self.node[ids] = nxt
            node = nxt
            nt = g.ntype[node]

            # --- kultur: härma den bästa grannen på samma plats
            if p.culture and len(ids) > 1:
                cop = ids[rng.random(len(ids)) < p.copy_rate]
                if len(cop):
                    order = np.argsort(self.node[ids], kind="stable")
                    sid, sn = ids[order], self.node[ids][order]
                    starts = np.r_[0, np.nonzero(np.diff(sn))[0] + 1]
                    # bästa myran (högst "blomstring") på varje plats
                    pr = self.prosper[sid]
                    best_idx = np.array([s0 + np.argmax(pr[s0:e0]) for s0, e0 in zip(starts, np.r_[starts[1:], len(sid)])])
                    best_of_node = dict(zip(sn[starts].tolist(), sid[best_idx].tolist()))
                    model = np.array([best_of_node[n] for n in self.node[cop].tolist()])
                    keep = self.prosper[model] > self.prosper[cop]
                    if keep.any():
                        self._imitate(cop[keep], model[keep])

            # --- vid automaten: känn om den är levande (kravet uppfyllt) eller död, plocka mat
            at_c = nt == CLAUSE
            alive_c = self.sat_prev[node[at_c] - g.clause_node[0]]
            self.last_empty[ids[at_c]] = (~alive_c).astype(float)
            arrived = ids[at_c]
            if len(arrived):
                r = alive_c.astype(float)
                self.prosper[arrived] = p.prosper_decay * self.prosper[arrived] + (1 - p.prosper_decay) * r
                if p.learning:
                    # belöning: att komma fram till en levande automat, jämfört med hur det brukar vara
                    adv = (r - self.reward_base)[:, None, None]
                    rows = [O["deposit_clay"], O["remove_clay"]]
                    upd = p.learn_rate * adv * self.elig[arrived]
                    self.G[arrived[:, None], rows] = np.clip(self.G[arrived[:, None], rows] + upd, -10, 10)
                self.reward_base = 0.99 * self.reward_base + 0.01 * float(r.mean())
            cand = ids[at_c & ~self.carrying[ids] & (self.food[node] >= 1.0)]
            if len(cand):
                cand = rng.permutation(cand)
                cn = self.node[cand]
                order = np.argsort(cn, kind="stable")
                cand, cn = cand[order], cn[order]
                starts = np.r_[0, np.nonzero(np.diff(cn))[0] + 1]
                counts = np.diff(np.r_[starts, len(cn)])
                rank = np.arange(len(cn)) - np.repeat(starts, counts)
                take = cand[rank < np.floor(self.food[cn])]
                self.carrying[take] = True
                np.subtract.at(self.food, self.node[take], 1.0)

            # --- i boet: lämna mat
            home = ids[(nt == NEST) & self.carrying[ids]]
            self.carrying[home] = False
            self.delivered[home] += 1
            self.store += len(home)
            stats["delivered"] = len(home)

        # --- världens fysik
        np.clip(self.clay, 0, p.clay_cap, out=self.clay)
        self.clay *= (1 - p.erosion)
        new_val = self._values(self.val)
        stats["flips"] = int((new_val != self.val).sum())
        self.val = new_val
        sat = g.satisfied(self.val)
        frac = float(sat.mean())
        gain = np.clip((frac - p.sat_floor) / (1 - p.sat_floor), 0, 1) ** p.sat_power
        if sat.all():
            gain *= p.full_bonus
        cn = g.clause_node
        if sat.any():
            self.food[cn[sat]] += p.food_full * gain / sat.sum()
        self.food[cn[~sat]] *= p.food_rot
        np.minimum(self.food, p.food_cap, out=self.food)
        self.pher *= (1 - p.pher_evap)
        self.signal *= p.signal_decay

        # --- liv och död
        self.store -= self.population * p.metabolism
        self.age[self.alive] += 1
        dying = self.alive & (self.age > self.life)
        if self.store < 0:
            self.store = 0.0
            dying |= self.alive & (rng.random(len(self.alive)) < p.starve_prob)
        stats["deaths"] = int(dying.sum())
        self.alive &= ~dying

        n_birth = int(min(p.max_births_per_tick, self.store // p.birth_cost, p.pop_cap - self.population))
        if n_birth > 0 and self.population > 0:
            live = np.nonzero(self.alive)[0]
            if self.queen is not None:
                kids = self._daughters(n_birth)
            elif p.evolution:
                if p.selection == "individual":
                    w = self.delivered[live] / (self.age[live] + 100.0) + 1e-3
                else:
                    w = np.ones(len(live))
                parents = rng.choice(live, size=n_birth, p=w / w.sum())
                kids = self.mutate(self.G[parents])
            else:
                kids = self.founders[rng.integers(0, len(self.founders), n_birth)]
            self.store -= n_birth * p.birth_cost
            self._spawn(kids)
            stats["births"] = n_birth

        stats.update(tick=self.tick, pop=self.population, store=round(self.store, 3), sat_frac=frac,
                     n_sat=int(sat.sum()), m=g.m, all_sat=bool(sat.all()))
        self.sat = sat
        return stats

    def assignment(self) -> list[bool]:
        return [bool(x) for x in self.val]
