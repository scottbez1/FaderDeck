// Tiny CSG runner on manifold.
//   S name nv nt  / nv lines "x y z" / nt lines "a b c"      define a closed solid
//   O dst U|D|I n src1 .. srcn                                 union / difference (src1 - rest) / intersection
//   W name file                                                write indexed mesh: u32 nv, u32 nt, f32 xyz*nv, u32 abc*nt
//   T dst src dx dy dz                                         translate
//   V name                                                     print volume, bbox, genus
#include <manifold/manifold.h>
#include <cstdio>
#include <fstream>
#include <iostream>
#include <map>
#include <sstream>
#include <string>
using namespace manifold;

int main(int argc, char** argv) {
  std::ifstream in(argv[1]);
  std::map<std::string, Manifold> M;
  std::string cmd;
  while (in >> cmd) {
    if (cmd == "S") {
      std::string name; size_t nv, nt; in >> name >> nv >> nt;
      MeshGL m; m.numProp = 3; m.vertProperties.resize(nv * 3); m.triVerts.resize(nt * 3);
      for (auto& v : m.vertProperties) in >> v;
      for (auto& t : m.triVerts) in >> t;
      m.Merge();
      Manifold s(m);
      if (s.Status() != Manifold::Error::NoError) { fprintf(stderr, "solid %s: error %d\n", name.c_str(), (int)s.Status()); return 1; }
      if (s.Volume() <= 0) fprintf(stderr, "solid %s: volume %g\n", name.c_str(), s.Volume());
      M[name] = s;
    } else if (cmd == "O") {
      std::string dst, op; int n; in >> dst >> op >> n;
      std::vector<Manifold> src(n);
      for (int i = 0; i < n; i++) { std::string s; in >> s; if (!M.count(s)) { fprintf(stderr, "missing %s\n", s.c_str()); return 1; } src[i] = M[s]; }
      Manifold r;
      if (op == "U") r = Manifold::BatchBoolean(src, OpType::Add);
      else if (op == "D") { std::vector<Manifold> rest(src.begin() + 1, src.end()); r = rest.empty() ? src[0] : src[0] - Manifold::BatchBoolean(rest, OpType::Add); }
      else { r = src[0]; for (int i = 1; i < n; i++) r = r ^ src[i]; }
      M[dst] = r;
    } else if (cmd == "T") {
      std::string dst, src; double x, y, z; in >> dst >> src >> x >> y >> z;
      M[dst] = M[src].Translate({x, y, z});
    } else if (cmd == "W") {
      std::string name, file; in >> name >> file;
      MeshGL m = M[name].GetMeshGL();
      uint32_t nv = m.NumVert(), nt = m.NumTri();
      std::ofstream o(file, std::ios::binary);
      o.write((char*)&nv, 4); o.write((char*)&nt, 4);
      for (uint32_t i = 0; i < nv; i++) o.write((char*)&m.vertProperties[i * m.numProp], 12);
      o.write((char*)m.triVerts.data(), nt * 12);
    } else if (cmd == "V") {
      std::string name; in >> name; auto& s = M[name]; auto b = s.BoundingBox();
      printf("%s vol %.3f tris %zu genus %d bbox [%.2f %.2f %.2f]..[%.2f %.2f %.2f] status %d\n", name.c_str(), s.Volume(), s.NumTri(), s.Genus(),
             b.min.x, b.min.y, b.min.z, b.max.x, b.max.y, b.max.z, (int)s.Status());
    }
  }
}
