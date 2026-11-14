import numpy as np, json, struct, sys
def load(fn):
    d = open(fn, 'rb').read(); nv, nt = struct.unpack('<II', d[:8])
    v = np.frombuffer(d, '<f4', nv*3, 8).reshape(-1, 3).astype(np.float64); t = np.frombuffer(d, '<u4', nt*3, 8+nv*12).reshape(-1, 3)
    return v, t
def inside(pts, v, t):
    # ray along +x with a slight skew; parity
    A, B, C = v[t[:,0]], v[t[:,1]], v[t[:,2]]
    d = np.array([1, 1e-4, 2e-4]); d /= np.linalg.norm(d)
    e1, e2 = B - A, C - A; h = np.cross(d, e2); a = (e1*h).sum(1); ok = np.abs(a) > 1e-12; f = np.where(ok, 1/np.where(ok, a, 1), 0)
    res = np.zeros(len(pts), bool)
    for i0 in range(0, len(pts), 2000):
        P = pts[i0:i0+2000, None, :]; s = P - A[None]; u = f * (s*h).sum(2); q = np.cross(s, e1[None]); w = f * (q*d).sum(2); tt = f * (q*e2[None]).sum(2)
        hit = ok & (u >= 0) & (w >= 0) & (u + w <= 1) & (tt > 0)
        res[i0:i0+2000] = hit.sum(1) % 2 == 1
    return res
if __name__ == '__main__':
    probe = json.load(open('print/probe.json')); part = sys.argv[1]; v, t = load(f'print/{part}.mesh')
    for g in sys.argv[2:]:
        p = np.array(probe[g]).reshape(-1, 3); r = inside(p, v, t); q = p[r]
        print(g, len(p), 'inside', r.sum())
        if len(q):
            # cluster summary by rounding
            keys = {}
            for x in q: keys.setdefault((round(x[0]/10), round(x[1]/2), round(x[2]/10)), []).append(x)
            for k, xs in sorted(keys.items(), key=lambda kv: -len(kv[1]))[:12]: xs = np.array(xs); print('  ', len(xs), xs.min(0).round(2), xs.max(0).round(2))
