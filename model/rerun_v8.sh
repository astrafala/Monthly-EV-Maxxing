#!/bin/sh
# Full version 8 pipeline after the grid ("python3 optimize_v8.py grid", resumable with "grid resume").
# Each stage writes stage_v8_<name>.done when it finishes; a rerun skips finished stages (rm stage_v8_*.done to redo all).
set -e
cd "$(dirname "$0")"
run() {   # run <name> <command...>
  n=$1; shift
  if [ -f "stage_v8_$n.done" ]; then echo "skip $n"; return 0; fi
  date; echo "stage $n"
  "$@"
  touch "stage_v8_$n.done"
}
run streams python3 streams_v8.py
run tests sh -c "python3 tests_v8.py > tests_v8.log 2>&1 && grep -q 'all passed' tests_v8.log"
run refine sh -c "python3 optimize_v8.py refine > opt_v8_refine.log 2>&1"
run futures sh -c "python3 optimize_v8.py futures > opt_v8_futures.log 2>&1"
run final sh -c "python3 optimize_v8.py final > opt_v8_final.log 2>&1"
run verify sh -c "python3 verify_v8.py > verify_v8.log 2>&1"
run sens sh -c "python3 sens_v8.py > sens_v8.log 2>&1"
run show sh -c "python3 lockstep_portfolio_v8.py show > lockstep_v8_show.log 2>&1"
for st in main long pairfirms budget stress corr news behav; do
  run $st sh -c "python3 lockstep_portfolio_v8.py $st >> lockstep_v8.log 2>&1"
done
date; echo pipeline-done
