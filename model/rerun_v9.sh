#!/bin/sh
# Full version 9 pipeline. Each stage writes stage_v9_<name>.done when it finishes; a rerun skips finished stages
# (rm stage_v9_*.done to redo all). The grid is resumable ("python3 optimize_v9.py grid resume").
set -e
cd "$(dirname "$0")"
run() {   # run <name> <command...>
  n=$1; shift
  if [ -f "stage_v9_$n.done" ]; then echo "skip $n"; return 0; fi
  date; echo "stage $n"
  "$@"
  touch "stage_v9_$n.done"
}
run streams python3 streams_v9.py
run tests sh -c "python3 tests_v9.py > tests_v9.log 2>&1 && grep -q 'all passed' tests_v9.log"
run grid sh -c "if [ -s opt_v9_grid.jsonl ]; then python3 optimize_v9.py grid resume >> opt_v9_grid.log 2>&1; else python3 optimize_v9.py grid > opt_v9_grid.log 2>&1; fi"
run refine sh -c "python3 optimize_v9.py refine > opt_v9_refine.log 2>&1"
run futures sh -c "python3 optimize_v9.py futures > opt_v9_futures.log 2>&1"
run final sh -c "python3 optimize_v9.py final > opt_v9_final.log 2>&1"
run continuing sh -c "python3 continuing_v9.py > continuing_v9.log 2>&1"
run verify sh -c "python3 verify_v9.py > verify_v9.log 2>&1"
run sens sh -c "python3 sens_v9.py > sens_v9.log 2>&1"
run show sh -c "python3 lockstep_portfolio_v9.py show > lockstep_v9_show.log 2>&1"
for st in main long pairfirms budget stress corr news behav; do
  run $st sh -c "python3 lockstep_portfolio_v9.py $st >> lockstep_v9.log 2>&1"
done
date; echo pipeline-done
