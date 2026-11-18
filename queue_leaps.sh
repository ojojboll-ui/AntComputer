#!/bin/bash
# Större kliv: Baldwin + 4 minnesceller + Cauchy-mutationer + makromutationer + invandrare, frö 1-10.
# Startar när minnesexperimentet är klart. Tål omstarter.
cd "$(dirname "$0")"
until grep -q MEM_DONE runs_mem_stats.log 2>/dev/null; do sleep 120; done
evo() {  # namn frö
  local log=runs_${1//-/_}.log
  [ -f runs/$1/evolution.md ] && return
  local extra=""
  [ -f runs/$1/state.json ] && extra="--resume"
  nice -n 10 python3 evolve.py --name $1 --mode baldwin --seed $2 --mem 4 --jumps cauchy --macro 0.1 --immigrants 2 \
    --generations 50 --workers 1 $extra >> $log 2>&1
}
export -f evo
for s in $(seq 1 10); do [ $s = 1 ] && echo "evo-baldwin-mem4-kliv 1" || echo "evo-baldwin-mem4-kliv-s$s $s"; done \
  | xargs -P 4 -L 1 bash -c 'evo "$0" "$1"'
python3 seed_stats.py baldwin-mem4-kliv baldwin-mem4 $(seq 1 10) > runs_kliv_stats.log 2>&1
echo KLIV_DONE >> runs_kliv_stats.log
