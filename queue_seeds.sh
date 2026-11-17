#!/bin/bash
# Baldwin med fler frön, sedan bara gener med samma frön som kontroll. Tål omstarter.
cd "$(dirname "$0")"
evo() {  # namn läge frö
  local log=runs_${1//-/_}.log
  [ -f runs/$1/evolution.md ] && return
  if [ -f runs/$1/state.json ]; then
    nice -n 10 python3 evolve.py --name $1 --mode $2 --seed $3 --generations 50 --workers 1 --resume >> $log 2>&1
  else
    nice -n 10 python3 evolve.py --name $1 --mode $2 --seed $3 --generations 50 --workers 1 > $log 2>&1
  fi
}
for s in 2 3 4 5; do evo evo-baldwin-s$s baldwin $s & done; wait
for s in 2 3 4 5; do evo evo-s$s none $s & done; wait
python3 compare_evo.py runs/evo-baldwin runs/evo-baldwin-s{2,3,4,5} runs/evo runs/evo-s{2,3,4,5} > runs_compare_seeds.log
echo SEEDS_DONE >> runs_compare_seeds.log
