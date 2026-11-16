#!/bin/bash
# Kör hela kön. Säker att starta om efter ett avbrott: färdiga steg hoppas över, påbörjade fortsätter.
cd "$(dirname "$0")"
evo() {  # namn läge workers
  local log=runs_${1//-/_}.log
  [ -f runs/$1/evolution.md ] && return
  if [ -f runs/$1/queens.npy ]; then
    nice -n 10 python3 evolve.py --name $1 --mode $2 --generations 50 --workers $3 --resume --resume-log $log > $log.resume 2>&1
  else
    nice -n 10 python3 evolve.py --name $1 --mode $2 --generations 50 --workers $3 > $log 2>&1
  fi
}
evo evo-baldwin baldwin 1 & evo evo-lamarck lamarck 1 & evo evo-culture culture 2 & wait
python3 compare_evo.py runs/evo runs/evo-blank runs/evo-baldwin runs/evo-lamarck runs/evo-culture > runs_compare.log; echo MODES_DONE >> runs_compare.log
grep -q VIKTER_DONE runs_vikter.log 2>/dev/null || { nice -n 10 python3 weights.py --name vikter --workers 4 > runs_vikter.log 2>&1 && echo VIKTER_DONE >> runs_vikter.log; }
for m in baldwin+culture lamarck+culture culture+heritage baldwin+culture+heritage; do evo evo-$(echo $m | tr + -) $m 1 & done; wait
python3 compare_evo.py runs/evo runs/evo-blank runs/evo-baldwin runs/evo-lamarck runs/evo-culture runs/evo-baldwin-culture runs/evo-lamarck-culture runs/evo-culture-heritage runs/evo-baldwin-culture-heritage > runs_compare_all.log; echo ALL_DONE >> runs_compare_all.log
