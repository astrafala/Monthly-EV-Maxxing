#!/bin/sh
# Full version 6 pipeline on the corrected engine (same-bar ties resolved from sub-steps).
set -e
cd "$(dirname "$0")"
date; python3 optimize_v6.py grid > opt_v6_grid.log 2>&1
date; python3 optimize_v6.py refine > opt_v6_refine.log 2>&1
date; python3 optimize_v6.py edge > opt_v6_edge.log 2>&1
date; python3 optimize_v6.py futures > opt_v6_futures.log 2>&1
date; python3 optimize_v6.py futures_refine >> opt_v6_futures.log 2>&1
date; python3 optimize_v6.py bold > opt_v6_bold.log 2>&1
date; python3 optimize_v6.py final6 > opt_v6_final.log 2>&1
date; echo pipeline-done
