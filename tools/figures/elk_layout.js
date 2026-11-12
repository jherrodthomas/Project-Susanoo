#!/usr/bin/env node
// Lay out a batch of ELK graphs: JSON array on stdin -> JSON array of laid-out graphs on stdout.
// elkjs is pinned in package.json so positions are identical locally and in CI.
'use strict';
const ELK = require('elkjs/lib/elk.bundled.js');

let raw = '';
process.stdin.on('data', (c) => (raw += c));
process.stdin.on('end', async () => {
  const elk = new ELK();
  const graphs = JSON.parse(raw);
  const out = [];
  for (const g of graphs) out.push(await elk.layout(g));
  process.stdout.write(JSON.stringify(out));
});
