#!/usr/bin/env python3
"""Compare two raw float32 renders; exit 1 if they differ by more than 1e-5."""
import sys
from array import array

TOLERANCE = 1e-5


def load(path):
    a = array("f")
    with open(path, "rb") as f:
        a.frombytes(f.read())
    return a


a, b = load(sys.argv[1]), load(sys.argv[2])
if len(a) != len(b):
    print(f"FAIL length {len(a)} vs {len(b)}")
    sys.exit(1)

max_diff = 0.0
first_bad = None
peak = 0.0
for i, (x, y) in enumerate(zip(a, b)):
    d = abs(x - y)
    if d > max_diff:
        max_diff = d
    if d > TOLERANCE and first_bad is None:
        first_bad = i
    peak = max(peak, abs(x))

ok = max_diff <= TOLERANCE
msg = f"max diff {max_diff:.3e} (output peak {peak:.3f})"
if first_bad is not None:
    msg += f", first over tolerance at sample {first_bad}"
print(("ok   " if ok else "FAIL ") + msg)
sys.exit(0 if ok else 1)
