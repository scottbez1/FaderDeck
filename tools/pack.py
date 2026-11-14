"""Pack tessellated meshes into one compact binary per model, merged by material.

Layout: [u32 headerLen][header JSON utf8, padded to 4][per group: i16 pos*3 (mm*100), pad4, u32 idx]
"""
import json, struct, sys, re

def mat_crow(name, i):
    n = name.upper()
    if 'COVER' in n or n.endswith('5-79-PANEL'): return 'shell'
    if 'LCD_ASM' in n: return 'paperedge' if i == 1 else 'panel'
    if 'NONE-3307' in n: return 'header'   # stock right-angle 2x10 GPIO header
    if 'XB-TM' in n: return 'dial'
    if 'KEY-579' in n: return 'key'
    if 'M2_5X3_5' in n or 'TYPE_C' in n: return 'metal'
    if 'PCB' in n: return 'pcb'
    return 'comp'

def mat_fader(name, i, color):
    name = name.split('/')[-1]
    if 'reference_pcb' in name: return None
    if 'stem' in name: return 'stem'
    if 'frame' in name: return 'frame'
    if 'motor' in name and color and color[0] > 0.55: return 'metal'
    if 'motor' in name: return 'motor'
    return 'term'

def pack(raw_path, out_path, matfn):
    meshes = json.load(open(raw_path))
    groups = {}
    for i, m in enumerate(meshes):
        mat = matfn(m['name'] or '', i) if matfn is mat_crow else matfn(m['name'] or '', i, m.get('color'))
        if mat is None: continue
        g = groups.setdefault(mat, {'pos': [], 'idx': []})
        base = len(g['pos']) // 3
        g['pos'].extend(m['pos'])
        g['idx'].extend(base + k for k in m['idx'])
    header, blobs = [], []
    for mat, g in groups.items():
        pos = b''.join(struct.pack('<h', max(-32768, min(32767, round(v * 100)))) for v in g['pos'])
        if len(pos) % 4: pos += b'\0' * (4 - len(pos) % 4)
        idx = struct.pack('<%dI' % len(g['idx']), *g['idx'])
        header.append({'mat': mat, 'v': len(g['pos']) // 3, 'i': len(g['idx'])})
        blobs.append(pos + idx)
    h = json.dumps(header).encode()
    h += b' ' * ((4 - len(h) % 4) % 4)
    with open(out_path, 'wb') as f:
        f.write(struct.pack('<I', len(h)) + h + b''.join(blobs))
    print(out_path, header)

pack('crow.raw.json', 'crowpanel.bin', mat_crow)
pack('fader.raw.json', 'fader.bin', mat_fader)
