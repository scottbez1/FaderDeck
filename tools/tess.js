// Tessellate a STEP file with occt-import-js and dump per-mesh summary + compact binary.
// usage: node tess.js <in.step> <out-prefix> [linDefl]
const fs = require('fs');
const path = require('path');
const occtFactory = require(process.env.OCCT_IMPORT_JS || 'occt-import-js');

(async () => {
  const [, , inPath, outPrefix, defl] = process.argv;
  const occt = await occtFactory();
  const buf = new Uint8Array(fs.readFileSync(inPath));
  const res = occt.ReadStepFile(buf, {
    linearUnit: 'millimeter',
    linearDeflectionType: 'absolute_value',
    linearDeflection: parseFloat(defl || '0.08'),
    angularDeflection: 0.35,
  });
  if (!res.success) { console.error('fail'); process.exit(1); }

  // Walk node tree to get names per mesh index.
  const meshNames = {};
  (function walk(node, trail) {
    const t = node.name ? trail.concat(node.name) : trail;
    (node.meshes || []).forEach(mi => { meshNames[mi] = t.join('/'); });
    (node.children || []).forEach(c => walk(c, t));
  })(res.root, []);

  const summary = [];
  let triTotal = 0;
  res.meshes.forEach((m, i) => {
    const p = m.attributes.position.array;
    let mn = [1e9, 1e9, 1e9], mx = [-1e9, -1e9, -1e9];
    for (let k = 0; k < p.length; k += 3) for (let a = 0; a < 3; a++) {
      mn[a] = Math.min(mn[a], p[k + a]); mx[a] = Math.max(mx[a], p[k + a]);
    }
    const tris = m.index.array.length / 3;
    triTotal += tris;
    summary.push({ i, name: meshNames[i] || m.name, color: m.color, tris,
      min: mn.map(v => +v.toFixed(2)), max: mx.map(v => +v.toFixed(2)) });
  });
  fs.writeFileSync(outPrefix + '.summary.json', JSON.stringify(summary, null, 1));
  fs.writeFileSync(outPrefix + '.raw.json', JSON.stringify(res.meshes.map((m, i) => ({
    name: meshNames[i] || m.name, color: m.color,
    pos: Array.from(m.attributes.position.array), idx: Array.from(m.index.array),
  }))));
  console.log('meshes', res.meshes.length, 'tris', triTotal);
})();
