#!/bin/sh
set -e
cd "$(dirname "$0")"
date; python3 sens_v6.py > sens_v6.log 2>&1
date; python3 sens_v6.py cost1 >> sens_v6.log 2>&1
date; python3 timing_v6.py > timing_v6.log 2>&1
date; python3 verify_v6.py > verify_v6.log 2>&1
date; python3 lockstep_portfolio_v6.py --lives=50 > lockstep_v6.log 2>&1
date; echo downstream-done
