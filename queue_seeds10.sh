#!/bin/bash
# Frö 6-10 för Baldwin och bara gener, fyra åt gången. Tål omstarter.
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
export -f evo
for s in 6 7 8 9 10; do echo "evo-baldwin-s$s baldwin $s"; echo "evo-s$s none $s"; done | xargs -P 4 -L 1 bash -c 'evo "$0" "$1" "$2"'
python3 seed_stats.py baldwin none 1 2 3 4 5 6 7 8 9 10 > runs_seed_stats.log
echo SEEDS10_DONE >> runs_seed_stats.log
