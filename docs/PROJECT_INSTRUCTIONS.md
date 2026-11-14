# Working on FaderDeck: instructions for Claude

Paste these into a Claude Project's instructions (or keep them here as CLAUDE.md-style rules).

- The enclosure is defined in `sim/index.html` (`printModel()`); STLs are built from it with `./run.sh`. Never edit STLs by hand.
- Read `docs/DESIGN.md` first: frames, parts, assembly order, and the decisions behind them.
- Don't move the display, change printed parts, or change hardware without asking. When a fix would change a part I didn't
  ask about, say so and ask first.
- Before publishing or sending files, run `./run.sh` and read the exact checks. Report anything other than the two expected
  contacts (the panel passing the snap bumps; the outer FaderBuddy corners on the plate's way in).
- Check that features still work, not just that they clear: feet support their pads, snaps still engage, screws still reach
  their threads, walls stay thick enough, everything prints in its orientation without supports.
- Check against the full component meshes (`build/collide`), not sampled points: sampling missed real collisions here before.
- When reporting, say which files changed and which didn't, so I know what to reprint.
- Simulator-only changes (UI, the assembly guide, rendering) must not change the printed parts; confirm the STLs are unchanged.
