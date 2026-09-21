# Heterotic model-source provenance audit

The repository now separates recoverable model-defining data from the historical bulk-spectrum inputs that were never committed.

## Recoverable vector sets

Five explicit vector witnesses are frozen and replayable from Git:

1. the Z6-I flagship SM_20260917_3, with complete 16D V,W3 and vanishing W2;
2. the committed Z6-II Standard-Model witness SM_20260917_1383, with complete 16D V,W2,W3;
3. the explicit first-E8 Z6-II gauge-embedding witness from w33_z6ii_sm_shape_builder.json;
4. the published BHLR Z6-II benchmark representatives;
5. the orbifolder-shipped lattice-equivalent BHLR representatives.

The BHLR published and shipped representatives are checked to differ by E8 x E8 lattice vectors.

## Missing historical corpus

Three exact Git trees were inspected:

- hidden branch copilot/raw-z6-ii-model-corpus, commit 21f1dbf..., tree 6f6a888..., 1479 entries;
- D-flat-era commit 28620b4..., tree a5a4c448..., 1448 entries;
- D-flat-era commit 3e655d0..., tree 1dfa5d2d..., 1402 entries.

All three contain zero matches for sp1/, sp2/, and unbroken2.py. Those are precisely the paths referenced by the old bulk-flatness calculations. Therefore the historical 215-model spectrum corpus is not reproducible from Git alone.

This is a provenance result, not a physics no-go. Models can be regenerated where defining vectors survive, or the external raw corpus can be recovered separately. What is blocked is claiming a class-wide exact 215-model D/F-flatness replay from the repository as it currently exists.
