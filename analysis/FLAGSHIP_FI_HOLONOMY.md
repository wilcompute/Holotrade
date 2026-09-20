# Exact FI cone and joint-holonomy followthrough

September20,2026. The new producers calculate from the actual stored weights; their LP outputs are converted to exact rational witnesses and checked before publication.

`flagship_fi_weight_dump.cpp` extends the prior all-weight dumper with the engine's anomalous flag, charge trace and seven U1 generators. It was built against the existing orbifolder1.2.1 objects under `/home/wiljd/orb/build`, with headers under `/home/wiljd/orb/src/orbifolder-1.2.1/src` and GSL under `/home/wiljd/orb/sysroot`. Running on `/home/wiljd/orb/scan/cp/w_Z6I_27/m1.txt` produces the archived `flagship_fi_weights.txt`. All628 weight rows match the prior dump. The anomalous generator has norm squared50/3 and the engine trace is200. Engine `corbifold.cpp` constructs the generator as the left-chiral weight sum divided by12 and stores12 times its norm squared. This is not a physical FI scale measurement.

`flagship_full_cartan_fi_audit.py` extends c555ac5 from canonical representatives to every physical field option in each of14 positive projected rank-four circuits, allowing all their component mixtures. Each retains its primitive five-type totals. Exact Farkas witnesses prove infeasibility both at zero FI and with any nonnegative coefficient of the actual anomalous-generator ray. The result is stronger than testing one representative per type.

The union of all65 singlets has132 component columns and admits exact Cartan solutions at zero FI and positive FI. In the positive-ray normalization `sum p_i t_i=-t_A`, the sparse solution is:

- n_2 components0..4 each3/2;
- n_11 component0 and n_16 component0 each5;
- n_19 components0,1 each11/2;
- n_20 component0 has6.

The component indices refer to the archived weight-row order. Hidden nonabelian off-diagonal D equations and all F equations remain untested. This is a necessary Cartan witness, not a supersymmetric vacuum, and differs from babfd48's restricted19 mass-coupling singlets. The classical anomalous-U1 context is [Cleaver et al.](https://arxiv.org/abs/hep-th/9711178).

`flagship_joint_holonomy_tensors.py` constructs explicit projectors on the prior nine-weight orbit. With common phases removed, W is W3 and H is3V; `P0=(I+W+W^2)/3`, `P_T=P0(I+H)/2`, `P_D=P0(I-H)/2`. These give ranks3 and2 in exact cyclotomic arithmetic. The block census belongs to `the_standard_model_is_the_joint_stabiliser_and_mu_is_universal.py`: associative centralizer dimension17, traceless Lie dimension16. The new artifact makes the projectors explicit. The endomorphism ansatz `m_T P_T + m_D P_D` is globally allowed by the joint centralizer and fails local-A8 invariance. It is not a calculation of coefficients or world-sheet amplitudes. Missing-partner plane ownership remains a6f1cae/61d7ea3.

`flatness_scope_counterexamples.py` supplies separate symbolic scope regressions for the incoming Gordan and F/D discussion. An R selection rule can forbid W even with a neutral monomial and a D-flat point. Nonempty W=(xy-1)^2 can have a D/F-flat critical point at x=y=1 by cancellation. W=z*x^2 vanishes on the positively charged x-only support, while F_z is nonzero. These are toy models, not claimed string vacua or contradictions of the measured charge cones. Actual string selection rules are an additional question ([primary reference](https://arxiv.org/abs/1107.2137)). Existing stronger parallel wording is preserved pending the user's requested choice.

Run the three Python producers without flags to check, or with `--write` to reproduce adjacent certificates. Run both `tests/test_flagship_fi_holonomy.py` and `tests/test_flagship_singlet_invariants.py`. The new tests independently reconstruct every stored primal and dual matrix, rather than compare floating-point solver vertices. Six tests passed before the final ownership metadata clarification; the publication check reruns the affected suite.

## Further nonabelian check: the sparse candidate fails

The stored positive-FI Cartan solution is not a full D-flat vacuum. The unbroken root `(0,-1,0,1,0,0,0,0 | 0,0,0,0,0,0,0,0)` has only one active transition, from n_2 component1 to component0. Its lower weight pairs to -1 with the normalized root, proving the raising matrix element is nonzero. Both squared VEVs are3/2, so the unique bilinear cannot vanish by changing phases. This refutes this specific sparse solution; it does not rule out other hidden-charged configurations.

All34 one-component singlets together also fail to cancel the positive actual FI ray; a separate exact Farkas witness is stored. The anomalous generator projects onto the four organizer roots as `(-8/3,2/3,2,-11/3)`. Thus retaining fixed zero-D projected circuit ratios cannot absorb any positive FI coefficient. A viable next candidate must change those ratios and address the nonabelian moments explicitly, before the superpotential equations can be assessed.
