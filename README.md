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
pip install python-sat   # valfritt: facit för det öppna oraklet
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

Fler verktyg:
- `sweep.py`: kör samma jämförelse över många frön (t.ex. olika avslöjandeordningar)
- `scaling.py`: mäter hur svårigheten växer med problemets storlek, jämfört med WalkSAT och slumpvandring

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
| `fresh` | slumpad 3-SAT, 4,26 krav per variabel | varje lösning ger ett **helt nytt** problem: tryck mot generella strategier |

### Progressivt orakel: problemet visar sig under räkningens gång

Med `--reveal` döljs större delen av problemet. Kolonin ser bara de krav som
avslöjats hittills. När den har hållit dem uppfyllda (eller en andel `--reveal-at`
av dem) i 20 tick avslöjar oraklet nästa steg, med lite bonusmat. Problemet räknas
som löst först när allt är avslöjat och uppfyllt.

| `--reveal` | vad som avslöjas härnäst |
|---|---|
| `off` | allt syns från början (förval) |
| `natural` | problemets egen ordning. För faktorisering: **svaret siffra för siffra**, produktens lägsta bit först tillsammans med kretsen som räknar ut den |
| `random` | slumpade krav |
| `adversarial` | krav som kolonins nuvarande svar bryter mot (oraklet som motståndare) |
| `friendly` | krav som kolonins svar redan uppfyller (oraklet som snäll lärare) |

Rapporten visar för varje avslöjande hur många av *alla* krav, även de dolda, kolonins
svar redan uppfyllde. Svep över många frön görs med `sweep.py`:

```bash
python sweep.py --name reveal-sat --oracle sat --seeds 6 --ticks 30000
python sweep.py --name reveal-factor --oracle factor --seeds 6 --ticks 30000
```

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

## Resultat från experimentrundan om progressivt avslöjande

### Hjälper det att avslöja problemet gradvis? Nej, inte i nuvarande form

Växande 3-SAT, 6 frön × 4 kolonier × 30 000 tick (`sweep.py`):

| `--reveal` | lösta problem (medel) | median-tick till första lösning |
|---|---|---|
| off | **8,3** | **2 370** |
| friendly | 4,2 | 12 908 |
| natural | 4,0 | 10 089 |
| adversarial | 3,0 | 10 549 |
| random | 1,7 | 18 953 |

Faktorisering av 15 (6 frön per läge): ingen koloni lyckades i något läge. Med gradvis
avslöjande kom de som längst till 92 % av problemet avslöjat och uppfyllt (`friendly`).

Trolig förklaring: när få krav syns finns det mat även med ett dåligt svar. Trycket att bli bättre
försvinner, och varje nytt avslöjande slår omkull kolonins jämvikt.

### Skalning på riktigt svåra problem (`scaling.py`)

Slumpad 3-SAT (inte planterad) med 4,26 krav per variabel, där de svåraste problemen ligger.
Tabellen visar median antal flips och hur många av instanserna som löstes inom 40 000 tick.

| n | WalkSAT | slumpvandring | myror med instinkter | myror tränade på `fresh` | **handgjorda reparatörer** |
|---|---|---|---|---|---|
| 10 | 14 | 54 | 2/6 lösta | 4/10 lösta | 6/6 lösta, 90 flips |
| 20 | 42 | 181 | 0/6 | 0/10 | 5/6 lösta, 2 576 flips |
| 30 | 140 | 1 013 | 0/6 | 1/10 | 3/6 lösta |
| 40–50 | 188–494 | 2 308–20 320 | 0 | 0 | 0 |

De handgjorda reparatörerna har en enda handskriven regel: "kommer du från en död automat och
står i en förlorande kammare, lägg lera". Det är slumpvandringsmetoden översatt till myrbeteende.

Slutsatser:
1. **Evolutionen är en flaskhals.** En enkel regel som evolutionen inte hittade på 60 000 tick
   är dramatiskt bättre än allt evolverat. Urvalet är för svagt: fyra kolonier, och belöningen
   kopplas inte till själva reparationsbeteendet.
2. **Fysiken är också en flaskhals.** Även med rätt regel behöver myrorna 10–15 gånger fler flips
   än slumpvandringen de imiterar. Hundratals myror bygger samtidigt utan samordning, leran
   eroderar, och trögheten gör att varje ändring tar tid.
3. Att planterade problem gick bra berodde till stor del på att de är lätta.

## Äkta evolutionärt tryck (`evolve.py`)

24 drottningar per generation, arbetarna är hennes döttrar, varje generation helt nya slumpade
3-SAT-problem vid 4,26 krav per variabel. Mat ger överlevnad, lösningar ger fortplantning, och
problemen växer när hälften av kolonierna klarar nuvarande storlek. 50 generationer, ett frö.

| körning | nådde storlek | lösta problem totalt | reparationsfokus vid slutet |
|---|---|---|---|
| med födosöksinstinkter | n = 18 | 183 | 0,35 |
| utan instinkter | n = 16 | 151 | 0,87 |

Kolonierna med instinkter utvecklade en egen strategi: **skydda det som fungerar**. Deras mest
förändrade gen är "lägg lera där det finns mat", alltså på kammare som redan vinner. Det är den
ena halvan av WalkSAT: välj den ändring som förstör minst. Den handgjorda regeln motsvarar den
andra halvan: reparera ett brutet krav. Evolutionen återupptäckte alltså en del av en känd
algoritm, utan att knuffas dit.

Bästa drottningen från varje körning testades på nya problem (`examples/skalning-evolverade.md`).
På 10 variabler löste de evolverade 4 av 6 problem mot 2 av 6 för instinktmyrorna. Den med
instinkter behövde 156 flips i median, nära den handgjorda regelns 90. Vid 20 variabler och uppåt
löser de nästan inget, och den handgjorda regeln är fortfarande bäst.

Jämförelser med inlärning under livet (Baldwin), ärftlig inlärning (Lamarck), kultur och kulturarv
mellan kolonier pågår, se `evolve.py --mode` och `compare_evo.py`.

## Det öppna oraklet: kända problem, okänt svar (`open_oracle.py`)

21 klassiska problem (Ramsey, Schur, van der Waerden, duvslag, graffärgning, damer, faktorisering),
i par där det ena går att lösa och det andra är bevisat omöjligt. Oraklet visste inte vilket. Det
betalade bara mat för uppfyllda krav. Facit räknades ut efteråt med en riktig SAT-lösare. Fyra
arvsmassor, 40 000 tick var, ett frö. Hela tabellen finns i `examples/oppet-orakel.md`.

| arvsmassa | lösbara lösta (av 11) | omöjliga där bästa möjliga nåddes (av 10) |
|---|---|---|
| instinkt | 0 | 5 |
| evolverad | 2 | 6 |
| evolverad utan instinkter | 1 | 5 |
| handgjord reparatör | 7 | 9 |

* **Inget nytt hittades.** Myrorna löste bara små problem som WalkSAT klarar på 3 till 20 flips.
  De större (Schur 13, van der Waerden 34, 8 damer, Ramsey K17) blev nästan men aldrig helt lösta.
* **När det är omöjligt hittar de ofta det bästa möjliga.** Det handlar om bästa möjliga antal
  uppfyllda krav (MAX-SAT). Den handgjorda regeln nådde det på 9 av 10 omöjliga problem.
* **De lugnar ner sig när det är omöjligt.** Olösta kolonier på omöjliga problem ändrade sitt
  svar 0,05 gånger per tick sent i körningen. På lösbara men olösta problem var det 0,17. En
  koloni som fastnat på ett omöjligt problem slutar alltså leta, utan att någon har sagt att det
  är omöjligt. Det är en antydan, ett frö, inte ett bevis.
* **Många kolonier dog ut (†).** Ekonomin är byggd för 3-SAT. På problem med många långa krav
  räckte maten inte, så vikterna i ekonomin behöver justeras per problemfamilj.

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
