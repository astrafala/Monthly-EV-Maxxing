#!/bin/sh
# Full version 7 pipeline. Run "python3 optimize_v7.py grid" first; then this script runs every later stage in order.
# (The final stage also refines, once, the grid's best settings inside firm-specific risk ceilings: FTMO 1.5%.)
set -e
cd "$(dirname "$0")"
if [ "$1" = "--from-long" ]; then
date; python3 lockstep_portfolio_v7.py long >> lockstep_v7.log 2>&1
date; python3 lockstep_portfolio_v7.py pairfirms >> lockstep_v7.log 2>&1
date; python3 lockstep_portfolio_v7.py budget >> lockstep_v7.log 2>&1
date; python3 lockstep_portfolio_v7.py stress >> lockstep_v7.log 2>&1
date; python3 lockstep_portfolio_v7.py corr >> lockstep_v7.log 2>&1
date; python3 lockstep_portfolio_v7.py news >> lockstep_v7.log 2>&1
date; python3 lockstep_portfolio_v7.py behav >> lockstep_v7.log 2>&1
date; echo pipeline-done; exit 0
fi
if [ "$1" != "--from-final" ]; then
date; python3 optimize_v7.py refine > opt_v7_refine.log 2>&1
date; python3 optimize_v7.py futures > opt_v7_futures.log 2>&1
fi
date; python3 optimize_v7.py final > opt_v7_final.log 2>&1
date; python3 verify_v7.py > verify_v7.log 2>&1
date; python3 sens_v7.py > sens_v7.log 2>&1
date; python3 lockstep_portfolio_v7.py show > lockstep_v7.log 2>&1
date; python3 lockstep_portfolio_v7.py main >> lockstep_v7.log 2>&1
date; python3 lockstep_portfolio_v7.py long >> lockstep_v7.log 2>&1
date; python3 lockstep_portfolio_v7.py pairfirms >> lockstep_v7.log 2>&1
date; python3 lockstep_portfolio_v7.py budget >> lockstep_v7.log 2>&1
date; python3 lockstep_portfolio_v7.py stress >> lockstep_v7.log 2>&1
date; python3 lockstep_portfolio_v7.py corr >> lockstep_v7.log 2>&1
date; python3 lockstep_portfolio_v7.py news >> lockstep_v7.log 2>&1
date; python3 lockstep_portfolio_v7.py behav >> lockstep_v7.log 2>&1
date; echo pipeline-done
