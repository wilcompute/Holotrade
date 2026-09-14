'use strict';
// Trusted anchor must be protected independently from checkpoint data rollback.
const {execFileSync}=require('node:child_process');
const path=require('node:path');
const DS=require('./w33-dual-stream.js');
function createDurableDualStore({dataPath,anchorPath,python='python3'}){
  const call=req=>JSON.parse(execFileSync(python,[path.join(__dirname,'../scripts/w33_checkpoint_store.py'),dataPath,anchorPath],{input:JSON.stringify(req),encoding:'utf8',stdio:['pipe','pipe','pipe']}));
  function load(id,policy){
    const row=call({op:'load',id});if(!row)return null;
    const checkpoint=JSON.parse(row.wire);
    const stream=DS.resumeDualStream(policy,checkpoint,checkpoint.checkpointDigest);
    return {revision:row.revision,checkpoint,stream};
  }
  function save(id,policy,checkpoint,expectedRevision){
    // Canonical replay owns semantic validation; SQLite owns durable CAS.
    const clean=DS.resumeDualStream(policy,checkpoint,checkpoint.checkpointDigest).checkpoint();
    const old=load(id,policy);
    if((old?old.revision:0)!==expectedRevision)throw new Error('stale checkpoint revision');
    if(old){
      const a=old.checkpoint.body,b=clean.body;
      if(b.records.length<=a.records.length||JSON.stringify(b.header)!==JSON.stringify(a.header)||JSON.stringify(b.records.slice(0,a.records.length))!==JSON.stringify(a.records))throw new Error('checkpoint must extend trusted prefix');
    }
    const row=call({op:'save',id,wire:JSON.stringify(clean),expectedRevision});
    return {revision:row.revision,checkpointDigest:clean.checkpointDigest};
  }
  return Object.freeze({load,save});
}
module.exports={createDurableDualStore};
