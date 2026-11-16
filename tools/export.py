"""Deck-frame meshes -> print-oriented binary STLs, a zip per variant, and packed copies for the simulator to render.

    python3 tools/export.py            # every variant built in out/
    python3 tools/export.py d8k s3k    # just these

Writes stl/<variant>/*.stl and *.zip, sim/print/<variant>.json, and sim/print/variants.json (the manifest the page's
download list reads). File names, STL headers and LICENSE.txt carry the design version from VERSION; a part whose geometry
changed while VERSION stayed the same gets a warning at the end (bump VERSION and note it in CHANGELOG.md).
"""
import numpy as np, json, struct, base64, math, os, sys, glob, zipfile, hashlib
from pim import load
import license
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALL = ['d8k'] + [f's{n}{k}' for n in range(2, 9) for k in ('k', '')]
VARIANTS = sys.argv[1:] or [v for v in ALL if os.path.exists(os.path.join(ROOT, 'out', v, 'frame.json'))]

def base_tf(v):   # plate top on the bed: X = x, Y = z, Z = -y
    return np.stack([v[:, 0], v[:, 2], -v[:, 1]], 1)
def plate_tf(v):   # bottom on the bed (the display pads rise from its top): X = x, Y = -z, Z = y
    return np.stack([v[:, 0], -v[:, 2], v[:, 1]], 1)
def cover_tf(v):   # face down: same as the base's top-down, the visible top on the bed
    return base_tf(v)
def stl(fn, v, t, name):
    A, B, C = v[t[:, 0]], v[t[:, 1]], v[t[:, 2]]; n = np.cross(B - A, C - A); n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    rec = np.zeros(len(t), dtype=[('n', '<f4', 3), ('a', '<f4', 3), ('b', '<f4', 3), ('c', '<f4', 3), ('x', '<u2')])
    rec['n'], rec['a'], rec['b'], rec['c'] = n, A, B, C
    with open(fn, 'wb') as f: f.write(name.encode().ljust(80, b' ')[:80]); f.write(struct.pack('<I', len(t))); f.write(rec.tobytes())

LABEL = {'base': 'Base', 'fader-plate': 'Fader plate', 'cover': 'Cover', 'display-front': 'Display front', 'display-back': 'Display back'}
VER = license.VERSION
def prefix(v):
    return ('crowpanel-fader-deck' if v == 'd8k' else f'fader-deck-{int(v[1])}f' + ('-keys' if v.endswith('k') else '')) + f'-v{VER}'
def vtitle(v):
    return 'CrowPanel deck, 8 faders, 4 keys' if v == 'd8k' else f'screen-less deck, {int(v[1])} faders' + (', 4 keys' if v.endswith('k') else ', no keys')
def hardware(v):   # a list, shown as one bullet per line
    n = 8 if v == 'd8k' else int(v[1])
    hw = [f'{2 * n} × M3 × 4 wafer heads (faders to plate)', '4 × M3 × 4 wafer heads (plate to base)', '4 × M3 heat-set inserts (in the base)']
    if v == 'd8k': hw += ['4 × M2.5 × 4 flat heads (display back to the CrowPanel)', '2 × M2.5 × 8 socket caps (display to base, from behind)']
    if v.endswith('k'): hw.append('4 × Kailh Choc v1 switches')
    return hw + ['4 × Ø8 × 1.5 mm rubber pads']

manifest_fn = os.path.join(ROOT, 'sim', 'print', 'variants.json')
os.makedirs(os.path.dirname(manifest_fn), exist_ok=True)
manifest = json.load(open(manifest_fn)) if os.path.exists(manifest_fn) else {}
stale = []   # parts whose geometry changed under the same version
for v in VARIANTS:
    OUT = os.path.join(ROOT, 'out', v); fr = json.load(open(f'{OUT}/frame.json'))
    c, b = fr['c'], fr['b']; sb, cb = math.sin(b), math.cos(b)
    def slab_tf(q):   # face on the bed: X = x, Y = zh, Z = -yh
        yh = (q[:, 2] - c) * sb + q[:, 1] * cb; zh = (q[:, 2] - c) * cb - q[:, 1] * sb
        return np.stack([q[:, 0], zh, -yh], 1)
    def back_tf(q):   # outer face on the bed: X = x, Y = -zh, Z = yh
        yh = (q[:, 2] - c) * sb + q[:, 1] * cb; zh = (q[:, 2] - c) * cb - q[:, 1] * sb
        return np.stack([q[:, 0], -zh, yh], 1)
    parts = [('base_body', 'base', base_tf), ('plate', 'fader-plate', plate_tf), ('cover', 'cover', cover_tf)]
    if v == 'd8k': parts += [('slab_body', 'display-front', slab_tf), ('slab_back', 'display-back', back_tf)]
    SD = os.path.join(ROOT, 'stl', v); os.makedirs(SD, exist_ok=True)
    for f in glob.glob(f'{SD}/*'): os.remove(f)
    packed, entries = {}, []
    for mesh, part, tf in parts:
        q, t = load(f'{OUT}/{mesh}.mesh')
        p = tf(q); p = p - np.array([(p[:, 0].min() + p[:, 0].max()) / 2, (p[:, 1].min() + p[:, 1].max()) / 2, p[:, 2].min()])
        fn = f'{prefix(v)}_{part}.stl'; stl(f'{SD}/{fn}', p, t, license.stl_header(part, VER))
        size = [round(float(s), 1) for s in (p.max(0) - p.min(0))]
        print(v, part, len(t), 'tris, extents', size)
        geom = hashlib.sha1(open(f'{SD}/{fn}', 'rb').read()[84:]).hexdigest()[:12]   # the triangles, not the header
        old = {e['part']: e.get('geom') for e in manifest.get(v, {}).get('parts', [])} if manifest.get(v, {}).get('version') == VER else {}
        if old.get(part) and old[part] != geom: stale.append(f'{v} {part}')
        entries.append({'part': part, 'label': LABEL[part], 'file': fn, 'size': size, 'geom': geom})
        w = np.clip(np.round(q * 100), -32768, 32767).astype('<i2').tobytes(); w += b'\0' * (-len(w) % 4)
        packed[mesh] = base64.b64encode(w + t.astype('<u4').tobytes()).decode() + '|' + str(len(q))
    packed['frame'] = fr
    json.dump(packed, open(os.path.join(ROOT, 'sim', 'print', f'{v}.json'), 'w'))
    zn = f'{prefix(v)}.zip'
    lic = license.text(f'FaderDeck v{VER} printable parts: {vtitle(v)} (mm, in print orientation)', [e['file'] for e in entries])
    def put(z, name, data):   # a fixed timestamp, so an unchanged part makes an identical zip
        zi = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0)); zi.compress_type = zipfile.ZIP_DEFLATED; zi.external_attr = 0o644 << 16; z.writestr(zi, data)
    with zipfile.ZipFile(f'{SD}/{zn}', 'w') as z:
        for e in entries: put(z, e['file'], open(f'{SD}/{e["file"]}', 'rb').read())
        put(z, 'LICENSE.txt', lic)
    manifest[v] = {'version': VER, 'dir': f'stl/{v}', 'zip': zn, 'parts': entries, 'hardware': hardware(v), 'license': lic}
json.dump({k: manifest[k] for k in ALL if k in manifest}, open(manifest_fn, 'w'), indent=1)
if stale: print(f'\nWARNING: these parts changed but VERSION is still {VER}; bump VERSION and add a CHANGELOG.md entry:\n  ' + '\n  '.join(stale))

# for the published page (it can't serve STL files): each variant's STLs as base64 in one JSON, which the page zips for the
# viewer. Build output only (sim/dl/ is not committed)
DL = os.path.join(ROOT, 'sim', 'dl'); os.makedirs(DL, exist_ok=True)
for v in VARIANTS:
    m = manifest[v]
    json.dump({p['file']: base64.b64encode(open(os.path.join(ROOT, m['dir'], p['file']), 'rb').read()).decode() for p in m['parts']}, open(f'{DL}/{v}.json', 'w'))
