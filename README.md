# Myrdatorn

En virtuell myrstack som måste lösa riktiga matematiska problem för att överleva.
Inspirerad av myrdatorn hos Jeff Noon.

Myrorna vet inte att de räknar. De vill bara äta. Datorn, *oraklet*, styr
världens fysik så att mat bara finns när kolonin håller sitt bo i ett tillstånd
som motsvarar ett korrekt svar. När ett problem är löst verifieras svaret
oberoende, och oraklet skärper genast kraven.

## Snabbstart

```bash
pip install numpy
python run.py --name forsta --ticks 30000             # växande 3-SAT
python run.py --name faktor --oracle factor --ticks 100000 --trace-every 0
python run.py --name kontroll --no-evolution          # kontrollgrupp
python run.py --name snall --announce-changes         # myrorna förvarnas vid regelbyte
python run.py --help                                  # alla flaggor, t.ex. --param erosion=0.005
python tests/test_core.py
```

Varje körning skriver till `runs/<namn>/`:

| fil | innehåll |
|---|---|
| `report.md` | lösta problem, jämförelse mot klassiska algoritmer, beteendets fingeravtryck, vilka gener som förändrats |
| `replay.html` | öppna i webbläsaren och se kolonin arbeta (koloni 0) |
| `timeseries.csv` | befolkning, uppfyllda krav, lerbyggande och reparationsfokus över tid |
| `summary.json` | alla händelser och parametrar |
| `genomes_colony*.npy` | arvsmassan hos alla levande myror vid slutet |

Exempel finns i [`examples/`](examples/).

## Hur världen fungerar (kretsmodellen)

```
                 [krav 1]   [krav 2]   [krav 3]      <- matautomater: mat växer bara om kravet är uppfyllt
                  /  |  \    /   \      |   \
          (x1=S)(x1=F)(x2=S)(x2=F)(x3=S)(x3=F) ...   <- kammarpar: mest lera vinner = variabelns värde
                    \    \    |    /    /
                           [ BOET ]                  <- maten lämnas här, drottningen föder nya myror
```

- **Variabler är kammarpar.** Myrorna bär lera. Den kammare som leder med minst
  `flip_margin` lera vinner. Leran eroderar, så minnet måste underhållas.
- **Krav är matautomater**, förbundna med tunnlar till kamrarna för sina literaler.
  Ett uppfyllt krav "doftar levande" och producerar mat. Ett brutet krav är dött.
- **Matflödet** följer `((andel uppfyllda - 0.8) / 0.2)^2`, med dubbel fest när allt är
  uppfyllt och en jackpot när lösningen hållit i 20 tick. Under 80 % uppfyllt finns ingen mat alls.
- **Myrorna** har en arvsmassa `W` (12 × 11 vikter) som översätter vad de känner
  (bär mat? lera här? vinner den här kammaren? var senaste automaten död? hunger? larmsignal?)
  till tunnelval, lerbyggande, lerrivning och tre doftämnen utan förutbestämd betydelse.
  De föds med enkla födosöksinstinkter men **inget** om lera. Lerbyggandet måste de uppfinna själva.
- **Evolution:** arbetarna är sterila, som i verkligheten. Kolonier konkurrerar: var 1000:e
  tick ersätts den sämsta kolonin av muterad avkomma från den bästa (`--selection colony`).
  Alternativet `--selection individual` låter myror som bär hem mycket mat få fler barn.

## Oraklen

| `--oracle` | problemet | hur det utvecklas |
|---|---|---|
| `sat` | slumpad 3-SAT med planterad lösning | varje lösning ger 4 nya variabler och 16 nya krav; gamla krav finns kvar |
| `enumerate` | 3-SAT med många lösningar | varje funnen lösning förbjuds: hitta en till |
| `factor` | hitta p, q > 1 med p·q = N, kodat som en multiplikationskrets | nästa halvprimtal: 15, 21, 22, 25, 26, … |

Regelbyten är tysta som förval, så myrorna märker bara att maten tar slut. Med
`--announce-changes` får de en larmsignal som klingar av.

## Första resultaten (30 000 tick, 4 kolonier, frö 1)

| | med evolution | utan evolution (kontroll) |
|---|---|---|
| lösta problem | 8 | 5 |
| högsta nivå | 4 (löste n = 22 variabler, 88 krav) | 3 |

Jämfört med klassiska algoritmer, räknat i antal variabelbyten till lösning:

| problem | myrorna | WalkSAT | slumpvandring | blind slump |
|---|---|---|---|---|
| n = 10 | 396–1259 | 6 | 20 | 72 |
| n = 18 | 283 | 8 | 29 | 2210 |
| n = 22 | 308 | 22 | 55 | 4311 |

Ärlig tolkning:
- Myrorna är **mycket sämre än WalkSAT**, men **klart bättre än blind slump** när
  problemen växer. De använder alltså information om problemet på något sätt.
- Det intressanta är *hur*. Reparationsfokus, alltså hur ofta lera läggs där den lagar ett brutet
  krav, ligger **under 1**. Kolonierna gör alltså inte det WalkSAT gör. De verkar i stället
  stabilisera det som fungerar och låta det trasiga fluktuera. Det är en annan strategi, och det
  är precis den sortens sak experimentet ska hitta och som vi nu behöver förstå bättre.
- Faktorisering av 15 (27 variabler, 116 krav) har ännu inte lösts inom 30 000 tick. Kolonierna
  fastnar på 98–104 av 116 krav.
- Resultaten varierar mycket mellan slumpfrön. Slutsatser kräver många körningar per inställning.

## Vägen mot oraklet

1. **Statistik:** kör många frön per inställning och jämför med kontrollgruppen.
2. **Kastsystem:** låt drottningen ha flera arvsmassor, så att arbetsdelning kan uppstå.
3. **Rikare minne:** ett par bitar som myran själv kan skriva i, så att de kan "räkna" i kroppen.
4. **Problem som växer under räkningens gång:** oraklet lägger till krav redan när en viss andel
   är uppfylld, inte först när allt är löst.
5. **Oraklet på riktigt:** låt datorn välja *vilket* problem som ska ställas utifrån kolonins
   beteende, och läs av svaret i kolonins form i stället för i en förutbestämd kammare.
6. **Strategiarkeologi:** destillera den evolverade arvsmassan till en vanlig algoritm och
   testa om den slår kända metoder på någon klass av problem.

## Kod

- `antcomputer/problems.py`: problem som CNF plus oberoende verifierare (3-SAT, faktoriseringskrets)
- `antcomputer/oracle.py`: oraklen och hur de skärper kraven
- `antcomputer/world.py`: myrvärlden: graf, lera, mat, doft, arvsmassa, liv och död
- `antcomputer/baselines.py`: WalkSAT, slumpvandring, blind slump
- `antcomputer/experiment.py`: körloop, ö-selektion, loggning, rapport, inspelning
