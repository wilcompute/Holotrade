#!/usr/bin/env python3
"""The 40 cheap Payne covers form a rank-25 fast/slow spectral transform.

Let B be the 40x45 incidence matrix: B[x,t]=1 iff expensive target t is one
of the nine NEW Payne lines for cheap W33 axis x.  Let A40 be W33 adjacency and
A45 the collinearity graph of the expensive GQ(4,2).  The committed certificate
implies the exact integer identities

  B B^T = 8 I40 + J40 + 2 A40
  B^T B = 6 I45 + 2 J45 - 2 A45
  A40 B + B A45 = 5 J40x45 - B.

Thus B has singular spectrum sqrt(72)^1, sqrt(12)^24, 0^20 on the slow side;
it annihilates W33's -4 eigenspace (dimension 15) and the slow graph's +3
eigenspace (dimension 20), while identifying the two 24-dimensional sectors
A40=+2 and A45=-3.  This is exact finite linear algebra, not a physical Fourier
or quantum-channel claim.
"""
from __future__ import annotations
from fractions import Fraction
import json,itertools
from pathlib import Path
from w33_payne_slowpath_core import w33,form
ROOT=Path(__file__).resolve().parents[1]

def mm(A,B):return [[sum(A[i][k]*B[k][j] for k in range(len(B))) for j in range(len(B[0]))] for i in range(len(A))]
def tr(A):return [list(x) for x in zip(*A)]
def rank(A):
 M=[[Fraction(x) for x in r] for r in A];r=0
 for c in range(len(M[0])):
  p=next((i for i in range(r,len(M)) if M[i][c]),None)
  if p is None:continue
  M[r],M[p]=M[p],M[r];z=M[r][c];M[r]=[x/z for x in M[r]]
  for i in range(len(M)):
   if i!=r and M[i][c]:
    z=M[i][c];M[i]=[M[i][j]-z*M[r][j] for j in range(len(M[0]))]
  r+=1
 return r

def main():
 C=json.loads((ROOT/'data/slow_path_is_payne_derivative.json').read_text());R=json.loads((ROOT/'data/the_45_slot_rom_bijection.json').read_text());assert C['status']=='PASS' and R['valid']
 covers={int(k):set(v) for k,v in C['equivariant40']['covers'].items()};B=[[int(t in covers[x]) for t in range(45)] for x in range(40)]
 P,_=w33();A40=[[int(i!=j and form(P[i],P[j])==0) for j in range(40)] for i in range(40)]
 banks=R['linesB'];A45=[[0]*45 for _ in range(45)]
 for l in banks:
  for i,j in itertools.combinations(l,2):A45[i][j]=A45[j][i]=1
 BB=mm(B,tr(B));BTB=mm(tr(B),B)
 E40=[[8*int(i==j)+1+2*A40[i][j] for j in range(40)] for i in range(40)]
 E45=[[6*int(i==j)+2-2*A45[i][j] for j in range(45)] for i in range(45)]
 AB=mm(A40,B);BA=mm(B,A45);direct=[[AB[i][j]+BA[i][j] for j in range(45)] for i in range(40)];ED=[[5-B[i][j] for j in range(45)] for i in range(40)]
 row=[sum(r) for r in B];col=[sum(B[i][j] for i in range(40)) for j in range(45)]
 rowpair={};
 for i,j in itertools.combinations(range(40),2):rowpair[(A40[i][j],sum(B[i][t]*B[j][t] for t in range(45)))]=rowpair.get((A40[i][j],sum(B[i][t]*B[j][t] for t in range(45))),0)+1
 colpair={};
 for i,j in itertools.combinations(range(45),2):colpair[(A45[i][j],sum(B[x][i]*B[x][j] for x in range(40)))]=colpair.get((A45[i][j],sum(B[x][i]*B[x][j] for x in range(40))),0)+1
 checks={'row_sums_9':set(row)=={9},'column_sums_8':set(col)=={8},'BBt_identity':BB==E40,'BtB_identity':BTB==E45,'shifted_anti_intertwiner':direct==ED,'rank_25':rank(B)==25,'adjacent_fast_covers_intersect_3_opposite_intersect_1':rowpair=={(1,3):240,(0,1):540},'collinear_slow_targets_share_0_covers_noncollinear_share_2':colpair=={(1,0):270,(0,2):720}}
 out={'schema':'holotrade.payne-cover-spectral-intertwiner.v1','status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'incidence':{'shape':[40,45],'rowWeight':9,'columnWeight':8,'rank':rank(B),'fastPairCensus':{f'adj{a}_intersection{z}':n for (a,z),n in sorted(rowpair.items())},'slowPairCensus':{f'adj{a}_cocovers{z}':n for (a,z),n in sorted(colpair.items())}},'gramIdentities':['B B^T = 8 I_40 + J_40 + 2 A_W33','B^T B = 6 I_45 + 2 J_45 - 2 A_GQ45','A_W33 B + B A_GQ45 = 5 J_40x45 - B'],'singularSpectrum':{'sqrt(72)':1,'sqrt(12)':24,'0':20},'nontrivialChannel':'B^T maps the 24-dimensional W33 eigenvalue +2 sector isomorphically onto the 24-dimensional GQ(4,2) eigenvalue -3 sector, with squared singular value 12; W33 eigenvalue -4 (dimension 15) and slow eigenvalue +3 (dimension 20) lie in the respective kernels.','boundary':'Exact integer/rational linear algebra on the committed finite incidence data. Spectral transform is a mathematical statement only; no physical unitary, quantum channel, or energy advantage is claimed.'}
 if '--write' in __import__('sys').argv:(ROOT/'data/payne_cover_spectral_intertwiner.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
 print(json.dumps(out,indent=2,sort_keys=True));return 0 if out['status']=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
