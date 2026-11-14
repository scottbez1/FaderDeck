#!/bin/sh
# Builds the two command-line tools into ./build:
#   csg      - the CSG runner (manifold) that turns the simulator's solids into the printed parts
#   collide  - the exact interference checker (no dependencies)
# Needs a manifold build: MANIFOLD_DIR pointing at a checkout built as a static library, e.g.
#   git clone https://github.com/elalish/manifold && cd manifold && cmake -B build -G Ninja -DCMAKE_BUILD_TYPE=Release \
#     -DBUILD_SHARED_LIBS=OFF -DMANIFOLD_TEST=OFF -DMANIFOLD_PAR=OFF && ninja -C build
set -e
cd "$(dirname "$0")"
: "${MANIFOLD_DIR:=ext/manifold}"
mkdir -p build
g++ -O2 -std=c++17 tools/csg.cpp -I "$MANIFOLD_DIR/include" -I "$MANIFOLD_DIR/build/include" \
  $(find "$MANIFOLD_DIR/build" -name '*.a') -o build/csg
g++ -O2 -std=c++17 tools/collide.cpp -o build/collide
echo "built build/csg and build/collide"
