#!/bin/bash
# Skalningstest av Baldwin- och Lamarck-drottningarna mot den handgjorda regeln, efter viktsvepet.
cd "$(dirname "$0")"
until grep -q VIKTER_DONE runs_vikter.log 2>/dev/null; do sleep 60; done
[ -f runs/skala-larande/scaling.md ] || nice -n 10 python3 scaling.py --name skala-larande --sizes 10 20 30 40 --instances 6 \
  --genomes runs/evo-baldwin/best_queen_workers.npy runs/evo-lamarck/best_queen_workers.npy runs/handgjord/reparatorer.npy \
  --workers 1 > runs_skala_larande.log 2>&1
