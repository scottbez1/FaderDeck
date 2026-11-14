#!/bin/sh
# Assemble the static site (for GitHub Pages) in _site/: the simulator page, the model data it loads, every variant's packed
# meshes, and every variant's STLs and zip, served next to the page so its download links fetch them directly
set -e
cd "$(dirname "$0")/.."
rm -rf _site && mkdir -p _site/print _site/stl
mkdir -p _site/third_party
cp sim/index.html sim/knob.json _site/
cp sim/third_party/*.json sim/third_party/README.md _site/third_party/
cp sim/print/*.json _site/print/
for d in stl/*/; do v=$(basename "$d"); mkdir -p "_site/stl/$v"; cp "$d"*.stl "$d"*.zip "_site/stl/$v/"; done
touch _site/.nojekyll
echo "site: $(find _site -type f | wc -l) files, $(du -sh _site | cut -f1)"
