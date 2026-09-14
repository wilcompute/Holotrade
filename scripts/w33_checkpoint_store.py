"""SQLite checkpoint CAS with an independently trusted rollback anchor.
Both files must be on a reliable SQLite-supported filesystem. The anchor is
outside the data rollback adversary's authority. Restoring both defeats this
scheme; this is not remote attestation, tamper-proof hardware, or delivery dedup.
"""
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import sys

def request(data_path, anchor_path, req):
    data_path=Path(data_path).resolve();anchor_path=Path(anchor_path).resolve()
    if data_path==anchor_path or (data_path.exists() and anchor_path.exists() and os.path.samefile(data_path,anchor_path)):
        raise ValueError('separate trusted anchor required')
    # Read/open must not silently recreate a missing anchor beside existing data.
    if data_path.exists()!=anchor_path.exists():raise ValueError('missing data or trusted anchor')
    db=sqlite3.connect(str(data_path),timeout=10,isolation_level=None)
    try:
        db.execute('ATTACH DATABASE ? AS anchor',(str(anchor_path),))
        for schema in ('main','anchor'):
            assert db.execute(f'PRAGMA {schema}.journal_mode=DELETE').fetchone()[0]=='delete'
            db.execute(f'PRAGMA {schema}.synchronous=FULL')
        db.execute('BEGIN IMMEDIATE')
        db.execute('CREATE TABLE IF NOT EXISTS checkpoints (id TEXT PRIMARY KEY, revision INTEGER NOT NULL, digest TEXT NOT NULL, wire TEXT NOT NULL)')
        db.execute('CREATE TABLE IF NOT EXISTS anchor.heads (id TEXT PRIMARY KEY, revision INTEGER NOT NULL, digest TEXT NOT NULL)')
        key=req['id']
        if not isinstance(key,str) or not key:raise ValueError('stream id required')
        row=db.execute('SELECT revision,digest,wire FROM checkpoints WHERE id=?',(key,)).fetchone()
        head=db.execute('SELECT revision,digest FROM anchor.heads WHERE id=?',(key,)).fetchone()
        if (None if row is None else row[:2])!=head:raise ValueError('checkpoint rollback or anchor mismatch')
        if row and hashlib.sha256(row[2].encode()).hexdigest()!=row[1]:raise ValueError('corrupt checkpoint wire')
        result=None if row is None else {'revision':row[0],'wire':row[2],'digest':row[1]}
        if req['op']=='save':
            expected=req['expectedRevision']
            if type(expected) is not int or expected!=(0 if row is None else row[0]):raise ValueError('stale checkpoint revision')
            wire=req['wire']
            if not isinstance(wire,str):raise ValueError('wire must be text')
            json.loads(wire)
            digest=hashlib.sha256(wire.encode()).hexdigest();revision=expected+1
            db.execute('INSERT OR REPLACE INTO checkpoints VALUES (?,?,?,?)',(key,revision,digest,wire))
            db.execute('INSERT OR REPLACE INTO anchor.heads VALUES (?,?,?)',(key,revision,digest))
            result={'revision':revision,'digest':digest,'wire':wire}
        elif req['op']!='load':raise ValueError('unknown operation')
        # Explicit process-crash hooks for regression tests only.
        if req.get('_testCrash')=='before_commit':os._exit(71)
        db.execute('COMMIT')
        if req.get('_testCrash')=='after_commit':os._exit(72)
        return result
    finally:db.close()

if __name__=='__main__':
    print(json.dumps(request(sys.argv[1],sys.argv[2],json.load(sys.stdin))))
