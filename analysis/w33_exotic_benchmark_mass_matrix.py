#!/usr/bin/env python3
"""Explicit instanton-weighted rank-nine benchmark for the frozen SU(5) exotics.

This is NOT claimed to be the physical low-energy mass matrix.  The repository
certifies complete K_{9,12} allowed support at sextic+nonic order and positive
classical instanton kernels, but it does not yet specify a D/F-flat singlet
vacuum, canonically normalized Kahler metrics, or all physical-state/OPE phases.

We therefore answer the precise algebraic question left open by structural rank:
is the rank-nine locus still nonempty after the positive instanton weights are
inserted?  Yes.  On the complete allowed support choose the deterministic
coefficient specialization C_rc=(r+1)^c.  The first nine columns are a 9x9
Vandermonde matrix with exact nonzero determinant prod_{i<j}(j-i).  Multiplying
the eight sextic columns and four nonic columns by their positive instanton
factors preserves rank.  This gives an explicit numerical benchmark matrix of
rank nine and proves the bad-rank locus is a proper algebraic subset of the
allowed coupling/VEV parameter space.
"""
from __future__ import annotations
import json,math
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data'/'w33_exotic_benchmark_mass_matrix.json'

def rank_exact(A):
 from fractions import Fraction
 M=[[Fraction(int(x)) for x in row] for row in A];m=len(M);n=len(M[0]);r=0
 for c in range(n):
  z=next((i for i in range(r,m) if M[i][c]),None)
  if z is None:continue
  M[r],M[z]=M[z],M[r];q=M[r][c];M[r]=[x/q for x in M[r]]
  for i in range(m):
   if i!=r and M[i][c]:
    q=M[i][c];M[i]=[M[i][j]-q*M[r][j] for j in range(n)]
  r+=1
 return r

def main(write=True):
 sel=json.loads((ROOT/'data'/'w33_exotic_sextic_nonic_completion.json').read_text());ker=json.loads((ROOT/'data'/'w33_exotic_worldsheet_instanton_kernel.json').read_text())
 assert sel['status']=='PASS' and ker['status']=='PASS' and sel['combined_support']['structural_rank']==9
 assert sel['sextic']['covered_matrix_columns']==8 and sel['nonic']['covered_matrix_columns']==4
 xs=list(range(1,10));C=np.array([[x**c for c in range(12)] for x in xs],dtype=object)
 assert rank_exact(C.tolist())==9
 det=1
 for i in range(9):
  for j in range(i+1,9):det*=xs[j]-xs[i]
 assert det==5056584744960000
 s=float(ker['benchmark_T_1']['sextic_each_plane']);n=float(ker['benchmark_T_1']['nonic'])
 scales=np.array([s]*8+[n]*4,dtype=float);M=np.asarray(C,dtype=float)*scales[None,:]
 assert np.linalg.matrix_rank(M,tol=1e-8)==9
 singular=np.linalg.svd(M,compute_uv=False)
 out={'schema':'holotrade.w33_exotic_benchmark_mass_matrix.v1','status':'PASS',
 'headline':'The instanton-supported K9,12 exotic coupling support contains an explicit rank-nine numerical specialization. Choosing C_rc=(r+1)^c gives a Vandermonde first-nine-column minor with exact determinant 5056584744960000; multiplying the eight sextic and four nonic columns by their positive T_i=1 instanton factors preserves rank nine. Thus the rank<9 locus is a proper algebraic subset of the allowed coupling/VEV space.',
 'benchmark_assumptions':{'Kahler_moduli':[1,1,1],'canonical_field_metrics':'set to 1 for benchmark only','dimensionless_OPE_VEV_coefficient_specialization':'C_rc=(r+1)^c','physical_state_phases':'set positive for benchmark only'},
 'sector_scales':{'sextic_columns':8,'sextic_factor':s,'nonic_columns':4,'nonic_factor':n},
 'coefficient_matrix_integer':[[int(x) for x in row] for row in C.tolist()],
 'mass_matrix_benchmark':M.tolist(),'rank':9,'first_9_column_coefficient_minor_det':det,'singular_values':singular.tolist(),
 'algebraic_consequence':'Because one allowed specialization has rank nine, at least one 9x9 minor polynomial is nonzero; generic allowed coefficients therefore have rank nine away from a proper algebraic hypersurface.',
 'physical_boundary':'The repo does not yet provide a D/F-flat singlet VEV assignment, canonically normalized Kahler metrics, complete quantum/OPE normalizations, or physical-state phases for these operators. This matrix is an existence/benchmark witness in allowed coupling space, not a predicted mass spectrum or proof that the string vacuum selects this specialization.',
 'checks':{'parent_structural_rank9':True,'positive_instanton_scales':s>0 and n>0,'Vandermonde_det_nonzero':True,'benchmark_rank9':True}}
 if write:OUT.write_text(json.dumps(out,indent=2)+'\n')
 print(json.dumps(out,indent=2));return out
if __name__=='__main__':main(True)
