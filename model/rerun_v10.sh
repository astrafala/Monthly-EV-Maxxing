#!/bin/sh
# Full version 10 pipeline. Each stage writes stage_v10_<name>.done when it finishes; a rerun skips finished stages
# (rm stage_v10_*.done to redo all). The grid and refine stages resume where an interrupted run stopped.
set -e
cd "$(dirname "$0")"
run() {   # run <name> <command...>
  n=$1; shift
  if [ -f "stage_v10_$n.done" ]; then echo "skip $n"; return 0; fi
  date; echo "stage $n"
  "$@"
  touch "stage_v10_$n.done"
}
run streams python3 streams_v10.py
run tests sh -c "python3 tests_v10.py > tests_v10.log 2>&1 && grep -q 'all passed' tests_v10.log"
run grid sh -c "if [ -s opt_v10_grid.jsonl ]; then python3 optimize_v10.py grid resume >> opt_v10_grid.log 2>&1; else python3 optimize_v10.py grid > opt_v10_grid.log 2>&1; fi"
run refine sh -c "python3 optimize_v10.py refine > opt_v10_refine.log 2>&1"
run futures sh -c "python3 optimize_v10.py futures > opt_v10_futures.log 2>&1"
run final sh -c "python3 optimize_v10.py final > opt_v10_final.log 2>&1"
run continuing sh -c "python3 continuing_v10.py > continuing_v10.log 2>&1"
run price sh -c "python3 continuing_v10.py price > continuing_v10_price.log 2>&1"
run contcheck sh -c "python3 cont_check_v10.py > cont_check_v10.log 2>&1"
run verify sh -c "python3 verify_v10.py > verify_v10.log 2>&1"
run sens sh -c "python3 sens_v10.py > sens_v10.log 2>&1"
run show sh -c "python3 lockstep_portfolio_v10.py show > lockstep_v10_show.log 2>&1"
for st in main long pairfirms budget stress corr refusals behav bound; do
  run $st sh -c "python3 lockstep_portfolio_v10.py $st >> lockstep_v10.log 2>&1"
done
run audit sh -c "python3 audit_v10.py > audit_v10.log 2>&1"
date; echo pipeline-done
