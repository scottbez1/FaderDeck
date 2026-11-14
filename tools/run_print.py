"""Pull the printable solids out of the simulator, run the CSG, check interference, write meshes.

    python3 tools/run_print.py            # every variant
    python3 tools/run_print.py d8k s3k    # just these

Variants: d8k is the CrowPanel deck (8 faders, 4 keys); sN / sNk are screen-less decks with N = 2-8 faders, without / with
the four keys. Each variant's meshes, frame and check output go to out/<variant>/.
"""
import asyncio, json, subprocess, sys, math, os, time, struct
from playwright.async_api import async_playwright
# Paths: everything relative to the repo; the outside pieces come from the environment (see README)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIM, BIN = os.path.join(ROOT, 'sim'), os.path.join(ROOT, 'build')
THREE = os.environ.get('THREE_DIR', os.path.join(ROOT, 'ext', 'three'))   # a three.js checkout (r147-era build/ and examples/js/)
CHROMIUM = os.environ.get('CHROMIUM')                                     # optional: a specific Chromium for Playwright
PORT = int(os.environ.get('SIM_PORT', '8765'))
LOC = {'three.min.js': f'{THREE}/build/three.min.js', 'OrbitControls.js': f'{THREE}/examples/js/controls/OrbitControls.js'}

ALL = ['d8k'] + [f's{n}{k}' for n in range(2, 9) for k in ('k', '')]
def vhash(v):
    if v == 'd8k': return 'disp=1'
    return f'disp=0&nf={int(v[1])}&keys={1 if v.endswith("k") else 0}'
VARIANTS = sys.argv[1:] or ALL
for v in VARIANTS: assert v in ALL, f'unknown variant {v}'

async def grab():
    out = {}
    async with async_playwright() as p:
        b = await p.chromium.launch(**({'executable_path': CHROMIUM} if CHROMIUM else {}), args=['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'])
        for v in VARIANTS:
            pg = await b.new_page(); errs = []
            pg.on('pageerror', lambda e: errs.append(e.message))
            async def route(r):
                u = r.request.url
                for k, f in LOC.items():
                    if u.endswith(k): return await r.fulfill(path=f, content_type='application/javascript')
                if 'fonts.g' in u: return await r.abort()
                return await r.continue_()
            await pg.route('**/*', route)
            await pg.add_init_script('window.NO_IDLE_SPIN = true')
            await pg.goto(f'http://127.0.0.1:{PORT}/index.html#{vhash(v)}'); await pg.wait_for_timeout(7000)
            assert await pg.evaluate('CFG.id') == v
            model = json.loads(await pg.evaluate("JSON.stringify(printModel())"))
            probe = json.loads(await pg.evaluate("JSON.stringify(printProbe())"))
            comps = json.loads(await pg.evaluate("JSON.stringify(printComps())"))
            for e in errs: print(v, 'page error:', e)
            out[v] = (model, probe, comps); await pg.close()
        await b.close()
    return out

srv = subprocess.Popen([sys.executable, '-m', 'http.server', str(PORT)], cwd=SIM, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
try: grabbed = asyncio.run(grab())
finally: srv.terminate()

def wmesh(fn, pos, idx):
    with open(fn, 'wb') as f: f.write(struct.pack('<II', len(pos) // 3, len(idx) // 3)); f.write(struct.pack(f'<{len(pos)}f', *pos)); f.write(struct.pack(f'<{len(idx)}I', *idx))

for v in VARIANTS:
    model, probe, comps = grabbed[v]
    disp = v == 'd8k'
    OUT = os.path.join(ROOT, 'out', v); os.makedirs(OUT, exist_ok=True)
    PARTS = ['base_body', 'plate', 'cover'] + (['slab_body', 'slab_back'] if disp else [])
    print(f'===== {v} =====')
    fr = model['frame']; json.dump(fr, open(f'{OUT}/frame.json', 'w'))
    L = []
    for s in model['solids']:
        nv, nt = len(s['pos']) // 3, len(s['idx']) // 3
        L.append(f"S {s['name']} {nv} {nt}")
        L += [' '.join('%.5f' % q for q in s['pos'][i*3:i*3+3]) for i in range(nv)]
        L += [' '.join(str(q) for q in s['idx'][i*3:i*3+3]) for i in range(nt)]
    L += model['ops']
    pairs = [p for p in ['base_body slab_body', 'cover base_body', 'cover slab_body', 'plate base_body', 'plate cover', 'plate slab_body', 'slab_back slab_body', 'slab_back base_body', 'slab_back plate', 'slab_back cover']
             if all(q in PARTS for q in p.split())]
    for p in pairs: a, c = p.split(); L += [f"O x_{a}_{c} I 2 {a} {c}", f"V x_{a}_{c}"]
    # the cover comes off along the deck normal; only its snap bumps may touch the plate on the way (first ~2 mm)
    for d in [0.3, 1, 2, 3, 5, 8]:
        L += [f"T cv{d} cover 0 {d} 0", f"O xcvp{d} I 2 cv{d} plate", f"V xcvp{d}", f"O xcvb{d} I 2 cv{d} base_body", f"V xcvb{d}"]
    b = fr['b']; dz, dy = -math.cos(b), math.sin(b)
    if disp:   # insertion path: slide the slab (and the board) up its own plane
        for d in [0.5, 2, 5, 10, 20, 35]:
            L += [f"T sk{d} slab_back 0 {dy*d} {dz*d}", f"O xk{d} I 2 sk{d} base_body", f"V xk{d}", f"O xkc{d} I 2 sk{d} cover", f"V xkc{d}"]
            L += [f"T sl{d} slab_body 0 {dy*d} {dz*d}", f"O xs{d} I 2 sl{d} base_body", f"V xs{d}", f"O xc{d} I 2 sl{d} cover", f"V xc{d}", f"O xpl{d} I 2 sl{d} plate", f"V xpl{d}"]
    # the outer walls below the plate must come through every cut untouched (except the cable notch, which is meant to)
    bx = [(x, y, z) for x in (-300, 300) for y in (-300, -3.2) for z in (-300, 300)]
    L.append("S belowPlateChk 8 12"); L += ["%g %g %g" % p for p in bx]
    L += ["0 1 3", "0 3 2", "4 6 7", "4 7 5", "0 4 5", "0 5 1", "2 3 7", "2 7 6", "0 2 6", "0 6 4", "1 5 7", "1 7 3"]
    L += ["O wallsBelow I 2 shell belowPlateChk", "O wallsLost D 3 wallsBelow base_body cableNotch", "V wallsLost"]
    # the notch must actually open the wall: what it takes from the shell must not be zero
    L += ["O notchCut I 2 shell cableNotch", "V notchCut"]
    if disp:   # no cutter may break through the outside of the base: what any cut removed must lie inside the outer skin, 0.8 mm in
        L += ["O tpx U 2 tpockX0 tpockX1", "O breach D 2 tpx outer", "V breach"]
    json.dump(probe, open(f'{OUT}/probe.json', 'w'))
    for n in PARTS: L += [f"V {n}", f"W {n} {OUT}/{n}.mesh"]
    open(f'{OUT}/job.txt', 'w').write('\n'.join(L) + '\n')
    r = subprocess.run([os.path.join(BIN, 'csg'), f'{OUT}/job.txt'], capture_output=True, text=True)
    print(r.stdout); print(r.stderr[-3000:])

    # ---- exact component checks: whole triangle meshes against the printed parts (crossing depth > 0.01 mm, or vertices inside)
    C = ['M ' + n + f' {OUT}/{n}.mesh' for n in PARTS]
    for g, m in comps.items():
        if m['idx']: wmesh(f'{OUT}/c_{g}.mesh', m['pos'], m['idx']); C.append(f'M {g} {OUT}/c_{g}.mesh')
    have = {g for g, m in comps.items() if m['idx']}
    X = lambda label, comp, part, d=(0, 0, 0): C.append(f'X {label} {comp} {part} {d[0]:.4f} {d[1]:.4f} {d[2]:.4f}')
    for comp, parts in {'board': PARTS, 'screws': ['base_body', 'plate'], 'faders': ['base_body', 'plate', 'cover'],
                        'faderbuddy': ['base_body', 'plate'], 'choc': ['base_body', 'plate', 'cover']}.items():
        if comp in have:
            for p in parts: X(f'{comp}/{p}', comp, p)
    if disp:   # the display assembly slides down its own face onto the deck: the board on the way
        for d in [0.5, 1, 2, 4, 7, 10, 15, 20, 30]:
            for p in ['base_body', 'plate', 'cover']: X(f'slide{d}:board/{p}', 'board', p, (0, dy * d, dz * d))
    # the fader plate goes in with its faders and switches: straight down 3 mm behind its place, then forward-and-down onto the ledges
    path = [(h, 3) for h in (45, 30, 20, 12, 8, 5, 3.5)] + [(3.5 * k / 12, 3 * k / 12) for k in range(11, 0, -1)]
    for h, bk in path:
        for comp in ['faders', 'faderbuddy', 'choc']:
            if comp in have: X(f'plate-in_h{h:.2f}_b{bk:.2f}:{comp}', comp, 'base_body', (0, h, -bk))
    if disp:   # the panel into the display front from behind: only the snap bumps should touch on the way
        for d in [0.3, 0.8, 1.5, 2.5, 4, 8]: X(f'panel-in{d}:board/front', 'board', 'slab_body', (0, -math.cos(b) * d, -math.sin(b) * d))
    open(f'{OUT}/collide.txt', 'w').write('\n'.join(C) + '\n')
    t0 = time.time()
    r = subprocess.run([os.path.join(BIN, 'collide'), f'{OUT}/collide.txt'], capture_output=True, text=True)
    lines = r.stdout.splitlines(); hits = [l for l in lines if 'crossings     0 depth 0.000 | inside     0' not in l]
    print('\n'.join(hits)); print(r.stderr[-2000:]); print(f'exact checks: {len(lines)} pairs, {len(hits)} with contact, {time.time() - t0:.1f} s')
    open(f'{OUT}/checks.txt', 'w').write(r.stdout)

    # ---- feet: every rubber pad's footprint (0.2 mm above the rim) must sit on solid base, and the buttresses' slide-outs
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import numpy as np; from pim import load, inside
    bv, bt = load(f'{OUT}/base_body.mesh'); pp = np.array(fr['padPts'])
    sup = [(int(k), int(inside(pp[pp[:, 0] == k][:, 1:], bv, bt).sum()), int((pp[:, 0] == k).sum())) for k in sorted(set(pp[:, 0]))]
    print('feet: pads supported', ', '.join(f'{a}/{n}' for _, a, n in sup), '· buttress shift', fr['footShift'],
          '· OK' if all(a == n for _, a, n in sup) and len(sup) == 4 else '· CHECK')
