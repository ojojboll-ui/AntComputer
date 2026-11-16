#!/usr/bin/env python3
"""Jämför evolutionskörningar sida vid sida.

    python compare_evo.py runs/evo runs/evo-baldwin runs/evo-lamarck runs/evo-culture
"""
import json
import sys
from pathlib import Path


def main() -> None:
    rows = []
    for d in sys.argv[1:]:
        f = Path(d) / "evolution.json"
        if not f.exists():
            print(f"saknas: {f}")
            continue
        s = json.loads(f.read_text())
        log, a = s["log"], s["args"]
        last = log[-10:]
        first_raise = next((r["gen"] for r in log if r["n"] > log[0]["n"]), None)
        rows.append((Path(d).name, a.get("mode", "none"), a.get("blank_slate", False), len(log), log[-1]["n"],
                     sum(r["total_solved"] for r in log),
                     sum(r["share_solving"] for r in last) / len(last),
                     first_raise,
                     sum((r["median_repair_focus"] or 0) for r in last) / len(last)))
    L = ["| körning | läge | instinkter | generationer | slutlig storlek n | lösta problem totalt | "
         "andel som löser (sista 10 gen) | första storleksökning (gen) | reparationsfokus median (sista 10) |",
         "|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        L.append(f"| {r[0]} | {r[1]} | {'nej' if r[2] else 'ja'} | {r[3]} | {r[4]} | {r[5]} | {r[6]:.0%} | "
                 f"{'—' if r[7] is None else r[7]} | {r[8]:.2f} |")
    print("\n".join(L))


if __name__ == "__main__":
    main()
