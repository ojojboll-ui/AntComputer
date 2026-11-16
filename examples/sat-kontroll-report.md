# Körning `sat-kontroll`

Orakel: **sat**, 4 kolonier, 30000 tick, frö 1, evolution AV (urval: colony), förvarning vid byte av. Tid: 71.3 s.

Uppnådda nivåer per koloni: [0, 1, 1, 3]

## Lösta problem

| tick | koloni | problem | svar | verifierat | myr-flips | WalkSAT | slumpvandring | blind slump |
|---|---|---|---|---|---|---|---|---|
| 191 | 3 | 3-SAT n=10 m=40 | tilldelning 1000110011 | ja | 35 | 6 | 20 | 72 |
| 1058 | 3 | 3-SAT n=14 m=56 | tilldelning 10011100111001 | ja | 123 | 10 | 40 | 532 |
| 8906 | 2 | 3-SAT n=10 m=40 | tilldelning 1000100011 | ja | 918 | 6 | 20 | 72 |
| 14791 | 3 | 3-SAT n=18 m=72 | tilldelning 100010001100000111 | ja | 1843 | 14 | 59 | 2045 |
| 17497 | 1 | 3-SAT n=10 m=40 | tilldelning 1100100011 | ja | 2319 | 6 | 20 | 72 |

Flips = antal gånger en variabel bytt värde innan lösningen. Jämförelsealgoritmerna visar median över 20 körningar (— = löste inte hälften inom gränsen).

## Var kolonierna slutade

- Koloni 0: nivå 0, 3-SAT n=10 m=40, befolkning 150, 40/40 krav uppfyllda
- Koloni 1: nivå 1, 3-SAT n=14 m=56, befolkning 119, 51/56 krav uppfyllda
- Koloni 2: nivå 1, 3-SAT n=14 m=56, befolkning 217, 53/56 krav uppfyllda
- Koloni 3: nivå 3, 3-SAT n=22 m=88, befolkning 118, 79/88 krav uppfyllda

## Beteendets fingeravtryck (sista tiondelen av körningen)

*Reparationsfokus* > 1 betyder att leran oftare än slumpen läggs där den lagar ett brutet krav (det är kärnan i WalkSAT). Andelar visar *vem* som bygger.

| koloni | reparationsfokus | andel lera från matbärare | andel lera efter död automat |
|---|---|---|---|
| 0 | 1.08 | 0.05 | 0.08 |
| 1 | 1.04 | 0.07 | 0.09 |
| 2 | 1.15 | 0.06 | 0.09 |
| 3 | 1.11 | 0.06 | 0.08 |

## Gener som förändrats mest (jämfört med medfödd instinkt)

Läs som: *när myran känner `input`, påverkas `output` med vikten `nu`*.

| koloni | output | input | start | nu | spridning |
|---|---|---|---|---|---|
| 0 | lay_0 | pad_winning | 0.0 | -0.13 | 0.3 |
| 0 | lay_1 | at_pad | 0.0 | 0.13 | 0.31 |
| 0 | deposit_clay | at_clause | 0.0 | -0.11 | 0.32 |
| 0 | remove_clay | food_here | 0.0 | -0.1 | 0.38 |
| 0 | remove_clay | last_clause_dead | 0.0 | 0.1 | 0.29 |
| 0 | lay_0 | bias | -2.0 | -2.1 | 0.32 |
| 0 | follow_0 | at_clause | 0.0 | -0.09 | 0.32 |
| 0 | back_attr | hunger | 0.0 | 0.08 | 0.32 |
| 0 | lay_0 | at_clause | 0.0 | -0.08 | 0.32 |
| 0 | follow_2 | at_clause | 0.0 | -0.08 | 0.31 |
| 0 | follow_0 | last_clause_dead | 0.0 | -0.07 | 0.3 |
| 0 | food_attr | at_nest | 0.0 | 0.07 | 0.3 |
| 1 | follow_2 | hunger | 0.0 | -0.1 | 0.28 |
| 1 | deposit_clay | food_here | 0.0 | 0.07 | 0.31 |
| 1 | lay_2 | at_pad | 0.0 | 0.07 | 0.3 |
| 1 | clay_attr | carrying | 0.0 | -0.07 | 0.26 |
| 1 | follow_2 | carrying | 0.0 | 0.07 | 0.3 |
| 1 | follow_0 | bias | 1.0 | 0.93 | 0.25 |
| 1 | food_attr | at_nest | 0.0 | 0.07 | 0.31 |
| 1 | lay_1 | food_here | 0.0 | -0.07 | 0.33 |
| 1 | follow_2 | at_nest | 0.0 | 0.06 | 0.28 |
| 1 | food_attr | at_pad | 0.0 | 0.06 | 0.27 |
| 1 | remove_clay | bias | -2.0 | -1.94 | 0.3 |
| 1 | back_attr | food_here | 0.0 | -0.06 | 0.32 |
| 2 | follow_1 | at_clause | 0.0 | -0.1 | 0.33 |
| 2 | follow_2 | at_clause | 0.0 | -0.07 | 0.33 |
| 2 | nest_attr | clay_here | 0.0 | -0.07 | 0.33 |
| 2 | follow_1 | hunger | 0.0 | 0.07 | 0.32 |
| 2 | clay_attr | at_nest | 0.0 | -0.06 | 0.3 |
| 2 | back_attr | last_clause_dead | 0.0 | -0.06 | 0.3 |
| 2 | nest_attr | pad_winning | 0.0 | -0.06 | 0.31 |
| 2 | nest_attr | bias | -0.5 | -0.44 | 0.32 |
| 2 | follow_1 | food_here | 0.0 | -0.06 | 0.33 |
| 2 | lay_2 | last_clause_dead | 0.0 | 0.06 | 0.31 |
| 2 | food_attr | pad_winning | 0.0 | 0.06 | 0.31 |
| 2 | food_attr | last_clause_dead | 0.0 | -0.06 | 0.25 |
| 3 | lay_1 | at_pad | 0.0 | 0.13 | 0.3 |
| 3 | lay_0 | pad_winning | 0.0 | -0.12 | 0.3 |
| 3 | deposit_clay | at_clause | 0.0 | -0.11 | 0.33 |
| 3 | remove_clay | food_here | 0.0 | -0.09 | 0.37 |
| 3 | follow_0 | at_clause | 0.0 | -0.09 | 0.3 |
| 3 | remove_clay | last_clause_dead | 0.0 | 0.09 | 0.28 |
| 3 | back_attr | hunger | 0.0 | 0.08 | 0.31 |
| 3 | lay_0 | bias | -2.0 | -2.07 | 0.3 |
| 3 | lay_0 | at_clause | 0.0 | -0.07 | 0.31 |
| 3 | follow_2 | at_clause | 0.0 | -0.07 | 0.31 |
| 3 | food_attr | at_nest | 0.0 | 0.06 | 0.3 |
| 3 | remove_clay | bias | -2.0 | -2.06 | 0.3 |
