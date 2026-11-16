# Skalning `skala-evo`

Slumpad 3-SAT med 4.26 krav per variabel, 6 lösbara instanser per storlek. Myrorna får högst 40000 tick per instans. Värden är medianer i antal variabelbyten (flips); en olöst instans räknas som oändligt lång (— = median olöst).

| n | WalkSAT | slumpvandring | instinct (flips) | evo_best_queen_workers (flips) | evo-blank_best_queen_workers (flips) | handgjord_reparatorer (flips) | instinct lösta | evo_best_queen_workers lösta | evo-blank_best_queen_workers lösta | handgjord_reparatorer lösta |
|---|---|---|---|---|---|---|---|---|---|---|
| 10 | 14 | 54 | — | 156 | 1102 | 90 | 2/6 | 4/6 | 4/6 | 6/6 |
| 20 | 42 | 181 | — | — | — | 2576 | 0/6 | 0/6 | 0/6 | 5/6 |
| 30 | 140 | 1013 | — | — | — | — | 0/6 | 1/6 | 0/6 | 3/6 |
| 40 | 188 | 2308 | — | — | — | — | 0/6 | 0/6 | 0/6 | 0/6 |
| 50 | 494 | 20320 | — | — | — | — | 0/6 | 0/6 | 0/6 | 0/6 |

## Tillväxt

*Faktor per variabel*: hur mycket svårare varje extra variabel gör problemet, om tillväxten är exponentiell. *Grad*: exponenten om den i stället är polynomiell (n^grad). R² visar vilken modell som passar bäst. Med så här få storlekar är siffrorna en fingervisning, inte ett bevis.

| metod | faktor per variabel | R² exp | grad | R² poly | storlekar |
|---|---|---|---|---|---|
| walksat | 1.089 | 0.97 | 2.13 | 0.97 | [10, 20, 30, 40, 50] |
| random_walk | 1.155 | 0.98 | 3.45 | 0.91 | [10, 20, 30, 40, 50] |
| ants_instinct | för få lösta storlekar | | | | |
| ants_evo_best_queen_workers | för få lösta storlekar | | | | |
| ants_evo-blank_best_queen_workers | för få lösta storlekar | | | | |
| ants_handgjord_reparatorer | för få lösta storlekar | | | | |
