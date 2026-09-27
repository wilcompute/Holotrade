import importlib.util,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
S=importlib.util.spec_from_file_location("p",R/"analysis"/"w33_frame_bundle_three_k81_slices.py")
P=importlib.util.module_from_spec(S);S.loader.exec_module(P)
C=json.loads((R/"data"/"w33_frame_bundle_three_k81_slices.json").read_text())
def test_replay(): assert P.payload()==C
def test_three_k81_slices():
    assert [x["after_external_C3"]["dimension"] for x in C["three_slice_decomposition"]["slices"]]==[81,81,81]
    assert C["three_slice_decomposition"]["total_dimension"]==243
def test_mu12_intersection():
    assert C["mu12_compatibility"]["commuting_D12_powers"]==[0,4,8]
    assert C["checks"]["FI_fourth_power_is_scalar"]
