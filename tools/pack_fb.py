"""FaderBuddy board (KiCad STEP export, tessellated by tess.js) -> sim/third_party/fb.json, in the fader model's own frame.

  node tools/tess.js third_party/faderbuddy/faderbuddy_motor_fader_main.step out/fb 0.08
  python3 tools/pack_fb.py out/fb.raw.json sim/third_party/fb.json

The board's pads line up with the fader's pins: KiCad (kx, ky, kz) -> fader (ky + 50, 22.7 - kz, 100 - kx). Terminal pins land
at fader z 43.8, motor pins at z -9.55, the board's top face (components) on y 21.1, facing the fader. Copper, pads, vias and
silkscreen are left out; the male right-angle header is kept as its own group (hdr_*) so the end of the chain can drop it."""
import json, struct, base64, collections, sys
raw = json.load(open(sys.argv[1])); groups = collections.OrderedDict()
for m in raw:
    n = m['name']
    if n.endswith(('_copper', '_pad', '_via', '_silkscreen')): continue
    col = m.get('color') or [0.2, 0.2, 0.2]
    key = 'c_%02x%02x%02x' % tuple(int(max(0, min(1, c)) * 255) for c in col[:3])
    if n.endswith('_soldermask'): key = 'fbmask'
    if n.endswith('_PCB'): key = 'fbfr4'
    if 'PinHeader_1x05' in n: key = 'hdr_' + key
    g = groups.setdefault(key, {'pos': [], 'idx': []}); base = len(g['pos']) // 3; p = m['pos']
    for k in range(0, len(p), 3): g['pos'] += [p[k + 1] + 50, 22.7 - p[k + 2], 100 - p[k]]
    g['idx'] += [base + i for i in m['idx']]
header, blobs = [], []
for mat, g in groups.items():
    pos = b''.join(struct.pack('<h', max(-32768, min(32767, round(v * 100)))) for v in g['pos']); pos += b'\0' * (-len(pos) % 4)
    blobs.append(pos + struct.pack('<%dI' % len(g['idx']), *g['idx'])); header.append({'mat': mat, 'v': len(g['pos']) // 3, 'i': len(g['idx'])})
h = json.dumps(header).encode(); h += b' ' * (-len(h) % 4)
json.dump({'b64': base64.b64encode(struct.pack('<I', len(h)) + h + b''.join(blobs)).decode()}, open(sys.argv[2], 'w'))
