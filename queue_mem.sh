#!/bin/bash
# Rikare hjärnor och större kliv, i ordning:
#   1. Baldwin + 4 minnesceller, frö 1-10
#   2. samma + större kliv (Cauchy-mutationer, makromutationer, invandrare), frö 1-10
#   3. Baldwin + 4 minnesceller + memes + större kliv, frö 1-10
#   4. en klivmekanism i taget (bara Cauchy, bara makromutationer, bara invandrare), frö 1-5
#   5. större kliv i 100 generationer: fortsätter de färdiga 50-generationskörningarna, frö 1, 2 och 9
#   6. Baldwin + 4 minnesceller + memes (minnen sprids mellan systrar), frö 1-10
#   7. bara gener + 4 minnesceller, frö 1-10
# Tål omstarter: färdiga körningar hoppas över, avbrutna fortsätter, och en körning som redan
# pågår (t.ex. startad av en tidigare kö) väntas in i stället för att startas en gång till.
cd "$(dirname "$0")"
evo() {  # namn läge frö [extra flaggor]
  local name=$1 mode=$2 seed=$3; shift 3
  while pgrep -f "evolve.py --name $name " >/dev/null; do sleep 60; done
  [ -f runs/$name/evolution.md ] && return
  local resume=""
  [ -f runs/$name/state.json ] && resume="--resume"
  nice -n 10 python3 evolve.py --name $name --mode $mode --seed $seed --mem 4 --generations 50 --workers 1 \
    "$@" $resume >> runs_${name//-/_}.log 2>&1
}
longer() {  # namn från läge frö [extra flaggor]: fortsätt en färdig körning till 100 generationer
  local name=$1 from=$2; shift 2
  until [ -f runs/$from/evolution.md ]; do sleep 60; done
  if [ ! -d runs/$name ]; then
    cp -r runs/$from runs/$name
    rm -f runs/$name/evolution.md runs/$name/evolution.json runs/$name/best_queen_workers.npy
  fi
  evo $name "$@" --generations 100
}
export -f evo longer
run() { [ $2 = 1 ] && echo evo-$1 || echo evo-$1-s$2; }
LEAPS="--jumps cauchy --macro 0.1 --immigrants 2"
{ for s in $(seq 1 10); do echo "evo $(run baldwin-mem4 $s) baldwin $s"; done
  for s in $(seq 1 10); do echo "evo $(run baldwin-mem4-kliv $s) baldwin $s $LEAPS"; done
  # 100 generationer bara på tre frön: bäst (2), mitten (1) och svagast (9). Frö 1 och 2 var redan
  # igång när ordningen ändrades och ligger därför först, så att de pågående körningarna tas om hand.
  for s in 1 2; do echo "longer $(run baldwin-mem4-kliv100 $s) $(run baldwin-mem4-kliv $s) baldwin $s $LEAPS"; done
  for s in $(seq 1 10); do echo "evo $(run baldwin-mem4-memes-kliv $s) baldwin+memes $s $LEAPS"; done
  # Vilken klivmekanism gör jobbet? En i taget, frö 1-5, varvade per frö så att en första
  # jämförelse finns efter ett par dygn.
  for s in $(seq 1 5); do
    echo "evo $(run baldwin-mem4-cauchy $s) baldwin $s --jumps cauchy"
    echo "evo $(run baldwin-mem4-makro $s) baldwin $s --macro 0.1"
    echo "evo $(run baldwin-mem4-invandrare $s) baldwin $s --immigrants 2"
  done
  echo "longer $(run baldwin-mem4-kliv100 9) $(run baldwin-mem4-kliv 9) baldwin 9 $LEAPS"
  for s in $(seq 1 10); do echo "evo $(run baldwin-mem4-memes $s) baldwin+memes $s"; done
  for s in $(seq 1 10); do echo "evo $(run none-mem4 $s) none $s"; done; } \
  | xargs -P 4 -L 1 bash -c '"$@"' _
stats() { python3 seed_stats.py "$@" $(seq 1 10); echo; }
{ echo "## Baldwin: med mot utan minne"; stats baldwin-mem4 baldwin
  echo "## Baldwin med minne: större kliv mot vanliga"; stats baldwin-mem4-kliv baldwin-mem4
  echo "## Större kliv: 100 mot 50 generationer (frö 1, 2, 9)"; python3 seed_stats.py baldwin-mem4-kliv100 baldwin-mem4-kliv 1 2 9; echo
  echo "## Baldwin med minne: memes mot utan memes"; stats baldwin-mem4-memes baldwin-mem4
  echo "## Större kliv: med mot utan memes"; stats baldwin-mem4-memes-kliv baldwin-mem4-kliv
  for m in cauchy makro invandrare; do
    echo "## En mekanism ($m) mot vanliga steg, frö 1-5"; python3 seed_stats.py baldwin-mem4-$m baldwin-mem4 1 2 3 4 5; echo
    echo "## En mekanism ($m) mot alla tre, frö 1-5"; python3 seed_stats.py baldwin-mem4-$m baldwin-mem4-kliv 1 2 3 4 5; echo
  done
  echo "## Bara gener: med mot utan minne"; stats none-mem4 none
  echo "## Med minne: Baldwin mot bara gener"; stats baldwin-mem4 none-mem4; } > runs_mem_stats.log 2>&1
echo MEM_DONE >> runs_mem_stats.log
