"""Pin the floating-point code paths of a level-2 run, so it gives the same numbers on every x86-64 CPU.

NumPy's matrix products go through OpenBLAS, which picks a kernel for the CPU it runs on (an AVX-512 kernel on one
machine, an AVX2 kernel on another), and NumPy picks its own vector loops the same way. The kernels round differently
in the last digit, and a walk on rough ground amplifies that: before this pin, the loaded downhill-20° terrain walk
reached a maximum tilt of 8.8° with the AVX-512 kernel and 5.0° with the AVX2 kernel, so the CI compare passed or
failed with the runner it landed on.

The pin forces one kernel and one thread for OpenBLAS, and turns NumPy's AVX-512 loops off. Every GitHub-hosted x86-64
runner has AVX2, so the pinned paths exist on all of them. The variables only take effect before NumPy loads, so a run
that was started without them starts itself again with them (`run_pinned`). MuJoCo's own code is compiled for one
instruction set and needs no pin. Other architectures (ARM) give their own numbers.
"""
from __future__ import annotations

import os
import subprocess
import sys

PIN = {
    "OPENBLAS_CORETYPE": "Haswell",                           # AVX2 + FMA kernel, whatever the CPU offers beyond it
    "OPENBLAS_NUM_THREADS": "1",                              # one thread: a fixed summation order
    "NPY_DISABLE_CPU_FEATURES": "X86_V4 AVX512_ICL AVX512_SPR",  # NumPy 2.5 names of its AVX-512 dispatch targets
}


def pinned() -> bool:
    return all(os.environ.get(k) == v for k, v in PIN.items())


def run_pinned(module: str, argv: list[str]) -> int | None:
    """None if this process is already pinned (carry on); otherwise run `python -m module argv` pinned, return its code."""
    if pinned():
        return None
    return subprocess.run([sys.executable, "-m", module, *argv], env={**os.environ, **PIN}).returncode
