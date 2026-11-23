const fs = require('fs');
const path = require('path');
const assert = require('assert');

function runTest() {
  console.log('Running contracts module validation...');

  const contractsDir = path.resolve(__dirname, '../src');
  const abisDir = path.resolve(__dirname, '../../shared/abis');

  const files = ['AgentWallet.sol', 'Escrow.sol', 'ReputationRegistry.sol'];
  for (const file of files) {
    const fullPath = path.join(contractsDir, file);
    assert(fs.existsSync(fullPath), `Missing contract file: ${file}`);
    const content = fs.readFileSync(fullPath, 'utf8');
    assert(content.includes('pragma solidity ^0.8.20'), `Contract ${file} missing valid pragma`);
    assert(content.includes('contract ' + file.replace('.sol', '')), `Contract definition missing in ${file}`);
  }

  const abis = ['AgentWallet.json', 'Escrow.json', 'ReputationRegistry.json'];
  for (const abiFile of abis) {
    const fullAbiPath = path.join(abisDir, abiFile);
    assert(fs.existsSync(fullAbiPath), `Missing ABI file: ${abiFile}`);
    const abiContent = JSON.parse(fs.readFileSync(fullAbiPath, 'utf8'));
    assert(Array.isArray(abiContent), `ABI ${abiFile} must be a JSON array`);
    assert(abiContent.length > 0, `ABI ${abiFile} is empty`);
  }

  console.log('Contracts module validation PASSED (3 contracts, 3 ABIs verified).');
}

runTest();
