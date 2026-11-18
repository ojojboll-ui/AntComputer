#!/bin/bash
# Rikare hjärnor: 4 minnesceller. Baldwin först (frö 1-10), sedan bara gener. Tål omstarter.
cd "$(dirname "$0")"
evo() {  # namn läge frö
  local log=runs_${1//-/_}.log
  [ -f runs/$1/evolution.md ] && return
  local extra=""
  [ -f runs/$1/state.json ] && extra="--resume"
  nice -n 10 python3 evolve.py --name $1 --mode $2 --seed $3 --mem 4 --generations 50 --workers 1 $extra >> $log 2>&1
}
export -f evo
name() { [ $2 = 1 ] && echo evo-$1-mem4 || echo evo-$1-mem4-s$2; }
{ for s in $(seq 1 10); do echo "$(name baldwin $s) baldwin $s"; done
  for s in $(seq 1 10); do echo "$(name none $s) none $s"; done; } | xargs -P 4 -L 1 bash -c 'evo "$0" "$1" "$2"'
{ python3 seed_stats.py baldwin-mem4 baldwin $(seq 1 10); echo; python3 seed_stats.py none-mem4 none $(seq 1 10)
  echo; python3 seed_stats.py baldwin-mem4 none-mem4 $(seq 1 10); } > runs_mem_stats.log 2>&1
echo MEM_DONE >> runs_mem_stats.log
