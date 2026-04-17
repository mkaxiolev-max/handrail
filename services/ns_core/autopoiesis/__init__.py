"""Minimal Autopoiesis — compiler + ProgramRuntime + self-loop."""
from .initiatives import SEED_INITIATIVES
from .runtime import ProgramRuntime as AutopoeticRuntime

__all__ = ["SEED_INITIATIVES", "AutopoeticRuntime"]
