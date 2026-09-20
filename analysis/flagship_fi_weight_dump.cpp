#include <stdio.h>
#include <cstdlib>
#include "cprompt.h"
#include "cspectrum.h"
#include "canalysemodel.h"
using namespace std;
unsigned SELFDUALLATTICE;
int main(int argc, char *argv[])
{
  ifstream in(argv[1]);
  ostringstream devnull;
  CPrint Quiet(Tstandard, &devnull);
  string prog = "";
  COrbifoldGroup G;
  if (!G.LoadOrbifoldGroup(in, prog)) return 2;
  COrbifold O(G);
  vector<SConfig> cfg;
  bool bSM = true, bPS = false, bSU5 = false;
  CAnalyseModel A;
  A.AnalyseModel(O, O.StandardConfig, bSM, bPS, bSU5, cfg, Quiet, 3, false);
  if (!bSM || cfg.empty()) { cout << "noSM" << endl; return 3; }
  SConfig c = cfg[0];
  cout.precision(17);
  cout << "FI " << c.SymmetryGroup.IsFirstU1Anomalous << " " << c.SymmetryGroup.D0_FI_term << endl;
  for (unsigned a=0; a<c.SymmetryGroup.GaugeGroup.u1directions.size(); ++a) {
    cout << "U1 " << a;
    for (unsigned j=0; j<16; ++j) cout << " " << c.SymmetryGroup.GaugeGroup.u1directions[a][j];
    cout << endl;
  }
  unsigned L = c.use_Labels;
  const vector<CSector> &S = O.GetSectors();
  for (unsigned i = 0; i < c.Fields.size(); ++i)
  {
    const CField &F = c.Fields[i];
    string lb = F.Labels[L];
    // Dump every physical field, including singlets; do not infer missing states.
    const CSpaceGroupElement &g = F.SGElement;
    size_t nw = F.GetNumberOfLMWeights();
    for (size_t w = 0; w < nw; ++w)
    {
      const CVector &P = F.GetLMWeight(w, S);
      cout.precision(17); cout << "W " << lb << "_" << F.Numbers[L] << " k=" << g.Get_k() << " n=";
      for (unsigned t = 0; t < 6; ++t) cout << (t?",":"") << g.Get_n(t);
      cout << " q=";
      for (unsigned t = 0; t < F.q_sh.size(); ++t) cout << (t?",":"") << F.q_sh[t];
      cout << " osc=" << F.GetNumberOfOscillators(S);
      cout << " P=";
      for (unsigned t = 0; t < P.size(); ++t) cout << (t?",":"") << P[t];
      cout << endl;
    }
  }
  return 0;
}
