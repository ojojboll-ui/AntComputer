# Körning `sat-demo`

Orakel: **sat**, 4 kolonier, 30000 tick, frö 1, evolution på (urval: colony), förvarning vid byte av. Tid: 88.1 s.

Uppnådda nivåer per koloni: [4, 1, 1, 2]

## Lösta problem

| tick | koloni | problem | svar | verifierat | myr-flips | WalkSAT | slumpvandring | blind slump |
|---|---|---|---|---|---|---|---|---|
| 3925 | 0 | 3-SAT n=10 m=40 | tilldelning 1010100100 | ja | 396 | 6 | 20 | 72 |
| 3983 | 3 | 3-SAT n=10 m=40 | tilldelning 1010100000 | ja | 469 | 6 | 20 | 72 |
| 5231 | 1 | 3-SAT n=10 m=40 | tilldelning 1000100011 | ja | 838 | 6 | 20 | 72 |
| 5872 | 0 | 3-SAT n=14 m=56 | tilldelning 10001000110111 | ja | 211 | 9 | 22 | 569 |
| 7492 | 3 | 3-SAT n=14 m=56 | tilldelning 10101001000110 | ja | 134 | 9 | 22 | 569 |
| 8583 | 0 | 3-SAT n=18 m=72 | tilldelning 101010010001110111 | ja | 283 | 8 | 29 | 2210 |
| 13691 | 2 | 3-SAT n=10 m=40 | tilldelning 1000110011 | ja | 1259 | 6 | 20 | 72 |
| 22706 | 0 | 3-SAT n=22 m=88 | tilldelning 1010100100011001101110 | ja | 308 | 22 | 55 | 4311 |

Flips = antal gånger en variabel bytt värde innan lösningen. Jämförelsealgoritmerna visar median över 20 körningar (— = löste inte hälften inom gränsen).

## Var kolonierna slutade

- Koloni 0: nivå 4, 3-SAT n=26 m=104, befolkning 182, 95/104 krav uppfyllda
- Koloni 1: nivå 1, 3-SAT n=14 m=56, befolkning 150, 51/56 krav uppfyllda
- Koloni 2: nivå 1, 3-SAT n=14 m=56, befolkning 306, 55/56 krav uppfyllda
- Koloni 3: nivå 2, 3-SAT n=18 m=72, befolkning 75, 66/72 krav uppfyllda

## Beteendets fingeravtryck (sista tiondelen av körningen)

*Reparationsfokus* > 1 betyder att leran oftare än slumpen läggs där den lagar ett brutet krav (det är kärnan i WalkSAT). Andelar visar *vem* som bygger.

| koloni | reparationsfokus | andel lera från matbärare | andel lera efter död automat |
|---|---|---|---|
| 0 | 0.78 | 0.09 | 0.02 |
| 1 | 0.61 | 0.09 | 0.02 |
| 2 | 0.51 | 0.09 | 0.01 |
| 3 | 0.99 | 0.23 | 0.01 |

## Gener som förändrats mest (jämfört med medfödd instinkt)

Läs som: *när myran känner `input`, påverkas `output` med vikten `nu`*.

| koloni | output | input | start | nu | spridning |
|---|---|---|---|---|---|
| 0 | follow_0 | bias | 1.0 | 3.0 | 0.33 |
| 0 | clay_attr | at_nest | 0.0 | -1.81 | 0.3 |
| 0 | back_attr | at_nest | 0.0 | -1.78 | 0.25 |
| 0 | follow_1 | pad_winning | 0.0 | -1.7 | 0.41 |
| 0 | lay_0 | at_clause | 0.0 | -1.67 | 0.41 |
| 0 | lay_0 | pad_winning | 0.0 | -1.58 | 0.41 |
| 0 | follow_2 | pad_winning | 0.0 | 1.45 | 0.42 |
| 0 | lay_1 | change_signal | 0.0 | 1.36 | 0.4 |
| 0 | back_attr | clay_here | 0.0 | -1.3 | 0.39 |
| 0 | clay_attr | at_clause | 0.0 | -1.3 | 0.34 |
| 0 | follow_1 | at_pad | 0.0 | 1.26 | 0.4 |
| 0 | follow_2 | clay_here | 0.0 | -1.25 | 0.56 |
| 1 | follow_0 | bias | 1.0 | 2.99 | 0.34 |
| 1 | clay_attr | at_nest | 0.0 | -1.8 | 0.32 |
| 1 | back_attr | at_nest | 0.0 | -1.78 | 0.25 |
| 1 | follow_1 | pad_winning | 0.0 | -1.67 | 0.41 |
| 1 | lay_0 | at_clause | 0.0 | -1.66 | 0.42 |
| 1 | lay_0 | pad_winning | 0.0 | -1.58 | 0.41 |
| 1 | follow_2 | pad_winning | 0.0 | 1.43 | 0.46 |
| 1 | lay_1 | change_signal | 0.0 | 1.37 | 0.4 |
| 1 | back_attr | clay_here | 0.0 | -1.3 | 0.4 |
| 1 | clay_attr | at_clause | 0.0 | -1.3 | 0.35 |
| 1 | follow_1 | at_pad | 0.0 | 1.27 | 0.4 |
| 1 | follow_2 | clay_here | 0.0 | -1.26 | 0.56 |
| 2 | follow_0 | bias | 1.0 | 3.08 | 0.5 |
| 2 | back_attr | at_nest | 0.0 | -1.73 | 0.3 |
| 2 | clay_attr | at_nest | 0.0 | -1.73 | 0.42 |
| 2 | lay_0 | pad_winning | 0.0 | -1.73 | 0.33 |
| 2 | lay_0 | at_clause | 0.0 | -1.67 | 0.34 |
| 2 | lay_1 | change_signal | 0.0 | 1.52 | 0.36 |
| 2 | follow_1 | pad_winning | 0.0 | -1.51 | 0.27 |
| 2 | lay_2 | pad_winning | 0.0 | 1.43 | 0.42 |
| 2 | follow_2 | clay_here | 0.0 | -1.34 | 0.67 |
| 2 | follow_1 | at_pad | 0.0 | 1.33 | 0.48 |
| 2 | deposit_clay | at_nest | 0.0 | -1.25 | 0.34 |
| 2 | nest_attr | change_signal | 0.0 | 1.24 | 0.32 |
| 3 | follow_0 | bias | 1.0 | 3.01 | 0.37 |
| 3 | lay_0 | at_clause | 0.0 | -1.79 | 0.33 |
| 3 | clay_attr | at_nest | 0.0 | -1.76 | 0.23 |
| 3 | follow_1 | pad_winning | 0.0 | -1.7 | 0.21 |
| 3 | lay_0 | pad_winning | 0.0 | -1.65 | 0.38 |
| 3 | back_attr | at_nest | 0.0 | -1.56 | 0.43 |
| 3 | food_attr | at_clause | 0.0 | 1.38 | 0.49 |
| 3 | nest_attr | pad_winning | 0.0 | 1.37 | 0.21 |
| 3 | clay_attr | at_clause | 0.0 | -1.35 | 0.23 |
| 3 | follow_2 | food_here | 0.0 | 1.29 | 0.36 |
| 3 | follow_1 | at_pad | 0.0 | 1.28 | 0.36 |
| 3 | follow_2 | pad_winning | 0.0 | 1.27 | 0.23 |
