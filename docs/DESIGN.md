# FaderDeck enclosure: design notes

How the enclosure is put together and why, as of the parts in `stl/`. Numbers are mm. The CrowPanel deck (`d8k`) is described
first; the screen-less family is at the end.

## Frames

- **Deck frame** (everything in `printModel()` and the checks): x across (+ right, seen from the front), z front to back
  (+ toward the user), y up from the deck top. The cover's top face is y = 0; the cover is 1.4 thick, so the fader plate's top
  is y = -1.4 and its bottom (and the base's top face) y = -3.4. The deck stands at 12.6° on the desk.
- **Hinge frame** (the display): x as above, yh square to the display face (+ out of the screen), zh along the face (+ down
  toward the faders). The display leans back 32.4° from the deck; the crease where its face meets the deck is at deck z = -41.
  hinge → deck: `y = yh·cos b - zh·sin b`, `z = c + yh·sin b + zh·cos b`.
- **CrowPanel STEP frame**: the panel's own; its active area is centred 3.6 mm right of the board's centre (measured on a print),
  so the board sits 3.6 mm left of the window, and the window stays centred over the faders.

## The five parts

- **Base**: the shell, open at the bottom, with tucked-in walls and four rubber-pad feet. Inside: a ledge round the top edge that
  the fader plate rests on (deep at the front, where it reaches under the fader motors), side walls thickened where there's room,
  four M3 inserts (front corners and sides), and two bolt tubes from the rear wall to the display. Feet sit where they clear the
  faders (the front pair sit behind the fader motors); each pad is fully supported and each foot is a 45° buttress blended into
  its wall.
- **Fader plate**: 2 mm, holding the eight faders (two M3 × 4 wafer heads each, heads in counterbores) and the four Choc switches
  (1.2 mm plate round each cut-out, Kailh's spec, with 45° pocket walls underneath so it prints bottom-down with no bridges). It
  is solid to the back except five small pockets where the CrowPanel's lower edge dips through, and rises into two 3 mm pads
  behind the panel's bottom standoffs. Prints bottom-down.
- **Cover**: 1.4 mm, wraps the plate's edge and clips on with eight snap bumps (two per side at the thirds, two front, two
  back) into dimples in the plate's edge. Hides every screw on the deck.
- **Display front**: 2 mm face and 1.6 mm walls, open at the bottom. The CrowPanel presses in from behind and six snap bumps catch
  its PCB's back edge (0.45-0.5 mm over it); two ribs locate the board's short side. Two tongues run forward under the plate and
  cover to stop the display tipping back. Top corners: 2.2 mm inside (the PCB's 2 mm corners), 4 mm outside.
- **Display back**: cosmetic, 1.8 mm, sits inside the walls on the PCB's standoff faces, four M2.5 × 4 flat heads into the top
  corner and middle standoffs. BOOT and RST poke through; the GPIO socket shows through a notch.

## How it goes together (and the reasons)

1. **Faders chained, then into the plate.** Each FaderBuddy is soldered under its fader; the boards' 5-pin headers plug into the
   next board's socket, so the eight go in as one block.
2. **Plate into the base: drop 3 mm behind, slide forward.** The base's front ledge reaches under the fader motors for support;
   the plate clears it by going in behind its place and sliding forward and down. The base keeps the drop path clear.
3. **Plate screws**: four M3 × 4 wafer heads into inserts (the same screws as the faders; enough in the build). The back of the plate is held by the display bolts (step 7) instead
   of separate screws.
4. **Cover**, then **switches and knobs**.
5. **Display**: CrowPanel into the front, the back screwed on, then the assembly slides down its own face onto the deck: the
   tongues hook under the plate and cover, the panel's lower edge drops into the plate's pockets.
6. **Two M2.5 × 8 bolts from outside the base's rear wall**, through the base and the plate's pads, into the panel's bottom
   standoffs. They hold the display down (stopping it tipping forward), and the back of the plate to the base. The cover is
   not clamped: the pads come up through holes in it. The heads seat in spot faces square to the bolt.

## Decisions worth remembering

- The display's position comes from a fit (`fitDisplay`): as low and far forward as the faders allow. It keeps the knob at the
  end of its travel 1.1 mm clear of the face, keeps every part of the panel clear of the fader frames (which run 14 mm behind
  their rear screws, right under the plate), and the fader screw heads. Current result: 12.3 mm from the knob tops to the
  first row of pixels.
- The panel's lower-edge parts (USB-C, SD) set the display height: they ride 0.4-0.6 mm over the fader frames.
- Wires from the back of the CrowPanel go down the pass beside the USB-C opening (about 19 mm wide) into the base, behind the
  fader motors.
- Power: inject 5 V at the CrowPanel's battery connector (B1, SH1.0) or at D2's unstriped end (USB side); keep the supply at or
  below 5.25 V. Run the motor 5 V to FaderBuddy as its own pair; take FaderBuddy's 3.3 V logic from the panel's GPIO header 3V3.
- Printed and assembled: the base from the latest export went together fine, including the FaderBuddy boards.

## The simulator

`sim/index.html` is both the design tool and the source of the geometry. Sliders were dropped as the design settled (display angle,
incline, lip); the fixed values live as constants near the top of the 3D code. `printModel()` builds every part; the shapes the
parts must avoid come from the actual component models (fader bodies by depth band, the panel's own points, the Choc switches).

## Screen-less decks (s2-s8, s2k-s8k)

A family rather than one-offs: the base's two ends are fixed shapes and only the middle grows with the fader count (17.85 mm
per fader), so every size shares the same end walls, foot placement and screw positions relative to its ends.

- **Layout**: faders (and the key column, when fitted) centred on x = 0. The plain end sits 25 mm out from the outer fader's
  centre; the key end 12.4 mm out from the keys, which keep the display deck's spacing (16.5 mm past the last fader). The
  keyless decks are about 4 mm narrower than the keyed ones.
- **Base length**: the rear edge is at z = -61.2, from the fader bodies' rear ends (z = -54) plus the plate's 3 mm slide-in and
  the wall. The rear wall's tuck is capped at 4.5 mm so the FaderBuddy boards' lower rear corners clear it on the way in.
- **Plate screws**: four M3 × 4 wafer heads into inserts at the corners, 14.5 mm out from the outer faders (in line with the
  keys on that side), each boss bridged to its side wall. Nothing holds the back of the plate but these and the ledge.
- **Feet**: placed clear of the FaderBuddy boards as well as the faders, seated and along the plate's way in, so each 45°
  buttress stays whole and fully supports its pad.
- **Corners**: all four rounded 7 mm in plan (the display deck keeps 1.5 mm rear corners).
- **Cover snaps**: as on the display deck, with the front and back pairs closing in on narrow decks.
- **Cable notch** (every base, the display deck's too): an inverted U through the bottom of the rear wall at the centre,
  4 mm wide, its round top 4.5 mm above the rim.
- **Not offered**: one fader. The display deck stays eight faders and four keys.

## The fader knob

`tools/knob.py` builds it (the CSG runner, same as the enclosure). 23.5 × 10.6 mm, 7.7 mm tall at its ends: square ends with
a chamfered top edge, two straight ramps down to a flat 6 mm land, three short V grip grooves on each ramp, and a flush 1.5 mm
inlay bar (a separate print, contrasting colour) across the land as the position mark. It keeps the lever slot of the knob it
replaced (1.2 × 8.2 mm, 6.1 mm deep, with a 0.3 mm lead-in) and stays inside that knob's envelope, so the display fit is unchanged.
Under each end a 1.4 mm 45° chamfer keeps the knob's lower end 1.17 mm off the display face at the end of its travel (the fit's
limit is 1.1 mm; without it the square end came within 0.74 mm).
