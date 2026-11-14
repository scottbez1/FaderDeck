# Third-party material

Everything in this folder, and the model meshes in `sim/third_party/`, comes from other projects and keeps its own license.
None of it is covered by FaderDeck's own licenses (see the top-level README).

| What | Where | From | License |
|---|---|---|---|
| Motorised fader model (60 mm) | `faderbuddy/motor_fader_60mm.step` | [FaderBuddy](https://github.com/scottbez1/FaderBuddy), `reference/motor_fader_60mm/` | Apache-2.0 (`faderbuddy/LICENSE.txt`) |
| FaderBuddy board model | `faderbuddy/faderbuddy_motor_fader_main.step` | [FaderBuddy](https://github.com/scottbez1/FaderBuddy), a KiCad 3D export of its board | Apache-2.0 (`faderbuddy/LICENSE.txt`) |
| Fader and FaderBuddy meshes for the simulator | `sim/third_party/fader.json`, `sim/third_party/fb.json` | Derived from the two models above | Apache-2.0 (`faderbuddy/LICENSE.txt`) |
| CrowPanel display mesh for the simulator | `sim/third_party/crowpanel.json` | Derived from Elecrow's CrowPanel ESP32 5.79" model | No license stated by Elecrow; see `elecrow-crowpanel/README.md` |

## Used at build or run time, not included here

| What | How it's used | License |
|---|---|---|
| [three.js](https://threejs.org) r147 | Loaded by the simulator page from a CDN | MIT |
| [manifold](https://github.com/elalish/manifold) | Fetched and built by `build.sh` / CI; linked into `build/csg` | Apache-2.0 |
| [occt-import-js](https://github.com/kovacsv/occt-import-js) | Used by `tools/tess.js` to tessellate STEP files, when regenerating the meshes | LGPL-2.1 |
| [Playwright](https://playwright.dev) and Chromium | Run the simulator headless during the build | Apache-2.0 / BSD-3-Clause |
| Google Fonts: Archivo, Archivo Narrow, Barlow, Barlow Condensed, JetBrains Mono | Loaded by the simulator page | SIL Open Font License 1.1 |
