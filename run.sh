#!/bin/sh
# Rebuild every printed part of every variant (or just the ones named: ./run.sh d8k s4k) from the simulator, run all the
# checks, and export the STLs (stl/<variant>/), the zips and the packed meshes the simulator shows (sim/print/)
set -e
cd "$(dirname "$0")"
python3 tools/run_print.py "$@" | tee out/run.log
python3 tools/export.py "$@"
