# Skalning `skala-larande-med`

Slumpad 3-SAT med 4.26 krav per variabel, 6 lösbara instanser per storlek. Myrorna får högst 40000 tick per instans. Värden är medianer i antal variabelbyten (flips); en olöst instans räknas som oändligt lång (— = median olöst).

| n | WalkSAT | slumpvandring | instinct (flips) | evo-baldwin_best_queen_workers (flips) | evo-lamarck_best_queen_workers (flips) | handgjord_reparatorer (flips) | instinct lösta | evo-baldwin_best_queen_workers lösta | evo-lamarck_best_queen_workers lösta | handgjord_reparatorer lösta |
|---|---|---|---|---|---|---|---|---|---|---|
| 10 | 12 | 46 | — | 46 | 186 | 153 | 1/6 | 6/6 | 6/6 | 6/6 |
| 20 | 44 | 186 | — | 1412 | — | 932 | 0/6 | 4/6 | 1/6 | 6/6 |
| 30 | 179 | 1286 | — | — | — | — | 0/6 | 3/6 | 0/6 | 3/6 |
| 40 | 158 | 2119 | — | — | — | — | 0/6 | 3/6 | 0/6 | 1/6 |

## Tillväxt

*Faktor per variabel*: hur mycket svårare varje extra variabel gör problemet, om tillväxten är exponentiell. *Grad*: exponenten om den i stället är polynomiell (n^grad). R² visar vilken modell som passar bäst. Med så här få storlekar är siffrorna en fingervisning, inte ett bevis.

| metod | faktor per variabel | R² exp | grad | R² poly | storlekar |
|---|---|---|---|---|---|
| walksat | 1.096 | 0.87 | 2.04 | 0.94 | [10, 20, 30, 40] |
| random_walk | 1.144 | 0.96 | 2.90 | 0.97 | [10, 20, 30, 40] |
| ants_instinct | för få lösta storlekar | | | | |
| ants_evo-baldwin_best_queen_workers | för få lösta storlekar | | | | |
| ants_evo-lamarck_best_queen_workers | för få lösta storlekar | | | | |
| ants_handgjord_reparatorer | för få lösta storlekar | | | | |
