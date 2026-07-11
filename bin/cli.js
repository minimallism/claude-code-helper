#!/usr/bin/env node

const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

const serverPath = path.resolve(__dirname, '..', 'server.py');

// 检查 Python 3 是否可用
function checkPython() {
  return new Promise((resolve) => {
    const test = spawn('python3', ['--version'], { stdio: 'ignore' });
    test.on('error', () => resolve(false));
    test.on('close', (code) => resolve(code === 0));
  });
}

async function main() {
  if (!fs.existsSync(serverPath)) {
    console.error(`❌ server.py not found at: ${serverPath}`);
    process.exit(1);
  }

  const hasPython = await checkPython();
  if (!hasPython) {
    console.error('❌ Python 3 is required but not found in PATH.');
    console.error('💡 Please install Python 3.10+ and try again.');
    process.exit(1);
  }

  console.log('🚀 Starting Claude Code History Cleaner...\n');

  const proc = spawn('python3', [serverPath], {
    stdio: 'inherit',
    cwd: path.dirname(serverPath)
  });

  proc.on('close', (code) => {
    process.exit(code || 0);
  });

  proc.on('error', (err) => {
    console.error('❌ Failed to start server:', err.message);
    process.exit(1);
  });
}

main();
