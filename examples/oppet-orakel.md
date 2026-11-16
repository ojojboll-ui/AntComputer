# Det öppna oraklet `oppet`

Oraklet visste inte om problemen gick att lösa. Facit (kolumnerna *facit* och *bästa möjliga*) räknades ut i efterhand med en riktig SAT-lösare och nådde aldrig myrorna. Varje koloni fick högst 40000 tick.

Cell: **LÖST** (verifierat, tick) eller bästa antal uppfyllda krav kolonin nådde. ★ = nådde bästa möjliga på ett omöjligt problem.

| problem | facit | bästa möjliga | WalkSAT (flips) | instinkt | evolverad | evolverad utan instinkter | handgjord reparatör |
|---|---|---|---|---|---|---|---|
| Ramsey: K5 utan röd K3 och blå K3 | lösbart | 20/20 | 3 | 20/20 † | **LÖST** (t=4236) | **LÖST** (t=595) | **LÖST** (t=924) |
| Ramsey: K6 utan röd K3 och blå K3 | omöjligt | 38/40 | — | 34/40 † | 38/40 ★ † | 38/40 ★ † | 38/40 ★ † |
| Ramsey: K8 utan röd K3 och blå K4 | lösbart | 126/126 | 12 | 124/126 † | 123/126 † | 121/126 † | **LÖST** (t=817) |
| Ramsey: K9 utan röd K3 och blå K4 | omöjligt | 209/210 | — | 205/210 † | 204/210 † | 201/210 † | 209/210 ★ |
| Ramsey: K17 utan röd K4 och blå K4 | lösbart | 4760/4760 | — | 3999/4760 † | 3640/4760 † | 4321/4760 † | 4716/4760 † |
| Schur: 1..4 i 2 färger | lösbart | 12/12 | 7 | 12/12 † | 12/12 † | 8/12 † | **LÖST** (t=862) |
| Schur: 1..5 i 2 färger | omöjligt | 16/17 | — | 16/17 ★ † | 16/17 ★ † | 14/17 † | 16/17 ★ † |
| Schur: 1..13 i 3 färger | lösbart | 139/139 | 736 | 136/139 | 136/139 † | 134/139 | 138/139 † |
| Schur: 1..14 i 3 färger | omöjligt | 160/161 | — | 157/161 † | 159/161 | 153/161 † | 160/161 ★ † |
| van der Waerden: 1..8 utan enfärgad följd av längd 3 | lösbart | 24/24 | 4 | 24/24 † | **LÖST** (t=766) | 23/24 † | **LÖST** (t=143) |
| van der Waerden: 1..9 utan enfärgad följd av längd 3 | omöjligt | 31/32 | — | 31/32 ★ | 31/32 ★ † | 31/32 ★ | 31/32 ★ |
| van der Waerden: 1..34 utan enfärgad följd av längd 4 | lösbart | 352/352 | 2145 | 301/352 † | 346/352 † | 303/352 † | 346/352 |
| van der Waerden: 1..35 utan enfärgad följd av längd 4 | omöjligt | 373/374 | — | 362/374 † | 364/374 | 342/374 † | 369/374 † |
| Duvslag: 4 duvor i 4 hål | lösbart | 28/28 | 5 | 27/28 † | 28/28 | 27/28 | **LÖST** (t=4084) |
| Duvslag: 5 duvor i 4 hål | omöjligt | 44/45 | — | 43/45 † | 44/45 ★ † | 44/45 ★ † | 44/45 ★ |
| Färgning: Petersengrafen med 3 färger | lösbart | 85/85 | 19 | 82/85 † | 81/85 † | 83/85 † | **LÖST** (t=9871) |
| Färgning: Petersengrafen med 2 färger | omöjligt | 47/50 | — | 45/50 † | 42/50 † | 46/50 † | 47/50 ★ † |
| 8 damer på 8x8-bräde | lösbart | 736/736 | 141 | 733/736 † | 733/736 | 730/736 | 735/736 |
| 3 damer på 3x3-bräde | omöjligt | 30/31 | — | 30/31 ★ † | 30/31 ★ | 30/31 ★ | 30/31 ★ † |
| Faktorisera 15 | lösbart | 116/116 | 63 | 114/116 | 112/116 | 111/116 † | 115/116 |
| Faktorisera 13 (primtal?) | omöjligt | 115/116 | — | 112/116 † | 112/116 † | 112/116 | 115/116 ★ † |

† = kolonin dog ut.

## Vad gör kolonierna när det är omöjligt?

Sista fjärdedelen av körningen, för kolonier som inte löste problemet. *Flips per tick* visar hur mycket de fortfarande ändrar sitt svar.

| facit | antal körningar | befolkning | andel krav uppfyllda | flips per tick | andel som nådde bästa möjliga |
|---|---|---|---|---|---|
| lösbart (olösta) | 16 | 172 | 0.913 | 0.17 | 2/16 |
| omöjligt (olösta) | 15 | 192 | 0.932 | 0.05 | 11/15 |
