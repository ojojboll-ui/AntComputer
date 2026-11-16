# Skalning `skala`

Slumpad 3-SAT med 4.26 krav per variabel, 10 lösbara instanser per storlek. Myrorna får högst 40000 tick per instans. Värden är medianer i antal variabelbyten (flips); en olöst instans räknas som oändligt lång (— = median olöst).

| n | WalkSAT | slumpvandring | instinct (flips) | trana (flips) | instinct lösta | trana lösta |
|---|---|---|---|---|---|---|
| 10 | 12 | 52 | — | — | 3/10 | 4/10 |
| 15 | 36 | 144 | — | — | 1/10 | 1/10 |
| 20 | 46 | 140 | — | — | 0/10 | 0/10 |
| 25 | 128 | 478 | — | — | 0/10 | 0/10 |
| 30 | 96 | 325 | — | — | 0/10 | 1/10 |
| 40 | 163 | 2396 | — | — | 0/10 | 0/10 |
| 50 | 579 | 27037 | — | — | 0/10 | 0/10 |

## Tillväxt

*Faktor per variabel*: hur mycket svårare varje extra variabel gör problemet, om tillväxten är exponentiell. *Grad*: exponenten om den i stället är polynomiell (n^grad). R² visar vilken modell som passar bäst. Med så här få storlekar är siffrorna en fingervisning, inte ett bevis.

| metod | faktor per variabel | R² exp | grad | R² poly | storlekar |
|---|---|---|---|---|---|
| walksat | 1.088 | 0.91 | 2.15 | 0.93 | [10, 15, 20, 25, 30, 40, 50] |
| random_walk | 1.156 | 0.94 | 3.44 | 0.82 | [10, 15, 20, 25, 30, 40, 50] |
| ants_instinct | för få lösta storlekar | | | | |
| ants_trana | för få lösta storlekar | | | | |
