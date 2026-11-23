const fs = require('fs');
const path = require('path');
const assert = require('assert');

function runTest() {
  console.log('Running dashboard module structure and scaffold validation...');

  const requiredFiles = [
    'package.json',
    'tsconfig.json',
    'tailwind.config.js',
    'app/layout.tsx',
    'app/page.tsx',
    'app/providers.tsx',
    'components/Header.tsx',
    'components/QuoteCard.tsx'
  ];

  for (const file of requiredFiles) {
    const fullPath = path.resolve(__dirname, '..', file);
    assert(fs.existsSync(fullPath), `Missing required dashboard file: ${file}`);
  }

  // Validate package.json
  const pkg = JSON.parse(fs.readFileSync(path.resolve(__dirname, '../package.json'), 'utf8'));
  assert(pkg.name === 'auditagent-dashboard', 'Unexpected package name');
  assert(pkg.dependencies.next, 'Missing next dependency');
  assert(pkg.dependencies.wagmi, 'Missing wagmi dependency');

  console.log('Dashboard module validation PASSED (All files & config verified).');
}

runTest();
