// Exact interference checker: component triangle soups against closed printed parts.
//   M name file                        load a mesh: u32 nv, u32 nt, f32 xyz*nv, u32 abc*nt (the csg runner's W format)
//   X label comp part dx dy dz         test comp (moved by dx dy dz) against part:
//      crossings: comp/part triangle pairs that genuinely cross. Each pair is scored by how far they pass through each other
//        (the smaller of: how far the comp triangle reaches behind the part triangle's plane, how far the part triangle straddles
//        the comp triangle's plane), so touching faces, coplanar or square, score ~0
//      inside: comp vertices inside the part (ray parity, 3 rays vote) and the deepest of them (true distance to the surface);
//        this also catches a piece buried wholly inside a part, which crosses nothing
//   Output: one line per X: label, crossings over 0.01 mm, max crossing depth, bbox of those crossings, inside count/max depth
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <fstream>
#include <iostream>
#include <map>
#include <numeric>
#include <sstream>
#include <string>
#include <vector>
using V = std::array<double, 3>;
static V sub(V a, V b) { return {a[0] - b[0], a[1] - b[1], a[2] - b[2]}; }
static V add(V a, V b) { return {a[0] + b[0], a[1] + b[1], a[2] + b[2]}; }
static V mul(V a, double s) { return {a[0] * s, a[1] * s, a[2] * s}; }
static double dot(V a, V b) { return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]; }
static V cross(V a, V b) { return {a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]}; }
static double len(V a) { return std::sqrt(dot(a, a)); }

struct Mesh { std::vector<V> v; std::vector<std::array<uint32_t, 3>> t; };
struct Box { V lo{1e30, 1e30, 1e30}, hi{-1e30, -1e30, -1e30};
  void add(V p) { for (int i = 0; i < 3; i++) { lo[i] = std::min(lo[i], p[i]); hi[i] = std::max(hi[i], p[i]); } }
  void add(const Box& b) { add(b.lo); add(b.hi); }
  bool hit(const Box& b, double e = 0) const { for (int i = 0; i < 3; i++) if (lo[i] > b.hi[i] + e || b.lo[i] > hi[i] + e) return false; return true; } };

struct BVH {   // over the triangles of one mesh (with an offset applied to its vertices)
  struct Node { Box b; int l = -1, r = -1, s = 0, n = 0; };
  std::vector<Node> nodes; std::vector<int> idx; std::vector<std::array<V, 3>> tri; std::vector<Box> tb;
  void build(const Mesh& m, V off) {
    tri.resize(m.t.size()); tb.resize(m.t.size());
    for (size_t i = 0; i < m.t.size(); i++) { for (int k = 0; k < 3; k++) { tri[i][k] = add(m.v[m.t[i][k]], off); tb[i].add(tri[i][k]); } }
    idx.resize(tri.size()); std::iota(idx.begin(), idx.end(), 0); nodes.clear(); nodes.reserve(2 * tri.size() + 1);
    if (!tri.empty()) rec(0, (int)tri.size());
  }
  int rec(int s, int n) {
    int me = nodes.size(); nodes.push_back({}); Box b; for (int i = s; i < s + n; i++) b.add(tb[idx[i]]); nodes[me].b = b;
    if (n <= 4) { nodes[me].s = s; nodes[me].n = n; return me; }
    int ax = 0; double best = -1; for (int a = 0; a < 3; a++) if (b.hi[a] - b.lo[a] > best) { best = b.hi[a] - b.lo[a]; ax = a; }
    auto c = [&](int i) { return tb[i].lo[ax] + tb[i].hi[ax]; };
    std::nth_element(idx.begin() + s, idx.begin() + s + n / 2, idx.begin() + s + n, [&](int a, int b2) { return c(a) < c(b2); });
    int l = rec(s, n / 2), r = rec(s + n / 2, n - n / 2); nodes[me].l = l; nodes[me].r = r; return me;
  }
};

// ---- triangle/triangle: the segment where they cross (interval method). Returns false if they don't
static bool triTri(const std::array<V, 3>& A, const std::array<V, 3>& B, V& p0, V& p1) {
  V nB = cross(sub(B[1], B[0]), sub(B[2], B[0])); double lB = len(nB); if (lB < 1e-12) return false; nB = mul(nB, 1 / lB);
  V nA = cross(sub(A[1], A[0]), sub(A[2], A[0])); double lA = len(nA); if (lA < 1e-12) return false; nA = mul(nA, 1 / lA);
  double dA[3], dB[3]; const double eps = 1e-7;
  for (int i = 0; i < 3; i++) { dA[i] = dot(sub(A[i], B[0]), nB); dB[i] = dot(sub(B[i], A[0]), nA); if (std::fabs(dA[i]) < eps) dA[i] = 0; if (std::fabs(dB[i]) < eps) dB[i] = 0; }
  if ((dA[0] > 0 && dA[1] > 0 && dA[2] > 0) || (dA[0] < 0 && dA[1] < 0 && dA[2] < 0)) return false;
  if ((dB[0] > 0 && dB[1] > 0 && dB[2] > 0) || (dB[0] < 0 && dB[1] < 0 && dB[2] < 0)) return false;
  if (dA[0] == 0 && dA[1] == 0 && dA[2] == 0) return false;   // coplanar: touching, not crossing
  V D = cross(nA, nB); double lD = len(D); if (lD < 1e-12) return false; D = mul(D, 1 / lD);
  // the segment of a triangle on the other's plane, as points
  auto seg = [&](const std::array<V, 3>& T, const double* d, V& a, V& b) {
    std::vector<V> pts;
    for (int i = 0; i < 3; i++) { int j = (i + 1) % 3;
      if (d[i] == 0) pts.push_back(T[i]);
      if ((d[i] < 0 && d[j] > 0) || (d[i] > 0 && d[j] < 0)) { double s = d[i] / (d[i] - d[j]); pts.push_back(add(T[i], mul(sub(T[j], T[i]), s))); } }
    if (pts.empty()) return false;
    a = b = pts[0]; double ta = dot(a, D), tb2 = ta;
    for (auto& p : pts) { double t = dot(p, D); if (t < ta) { ta = t; a = p; } if (t > tb2) { tb2 = t; b = p; } }
    return true; };
  V a0, a1, b0, b1; if (!seg(A, dA, a0, a1) || !seg(B, dB, b0, b1)) return false;
  double s0 = std::max(dot(a0, D), dot(b0, D)), s1 = std::min(dot(a1, D), dot(b1, D));
  if (s1 < s0 - 1e-9) return false;
  p0 = dot(a0, D) >= dot(b0, D) ? a0 : b0; p1 = dot(a1, D) <= dot(b1, D) ? a1 : b1;
  return true;
}

// ---- inside test: parity along a ray (Möller–Trumbore), through the BVH
static bool rayBox(const Box& b, V o, V d, double tmax) {
  double t0 = 0, t1 = tmax;
  for (int i = 0; i < 3; i++) { if (std::fabs(d[i]) < 1e-15) { if (o[i] < b.lo[i] || o[i] > b.hi[i]) return false; continue; }
    double a = (b.lo[i] - o[i]) / d[i], c = (b.hi[i] - o[i]) / d[i]; if (a > c) std::swap(a, c); t0 = std::max(t0, a); t1 = std::min(t1, c); if (t0 > t1) return false; }
  return true;
}
static int rayCount(const BVH& h, V o, V d) {
  int cnt = 0; std::vector<int> st{0};
  while (!st.empty()) { int ni = st.back(); st.pop_back(); const auto& n = h.nodes[ni]; if (!rayBox(n.b, o, d, 1e9)) continue;
    if (n.l < 0) { for (int k = n.s; k < n.s + n.n; k++) { const auto& T = h.tri[h.idx[k]];
        V e1 = sub(T[1], T[0]), e2 = sub(T[2], T[0]), p = cross(d, e2); double det = dot(e1, p); if (std::fabs(det) < 1e-14) continue;
        double inv = 1 / det; V s = sub(o, T[0]); double u = dot(s, p) * inv; if (u < 0 || u > 1) continue;
        V q = cross(s, e1); double v = dot(d, q) * inv; if (v < 0 || u + v > 1) continue; double t = dot(e2, q) * inv; if (t > 1e-9) cnt++; } }
    else { st.push_back(n.l); st.push_back(n.r); } }
  return cnt;
}
static bool inside(const BVH& h, V p) {
  static const V dirs[3] = {{0.5773, 0.5779, 0.5768}, {-0.6124, 0.3536, 0.7071}, {0.2673, -0.8018, 0.5345}};
  int votes = 0; for (auto& d : dirs) votes += rayCount(h, p, d) & 1; return votes >= 2;
}
// distance from p to the nearest triangle (Ericson's closest point), through the BVH
static V closestTri(V p, const std::array<V, 3>& T) {
  V a = T[0], b = T[1], c = T[2], ab = sub(b, a), ac = sub(c, a), ap = sub(p, a);
  double d1 = dot(ab, ap), d2 = dot(ac, ap); if (d1 <= 0 && d2 <= 0) return a;
  V bp = sub(p, b); double d3 = dot(ab, bp), d4 = dot(ac, bp); if (d3 >= 0 && d4 <= d3) return b;
  double vc = d1 * d4 - d3 * d2; if (vc <= 0 && d1 >= 0 && d3 <= 0) return add(a, mul(ab, d1 / (d1 - d3)));
  V cp = sub(p, c); double d5 = dot(ab, cp), d6 = dot(ac, cp); if (d6 >= 0 && d5 <= d6) return c;
  double vb = d5 * d2 - d1 * d6; if (vb <= 0 && d2 >= 0 && d6 <= 0) return add(a, mul(ac, d2 / (d2 - d6)));
  double va = d3 * d6 - d5 * d4; if (va <= 0 && (d4 - d3) >= 0 && (d5 - d6) >= 0) return add(b, mul(sub(c, b), (d4 - d3) / ((d4 - d3) + (d5 - d6))));
  double den = 1 / (va + vb + vc); return add(a, add(mul(ab, vb * den), mul(ac, vc * den)));
}
static double dist(const BVH& h, V p) {
  double best = 1e30; std::vector<int> st{0};
  while (!st.empty()) { int ni = st.back(); st.pop_back(); const auto& n = h.nodes[ni];
    double dd = 0; for (int i = 0; i < 3; i++) { double e = std::max({n.b.lo[i] - p[i], 0.0, p[i] - n.b.hi[i]}); dd += e * e; }
    if (dd > best * best) continue;
    if (n.l < 0) { for (int k = n.s; k < n.s + n.n; k++) best = std::min(best, len(sub(p, closestTri(p, h.tri[h.idx[k]])))); }
    else { st.push_back(n.l); st.push_back(n.r); } }
  return best;
}

int main(int argc, char** argv) {
  std::ifstream in(argv[1]); std::map<std::string, Mesh> M; std::map<std::string, BVH> partBVH; std::string cmd;
  auto load = [](const std::string& f) { Mesh m; std::ifstream s(f, std::ios::binary); uint32_t nv, nt; s.read((char*)&nv, 4); s.read((char*)&nt, 4);
    std::vector<float> xyz(nv * 3); s.read((char*)xyz.data(), nv * 12); m.v.resize(nv); for (uint32_t i = 0; i < nv; i++) m.v[i] = {xyz[3 * i], xyz[3 * i + 1], xyz[3 * i + 2]};
    m.t.resize(nt); s.read((char*)m.t.data(), nt * 12); return m; };
  while (in >> cmd) {
    if (cmd == "M") { std::string n, f; in >> n >> f; M[n] = load(f); }
    else if (cmd == "X") {
      std::string label, cn, pn; double dx, dy, dz; in >> label >> cn >> pn >> dx >> dy >> dz;
      if (!M.count(cn) || !M.count(pn)) { printf("%s missing\n", label.c_str()); continue; }
      if (!partBVH.count(pn)) partBVH[pn].build(M[pn], {0, 0, 0});
      const BVH& P = partBVH[pn]; BVH C; C.build(M[cn], {dx, dy, dz});
      if (P.tri.empty() || C.tri.empty()) { printf("%s empty\n", label.c_str()); continue; }
      // dual traversal for crossing pairs
      int nCross = 0; double maxD = 0; Box cb; std::vector<char> crossTri(C.tri.size(), 0);
      std::vector<std::pair<int, int>> st{{0, 0}};
      while (!st.empty()) { auto [a, b] = st.back(); st.pop_back(); const auto &na = C.nodes[a], &nb = P.nodes[b]; if (!na.b.hit(nb.b)) continue;
        bool la = na.l < 0, lb = nb.l < 0;
        if (la && lb) { for (int i = na.s; i < na.s + na.n; i++) for (int j = nb.s; j < nb.s + nb.n; j++) {
            int ti = C.idx[i], tj = P.idx[j]; if (!C.tb[ti].hit(P.tb[tj])) continue; V p0, p1;
            if (!triTri(C.tri[ti], P.tri[tj], p0, p1)) continue;
            const auto &A = C.tri[ti], &B = P.tri[tj];
            V nB = cross(sub(B[1], B[0]), sub(B[2], B[0])); nB = mul(nB, 1 / len(nB)); V nA = cross(sub(A[1], A[0]), sub(A[2], A[0])); nA = mul(nA, 1 / len(nA));
            double behind = 0; for (auto& q : A) behind = std::max(behind, -dot(sub(q, B[0]), nB));   // the part's normals point out
            double pos = 0, neg = 0; for (auto& q : B) { double s = dot(sub(q, A[0]), nA); pos = std::max(pos, s); neg = std::max(neg, -s); }
            double depth = std::min(behind, std::min(pos, neg));
            crossTri[ti] = 1;
            if (depth > 0.01) { nCross++; maxD = std::max(maxD, depth); cb.add(p0); cb.add(p1); } } }
        else if (la || (!lb && (nb.b.hi[0] - nb.b.lo[0]) > (na.b.hi[0] - na.b.lo[0]))) { st.push_back({a, nb.l}); st.push_back({a, nb.r}); }
        else { st.push_back({na.l, b}); st.push_back({na.r, b}); } }
      // comp vertices inside the part, and how deep
      std::vector<V> vs(M[cn].v.size()); for (size_t i = 0; i < vs.size(); i++) vs[i] = add(M[cn].v[i], {dx, dy, dz});
      Box pb = P.nodes[0].b; int nIn = 0; double maxIn = 0; Box ib;
      for (auto& p : vs) { if (!pb.hit(Box{p, p})) continue; if (!inside(P, p)) continue; double d = dist(P, p); if (d < 0.01) continue; nIn++; maxIn = std::max(maxIn, d); ib.add(p); }
      printf("%-28s crossings %5d depth %.3f", label.c_str(), nCross, maxD);
      if (nCross) printf(" at [%.2f %.2f %.2f]..[%.2f %.2f %.2f]", cb.lo[0], cb.lo[1], cb.lo[2], cb.hi[0], cb.hi[1], cb.hi[2]);
      printf(" | inside %5d depth %.3f", nIn, maxIn);
      if (nIn) printf(" at [%.2f %.2f %.2f]..[%.2f %.2f %.2f]", ib.lo[0], ib.lo[1], ib.lo[2], ib.hi[0], ib.hi[1], ib.hi[2]);
      printf("\n"); fflush(stdout);
    }
  }
}
