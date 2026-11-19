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

### Inlärning under livet, Lamarck och kultur

Samma uppsättning, 50 generationer, ett frö per läge (`examples/jamforelse-lagen.md`).

| läge | nådde storlek | lösta problem totalt | andel som löser (sista 10 gen) | reparationsfokus |
|---|---|---|---|---|
| bara gener | n = 18 | 183 | 7 % | 0,35 |
| bara gener, utan instinkter | n = 16 | 151 | 2 % | 0,87 |
| kultur (härma den bästa grannen) | n = 18 | 175 | 8 % | 0,58 |
| **Baldwin** (lär sig under livet, ärvs inte) | **n = 28** | **510** | **41 %** | **2,08** |
| **Lamarck** (det inlärda skrivs in i generna) | n = 26 | 381 | 30 % | 2,25 |

* **Inlärning under livet nästan tredubblar antalet lösta problem** och tar kolonierna till
  28 variabler, mot 18 för bara gener.
* **Baldwin-effekten syns i generna.** I Baldwin-läget ärvs inget av det inlärda. Ändå är bästa
  drottningens mest förändrade gen "lägg lera när kravet jag just kom från var dött" (0 → +3,0),
  tillsammans med en lägre grundlust att lägga lera (−2 → −3,3). Det är nästan exakt den
  handgjorda reparationsregeln (+5 och −4). De som hade lättast att *lära sig* regeln vann, och
  till slut blev den medfödd. Det är genetisk assimilation, som Hinton och Nowlan beskrev 1987.
  Lamarck hittade samma regel (+2,4), och dessutom "lägg inte lera på den kammare som redan
  vinner" (−1,4), vilket också finns i den handgjorda regeln.
* **Lamarck var inte bättre än Baldwin.** Att skriva in det inlärda direkt i generna tar också
  med brus från livet. Selektion på förmågan att lära verkar räcka.
* **Kultur ensam gjorde ingen skillnad.** Att härma den som har det bäst sprider vanor, men i den
  här världen är "den som har det bäst" ofta bara den som står närmast maten.
* **Förbehåll:** ett frö per läge. Inlärningen belönar att komma fram till ett krav som ger mat.
  Det är samma signal som världen redan ger, inte svaret, men den gör det lättare att upptäcka
  att reparation lönar sig.

### Tio frön: håller Baldwin-resultatet?

Baldwin och bara gener med samma tio frön, alltså samma problemström parvis
(`examples/jamforelse-tio-fron.md`, räknat med `seed_stats.py`).

| frö | Baldwin: storlek | Baldwin: lösta | bara gener: storlek | bara gener: lösta | reparationsgenen Baldwin / bara gener |
|---|---|---|---|---|---|
| 1 | 28 | 510 | 18 | 183 | +3,0 / +0,1 |
| 2 | 24 | 464 | 26 | 422 | +2,6 / +1,4 |
| 3 | 14 | 207 | 20 | 349 | +0,1 / +1,1 |
| 4 | 28 | 453 | 14 | 225 | +2,1 / +0,3 |
| 5 | 32 | 593 | 14 | 239 | +2,6 / +0,3 |
| 6 | 20 | 355 | 14 | 390 | +1,3 / +1,2 |
| 7 | 18 | 130 | 18 | 87 | −0,2 / +0,1 |
| 8 | 20 | 339 | 24 | 399 | +1,4 / +1,3 |
| 9 | 14 | 142 | 16 | 250 | −0,2 / −0,2 |
| 10 | 22 | 446 | 16 | 142 | +1,9 / +0,3 |
| **median** | **21** | **400** | **17** | **244** | **+1,7 / +0,3** |

*Reparationsgenen* är vikten från "kravet jag kom från var dött" till "lägg lera" hos bästa
drottningen i sista generationen. Den börjar på 0.

* **I genomsnitt är Baldwin bättre, men inte säkert.** Fler lösta i 6 av 10 frön, i snitt +95
  problem (parat t-test p ≈ 0,15). De fem första fröna överdrev skillnaden.
* **Reparationsgenen avgör allt.** Hur stark den blev förklarar nästan hela skillnaden mellan
  körningarna (korrelation 0,97 med antal lösta för Baldwin, 0,87 utan inlärning). De som fick den
  löste i snitt 493 problem, de andra 235.
* **Bara inlärning tar genen hela vägen.** Den blev +1,9 eller mer i 5 av 10 Baldwin-körningar och
  aldrig över +1,4 utan inlärning (0 av 10). Det är statistiskt säkert (Fishers exakta test
  p ≈ 0,03), med förbehållet att gränsen valdes efter att vi sett siffrorna. Utan inlärning når
  evolutionen ofta halvvägs (+1,1 till +1,4) och fastnar.
* **Det är ett lotteri med eller utan inlärning.** Hälften av Baldwin-körningarna hittade aldrig
  regeln och klarade sig då inte bättre än bara gener.
* **Sammanfattning:** inlärning under livet gör inte myrorna generellt smartare. Den gör det
  möjligt för evolutionen att ta sista steget till en känd, effektiv regel, ungefär varannan gång.
  Det är Baldwin-effekten i liten skala: inlärningen jämnar ut landskapet så att selektionen hittar
  toppen. När det lyckas löser kolonierna dubbelt så många problem.

### Rikare hjärnor: minne (`--mem`)

Hittills har myran varit en ren reflex: samma intryck ger alltid samma beteende. Med `--mem N`
får varje myra N egna minnesceller (värden −1 till 1). Hjärnan läser dem som extra sinnen och
skriver nya värden i dem varje tick, så den blir ett litet återkopplat nätverk som kan bära med
sig något från förra kammaren, förra kravet eller förra varvet. Cellerna är tomma vid födseln,
och arvsmassan har inga instinkter för dem: vad de ska betyda måste evolutionen hitta på.

    python evolve.py --name evo-baldwin-mem4 --mode baldwin --mem 4

**Preliminärt (5 av 10 frön):** med minne löste Baldwin färre problem än utan i alla fem frön
(median 205 mot 464, parat t-test p ≈ 0,03). Troligen för att arvsmassan växer från 132 till 240
vikter, så evolutionen söker långsammare.

**Används minnet?** `ablation.py` kör de färdiga drottningarna med minnet påslaget och fruset
(`mem_rate=0`, cellerna förblir 0), 10 kolonieliv var på samma problem (`examples/ablation-minne.md`).
Med fruset minne löste de 5 problem i stället för 13, och i de två bästa fröna sjönk maten med
21 % och 40 %. Minnet används alltså. Drottningarna som hann bygga upp ett beteende har gjort sig
beroende av det, fast det totalt sett gjort evolutionen långsammare. Få lösta problem per körning,
så ta siffrorna som en riktning, inte ett säkert mått.

    python ablation.py --runs evo-baldwin-mem4 evo-baldwin-mem4-s2 --lives 10

### Större kliv (`--jumps cauchy`, `--macro`, `--immigrants`)

Evolutionen har bara tagit små steg från där den står, och hittar därför bara det som ligger nära
startpunkten. Tre sätt att låta den hoppa längre, som kan kombineras:

* **Cauchy-mutationer:** oftast lika små som förut, men ibland enorma.
* **Makromutationer:** en hel rad i hjärnan (allt som styr ett beteende) kopieras över en annan
  eller byter plats med den, som när gener dupliceras i naturen.
* **Invandrare:** de sämsta drottningarna ersätts varje generation av helt nya slumpade, så att
  mångfalden inte dör ut.

### Memes: minnen som sprids (`--mode baldwin+memes`)

Kulturläget sprider beteende (vikterna i hjärnan) och gjorde det sämre. Memes sprider i stället
innehållet i minnet: en myra som möter en syster som blomstrar mer på samma plats tar ibland över
halva hennes minne, med lite brus. Systrar har nästan samma arvsmassa och kan därför läsa varandras
minnen, så det fungerar som ett slags kommunikation ("jag kom just från en död automat"). Inget
facit används: "blomstrar" betyder bara hur ofta myran nyligen hittat levande automater.

    python evolve.py --name evo-baldwin-mem4-memes --mode baldwin+memes --mem 4

### Kön

Pågår, i den här ordningen (`queue_mem.sh`), frö 1 till 10 för att kunna jämföras parvis:
Baldwin med 4 minnesceller, samma med större kliv, samma med memes, och sist bara gener med
4 minnesceller.

### Klarar de lärande drottningarna nya, större problem?

Bästa drottningen från Baldwin och Lamarck mot den handgjorda regeln, på nya slumpade 3-SAT-problem
(`examples/skalning-larande-utan-inlarning.md`). Testet kördes **utan** inlärning, alltså bara med
det som blivit medfött. Lösta av 6 per storlek:

| n | WalkSAT (flips) | instinkt | Baldwin | Lamarck | handgjord |
|---|---|---|---|---|---|
| 10 | 12 | 2 | 5 | 6 | 6 |
| 20 | 44 | 0 | 3 | 4 | 5 |
| 30 | 179 | 0 | 2 | 1 | 3 |
| 40 | 158 | 0 | **2** | 0 | 0 |

Baldwin-drottningen är den enda som löst något på 40 variabler, men skillnaden är 2 av 6 och
därmed inom bruset. Den handgjorda regeln är fortfarande bäst upp till 30.

Samma test **med** inlärning påslagen (`scaling.py --learning`,
`examples/skalning-larande-med-inlarning.md`):

| n | WalkSAT (flips) | instinkt | Baldwin | Lamarck | handgjord |
|---|---|---|---|---|---|
| 10 | 12 | 1 | 6 (46 flips) | 6 (186) | 6 (153) |
| 20 | 44 | 0 | 4 | 1 | **6** |
| 30 | 179 | 0 | 3 | 0 | 3 |
| 40 | 158 | 0 | **3** | 0 | 1 |

* **Baldwin-drottningen är den första evolverade arvsmassan som är jämbördig med den handgjorda
  regeln:** 16 av 24 lösta för båda. Den är bättre på de största problemen (3 mot 1 på 40
  variabler) och snabbare på de minsta (46 flips mot 153). Den handgjorda regeln är bättre på 20.
* **Lamarck blev sämre med inlärning påslagen.** Dess gener är redan fulla av inlärt brus.
  Baldwin-drottningen selekterades för att *kunna lära sig*, och det är just det som lönar sig här.
* Båda är fortfarande långt efter WalkSAT, som löser alla med 12 till 179 flips.

### Kombinationer av inlärning och kultur

Samma uppsättning, 50 generationer, ett frö (`examples/jamforelse-alla-lagen.md`).

| läge | nådde storlek | lösta totalt | andel som löser (sista 10 gen) | reparationsfokus |
|---|---|---|---|---|
| **Baldwin** | **n = 28** | **510** | **41 %** | 2,08 |
| Lamarck | n = 26 | 381 | 30 % | 2,25 |
| Baldwin + kultur + kulturarv | n = 18 | 335 | 19 % | 1,13 |
| Baldwin + kultur | n = 18 | 307 | 19 % | 0,84 |
| kultur + kulturarv | n = 24 | 302 | 21 % | 1,31 |
| Lamarck + kultur | n = 18 | 197 | 4 % | 0,03 |
| bara gener | n = 18 | 183 | 7 % | 0,35 |
| kultur | n = 18 | 175 | 8 % | 0,58 |

* **Kultur gör inlärningen sämre.** Baldwin + kultur löste 40 % färre problem än Baldwin ensam,
  och Lamarck + kultur tappade nästan all reparation (0,03). När myrorna härmar grannen som har
  det bäst skrivs det de själva lärt sig över. Den som har mest mat är oftast den som står vid
  ett krav som redan fungerar, inte den som just reparerat ett trasigt. Kulturen sprider alltså
  fel lärdom.
* **Kulturarv hjälper kulturen.** Kultur ensam gav ingenting, men när en ny koloni ärver
  mor-kolonins vanor nådde den 24 variabler och löste 302 problem. Det är nästan lika mycket som
  Baldwin + kultur. Kulturen behöver kunna byggas på över generationer för att göra nytta, ungefär
  som hos människor.
* **Den bästa kombinationen är den enklaste:** gener plus egen inlärning under livet, utan att
  härma andra.
* Ett frö per läge, så rangordningen i mitten av tabellen är osäker. Skillnaden mellan Baldwin
  och resten är däremot stor.

## Det öppna oraklet: kända problem, okänt svar (`open_oracle.py`)

21 klassiska problem (Ramsey, Schur, van der Waerden, duvslag, graffärgning, damer, faktorisering),
i par där det ena går att lösa och det andra är bevisat omöjligt. Oraklet visste inte vilket. Det
betalade bara mat för uppfyllda krav. Facit räknades ut efteråt med en riktig SAT-lösare. Fyra
arvsmassor, 40 000 tick var, ett frö. Hela tabellen finns i `examples/oppet-orakel.md`.

| arvsmassa | lösbara lösta (av 11) | omöjliga där bästa möjliga nåddes (av 10) |
|---|---|---|
| instinkt | 0 | 3 |
| evolverad | 2 | 5 |
| evolverad utan instinkter | 1 | 4 |
| handgjord reparatör | 6 | 9 |

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

### Vikter mot krav (`weights.py`)

Hela katalogen med 10 uppsättningar av ekonomins vikter, två arvsmassor (evolverad och handgjord),
20 000 tick, ett frö (`examples/vikter-mot-krav.md`). Siffror: lösta lösbara (av 22) · omöjliga där
bästa möjliga nåddes (av 20) · utdöda kolonier (av 42).

| vikter | lösta | bästa möjliga | utdöda |
|---|---|---|---|
| billig myra (halv förbrukning och födelsekostnad) | 11 | 14 | 7 |
| mat från 60 % uppfyllt | 10 | 15 | 7 |
| **mat per krav 0,05 + från 60 %** | 9 | 14 | **0** |
| standard | 8 | 14 | 12 |
| mat först från 90 % | 5 | 11 | 31 |

* **Vikterna avgör om kolonin överlever, inte om den löser.** Antalet lösta ligger mellan 7 och 11
  för alla rimliga vikter, vilket är inom bruset för ett frö. Mat per krav plus mat redan från
  60 % tog bort all utdöing utan att lösningarna blev färre.
* **För hårt krav på mat dödar.** Mat först vid 90 % uppfyllt gav 31 utdöda kolonier av 42.
* **Slutsats:** flaskhalsen är inte ekonomin. Den rätta vikten för överlevnad är lätt att hitta, men
  den gör inte myrorna smartare. Det som verkligen flyttade resultaten var inlärning under livet.

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
