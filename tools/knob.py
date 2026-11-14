"""The FaderDeck fader knob: a body and a contrasting inlay bar, built with the CSG runner.

    python3 tools/knob.py

Frame (the simulator's knob frame): x across the knob, y up (the knob's seat is y = 0; it reaches 1.5 mm below it, round the
lever), z along the fader's travel. It stays inside the envelope the display fit and the checks assume (24 × 10.74 × 7.94 mm)
and keeps the lever slot of the knob it replaces (1.2 × 8.2 mm, 6.1 mm deep), so it fits the same fader.

Writes models/knob/fader-knob_body.stl and fader-knob_inlay.stl (print orientation, mm) and sim/knob.json.
"""
import numpy as np, os, subprocess, struct, json, base64, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from pim import load
import license
OUT = os.path.join(ROOT, 'out', 'knob'); os.makedirs(OUT, exist_ok=True)

def area(p): return sum(p[i][0] * p[(i + 1) % len(p)][1] - p[(i + 1) % len(p)][0] * p[i][1] for i in range(len(p))) / 2
def earclip(p):   # simple polygon -> triangles (indices), counter-clockwise input
    idx, tris = list(range(len(p))), []
    def inside(a, b, c, q):
        d = lambda u, v, w: (v[0] - u[0]) * (w[1] - u[1]) - (v[1] - u[1]) * (w[0] - u[0])
        return d(a, b, q) > 1e-12 and d(b, c, q) > 1e-12 and d(c, a, q) > 1e-12
    while len(idx) > 3:
        for k in range(len(idx)):
            i0, i1, i2 = idx[k - 1], idx[k], idx[(k + 1) % len(idx)]; a, b, c = p[i0], p[i1], p[i2]
            if (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]) <= 1e-12: continue
            if any(inside(a, b, c, p[j]) for j in idx if j not in (i0, i1, i2)): continue
            tris.append((i0, i1, i2)); idx.pop(k); break
        else: raise ValueError('ear clipping failed')
    tris.append(tuple(idx)); return tris

solids = []
def loft(name, levels):   # levels: [(2D outline, 3D points)], same point count, outline used for the end caps
    n = len(levels[0][0]); pos = [q for _, p3 in levels for q in p3]; tri = []
    for k in range(len(levels) - 1):
        for i in range(n): a, b, c, d = k * n + i, k * n + (i + 1) % n, (k + 1) * n + (i + 1) % n, (k + 1) * n + i; tri += [(a, b, c), (a, c, d)]
    for k, top in ((0, False), (len(levels) - 1, True)):
        p = levels[k][0]; ccw = area(p) > 0; q = p if ccw else p[::-1]; tt = earclip(q)
        if not ccw: tt = [tuple(n - 1 - i for i in t) for t in tt]
        tri += [tuple(k * n + i for i in (t if top else t[::-1])) for t in tt]
    P = np.array(pos); vol = sum(np.dot(P[a], np.cross(P[b], P[c])) for a, b, c in tri)
    if vol < 0: tri = [(a, c, b) for a, b, c in tri]
    solids.append((name, pos, tri)); return name
def prism(name, axis, poly, a0, a1):   # poly in the other two axes (x: (z, y); y: (x, z); z: (x, y)), from a0 to a1 along axis
    put = {'x': lambda u, v, a: (a, v, u), 'y': lambda u, v, a: (u, a, v), 'z': lambda u, v, a: (u, v, a)}[axis]
    return loft(name, [(poly, [put(u, v, a) for u, v in poly]) for a in (a0, a1)])
def rrect(x0, x1, z0, z1, r, n=6):
    o = []
    for cx, cz, a0 in ((x1 - r, z1 - r, 0), (x0 + r, z1 - r, 90), (x0 + r, z0 + r, 180), (x1 - r, z0 + r, 270)):
        o += [(cx + r * np.cos(np.radians(a0 + 90 * k / n)), cz + r * np.sin(np.radians(a0 + 90 * k / n))) for k in range(n + 1)]
    return o

# ---- shape (mm)
Y0, HL, HW0, HW1, RP = -1.5, 11.8, 5.3, 4.9, 2.0   # bottom, half length, half width at the bottom and at y = 8, plan corner radius
END_TOP, LAND, ZR, ZL, CH = 7.7, 6.0, 8.4, 3.0, .8   # end height, centre land height, ramp from z = ZR down to z = ZL, end chamfer
ramp = lambda z: LAND + (END_TOP - LAND) * (abs(z) - ZL) / (ZR - ZL)
# plan, drafted: narrower toward the top
loft('plan', [(rrect(-HW0, HW0, -HL, HL, RP), [(x, Y0 - .01, z) for x, z in rrect(-HW0, HW0, -HL, HL, RP)]),
              (rrect(-HW1, HW1, -HL + .4, HL - .4, RP), [(x, 8.5, z) for x, z in rrect(-HW1, HW1, -HL + .4, HL - .4, RP)])])
# side profile: square ends with a chamfer at the top, two straight ramps down to a flat land (a faceted valley), and a 1.4 mm
# 45° chamfer under each end: at the end of its travel the knob's lower end is what comes closest to the display face (1.1 mm)
half = [(HL - 1.4, Y0), (HL, Y0 + 1.4), (HL, END_TOP - CH), (HL - CH, END_TOP), (ZR, END_TOP), (ZL, LAND)]
side = half + [(-z, y) for z, y in half[::-1]]
prism('side', 'x', side, -8, 8)
# across: a 0.5 mm chamfer along the bottom edges
prism('across', 'z', [(-HW0 + .5, Y0), (HW0 - .5, Y0), (HW0 + .5, Y0 + 1), (HW0 + .5, 9), (-HW0 - .5, 9), (-HW0 - .5, Y0 + 1)], -13, 13)
# grip: three short V grooves across each ramp, stopping 1 mm inside the sides
grooves = []
for s in (-1, 1):
    for k, f in enumerate((.25, .5, .75)):
        zc = s * (ZL + f * (ZR - ZL)); tri = [(zc - .5, ramp(zc - .5) + .6), (zc + .5, ramp(zc + .5) + .6), (zc, ramp(zc) - .45)]
        if area(tri) < 0: tri = tri[::-1]
        grooves.append(prism(f'g{s}{k}', 'x', tri, -3.6, 3.6))
# the lever slot (as on the knob it replaces), with a 0.3 mm lead-in at the bottom
prism('slot', 'y', [(-.6, -4.1), (.6, -4.1), (.6, 4.1), (-.6, 4.1)], Y0 - 1, 4.6)
loft('lead', [([(-.9, -4.4), (.9, -4.4), (.9, 4.4), (-.9, 4.4)], [(x, Y0 - .01, z) for x, z in [(-.9, -4.4), (.9, -4.4), (.9, 4.4), (-.9, 4.4)]]),
              ([(-.6, -4.1), (.6, -4.1), (.6, 4.1), (-.6, 4.1)], [(x, Y0 + .3, z) for x, z in [(-.6, -4.1), (.6, -4.1), (.6, 4.1), (-.6, 4.1)]])])
# the inlay: a 1.5 mm bar across the land, flush, in a 1 mm pocket that stops short of the sides; 0.05 mm clearance all round
prism('pocket', 'y', rrect(-4.2, 4.2, -.8, .8, .3), 5.0, 7)
prism('inlay0', 'y', rrect(-4.15, 4.15, -.75, .75, .25), 5.05, LAND)
ops = ['O shape I 3 plan side across', f'O body D {3 + len(grooves)} shape slot lead pocket ' + ' '.join(grooves), 'O inlay U 1 inlay0',
       'O chk I 2 body inlay', 'V chk', 'V body', 'V inlay', f'W body {OUT}/body.mesh', f'W inlay {OUT}/inlay.mesh']
L = []
for name, pos, tri in solids:
    L.append(f'S {name} {len(pos)} {len(tri)}'); L += ['%.5f %.5f %.5f' % tuple(p) for p in pos]; L += ['%d %d %d' % t for t in tri]
open(f'{OUT}/job.txt', 'w').write('\n'.join(L + ops) + '\n')
r = subprocess.run([os.path.join(ROOT, 'build', 'csg'), f'{OUT}/job.txt'], capture_output=True, text=True); print(r.stdout, r.stderr)

def stl(fn, v, t, name):
    A, B, C = v[t[:, 0]], v[t[:, 1]], v[t[:, 2]]; n = np.cross(B - A, C - A); n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    rec = np.zeros(len(t), dtype=[('n', '<f4', 3), ('a', '<f4', 3), ('b', '<f4', 3), ('c', '<f4', 3), ('x', '<u2')]); rec['n'], rec['a'], rec['b'], rec['c'] = n, A, B, C
    with open(fn, 'wb') as f: f.write(name.encode().ljust(80, b' ')[:80]); f.write(struct.pack('<I', len(t))); f.write(rec.tobytes())
MD = os.path.join(ROOT, 'models', 'knob'); os.makedirs(MD, exist_ok=True)
packed = {}
for mesh, fn, tf in (('body', 'fader-knob_body.stl', lambda v: np.stack([v[:, 0], v[:, 2], v[:, 1] - Y0], 1)),       # bottom (slot side) on the bed
                     ('inlay', 'fader-knob_inlay.stl', lambda v: np.stack([v[:, 0], v[:, 1] - 5.05, v[:, 2]], 1))):  # on its side: 8.3 × 0.95 × 1.5 tall
    v, t = load(f'{OUT}/{mesh}.mesh'); p = tf(v); p = p - [0, 0, p[:, 2].min()]
    stl(os.path.join(MD, fn), p, t, license.stl_header(f'knob {mesh}'))
    print(mesh, len(t), 'tris, extents', (v.max(0) - v.min(0)).round(2), 'min', v.min(0).round(2), 'max', v.max(0).round(2))
    packed[{'body': 'body', 'inlay': 'accent'}[mesh]] = base64.b64encode(np.clip(np.round(v[t].reshape(-1, 3) * 100), -32768, 32767).astype('<i2').tobytes()).decode()
json.dump(packed, open(os.path.join(ROOT, 'sim', 'knob.json'), 'w'))
