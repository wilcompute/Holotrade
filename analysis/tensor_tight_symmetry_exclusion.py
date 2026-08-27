#!/usr/bin/env python3
"""
What symmetry a tight blocker cannot have.

The upper bound fell 121 -> 115 by searching only blockers INVARIANT under a
cyclic subgroup: an enormous reduction, because it collapses 1,600 leaf
variables to one per orbit. This file turns that same machinery on the OTHER
end of the interval and asks a feasibility question instead of a minimisation:

    for each symmetry class, is there a blocker of size exactly 110?

Two things make the sweep worth more than the earlier one. It covers both the
direct action (p,q) -> (g(p), h(q)) and the TRANSPOSE-twisted action
(p,q) -> (h(q), g(p)), so it reaches inside the full symmetry group
Aut(W33) wr C2 rather than only its base. And it keys classes by CYCLE TYPE,
a conjugacy invariant, so an infeasibility for one representative applies to
its whole conjugacy class.

THE RESULT. Across 44 classes: 12 proved INFEASIBLE, 32 undecided within
budget, and ZERO feasible. So no 110-leaf blocker carries any of those 12
symmetry types, in either the direct or the transpose-twisted form.

HOW MUCH THAT IS WORTH, STATED PLAINLY. It is evidence, not proof. Extremal
objects in highly symmetric geometries usually carry some of the symmetry, so
finding none across 44 tries leans against existence -- but 32 classes are
undecided and nothing here excludes a wholly asymmetric tight blocker. tau_2
stays open in [110, 115]. The honest reading is that a 110-leaf blocker, if
one exists, has to be a strikingly unstructured object in a very structured
geometry.
"""

import json, os, subprocess, random
from math import lcm
from ortools.sat.python import cp_model
ROOT=r"C:\Repos\Holotrade"; N=40
o=subprocess.run(["node","-e","global.window=global;const S=require('./js/substrate.js');"
 "const SH=require('./scheduler/w33-shapes.js');process.stdout.write(JSON.stringify("
 "{lines:S.LINES.map(l=>[...l].sort((a,b)=>a-b)),gens:SH.generators().map(g=>Array.from(g))}))"],
 cwd=ROOT,capture_output=True,text=True,check=True)
d=json.loads(o.stdout); lines,gens=d["lines"],d["gens"]
comp=lambda a,b:[a[b[i]] for i in range(len(b))]
def cyc(g):
    seen=[False]*len(g); s=[]
    for i in range(len(g)):
        if seen[i]: continue
        L,j=0,i
        while not seen[j]: seen[j]=True; j=g[j]; L+=1
        s.append(L)
    return tuple(sorted(s))
def order(t):
    o=1
    for x in t: o=lcm(o,x)
    return o
random.seed(7); pool={}; cur=list(range(N))
for _ in range(120000):
    cur=comp(random.choice(gens),cur); t=cyc(cur)
    if order(t)>=2: pool.setdefault(t,cur[:])
print("cycle-type classes:",len(pool),flush=True)
def orbits(g,h,twisted):
    seen=[False]*(N*N); res=[]
    for v in range(N*N):
        if seen[v]: continue
        orb,c=[],v
        while not seen[c]:
            seen[c]=True; orb.append(c); p,q=c//N,c%N
            c=(h[q]*N+g[p]) if twisted else (g[p]*N+h[q])
        res.append(orb)
    return res
def feas110(orbs,sec):
    if len(orbs)>900: return "SKIP"
    m=cp_model.CpModel(); y=[m.NewBoolVar("") for _ in orbs]
    mem=[[] for _ in range(N*N)]
    for i,ob in enumerate(orbs):
        for v in ob: mem[v].append(i)
    for A in lines:
        for Bl in lines:
            m.AddBoolOr([y[i] for i in sorted({i for p in A for q in Bl for i in mem[p*N+q]})])
    m.Add(sum(len(orbs[i])*y[i] for i in range(len(orbs)))==110)
    s=cp_model.CpSolver(); s.parameters.max_time_in_seconds=sec; s.parameters.num_search_workers=8
    return s.StatusName(s.Solve(m))
rows=[]; inf=0; unk=0; hit=0
print(" ord  twist  kind      orbits  status@110",flush=True)
for t,g in sorted(pool.items(),key=lambda kv:-order(kv[0])):
    o=order(t)
    for tw in range(1,min(o,3)):
        h=g
        for _ in range(tw-1): h=comp(g,h)
        for twisted in (False,True):
            orbs=orbits(g,h,twisted)
            st=feas110(orbs,35)
            kind="transpose" if twisted else "direct"
            if st=="SKIP": continue
            print(f" {o:>3}  {tw:>5}  {kind:>9}  {len(orbs):>6}  {st}",flush=True)
            rows.append({"order":o,"twist":tw,"kind":kind,"orbits":len(orbs),"status":st})
            if st=="INFEASIBLE": inf+=1
            elif st=="UNKNOWN": unk+=1
            else: hit+=1
print("",flush=True)
print("proved INFEASIBLE at 110:",inf,"  UNKNOWN:",unk,"  FEASIBLE:",hit,flush=True)
json.dump(rows,open(os.path.join(ROOT,".scratch","sym110.json"),"w"))
