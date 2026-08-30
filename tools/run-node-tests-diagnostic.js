'use strict'

const fs = require('node:fs')
const path = require('node:path')
const { spawnSync } = require('node:child_process')

const root = path.resolve(__dirname, '..')
const testsDir = path.join(root, 'tests')
const output = path.join(root, 'node-test-diagnostics.json')

const files = fs.readdirSync(testsDir)
  .filter((name) => name.endsWith('.test.js'))
  .sort()

const results = []
let failed = 0

for (const name of files) {
  const rel = path.join('tests', name)
  const started = Date.now()
  const child = spawnSync(process.execPath, ['--test', rel], {
    cwd: root,
    encoding: 'utf8',
    env: process.env,
    maxBuffer: 16 * 1024 * 1024,
  })

  const record = {
    file: rel.replaceAll('\\', '/'),
    status: child.status === 0 ? 'PASS' : 'FAIL',
    exitCode: child.status,
    signal: child.signal,
    durationMs: Date.now() - started,
  }

  if (child.status !== 0) {
    failed += 1
    record.stdout = child.stdout || ''
    record.stderr = child.stderr || ''
  }

  results.push(record)
  process.stdout.write(`${record.status} ${record.file} (${record.durationMs} ms)\n`)
}

const report = {
  schema: 'holotrade.node-test-diagnostics.v1',
  node: process.version,
  files: files.length,
  passed: files.length - failed,
  failed,
  results,
}

fs.writeFileSync(output, `${JSON.stringify(report, null, 2)}\n`)
process.stdout.write(`diagnostic report: ${path.relative(root, output)}; failed=${failed}\n`)
process.exitCode = failed === 0 ? 0 : 1
