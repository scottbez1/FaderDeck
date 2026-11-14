# FaderDeck: technical notes

How this repository is put together: the variants and their parts, the simulator the enclosure is designed in, the tool chain
that turns it into printable STLs, the checks, and the published site. For why the enclosure is shaped the way it is, see
[DESIGN.md](DESIGN.md).

## Layout

```
sim/          the simulator (index.html), print/ (each variant's packed meshes and the manifest) and third_party/ (component meshes)
tools/        the CSG runner, the interference checker, the build, export and site scripts, the STEP tessellator and packers
stl/          the printable parts per variant, stl/<variant>/, in print orientation (mm), with a zip of each set
models/       knob/, the FaderDeck fader knob (built by tools/knob.py)
third_party/  models from other projects, each with its source and license (see third_party/README.md)
docs/         this page, DESIGN.md (how the enclosure works and why), PROJECT_INSTRUCTIONS.md (working rules for Claude), images/
```

## Variants

- **CrowPanel deck** (`d8k`): eight faders, four Kailh Choc keys, and an Elecrow CrowPanel ESP32 5.79" e-paper display. Five
  parts.
- **Screen-less decks** (`s2`-`s8`, `s2k`-`s8k`): 2 to 8 faders, without or with the four-key column. Three parts each (base,
  fader plate, cover). The ends of the base are the same shape at every fader count; only the middle grows, 17.85 mm per fader.

Every base has a 4 mm cable notch at the bottom of its back wall.

| Variant | Parts | Base width |
|---|---|---|
| `d8k` CrowPanel deck | base, fader plate, cover, display front, display back | 181.7 mm |
| `sN` screen-less, N faders | base, fader plate, cover | 66.8 + 17.85 × (N − 2) mm |
| `sNk` screen-less, N faders and keys | base, fader plate, cover | 70.8 + 17.85 × (N − 2) mm |

Print orientation: base top face down, fader plate bottom face down, cover visible face down, display front face down, display
back outer face down; nothing needs supports. Each variant's sizes and hardware are in `sim/print/variants.json`.

Hardware (screen-less): 2 × N M3 × 4 wafer heads (faders to plate); 4 × M3 × 4 wafer heads into 4 × M3 heat-set inserts (plate
to base, at the four corners); 4 Kailh Choc v1 switches for the `k` variants; 4 × Ø8 × 1.5 mm rubber pads. The CrowPanel deck
adds 4 × M2.5 × 4 flat heads (display back to the CrowPanel's standoffs) and 2 × M2.5 × 8 socket caps (through the base's rear
wall and the plate's pads into the CrowPanel's bottom standoffs), and its plate inserts sit at the front corners and the sides.

The fader knob is printed separately and isn't part of the variants' files: `tools/knob.py` builds it into `models/knob/` (the
knob, slot side down, and its inlay bar, on its side in a contrasting colour, pressed into the groove across the knob's top).

## Running the simulator locally

Serve `sim/` over HTTP (`cd sim && python3 -m http.server`) and open `index.html` (`sim/stl` links to `../stl` for the
downloads). It loads three.js from a CDN. **Variant** picks the deck (`#disp=0&nf=4&keys=1` in the address works too; the 3D
view rebuilds in place) and lists its print files and hardware; **Section** gives two movable cut planes with capped, hatched
faces; **Printed parts** toggles each part; **Animated assembly guide** steps through the build.

## Rebuilding the parts

The geometry lives in the simulator: `printModel()` in `sim/index.html` emits every printed part as closed solids plus a list of
CSG operations. `tools/run_print.py` loads the page in headless Chromium, runs those operations with `build/csg` (on
[manifold](https://github.com/elalish/manifold)), runs every check, and writes the meshes; `tools/export.py` turns them into the
STLs and zips in `stl/` and the packed copies the simulator shows (`sim/print/<variant>.json`).

Setup, once:

```sh
# manifold, as a static library (CI pins the commit the committed STLs were built with: see .github/workflows/site.yml)
git clone https://github.com/elalish/manifold ext/manifold
cmake -S ext/manifold -B ext/manifold/build -G Ninja -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=OFF -DMANIFOLD_TEST=OFF -DMANIFOLD_PAR=OFF
ninja -C ext/manifold/build
# three.js r147 (build/three.min.js and examples/js/controls/OrbitControls.js), for offline headless runs
npm install --no-save --prefix ext/three-npm three@0.147.0   # then THREE_DIR=ext/three-npm/node_modules/three
pip install playwright numpy && python3 -m playwright install chromium
./build.sh
```

Then, after any change to `sim/index.html`:

```sh
./run.sh            # rebuild, check and export every variant (THREE_DIR, CHROMIUM, SIM_PORT, MANIFOLD_DIR can override the defaults)
./run.sh d8k s4k    # just these
python3 tools/gate.py   # fail if the checks found anything unexpected
```

### What the run checks

- **Part against part** (manifold): every pair of printed parts, the cover lifting off, the display sliding onto the deck.
- **Walls and breaches**: no cut may remove wall material below the plate except the intended holes (and the cable notch, which
  must open the wall); nothing may break through the outer skin.
- **Feet**: every rubber pad's footprint sits fully on solid base.
- **Exact component checks** (`build/collide`): the faders, FaderBuddy boards, CrowPanel, Choc switches and screws, as whole
  triangle meshes, against every printed part, seated and along the assembly paths (the plate dropping in 3 mm behind its place
  and sliding forward; the display sliding down its own face; the panel pressing into the display front). Touching faces score
  zero; it reports only parts that pass into each other, with where and how deep.

Expected contacts on a clean run, CrowPanel deck only: the CrowPanel passing the snap bumps on its way into the display front, and
the outer two FaderBuddy boards' rear corners on the plate's way in (a modelling difference: the real build goes together fine).
The screen-less decks check clean.

## The published site

`.github/workflows/site.yml` builds every variant from the simulator on each push (manifold pinned to the commit the STLs were
made with), fails if the checks find anything beyond the two known contacts (`tools/gate.py`), notes any STL that differs from
the committed one, and assembles the site (`tools/site.sh`): the simulator page with every variant's STLs and zip next to it, so
its download links fetch the files directly. Pushes to `main` publish it to GitHub Pages (repository **Settings → Pages →
Source: GitHub Actions**).

## Regenerating the model data

The simulator's component models are STEP files tessellated with
[occt-import-js](https://github.com/kovacsv/occt-import-js) (`tools/tess.js`, `OCCT_IMPORT_JS` points at its module) and packed
by `tools/pack.py` (CrowPanel, fader) and `tools/pack_fb.py` (FaderBuddy), into `sim/third_party/`. The fader and FaderBuddy
STEP files are in `third_party/faderbuddy/`; the CrowPanel STEP and schematics come from
[Elecrow](https://github.com/Elecrow-RD/CrowPanel-ESP32-5.79-E-paper-HMI-Display-with-272-792) and are not copied here.

## Licensing details

The printable parts (everything in `stl/` and `models/knob/`) are licensed under
[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). Each STL carries the attribution and license in its 80-byte
header and each zip includes a `LICENSE.txt`, both written by `tools/export.py` and `tools/knob.py` from `tools/license.py`.

Third-party material is kept apart, in `third_party/` and `sim/third_party/`, and keeps its own license: the fader and FaderBuddy
models are from [FaderBuddy](https://github.com/scottbez1/FaderBuddy) (Apache-2.0), and the CrowPanel mesh is derived from
Elecrow's model. `third_party/README.md` lists each one, where it came from and its license, along with the tools and libraries
the build and the page use without including them.
