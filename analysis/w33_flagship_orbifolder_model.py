#!/usr/bin/env python3
"""Write the recorded Z6-I W33 flagship as an orbifolder model file.

The six torus Wilson lines are represented as three geometric pairs.  The
recorded model has one order-three Wilson line W3.  Because the historical
analysis file froze V and W3 but not the original pair slot, this helper makes
that ambiguity explicit: --pair 01, 23, or 45.  The replay workflow runs all
three and accepts only the candidate reproducing the frozen flagship controls.

This file does not compute the spectrum; orbifolder 1.2.1 is the external
published spectrum engine. The historical scan now certifies --pair 45 as the
recorded flagship placement; the CI replay keeps the two shipped Z6-I geometry
files as the only remaining external ambiguity.
"""
from __future__ import annotations
import argparse
from fractions import Fraction as F
from pathlib import Path

V=tuple(F(x) for x in
"0,0,0,0,1/6,1/6,1/3,2/3,0,0,0,1/6,1/6,1/6,1/6,2/3".split(","))
W3=tuple(F(x) for x in
"-7/6,-5/6,-1/6,1/6,1/2,1/2,7/6,-1/6,-4/3,-2/3,1/3,-4/3,0,1/3,1,1/3".split(","))
ZERO=(F(0),)*16

def fmt(v):
    return " ".join(f"{x.numerator}/{x.denominator}" for x in v)

def write_model(path:Path, geometry:str, pair:str):
    if pair not in {"01","23","45"}:
        raise ValueError(pair)
    # Orbifolder model format: two gauge shifts followed by six Wilson lines.
    rows=[V,ZERO,ZERO,ZERO,ZERO,ZERO,ZERO,ZERO]
    i,j={"01":(2,3),"23":(4,5),"45":(6,7)}[pair]
    rows[i]=W3
    rows[j]=W3
    text=[
      "begin model",
      "Label:SM_20260917_3",
      f"SpaceGroup:{geometry}",
      "Lattice:E8xE8",
      "Shifts and Wilsonlines:",
      *[fmt(r) for r in rows],
      "end model",
      "",
    ]
    path.write_text("\n".join(text))
    print(path)
    print("geometry",geometry)
    print("pair",pair)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--geometry",required=True)
    ap.add_argument("--pair",choices=["01","23","45"],required=True)
    a=ap.parse_args()
    write_model(a.output,a.geometry,a.pair)

if __name__=="__main__":
    main()
