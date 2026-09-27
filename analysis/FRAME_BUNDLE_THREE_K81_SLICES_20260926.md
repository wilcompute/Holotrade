# The 243 frame bundle contains three exact K81 compiler carriers

Producer: `analysis/w33_frame_bundle_three_k81_slices.py`  
Certificate: `data/w33_frame_bundle_three_k81_slices.json`

This cross-repo packet joins two already exact results:

- Holotrade: the 27 complete two-qutrit factorisation frames form a regular torsor for the order-27 H27/elation group.
- W33-Theory Passes 11043–11047: a 9D latent module `A9 = 3χ + V + Vbar` is the unique minimal commutant dressing for which `V tensor A9 = Reg(H27)`.

The 27D regular frame module is

`Reg(H27) = sum_9 χ + 3V + 3Vbar`.

Partition the nine one-dimensional characters into the three parallel lines of one affine striation of the dual `F3^2`. For each line define

`A9_j = sum_{χ on line j} χ + V + Vbar`.

Then

`Reg(H27) = A9_0 direct-sum A9_1 direct-sum A9_2`,
and each `A9_j` has dimension 9.

If the existing two-qutrit fibre `C9` is equipped as

`V_internal tensor Reg(C3_external)`,

then each 81D slice satisfies

`A9_j tensor V_internal tensor Reg(C3_external) = Reg(H27) tensor Reg(C3) = Reg(K81)`.

Therefore the existing 243D frame bundle supports **three parallel 81D compiler carriers with no Hilbert-space enlargement**.

## The mu12 compatibility test

The frame bundle also carries the exact Qpsi clock

`D12 |F> = zeta12^{Qpsi(F)} |F>`

with charges `4^1, (-2)^10, 1^16`.

The producer rebuilds the 27-frame torsor and tests all twelve powers of `D12` against every one of the 27 H27/elation permutations.
Exactly three powers commute:

`k = 0, 4, 8`.

Equivalently,

`<D12> intersect Comm(Reg(H27)) = <D12^4> ~= C3`.

This is not another numerical coincidence. Since every Qpsi charge is congruent to 1 mod 3, `D12^4` is the same scalar `omega` on all 27 frames. Matter parity `D12^6` and the mod-four shadow `D12^3` distinguish the 1+10+16 frame classes and therefore fail to commute with the regular H27 action.

That independently reproduces the W33 compiler result that the FI/common-center `C3` is the surviving clock symmetry.

## Boundary

The three-slice decomposition is representation-theoretic. It requires a choice of dual-Hesse striation and an ordered internal/external qutrit action on each `C9` fibre. The full `D12` clock does not preserve the regular H27 action; only its FI `C3` does. No D/F-flat vacuum, energy scale, or hardware pulse follows from this packet.
