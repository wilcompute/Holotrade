# Durable exact-decoder checkpoints

`js/w33-durable-dual-stream.js` binds replay-verified dual streams to
`scripts/w33_checkpoint_store.py`. The latter uses two attached SQLite files:
checkpoint data and a separately trusted revision/digest anchor. DELETE journal
mode, FULL synchronization and a shared transaction provide local crash
atomicity under SQLite's documented filesystem assumptions. Revision CAS
rejects stale writers; stream replay and strict prefix extension reject invalid
or regressive saves. Reads verify both the trusted head and the wire hash.

The anchor must be protected independently. Restoring both files defeats this
scheme. No hardware monotonic counter, external attestation or exactly-once
delivery guarantee is claimed. The Python helper is the storage primitive;
call the JS wrapper for decoder-policy and mathematical witness validation.
Python 3 is a runtime dependency; `python` can be configured in store options.

```js
const {createDurableDualStore}=require('../js/w33-durable-dual-stream.js');
const store=createDurableDualStore({dataPath:'/data/checkpoints.db',anchorPath:'/trusted/heads.db'});
store.save('job-id',policy,stream.checkpoint(),0);
const {revision,stream:resumed}=store.load('job-id',policy);
// Append independently validated next records before saving revision+1.
```

Twelve focused decoder transaction tests pass, including actual process
restart, before/after-commit process exits, old-data restoration, corrupted wire,
stale revisions, regressive prefixes, and resumed signed delivery. This tests
software recovery; it does not simulate every filesystem/power-failure mode.
Run `node --test tests/w33-certified-decoder-transaction.test.js`.

The official [SQLite ATTACH contract](https://www.sqlite.org/lang_attach.html)
explains atomicity across attached databases and why WAL is excluded. W33's
prior `analysis/w33_durable_microstep_owner.py` already implemented SQLite guest
durability and explicitly excluded old-database rollback; this stream path adds
the independent anchor. The companion theory/control report is
[W33_FINITE_CONTROL_PHASE_ISA.md](https://github.com/wilcompute/W33-Theory/blob/master/analysis/W33_FINITE_CONTROL_PHASE_ISA.md).

Parallel intake pulled 1518cf9 through 5500c22 (five commits). The entire net
diff was read; orientation and stabilizer results remain credited to W33
Passes 4811/4814 and BT170. Sampled group checks in the two-27 source are not
promoted here to an independently exhaustive certificate.
