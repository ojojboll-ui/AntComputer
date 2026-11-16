# Körning `faktor-demo`

Orakel: **factor**, 4 kolonier, 30000 tick, frö 1, evolution på (urval: colony), förvarning vid byte av. Tid: 87.8 s.

Uppnådda nivåer per koloni: [0, 0, 0, 0]

## Lösta problem

| tick | koloni | problem | svar | verifierat | myr-flips | WalkSAT | slumpvandring | blind slump |
|---|---|---|---|---|---|---|---|---|

Flips = antal gånger en variabel bytt värde innan lösningen. Jämförelsealgoritmerna visar median över 20 körningar (— = löste inte hälften inom gränsen).

## Var kolonierna slutade

- Koloni 0: nivå 0, faktorisera 15, befolkning 68, 103/116 krav uppfyllda
- Koloni 1: nivå 0, faktorisera 15, befolkning 81, 101/116 krav uppfyllda
- Koloni 2: nivå 0, faktorisera 15, befolkning 150, 98/116 krav uppfyllda
- Koloni 3: nivå 0, faktorisera 15, befolkning 102, 104/116 krav uppfyllda

## Beteendets fingeravtryck (sista tiondelen av körningen)

*Reparationsfokus* > 1 betyder att leran oftare än slumpen läggs där den lagar ett brutet krav (det är kärnan i WalkSAT). Andelar visar *vem* som bygger.

| koloni | reparationsfokus | andel lera från matbärare | andel lera efter död automat |
|---|---|---|---|
| 0 | 0.87 | 0.05 | 0.07 |
| 1 | 0.90 | 0.02 | 0.07 |
| 2 | 0.92 | 0.03 | 0.08 |
| 3 | 1.04 | 0.02 | 0.08 |

## Gener som förändrats mest (jämfört med medfödd instinkt)

Läs som: *när myran känner `input`, påverkas `output` med vikten `nu`*.

| koloni | output | input | start | nu | spridning |
|---|---|---|---|---|---|
| 0 | lay_1 | clay_here | 0.0 | -3.46 | 0.39 |
| 0 | nest_attr | last_clause_dead | 0.0 | 2.6 | 0.55 |
| 0 | lay_1 | pad_winning | 0.0 | 2.03 | 1.16 |
| 0 | remove_clay | last_clause_dead | 0.0 | -1.82 | 0.67 |
| 0 | lay_2 | at_clause | 0.0 | 1.63 | 0.24 |
| 0 | follow_2 | hunger | 0.0 | -1.59 | 0.35 |
| 0 | deposit_clay | at_pad | 0.0 | 1.54 | 0.45 |
| 0 | deposit_clay | change_signal | 0.0 | -1.5 | 0.56 |
| 0 | lay_2 | carrying | 0.0 | 1.47 | 0.46 |
| 0 | nest_attr | at_clause | 0.0 | -1.43 | 0.17 |
| 0 | nest_attr | at_pad | 0.0 | 1.42 | 0.67 |
| 0 | follow_2 | carrying | 0.0 | 1.4 | 0.36 |
| 1 | lay_1 | clay_here | 0.0 | -3.29 | 0.53 |
| 1 | lay_2 | carrying | 0.0 | 2.06 | 0.37 |
| 1 | nest_attr | last_clause_dead | 0.0 | 1.68 | 0.61 |
| 1 | clay_attr | bias | 0.0 | -1.66 | 0.29 |
| 1 | lay_0 | pad_winning | 0.0 | -1.66 | 0.65 |
| 1 | food_attr | pad_winning | 0.0 | -1.53 | 0.34 |
| 1 | deposit_clay | hunger | 0.0 | -1.51 | 0.26 |
| 1 | follow_2 | carrying | 0.0 | 1.48 | 0.39 |
| 1 | lay_2 | at_clause | 0.0 | 1.46 | 0.23 |
| 1 | clay_attr | clay_here | 0.0 | 1.44 | 0.37 |
| 1 | follow_0 | bias | 1.0 | -0.38 | 0.45 |
| 1 | follow_1 | carrying | 1.0 | -0.36 | 0.6 |
| 2 | lay_1 | clay_here | 0.0 | -2.83 | 0.61 |
| 2 | nest_attr | last_clause_dead | 0.0 | 2.26 | 0.86 |
| 2 | follow_0 | last_clause_dead | 0.0 | 1.6 | 1.24 |
| 2 | deposit_clay | hunger | 0.0 | -1.5 | 0.66 |
| 2 | lay_2 | carrying | 0.0 | 1.42 | 0.38 |
| 2 | follow_2 | pad_winning | 0.0 | 1.34 | 0.43 |
| 2 | lay_2 | at_clause | 0.0 | 1.32 | 0.39 |
| 2 | deposit_clay | at_pad | 0.0 | 1.3 | 0.58 |
| 2 | food_attr | bias | 2.0 | 3.22 | 0.8 |
| 2 | lay_1 | change_signal | 0.0 | 1.22 | 0.35 |
| 2 | back_attr | change_signal | 0.0 | -1.22 | 0.51 |
| 2 | food_attr | last_clause_dead | 0.0 | 1.2 | 0.45 |
| 3 | lay_1 | clay_here | 0.0 | -2.87 | 0.58 |
| 3 | nest_attr | last_clause_dead | 0.0 | 2.2 | 0.89 |
| 3 | follow_0 | last_clause_dead | 0.0 | 1.54 | 1.23 |
| 3 | deposit_clay | hunger | 0.0 | -1.51 | 0.62 |
| 3 | lay_2 | carrying | 0.0 | 1.43 | 0.35 |
| 3 | lay_2 | at_clause | 0.0 | 1.33 | 0.37 |
| 3 | follow_2 | pad_winning | 0.0 | 1.33 | 0.41 |
| 3 | deposit_clay | at_pad | 0.0 | 1.26 | 0.59 |
| 3 | back_attr | change_signal | 0.0 | -1.23 | 0.49 |
| 3 | lay_1 | change_signal | 0.0 | 1.23 | 0.32 |
| 3 | food_attr | last_clause_dead | 0.0 | 1.2 | 0.41 |
| 3 | food_attr | bias | 2.0 | 3.19 | 0.79 |
