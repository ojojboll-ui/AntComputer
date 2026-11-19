#!/bin/bash
# Rikare hjärnor och större kliv, i ordning:
#   1. Baldwin + 4 minnesceller, frö 1-10
#   2. samma + större kliv (Cauchy-mutationer, makromutationer, invandrare), frö 1-10
#   3. Baldwin + 4 minnesceller + memes (minnen sprids mellan systrar), frö 1-10
#   4. bara gener + 4 minnesceller, frö 1-10
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
export -f evo
run() { [ $2 = 1 ] && echo evo-$1 || echo evo-$1-s$2; }
LEAPS="--jumps cauchy --macro 0.1 --immigrants 2"
{ for s in $(seq 1 10); do echo "$(run baldwin-mem4 $s) baldwin $s"; done
  for s in $(seq 1 10); do echo "$(run baldwin-mem4-kliv $s) baldwin $s $LEAPS"; done
  for s in $(seq 1 10); do echo "$(run baldwin-mem4-memes $s) baldwin+memes $s"; done
  for s in $(seq 1 10); do echo "$(run none-mem4 $s) none $s"; done; } \
  | xargs -P 4 -L 1 bash -c 'evo "$@"' _
stats() { python3 seed_stats.py "$@" $(seq 1 10); echo; }
{ echo "## Baldwin: med mot utan minne"; stats baldwin-mem4 baldwin
  echo "## Baldwin med minne: större kliv mot vanliga"; stats baldwin-mem4-kliv baldwin-mem4
  echo "## Baldwin med minne: memes mot utan memes"; stats baldwin-mem4-memes baldwin-mem4
  echo "## Bara gener: med mot utan minne"; stats none-mem4 none
  echo "## Med minne: Baldwin mot bara gener"; stats baldwin-mem4 none-mem4; } > runs_mem_stats.log 2>&1
echo MEM_DONE >> runs_mem_stats.log
